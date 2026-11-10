import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Card } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/PageState";
import { apiRequest } from "@/lib/api/client";

type CaseStatus = "new" | "in_review" | "escalated" | "resolved";
type CaseVerdict = "confirmed_fraud" | "false_positive" | "inconclusive";

interface FraudCase {
  id: string;
  caseNumber: string;
  decisionId: string;
  status: CaseStatus;
  assignedTo: string | null;
  verdict: CaseVerdict | null;
  feedbackComment: string | null;
  createdAt: string;
  updatedAt: string;
  resolvedAt: string | null;
  notes: Array<{ author: string; content: string; createdAt: string }>;
}

interface CaseListResponse {
  items: FraudCase[];
  total: number;
}

const statusLabels: Record<CaseStatus, string> = {
  new: "Nuevo",
  in_review: "En revisión",
  escalated: "Escalado",
  resolved: "Resuelto",
};

const verdictLabels: Record<CaseVerdict, string> = {
  confirmed_fraud: "Fraude confirmado",
  false_positive: "Falso positivo",
  inconclusive: "Inconcluso",
};

export function CasesPage() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<CaseStatus | "">("");
  const [decisionId, setDecisionId] = useState("");
  const [selectedCase, setSelectedCase] = useState<FraudCase | null>(null);
  const [assignment, setAssignment] = useState("");
  const [verdict, setVerdict] = useState<CaseVerdict>("confirmed_fraud");
  const [comment, setComment] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  const casesQuery = useQuery({
    queryKey: ["cases", status],
    queryFn: () => apiRequest<CaseListResponse>(`/cases${status ? `?status=${status}` : ""}`),
  });

  const createMutation = useMutation({
    mutationFn: () => apiRequest<FraudCase>("/cases", {
      method: "POST",
      body: { decisionId, assignedTo: assignment || undefined },
    }),
    onSuccess: () => {
      setDecisionId("");
      setFeedback("Caso abierto correctamente.");
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => apiRequest<FraudCase>(`/cases/${selectedCase?.id}`, {
      method: "PATCH",
      body: {
        status: "resolved",
        verdict,
        feedbackComment: comment || undefined,
        assignedTo: assignment || undefined,
      },
    }),
    onSuccess: (updated) => {
      setSelectedCase(updated);
      setFeedback("Feedback guardado y caso resuelto.");
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });

  if (casesQuery.isPending) return <LoadingState label="Cargando casos antifraude…" />;
  if (casesQuery.isError) {
    return <ErrorState message={casesQuery.error.message} onRetry={() => void casesQuery.refetch()} />;
  }

  const items = casesQuery.data.items;

  return (
    <section className="info-page" aria-labelledby="cases-title">
      <p className="section-kicker">Investigation workflow</p>
      <h1 id="cases-title">Fraud Cases</h1>
      <p className="info-lead">Convierte una decisión del modelo en una revisión trazable.</p>

      <div className="info-grid">
        <Card className="info-card">
          <span>Abrir caso</span>
          <strong>Desde una decisión</strong>
          <label htmlFor="case-decision-id">Decision ID</label>
          <input
            id="case-decision-id"
            className="filter-input"
            value={decisionId}
            onChange={(event) => setDecisionId(event.target.value)}
            placeholder="DEC-..."
          />
          <label htmlFor="case-assignment">Asignar a</label>
          <input
            id="case-assignment"
            className="filter-input"
            value={assignment}
            onChange={(event) => setAssignment(event.target.value)}
            placeholder="analyst@example.com"
          />
          <button
            className="button button-primary"
            type="button"
            disabled={!decisionId.trim() || createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            Abrir caso
          </button>
        </Card>

        <Card className="info-card">
          <span>Feedback humano</span>
          <strong>{selectedCase ? selectedCase.caseNumber : "Selecciona un caso"}</strong>
          <label htmlFor="case-verdict">Veredicto</label>
          <select
            id="case-verdict"
            className="filter-select"
            value={verdict}
            onChange={(event) => setVerdict(event.target.value as CaseVerdict)}
            disabled={!selectedCase || selectedCase.status === "resolved"}
          >
            {Object.entries(verdictLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <label htmlFor="case-comment">Comentario</label>
          <textarea
            id="case-comment"
            className="filter-input"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Explica la evidencia revisada…"
            rows={3}
            disabled={!selectedCase || selectedCase.status === "resolved"}
          />
          <button
            className="button button-primary"
            type="button"
            disabled={!selectedCase || selectedCase.status === "resolved" || updateMutation.isPending}
            onClick={() => updateMutation.mutate()}
          >
            Guardar feedback
          </button>
        </Card>
      </div>

      <Card className="drift-card">
        <div className="chart-toolbar">
          <div>
            <span className="section-kicker">{casesQuery.data.total} casos</span>
            <h2>Cola de investigación</h2>
          </div>
          <select
            className="filter-select"
            aria-label="Filtrar casos por estado"
            value={status}
            onChange={(event) => setStatus(event.target.value as CaseStatus | "")}
          >
            <option value="">Todos los estados</option>
            {Object.entries(statusLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
        {feedback && <p className="chart-window" role="status">{feedback}</p>}
        {createMutation.isError && <p className="chart-window">{createMutation.error.message}</p>}
        {updateMutation.isError && <p className="chart-window">{updateMutation.error.message}</p>}
        {items.length === 0 ? (
          <p className="info-lead">No hay casos con este filtro.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr><th>Caso</th><th>Decisión</th><th>Estado</th><th>Asignado</th><th>Veredicto</th></tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className={selectedCase?.id === item.id ? "selected-row" : ""}>
                    <td><button className="table-link" type="button" onClick={() => setSelectedCase(item)}>{item.caseNumber}</button></td>
                    <td>{item.decisionId}</td>
                    <td>{statusLabels[item.status]}</td>
                    <td>{item.assignedTo ?? "Sin asignar"}</td>
                    <td>{item.verdict ? verdictLabels[item.verdict] : "Pendiente"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </section>
  );
}