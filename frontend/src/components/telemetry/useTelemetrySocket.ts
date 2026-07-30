import { useEffect, useRef, useState } from "react";

import { env } from "../../config/env";

const MAX_RETRY_DELAY_MS = 30_000;
const EVENT_THROTTLE_MS = 1_000;

/**
 * Conecta al WebSocket de telemetría del backend de Colmena y llama a
 * `onEvent` cada vez que llega una respuesta nueva (con throttle para no
 * disparar refetch en ráfaga). Reintenta con backoff exponencial si se cae.
 *
 * Devuelve `true` mientras la conexión está viva: el caller puede usar eso
 * para apagar el polling de respaldo.
 */
export function useTelemetrySocket(
  formId: string | undefined,
  enabled: boolean,
  onEvent: () => void,
): boolean {
  const [connected, setConnected] = useState(false);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!formId || !enabled) {
      setConnected(false);
      return;
    }

    let socket: WebSocket | null = null;
    let disposed = false;
    let retryCount = 0;
    let retryTimer: number | undefined;
    let lastEventAt = 0;
    let trailingTimer: number | undefined;

    const wsBaseUrl = env.apiBaseUrl.replace(/^http/, "ws").replace(/\/+$/, "");

    const emitThrottled = () => {
      const now = Date.now();
      if (now - lastEventAt >= EVENT_THROTTLE_MS) {
        lastEventAt = now;
        onEventRef.current();
        return;
      }
      // Garantiza un refetch final tras una ráfaga de respuestas.
      if (trailingTimer === undefined) {
        trailingTimer = window.setTimeout(() => {
          trailingTimer = undefined;
          lastEventAt = Date.now();
          onEventRef.current();
        }, EVENT_THROTTLE_MS);
      }
    };

    const connect = () => {
      socket = new WebSocket(`${wsBaseUrl}/api/ws/telemetry/${formId}`);

      socket.onopen = () => {
        retryCount = 0;
        setConnected(true);
      };

      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data);
          if (event?.type === "response.submitted") {
            emitThrottled();
          }
        } catch {
          // mensaje no-JSON: ignorar
        }
      };

      socket.onclose = () => {
        setConnected(false);
        if (disposed) {
          return;
        }
        const delay = Math.min(MAX_RETRY_DELAY_MS, 1_000 * 2 ** retryCount);
        retryCount += 1;
        retryTimer = window.setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      disposed = true;
      window.clearTimeout(retryTimer);
      window.clearTimeout(trailingTimer);
      socket?.close();
      setConnected(false);
    };
  }, [formId, enabled]);

  return connected;
}
