import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/PageState";
import { useAuth } from "@/app/auth/AuthContext";
import { env } from "@/config/env";

import { CASES_REFRESH_MS, isPending, useCasesQuery, type FraudCase } from "./api";
import { CaseDetail } from "./components/CaseDetail";
import { CaseQueue } from "./components/CaseQueue";

type Tab = "pending" | "resolved" | "all";

const TABS: ReadonlyArray<{ id: Tab; label: string }> = [
  { id: "pending", label: "Pendientes" },
  { id: "resolved", label: "Resueltos" },
  { id: "all", label: "Todos" },
];

function byTab(tab: Tab) {
  return (item: FraudCase) =>
    tab === "all" ? true : tab === "pending" ? isPending(item) : !isPending(item);
}

function summary(cases: readonly FraudCase[]) {
  const pending = cases.filter(isPending).length;
  const confirmed = cases.filter((item) => item.verdict === "confirmed_fraud").length;
  const released = cases.filter((item) => item.verdict === "false_positive").length;
  const reviewed = confirmed + released;
  return {
    pending,
    confirmed,
    released,
    hitRate: reviewed > 0 ? Math.round((confirmed / reviewed) * 100) : null,
  };
}

export function CasesPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tab, setTab] = useState<Tab>("pending");
  const query = useCasesQuery();

  if (env.useMocks) {
    return (
      <EmptyState
        title="La revisión de casos necesita el backend"
        message="Los casos se crean cuando el modelo real bloquea una transacción. Configura VITE_USE_MOCKS=false para usarla."
      />
    );
  }
  if (query.isPending) return <LoadingState label="Cargando las transacciones bloqueadas…" />;
  if (query.isError) {
    return <ErrorState message={query.error.message} onRetry={() => void query.refetch()} />;
  }

  const cases = query.data.items;
  const stats = summary(cases);
  const requested = searchParams.get("case");
  const requestedCase = cases.find((item) => item.id === requested);
  // Si llega un caso por enlace (desde el Analizador), se muestra aunque esté en otra pestaña.
  const activeTab: Tab = requestedCase && !byTab(tab)(requestedCase) ? "all" : tab;
  const visible = cases.filter(byTab(activeTab));
  const selected = requestedCase ?? visible[0] ?? null;

  function select(id: string) {
    setSearchParams({ case: id }, { replace: true });
  }

  return (
    <div className="cases-page">
      <div className="analyzer-intro">
        <div>
          <h2 className="section-title">Transacciones bloqueadas</h2>
          <p className="section-subtitle">
            Cada transacción que la IA bloquea llega aquí automáticamente. Un analista puede ver por
            qué se bloqueó, confirmar el fraude o liberarla si era legítima.
          </p>
        </div>
        <span className="live-refresh" title={`Se actualiza cada ${CASES_REFRESH_MS / 1000} s`}>
          <span aria-hidden="true" className={query.isFetching ? "is-fetching" : undefined} />
          En vivo
        </span>
      </div>

      <div className="eval-kpis cases-kpis">
        <Card className="eval-kpi">
          <span>Pendientes de revisión</span>
          <strong>{stats.pending}</strong>
          <em>Bloqueadas que nadie ha revisado aún</em>
        </Card>
        <Card className="eval-kpi">
          <span>Fraudes confirmados</span>
          <strong>{stats.confirmed}</strong>
          <em>El analista confirmó el bloqueo</em>
        </Card>
        <Card className="eval-kpi">
          <span>Liberadas</span>
          <strong>{stats.released}</strong>
          <em>Eran legítimas: se desbloquearon</em>
        </Card>
        <Card className="eval-kpi">
          <span>Acierto de la IA</span>
          <strong>{stats.hitRate === null ? "—" : `${stats.hitRate}%`}</strong>
          <em>De los bloqueos revisados, cuántos eran fraude</em>
        </Card>
      </div>

      {cases.length === 0 ? (
        <Card className="cases-empty">
          <EmptyState
            title="No hay transacciones bloqueadas"
            message="Cuando el modelo bloquee una transacción aparecerá aquí automáticamente. Prueba con el escenario «Sospechosa» o «Fraude probable» del Analizador."
            action={
              <Link className="button button-primary" to="/analyzer">
                Ir al Analizador
              </Link>
            }
          />
        </Card>
      ) : (
        <div className="cases-layout">
          <Card className="cases-queue-card">
            <div className="metric-toggle cases-tabs" role="group" aria-label="Filtrar casos">
              {TABS.map((item) => {
                const count = cases.filter(byTab(item.id)).length;
                return (
                  <button
                    key={item.id}
                    type="button"
                    aria-pressed={activeTab === item.id}
                    onClick={() => {
                      setTab(item.id);
                      setSearchParams({}, { replace: true });
                    }}
                  >
                    {item.label} <span className="tab-count">{count}</span>
                  </button>
                );
              })}
            </div>
            {visible.length === 0 ? (
              <p className="case-hint cases-queue-empty">
                {activeTab === "pending"
                  ? "No quedan casos pendientes. ¡Cola al día!"
                  : "Todavía no hay casos resueltos."}
              </p>
            ) : (
              <CaseQueue cases={visible} selectedId={selected?.id ?? null} onSelect={select} />
            )}
          </Card>

          <Card className="cases-detail-card">
            {selected ? (
              <CaseDetail
                key={selected.id}
                item={selected}
                currentUser={user?.username ?? "analista"}
              />
            ) : (
              <EmptyState
                title="Selecciona un caso"
                message="Elige un caso de la cola para revisarlo."
              />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
