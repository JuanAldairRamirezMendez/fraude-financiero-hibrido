import { Link } from "react-router-dom";

import { EmptyState } from "@/components/ui/PageState";

interface ComingSoonPageProps {
  title: string;
  description: string;
}

export function ComingSoonPage({ title, description }: ComingSoonPageProps) {
  return (
    <EmptyState
      title={`${title} · Próximamente`}
      message={description}
      action={
        <Link className="button button-outline" to="/">
          Volver al overview
        </Link>
      }
    />
  );
}
