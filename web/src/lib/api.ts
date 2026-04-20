import { getWebApp } from "./telegram";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

export interface Variant {
  index: number;
  title: string;
  translit?: string;
  rationale?: string;
}

export interface SessionState {
  source_name: string | null;
  variants: Variant[];
  selected_index: number | null;
}

export interface VariantsResponse {
  variants: Variant[];
  session: SessionState;
}

export interface ApiError extends Error {
  status: number;
  code?: string;
}

function buildInitDataHeaders(): Record<string, string> {
  const wa = getWebApp();
  const initData = wa?.initData ?? "";
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (initData) headers["X-Telegram-Init-Data"] = initData;
  // dev-режим вне Telegram — backend подставит отладочного пользователя
  if (!initData && import.meta.env.DEV) headers["X-Debug-User"] = "1";
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...buildInitDataHeaders(),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    let code: string | undefined;
    let message = res.statusText || "Ошибка запроса";
    try {
      const data = await res.json();
      code = data?.code;
      message = data?.message ?? data?.detail ?? message;
    } catch {
      /* not json */
    }
    const err = new Error(message) as ApiError;
    err.status = res.status;
    err.code = code;
    throw err;
  }
  return (await res.json()) as T;
}

export function fetchSession(): Promise<SessionState> {
  return request<SessionState>("/api/session");
}

export function requestVariants(sourceName: string): Promise<VariantsResponse> {
  return request<VariantsResponse>("/api/variants", {
    method: "POST",
    body: JSON.stringify({ source_name: sourceName }),
  });
}

export function selectVariant(index: number): Promise<SessionState> {
  return request<SessionState>("/api/select", {
    method: "POST",
    body: JSON.stringify({ index }),
  });
}
