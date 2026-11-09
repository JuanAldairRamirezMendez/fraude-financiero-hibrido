import { useState } from "react";

import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/PageState";
import { Pagination } from "@/components/ui/Pagination";
import { downloadCsv } from "@/lib/csv";
import { formatDateTime } from "@/lib/format";

import type { AlertStatus, ModelAlert } from "../types";

const PAGE_SIZE = 5;

const statusVariant: Record<AlertStatus, BadgeVariant> = {
  UNACKNOWLEDGED: "warning",
  ACKNOWLEDGED: "info",
  RESOLVED: "success",
};

const columns: ReadonlyArray<Column<ModelAlert>> = [
  {
    key: "occurredAt",
    header: "Timestamp",
    render: (alert) => formatDateTime(alert.occurredAt),
  },
  {
    key: "modelId",
    header: "Model ID",
    render: (alert) => <span className="model-id">{alert.modelId}</span>,
  },
  { key: "alertType", header: "Alert Type", render: (alert) => alert.alertType },
  { key: "detail", header: "Details", render: (alert) => alert.detail },
  {
    key: "status",
    header: "Status",
    render: (alert) => <Badge variant={statusVariant[alert.status]}>{alert.status}</Badge>,
  },
];

interface AlertLogProps {
  alerts: ReadonlyArray<ModelAlert>;
}

export function AlertLog({ alerts }: AlertLogProps) {
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);

  const filteredAlerts =
    statusFilter === "all" ? alerts : alerts.filter((alert) => alert.status === statusFilter);
  const pageCount = Math.max(1, Math.ceil(filteredAlerts.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visibleAlerts = filteredAlerts.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  function exportCsv() {
    downloadCsv("sentinelai-model-alerts.csv", [
      ["Timestamp", "Model ID", "Alert Type", "Details", "Status"],
      ...alerts.map((alert) => [
        alert.occurredAt,
        alert.modelId,
        alert.alertType,
        alert.detail,
        alert.status,
      ]),
    ]);
  }

  return (
    <Card className="table-card alert-log">
      <ChartHeader
        title="Alert Log"
        subtitle="Recent model performance and data quality events"
        actions={
          <div className="table-actions">
            <label className="sr-only" htmlFor="alert-status-filter">
              Filtrar alertas por estado
            </label>
            <select
              id="alert-status-filter"
              className="filter-select"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value);
                setPage(1);
              }}
            >
              <option value="all">All statuses</option>
              <option value="UNACKNOWLEDGED">Unacknowledged</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESOLVED">Resolved</option>
            </select>
            <button
              type="button"
              className="utility-button"
              onClick={exportCsv}
              disabled={alerts.length === 0}
            >
              Export report
            </button>
          </div>
        }
      />

      {filteredAlerts.length === 0 ? (
        <EmptyState
          title="Sin alertas para este filtro"
          message="Prueba con otro estado o vuelve a cargar la información."
        />
      ) : (
        <>
          <DataTable
            caption="Bitácora de alertas de modelos"
            columns={columns}
            rows={visibleAlerts}
            rowKey={(alert) => alert.id}
          />
          <Pagination
            page={safePage}
            pageCount={pageCount}
            totalItems={filteredAlerts.length}
            pageSize={PAGE_SIZE}
            label="model alerts"
            onPageChange={setPage}
          />
        </>
      )}
    </Card>
  );
}
