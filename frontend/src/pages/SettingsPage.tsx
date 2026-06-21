import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Configuración"
        description="Aquí quedarán los ajustes generales del espacio de trabajo, la marca y los formatos de salida."
      />
      <EmptyState
        title="Configuración en preparación"
        description="La fase actual está centrada en el flujo del estudio. Los ajustes globales se integrarán después."
      />
    </div>
  );
}
