import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { ErrorState, LoadingState } from "@/components/ui/PageState";
import { env } from "@/config/env";
import { formatNumber } from "@/lib/format";

import { HighRiskTable } from "./components/HighRiskTable";
import { KpiGrid } from "./components/KpiGrid";
import { VolumeChart } from "./components/VolumeChart";
import { useOverviewQuery } from "./hooks";

const TYPE_FILTERS = ["All types", "online", "pos", "atm_withdrawal", "card_present_moto"] as const;

type TypeFilter = (typeof TYPE_FILTERS)[number];

export default function OverviewPage() {
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("All types");
  const searchTerm = (searchParams.get("q") ?? "").trim().toLowerCase();
  const { data, error, isError, isFetching, isPending, refetch } = useOverviewQuery({
    page: env.useMocks ? 1 : page,
    pageSize: 5,
    q: env.useMocks ? undefined : searchTerm || undefined,
    transactionType: env.useMocks || typeFilter === "All types" ? undefined : typeFilter,
  });

  if (isPending) {
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
    const matchesType = typeFilter === "All types" || transaction.type === typeFilter;
    const matchesSearch =
      searchTerm.length === 0 ||
      [transaction.id, transaction.customer, transaction.location, transaction.type].some((value) =>
        value.toLowerCase().includes(searchTerm),
      );
    return env.useMocks ? matchesType && matchesSearch : true;
  });
  const totalMatching = env.useMocks ? filteredTransactions.length : data.transactionPage.total;

  return (
    <>
      <KpiGrid kpis={data.kpis} />

      <Card className="chart-card">
        <ChartHeader
          title="Transaction Volume vs Fraud"
          subtitle={`${data.windowLabel} · Illustrative aggregate`}
          actions={
            <div className="chart-actions">
              <div className="chart-legend">
                <span>
                  <i className="blue" />
                  Transactions
                </span>
                <span>
                  <i className="red" />
                  Fraud events
                </span>
              </div>
              <button
                type="button"
                className="utility-button"
                onClick={() => void refetch()}
                disabled={isFetching}
              >
                {isFetching ? "Updating…" : "Refresh"}
              </button>
            </div>
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
                {filter}
              </button>
            ))}
          </div>
          <span>
            Showing {formatNumber(totalMatching)} of {formatNumber(data.totalTransactions)} processed
            transactions
          </span>
        </div>
        <VolumeChart />
      </Card>

      <HighRiskTable
        transactions={filteredTransactions}
        pageInfo={env.useMocks ? undefined : data.transactionPage}
        onPageChange={env.useMocks ? undefined : setPage}
      />
    </>
  );
}
