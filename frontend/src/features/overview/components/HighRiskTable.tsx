import { useState } from "react";

import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/PageState";
import { Pagination } from "@/components/ui/Pagination";
import { downloadCsv } from "@/lib/csv";
import { formatCurrency, formatDateTime } from "@/lib/format";

import type { Transaction, TransactionPageInfo, TransactionStatus } from "../types";

const PAGE_SIZE = 5;

const statusVariant: Record<TransactionStatus, BadgeVariant> = {
  Flagged: "warning",
  Review: "info",
  Approved: "success",
};

const columns: ReadonlyArray<Column<Transaction>> = [
  {
    key: "id",
    header: "ID",
    render: (transaction) => <span className="txn-id">{transaction.id}</span>,
  },
  {
    key: "occurredAt",
    header: "Timestamp",
    render: (transaction) =>
      transaction.occurredAt ? formatDateTime(transaction.occurredAt) : "Snapshot",
  },
  { key: "customer", header: "Customer", render: (transaction) => transaction.customer },
  {
    key: "amount",
    header: "Amount",
    render: (transaction) => <span className="amount">{formatCurrency(transaction.amount)}</span>,
  },
  { key: "location", header: "Location", render: (transaction) => transaction.location },
  { key: "type", header: "Type", render: (transaction) => transaction.type },
  {
    key: "score",
    header: "Score",
    render: (transaction) => <span className="risk-score">{transaction.score}</span>,
  },
  {
    key: "status",
    header: "Status",
    render: (transaction) => (
      <Badge variant={statusVariant[transaction.status]}>{transaction.status}</Badge>
    ),
  },
];

interface HighRiskTableProps {
  transactions: ReadonlyArray<Transaction>;
  pageInfo?: TransactionPageInfo;
  onPageChange?: (page: number) => void;
}

export function HighRiskTable({ transactions, pageInfo, onPageChange }: HighRiskTableProps) {
  const [page, setPage] = useState(1);
  const pageCount = pageInfo?.totalPages ?? Math.max(1, Math.ceil(transactions.length / PAGE_SIZE));
  const safePage = Math.min(pageInfo?.page ?? page, pageCount);
  const visibleTransactions = pageInfo
    ? transactions
    : transactions.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  function exportCsv() {
    downloadCsv("sentinelai-high-risk-transactions.csv", [
      ["ID", "Timestamp", "Customer", "Amount", "Location", "Type", "Score", "Status"],
      ...transactions.map((transaction) => [
        transaction.id,
        transaction.occurredAt ?? "",
        transaction.customer,
        transaction.amount.toFixed(2),
        transaction.location,
        transaction.type,
        String(transaction.score),
        transaction.status,
      ]),
    ]);
  }

  return (
    <Card className="table-card">
      <ChartHeader
        title="Recent High-Risk Transactions"
        subtitle="Transactions with a risk score above 80"
        actions={
          <div className="table-actions">
            <button
              type="button"
              className="utility-button"
              onClick={exportCsv}
              disabled={transactions.length === 0}
            >
              Export CSV
            </button>
          </div>
        }
      />
      {transactions.length === 0 ? (
        <EmptyState
          title="Sin transacciones de alto riesgo"
          message="Ninguna transacción coincide con los filtros seleccionados."
        />
      ) : (
        <>
          <DataTable
            caption="Transacciones recientes de alto riesgo"
            columns={columns}
            rows={visibleTransactions}
            rowKey={(transaction) => transaction.id}
          />
          <Pagination
            page={safePage}
            pageCount={pageCount}
            totalItems={pageInfo?.total ?? transactions.length}
            pageSize={pageInfo?.pageSize ?? PAGE_SIZE}
            label="high-risk transactions"
            onPageChange={(nextPage) => {
              setPage(nextPage);
              onPageChange?.(nextPage);
            }}
          />
        </>
      )}
    </Card>
  );
}
