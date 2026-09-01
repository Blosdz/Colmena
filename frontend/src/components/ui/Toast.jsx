import { createContext, useCallback, useContext, useState } from 'react';
import { AlertTriangle, CheckCircle2, X } from 'lucide-react';

import { ApiError } from '../../api/client.js';
import { cn } from '../../utils/cn.js';

const ToastContext = createContext(null);

let nextId = 1;

/**
 * D-20: los errores del backend hoy quedan mudos — una mutación falla y el
 * usuario no ve nada. `ToastProvider` centraliza la notificación (éxito o
 * error) en un solo lugar en vez de que cada componente reimplemente su
 * propio manejo de error. `showApiError` lee el envelope de `ApiError`
 * (`message` + `body` con detalle extra) para ofrecer "ver detalle técnico".
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const show = useCallback(
    ({ tone = 'info', title, detail, technicalDetail, duration = 6000 }) => {
      const id = nextId++;
      setToasts((current) => [...current, { id, tone, title, detail, technicalDetail }]);
      if (duration) {
        setTimeout(() => dismiss(id), duration);
      }
      return id;
    },
    [dismiss],
  );

  const showApiError = useCallback(
    (error, fallbackTitle = 'No se pudo completar la acción') => {
      if (error instanceof ApiError) {
        const extra = { ...(error.body || {}) };
        delete extra.error_code;
        delete extra.message;
        const hasExtra = Object.keys(extra).length > 0;
        return show({
          tone: 'error',
          title: fallbackTitle,
          detail: error.message,
          technicalDetail: hasExtra ? JSON.stringify(extra, null, 2) : null,
        });
      }
      return show({ tone: 'error', title: fallbackTitle, detail: error?.message });
    },
    [show],
  );

  return (
    <ToastContext.Provider value={{ show, showApiError, dismiss }}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast debe usarse dentro de <ToastProvider>');
  }
  return context;
}

const TONE_STYLES = {
  error: { icon: AlertTriangle, className: 'border-danger/20 bg-white text-dark' },
  success: { icon: CheckCircle2, className: 'border-turquoise/20 bg-white text-dark' },
  info: { icon: AlertTriangle, className: 'border-border bg-white text-dark' },
};

function ToastViewport({ toasts, onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-[100] flex w-full max-w-sm flex-col gap-2.5">
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onDismiss={() => onDismiss(toast.id)} />
      ))}
    </div>
  );
}

function ToastCard({ toast, onDismiss }) {
  const [showTechnical, setShowTechnical] = useState(false);
  const { icon: Icon, className } = TONE_STYLES[toast.tone] || TONE_STYLES.info;
  const iconColor = toast.tone === 'error' ? 'text-danger' : toast.tone === 'success' ? 'text-turquoise' : 'text-amber';

  return (
    <div className={cn('pointer-events-auto animate-colmena-fade-in rounded-2xl border p-4 shadow-glass', className)}>
      <div className="flex items-start gap-3">
        <Icon size={18} className={cn('mt-0.5 shrink-0', iconColor)} />
        <div className="min-w-0 flex-1">
          {toast.title ? <p className="text-sm font-semibold text-dark">{toast.title}</p> : null}
          {toast.detail ? <p className="mt-0.5 text-sm text-muted">{toast.detail}</p> : null}
          {toast.technicalDetail ? (
            <button
              type="button"
              onClick={() => setShowTechnical((v) => !v)}
              className="mt-1.5 text-xs font-medium text-amber hover:underline"
            >
              {showTechnical ? 'Ocultar detalle técnico' : 'Ver detalle técnico'}
            </button>
          ) : null}
          {showTechnical ? (
            <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-surfaceSoft p-2 text-[11px] text-muted">
              {toast.technicalDetail}
            </pre>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded-lg p-1 text-muted transition hover:bg-black/5 hover:text-dark"
          aria-label="Cerrar notificación"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}

export default ToastProvider;
