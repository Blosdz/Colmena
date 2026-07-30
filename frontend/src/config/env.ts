const fallbackApiBaseUrl = "http://127.0.0.1:8000";
const fallbackAppThesisSsoUrl = "http://localhost:5173/#/sso/colmena";

export const env = {
  apiBaseUrl: import.meta.env.VITE_COLMENA_API_BASE_URL?.trim() || fallbackApiBaseUrl,
  appThesisSsoUrl:
    import.meta.env.VITE_APPTHESIS_SSO_URL?.trim() || fallbackAppThesisSsoUrl,
  // Gateway público (AppThesis) que expone los formularios de Colmena como tenant.
  appThesisPublicUrl: import.meta.env.VITE_APPTHESIS_PUBLIC_URL?.trim() || "",
  tenantSlug: import.meta.env.VITE_COLMENA_TENANT_SLUG?.trim() || "colmena",
};

/** Construye el enlace público del formulario desde el .env (tenant en AppThesis). */
export function buildPublicFormUrl(publicSlug: string): string {
  if (env.appThesisPublicUrl) {
    const base = env.appThesisPublicUrl.replace(/\/+$/, "");
    return `${base}/#/${env.tenantSlug}/forms/${publicSlug}`;
  }
  // Fallback: servir desde el propio frontend de Colmena.
  return `${window.location.origin}/public/forms/${publicSlug}`;
}
