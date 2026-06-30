import { apiClient } from "./client";
import type { ColmenaUser } from "../auth/session";

interface AppThesisLinkResponse {
  ok: boolean;
  user: ColmenaUser;
  linked: boolean;
}

export const authApi = {
  /** Vincula la cuenta de Colmena a partir de un JWT emitido por AppThesis. */
  linkAppThesis(token: string) {
    return apiClient.post<AppThesisLinkResponse>("/api/v1/auth/appthesis", { token });
  },
};
