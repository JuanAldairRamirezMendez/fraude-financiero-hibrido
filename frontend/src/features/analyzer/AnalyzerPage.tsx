import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/PageState";

import { RiskAssessmentPanel } from "./components/RiskAssessmentPanel";
import { ShapChart } from "./components/ShapChart";
import { TransactionForm } from "./components/TransactionForm";
import { useAnalyzeTransaction } from "./hooks";
import { useMetadataQuery } from "./metadata";

const EMPTY_ASSESSMENT = (
  <EmptyState
    title="Sin análisis todavía"
    message="Completa el formulario y pulsa Analyze Transaction para generar una evaluación."
  />
);

export default function AnalyzerPage() {
  const mutation = useAnalyzeTransaction();
  const metadata = useMetadataQuery();
  const lastInput = mutation.variables;

  return (
    <>
      <div className="analyzer-intro">
        <div>
          <h2 className="section-title">Analyze a transaction</h2>
          <p className="section-subtitle">
            Enter transaction attributes to generate a live fraud risk assessment.
          </p>
        </div>
        <Badge variant="success">
          <span className="badge-dot" aria-hidden="true" />
          {metadata.data ? `Model online · ${metadata.data.model.modelVersion}` : "Model online"}
        </Badge>
      </div>

      <div className="analyzer-grid">
        <Card className="input-panel">
          <ChartHeader title="Transaction Input" subtitle="Transaction and account details" />
          <TransactionForm
            isPending={mutation.isPending}
            onSubmit={(input) => mutation.mutate(input)}
          />
        </Card>

        <Card className="decision-panel" aria-live="polite">
          {mutation.isPending ? (
            <LoadingState label="Analizando transacción…" />
          ) : mutation.isError ? (
            <ErrorState
              title="No se pudo analizar la transacción"
              message="El servicio no respondió. Inténtalo de nuevo."
              onRetry={lastInput ? () => mutation.mutate(lastInput) : undefined}
            />
          ) : mutation.data ? (
            <RiskAssessmentPanel assessment={mutation.data} />
          ) : (
            EMPTY_ASSESSMENT
          )}
        </Card>

        {mutation.data && !mutation.isPending ? (
          <ShapChart assessment={mutation.data} />
        ) : (
          <Card className="shap-panel">
            <EmptyState
              title="Explicación pendiente"
              message="El desglose SHAP aparecerá cuando se complete un análisis."
            />
          </Card>
        )}
      </div>
    </>
  );
}
