import { useState } from "react";

import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/PageState";
import { Pagination } from "@/components/ui/Pagination";
import { downloadCsv } from "@/lib/csv";
import { formatCurrency, formatDateTime } from "@/lib/format";
import { TRANSACTION_STATUS_LABELS, transactionTypeLabel } from "@/lib/labels";

import type { Transaction, TransactionPageInfo, TransactionStatus } from "../types";

const PAGE_SIZE = 5;

const statusVariant: Record<TransactionStatus, BadgeVariant> = {
  Flagged: "danger",
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
    header: "Fecha y hora",
    render: (transaction) =>
      transaction.occurredAt ? formatDateTime(transaction.occurredAt) : "Instantánea",
  },
  { key: "customer", header: "Cliente", render: (transaction) => transaction.customer },
  {
    key: "amount",
    header: "Monto",
    render: (transaction) => <span className="amount">{formatCurrency(transaction.amount)}</span>,
  },
  { key: "location", header: "Ubicación", render: (transaction) => transaction.location },
  { key: "type", header: "Tipo", render: (transaction) => transactionTypeLabel(transaction.type) },
  {
    key: "score",
    header: "Puntaje",
    render: (transaction) => <span className="risk-score">{transaction.score}</span>,
  },
  {
    key: "status",
    header: "Estado",
    render: (transaction) => (
      <Badge variant={statusVariant[transaction.status]}>
        {TRANSACTION_STATUS_LABELS[transaction.status] ?? transaction.status}
      </Badge>
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
      ["ID", "Fecha y hora", "Cliente", "Monto", "Ubicación", "Tipo", "Puntaje", "Estado"],
      ...transactions.map((transaction) => [
        transaction.id,
        transaction.occurredAt ?? "",
        transaction.customer,
        transaction.amount.toFixed(2),
        transaction.location,
        transactionTypeLabel(transaction.type),
        String(transaction.score),
        TRANSACTION_STATUS_LABELS[transaction.status] ?? transaction.status,
      ]),
    ]);
  }

  return (
    <Card className="table-card">
      <ChartHeader
        title="Transacciones recientes de alto riesgo"
        subtitle="Ordenadas de mayor a menor probabilidad de fraude. Desde el 24.7 % el modelo las bloquea."
        actions={
          <div className="table-actions">
            <button
              type="button"
              className="utility-button"
              onClick={exportCsv}
              disabled={transactions.length === 0}
            >
              Exportar CSV
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
            label="transacciones de alto riesgo"
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
