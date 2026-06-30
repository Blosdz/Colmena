import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";

import { router } from "./routes/router";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
);

// Hide the branded page loader once the app has mounted, keeping it visible
// for at least one full animation cycle so the honeycomb sequence plays through.
function hidePageLoader() {
  const loader = document.getElementById("page-loader");
  if (!loader) return;
  const MIN_VISIBLE_MS = 2400;
  const wait = Math.max(0, MIN_VISIBLE_MS - performance.now());
  window.setTimeout(() => {
    loader.classList.add("hidden");
    loader.addEventListener("transitionend", () => loader.remove(), { once: true });
  }, wait);
}

hidePageLoader();
