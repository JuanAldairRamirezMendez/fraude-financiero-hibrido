import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { ErrorState, LoadingState } from "@/components/ui/PageState";

import { AlertLog } from "./components/AlertLog";
import { DriftChart } from "./components/DriftChart";
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
          title="Concept Drift Analysis: Transaction Amounts"
          subtitle="Current production distribution compared with the original training dataset"
          actions={
            <div className="chart-actions">
              <div className="chart-legend">
                <span>
                  <i className="blue" />
                  Current data
                </span>
                <span>
                  <i className="cyan" />
                  Training data
                </span>
              </div>
            </div>
          }
        />
        <p className="chart-window">Window: {data.health.windowLabel}</p>
        <DriftStats health={data.health} />
        <DriftChart />
      </Card>

      <AlertLog alerts={data.alerts} />
    </>
  );
}
