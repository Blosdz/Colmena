import { Button } from "../ui/Button";
import { PrimaryAction } from "../ui/PrimaryAction";

export function WizardNavigation({
  canGoBack,
  canGoNext,
  backLabel = "Anterior",
  nextLabel = "Siguiente",
  onBack,
  onNext,
}: {
  canGoBack: boolean;
  canGoNext: boolean;
  backLabel?: string;
  nextLabel?: string;
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-5">
      <Button disabled={!canGoBack} onClick={onBack} variant="secondary">
        {backLabel}
      </Button>
      <PrimaryAction disabled={!canGoNext} onClick={onNext}>
        {nextLabel}
      </PrimaryAction>
    </div>
  );
}
