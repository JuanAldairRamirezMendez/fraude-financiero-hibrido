import { Link } from "react-router-dom";

import { EmptyState } from "@/components/ui/PageState";

export function NotFoundPage() {
  return (
    <EmptyState
      title="Página no encontrada"
      message="La ruta que buscas no existe o fue movida."
      action={
        <Link className="button button-outline" to="/">
          Ir al overview
        </Link>
      }
    />
  );
}
