import { apiClient } from "./client";
import type { ColmenaUser } from "../auth/session";

interface AppThesisLinkResponse {
  ok: boolean;
  user: ColmenaUser;
  linked: boolean;
}

export interface AuthTokenResponse {
  ok: boolean;
  token: string;
  user: ColmenaUser;
}

export const authApi = {
  /** Vincula la cuenta de Colmena a partir de un JWT emitido por AppThesis. */
  linkAppThesis(token: string) {
    return apiClient.post<AppThesisLinkResponse>("/api/v1/auth/appthesis", { token });
  },

  /** Alta de una cuenta standalone de Colmena. */
  register(payload: { name: string; email: string; password: string }) {
    return apiClient.post<AuthTokenResponse>("/api/v1/auth/register", payload);
  },

  /** Inicio de sesión con una cuenta standalone de Colmena. */
  login(payload: { email: string; password: string }) {
    return apiClient.post<AuthTokenResponse>("/api/v1/auth/login", payload);
  },

  /** Pide un enlace de recuperación. En desarrollo el backend devuelve `reset_url`. */
  requestPasswordReset(email: string) {
    return apiClient.post<{ ok: boolean; reset_url: string | null }>(
      "/api/v1/auth/password/reset-request",
      { email },
    );
  },

  /** Fija una nueva contraseña con el token del enlace y deja la sesión iniciada. */
  resetPassword(payload: { token: string; password: string }) {
    return apiClient.post<AuthTokenResponse>("/api/v1/auth/password/reset", payload);
  },
};
