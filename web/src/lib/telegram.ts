import { useEffect, useMemo, useRef } from "react";

export function getWebApp(): TelegramWebApp | undefined {
  return typeof window !== "undefined" ? window.Telegram?.WebApp : undefined;
}

export function useTelegramInit(): TelegramWebApp | undefined {
  const webApp = useMemo(() => getWebApp(), []);

  useEffect(() => {
    if (!webApp) return;
    try {
      webApp.ready();
      webApp.expand();
      webApp.setHeaderColor("#140418");
      webApp.setBackgroundColor("#140418");
    } catch {
      /* вне Telegram — просто игнорируем */
    }
  }, [webApp]);

  return webApp;
}

export function haptic(
  kind: "light" | "medium" | "heavy" | "soft" | "rigid" = "light"
): void {
  try {
    getWebApp()?.HapticFeedback.impactOccurred(kind);
  } catch {
    /* no-op */
  }
}

export function hapticNotify(type: "success" | "error" | "warning"): void {
  try {
    getWebApp()?.HapticFeedback.notificationOccurred(type);
  } catch {
    /* no-op */
  }
}

export interface MainButtonConfig {
  text: string;
  onClick: () => void;
  visible?: boolean;
  active?: boolean;
  progress?: boolean;
}

export function useMainButton(config: MainButtonConfig | null): void {
  const savedCb = useRef<(() => void) | null>(null);

  useEffect(() => {
    const wa = getWebApp();
    if (!wa) return;
    const mb = wa.MainButton;

    if (!config) {
      mb.hide();
      if (savedCb.current) mb.offClick(savedCb.current);
      savedCb.current = null;
      return;
    }

    mb.setText(config.text);
    if (config.active === false) mb.disable();
    else mb.enable();

    if (config.progress) mb.showProgress(true);
    else mb.hideProgress();

    const handler = () => config.onClick();
    if (savedCb.current) mb.offClick(savedCb.current);
    mb.onClick(handler);
    savedCb.current = handler;

    if (config.visible !== false) mb.show();
    else mb.hide();

    return () => {
      mb.offClick(handler);
      if (savedCb.current === handler) savedCb.current = null;
    };
  }, [config]);
}

export function openTgLink(url: string): void {
  const wa = getWebApp();
  if (wa) {
    if (url.startsWith("https://t.me/") || url.startsWith("tg://")) {
      wa.openTelegramLink(url);
    } else {
      wa.openLink(url);
    }
  } else if (typeof window !== "undefined") {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}
