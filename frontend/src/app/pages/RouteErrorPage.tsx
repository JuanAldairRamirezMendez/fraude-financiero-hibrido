import { isRouteErrorResponse, useRouteError } from "react-router-dom";

export function RouteErrorPage() {
  const error = useRouteError();
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : "Ocurrió un error inesperado al cargar la ruta.";

  return (
    <div className="app-fallback" role="alert">
      <h1>No se pudo cargar la página</h1>
      <p>{message}</p>
      <a className="button button-primary" href="/">
        Volver al inicio
      </a>
    </div>
  );
}
