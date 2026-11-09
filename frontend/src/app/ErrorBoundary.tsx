import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // En producción esto se envía a un servicio de observabilidad, nunca al usuario.
    console.error("Error de render no controlado", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="app-fallback" role="alert">
          <h1>Algo salió mal</h1>
          <p>Ocurrió un error inesperado en la interfaz.</p>
          <button
            type="button"
            className="button button-primary"
            onClick={() => window.location.reload()}
          >
            Recargar la página
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
