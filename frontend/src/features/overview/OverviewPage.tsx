import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { ErrorState, LoadingState } from "@/components/ui/PageState";
import { env } from "@/config/env";
import { isPending, useCasesQuery } from "@/features/cases/api";
import { EVALUATION } from "@/features/evaluation/data";
import { formatNumber } from "@/lib/format";
import { transactionTypeLabel, windowLabel } from "@/lib/labels";

import { HighRiskTable } from "./components/HighRiskTable";
import { KpiGrid } from "./components/KpiGrid";
import { FraudProfileChart } from "./components/FraudProfileChart";
import { useOverviewQuery } from "./hooks";

const ALL_TYPES = "all";
const TYPE_FILTERS = [ALL_TYPES, "online", "pos", "atm_withdrawal", "card_present_moto"] as const;

type TypeFilter = (typeof TYPE_FILTERS)[number];

const filterLabel = (filter: TypeFilter) =>
  filter === ALL_TYPES ? "Todos los tipos" : transactionTypeLabel(filter);

export default function OverviewPage() {
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<TypeFilter>(ALL_TYPES);
  const searchTerm = (searchParams.get("q") ?? "").trim().toLowerCase();
  // Mismo query que el contador del menú: los casos pendientes reales, en vivo.
  const cases = useCasesQuery(15_000);
  const {
    data,
    error,
    isError,
    isFetching,
    isPending: isLoading,
    refetch,
  } = useOverviewQuery({
    page: env.useMocks ? 1 : page,
    pageSize: 5,
    q: env.useMocks ? undefined : searchTerm || undefined,
    transactionType: env.useMocks || typeFilter === ALL_TYPES ? undefined : typeFilter,
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

  const filteredTransactions = data.transactions.filter((transaction) => {
    const matchesType = typeFilter === ALL_TYPES || transaction.type === typeFilter;
    const matchesSearch =
      searchTerm.length === 0 ||
      [transaction.id, transaction.customer, transaction.location, transaction.type].some((value) =>
        value.toLowerCase().includes(searchTerm),
      );
    return env.useMocks ? matchesType && matchesSearch : true;
  });
  const totalMatching = env.useMocks ? filteredTransactions.length : data.transactionPage.total;
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

      <Card className="chart-card overview-filters">
        <ChartHeader
          title="Transacciones del snapshot"
          subtitle={windowLabel(data.windowLabel)}
          actions={
            <button
              type="button"
              className="utility-button"
              onClick={() => void refetch()}
              disabled={isFetching}
            >
              {isFetching ? "Actualizando…" : "Actualizar"}
            </button>
          }
        />
        <div className="chart-toolbar">
          <div className="filter-chips" role="group" aria-label="Filtrar por tipo de transacción">
            {TYPE_FILTERS.map((filter) => (
              <button
                type="button"
                className={typeFilter === filter ? "active" : ""}
                onClick={() => {
                  setTypeFilter(filter);
                  setPage(1);
                }}
                aria-pressed={typeFilter === filter}
                key={filter}
              >
                {filterLabel(filter)}
              </button>
            ))}
          </div>
          <span>
            Mostrando {formatNumber(totalMatching)} de {formatNumber(data.totalTransactions)}{" "}
            transacciones procesadas
          </span>
        </div>
      </Card>

      <HighRiskTable
        transactions={filteredTransactions}
        pageInfo={env.useMocks ? undefined : data.transactionPage}
        onPageChange={env.useMocks ? undefined : setPage}
      />
    </>
  );
}
