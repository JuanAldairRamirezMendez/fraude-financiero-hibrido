import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { ErrorState, LoadingState } from "@/components/ui/PageState";
import { isPending, useCasesQuery } from "@/features/cases/api";
import { EVALUATION } from "@/features/evaluation/data";
import { formatNumber } from "@/lib/format";

import { FraudAnatomy } from "./components/FraudAnatomy";
import { FraudProfileChart } from "./components/FraudProfileChart";
import { KpiGrid } from "./components/KpiGrid";
import { useOverviewQuery } from "./hooks";

export default function OverviewPage() {
  // Mismo query que el contador del menú: los casos pendientes reales, en vivo.
  const cases = useCasesQuery(15_000);
  const {
    data,
    error,
    isError,
    isPending: isLoading,
    refetch,
  } = useOverviewQuery({
    page: 1,
    pageSize: 1,
  });

  if (isLoading) {
    return <LoadingState label="Cargando panel de transacciones…" />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  const caseItems = cases.data?.items;
  const kpis = caseItems
    ? data.kpis.map((kpi) => {
        if (kpi.id !== "pending-alerts") return kpi;
        const pending = caseItems.filter(isPending).length;
        const resolved = caseItems.length - pending;
        return {
          ...kpi,
          value: formatNumber(pending),
          trend: `${formatNumber(resolved)} resueltos · en vivo`,
        };
      })
    : data.kpis;

  return (
    <>
      <KpiGrid kpis={kpis} />

      <Card className="chart-card">
        <ChartHeader
          title="¿Dónde se concentra el fraude?"
          subtitle={`Tasa de fraude real en las ${formatNumber(EVALUATION.dataset.rows)} transacciones del dataset. En rojo, los grupos por encima del promedio.`}
        />
        <FraudProfileChart />
      </Card>

      <Card className="chart-card">
        <ChartHeader
          title="Anatomía de un fraude"
          subtitle="Compras reales de una tarjeta y el puntaje que el modelo dio a cada una: así detecta el fraude por el comportamiento, no por una compra aislada."
        />
        <FraudAnatomy />
      </Card>
    </>
  );
}
