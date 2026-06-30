import type { PropsWithChildren } from "react";
import { Navigate } from "react-router-dom";

import { isAuthenticated } from "./session";

export function RequireAuth({ children }: PropsWithChildren) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default RequireAuth;
