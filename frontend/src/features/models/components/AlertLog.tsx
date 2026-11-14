import { useState } from "react";

import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/PageState";
import { Pagination } from "@/components/ui/Pagination";
import { downloadCsv } from "@/lib/csv";
import { formatDateTime } from "@/lib/format";
import { ALERT_STATUS_LABELS, ALERT_TYPE_LABELS, alertDetail } from "@/lib/labels";

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
    header: "Fecha y hora",
    render: (alert) => formatDateTime(alert.occurredAt),
  },
  {
    key: "modelId",
    header: "ID del modelo",
    render: (alert) => <span className="model-id">{alert.modelId}</span>,
  },
  {
    key: "alertType",
    header: "Tipo de alerta",
    render: (alert) => ALERT_TYPE_LABELS[alert.alertType] ?? alert.alertType,
  },
  { key: "detail", header: "Detalle", render: (alert) => alertDetail(alert.detail) },
  {
    key: "status",
    header: "Estado",
    render: (alert) => (
      <Badge variant={statusVariant[alert.status]}>
        {ALERT_STATUS_LABELS[alert.status] ?? alert.status}
      </Badge>
    ),
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
      ["Fecha y hora", "ID del modelo", "Tipo de alerta", "Detalle", "Estado"],
      ...alerts.map((alert) => [
        alert.occurredAt,
        alert.modelId,
        ALERT_TYPE_LABELS[alert.alertType] ?? alert.alertType,
        alertDetail(alert.detail),
        ALERT_STATUS_LABELS[alert.status] ?? alert.status,
      ]),
    ]);
  }

  return (
    <Card className="table-card alert-log">
      <ChartHeader
        title="Registro de alertas"
        subtitle="Eventos recientes de rendimiento del modelo y calidad de datos"
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
              <option value="all">Todos los estados</option>
              {Object.entries(ALERT_STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="utility-button"
              onClick={exportCsv}
              disabled={alerts.length === 0}
            >
              Exportar reporte
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
            label="alertas del modelo"
            onPageChange={setPage}
          />
        </>
      )}
    </Card>
  );
}
