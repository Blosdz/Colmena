import { PageHeader } from '../../components/layout/PageHeader.jsx';
import { EmptyState } from '../../components/ui/EmptyState.jsx';

export default function SettingsPage() {
  return (
    <div className="colmena-page">
      <PageHeader
        title="Configuración"
        description="Aquí quedarán los ajustes generales del espacio de trabajo, la marca y los formatos de salida."
      />
      <EmptyState
        title="Configuración en preparación"
        description="La fase actual está centrada en el flujo del proyecto. Los ajustes globales se integrarán después."
      />
    </div>
  );
}
