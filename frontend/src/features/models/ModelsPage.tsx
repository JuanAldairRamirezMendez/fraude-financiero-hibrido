import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { ErrorState, LoadingState } from "@/components/ui/PageState";
import { windowLabel } from "@/lib/labels";

import { AlertLog } from "./components/AlertLog";
import { DriftStats } from "./components/DriftStats";
import { StatusBanner } from "./components/StatusBanner";
import { useModelsQuery } from "./hooks";

export default function ModelsPage() {
  const { data, error, isError, refetch } = useModelsQuery();

  if (isError || !data) {
    if (isError) {
      return (
        <ErrorState
          message={error instanceof Error ? error.message : undefined}
          onRetry={() => void refetch()}
        />
      );
    }

    return <LoadingState label="Cargando salud de los modelos…" />;
  }

  return (
    <>
      <StatusBanner health={data.health} />

      <Card className="drift-card">
        <ChartHeader
          title="Análisis de deriva (concept drift): montos de transacción"
          subtitle="Compara la distribución de los datos actuales con la del entrenamiento. Un PSI mayor al umbral indica que el modelo podría necesitar reentrenarse."
        />
        <p className="chart-window">Ventana: {windowLabel(data.health.windowLabel)}</p>
        <DriftStats health={data.health} />
      </Card>

      <AlertLog alerts={data.alerts} />
    </>
  );
}
