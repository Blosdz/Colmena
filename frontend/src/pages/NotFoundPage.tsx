import { Link } from "react-router-dom";

import { EmptyState } from "../components/ui/EmptyState";

export function NotFoundPage() {
  return (
    <EmptyState
      title="Pagina no encontrada"
      description="La ruta solicitada no existe dentro del MVP actual de Colmena."
    >
      <Link className="inline-flex h-11 items-center justify-center rounded-2xl bg-surfaceSoft px-4 text-sm font-medium text-dark transition hover:bg-[#f9edd0]" to="/">
        Volver al dashboard
      </Link>
    </EmptyState>
  );
}
