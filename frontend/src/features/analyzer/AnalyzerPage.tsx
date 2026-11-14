import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/PageState";

import { GroundTruthReveal } from "./components/GroundTruthReveal";
import { RiskAssessmentPanel } from "./components/RiskAssessmentPanel";
import { ShapChart } from "./components/ShapChart";
import { TransactionForm } from "./components/TransactionForm";
import { useAnalyzeTransaction } from "./hooks";
import { useMetadataQuery } from "./metadata";
import { updateAnalyzerSession, useAnalyzerSession } from "./session";

const EMPTY_ASSESSMENT = (
  <EmptyState
    title="Sin análisis todavía"
    message="Completa el formulario o elige un escenario y pulsa Analizar transacción."
  />
);

export default function AnalyzerPage() {
  const mutation = useAnalyzeTransaction();
  const metadata = useMetadataQuery();
  const lastInput = mutation.variables;
  // El último resultado se conserva al ir a Revisión de casos y volver.
  const [result] = useAnalyzerSession("result");
  const [analyzedSample] = useAnalyzerSession("analyzedSample");
  const analyze = (input: NonNullable<typeof lastInput>) =>
    mutation.mutate(input, { onSuccess: (data) => updateAnalyzerSession({ result: data }) });

  return (
    <>
      <div className="analyzer-intro">
        <div>
          <h2 className="section-title">Analizar una transacción</h2>
          <p className="section-subtitle">
            Ingresa los datos de la transacción para obtener una evaluación de riesgo en vivo.
          </p>
        </div>
        <Badge variant="success">
          <span className="badge-dot" aria-hidden="true" />
          {metadata.data
            ? `Modelo en línea · ${metadata.data.model.modelVersion}`
            : "Modelo en línea"}
        </Badge>
      </div>

      <div className="analyzer-grid">
        <Card className="input-panel">
          <ChartHeader
            title="Datos de la transacción"
            subtitle="Detalles de la operación y de la cuenta"
          />
          <TransactionForm
            isPending={mutation.isPending}
            onSubmit={(input, realSample) => {
              updateAnalyzerSession({ analyzedSample: realSample });
              analyze(input);
            }}
          />
        </Card>

        <Card className="decision-panel" aria-live="polite">
          {mutation.isPending ? (
            <LoadingState label="Analizando transacción…" />
          ) : mutation.isError ? (
            <ErrorState
              title="No se pudo analizar la transacción"
              message="El servicio no respondió. Inténtalo de nuevo."
              onRetry={lastInput ? () => analyze(lastInput) : undefined}
            />
          ) : result ? (
            <>
              <RiskAssessmentPanel assessment={result} />
              {analyzedSample && (
                <GroundTruthReveal sample={analyzedSample} decision={result.decision} />
              )}
            </>
          ) : (
            EMPTY_ASSESSMENT
          )}
        </Card>

        {result && !mutation.isPending ? (
          <ShapChart assessment={result} />
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
