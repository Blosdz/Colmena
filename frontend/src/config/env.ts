const fallbackApiBaseUrl = "http://127.0.0.1:8000";
const fallbackAppThesisSsoUrl = "http://localhost:5173/#/sso/colmena";

export const env = {
  apiBaseUrl: import.meta.env.VITE_COLMENA_API_BASE_URL?.trim() || fallbackApiBaseUrl,
  appThesisSsoUrl:
    import.meta.env.VITE_APPTHESIS_SSO_URL?.trim() || fallbackAppThesisSsoUrl,
};
