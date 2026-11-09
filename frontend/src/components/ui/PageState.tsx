import type { ReactNode } from "react";

import { Icon } from "./Icon";

interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Cargando información…" }: LoadingStateProps) {
  return (
    <div className="page-state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "No se pudo cargar la información",
  message = "Revisa tu conexión e inténtalo de nuevo.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="page-state error-state" role="alert">
      <span className="state-icon" aria-hidden="true">
        <Icon name="alert" size={24} />
      </span>
      <h2>{title}</h2>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="button button-outline" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  message?: string;
  action?: ReactNode;
}

export function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="page-state empty-state">
      <span className="state-icon" aria-hidden="true">
        <Icon name="search" size={24} />
      </span>
      <h2>{title}</h2>
      {message && <p>{message}</p>}
      {action}
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="page-skeleton" role="status" aria-live="polite" aria-label="Cargando página">
      <div className="skeleton skeleton-kpis" />
      <div className="skeleton skeleton-chart" />
      <div className="skeleton skeleton-table" />
    </div>
  );
}
