export {};

declare global {
  interface TelegramWebAppUser {
    id: number;
    first_name?: string;
    last_name?: string;
    username?: string;
    language_code?: string;
  }

  interface TelegramWebAppInitData {
    user?: TelegramWebAppUser;
    auth_date?: number;
    hash?: string;
  }

  interface TelegramHapticFeedback {
    impactOccurred: (
      style: "light" | "medium" | "heavy" | "rigid" | "soft"
    ) => void;
    notificationOccurred: (type: "error" | "success" | "warning") => void;
    selectionChanged: () => void;
  }

  interface TelegramMainButton {
    text: string;
    isVisible: boolean;
    isActive: boolean;
    show: () => void;
    hide: () => void;
    enable: () => void;
    disable: () => void;
    setText: (text: string) => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
    showProgress: (leaveActive?: boolean) => void;
    hideProgress: () => void;
  }

  interface TelegramBackButton {
    isVisible: boolean;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  }

  interface TelegramThemeParams {
    bg_color?: string;
    text_color?: string;
    hint_color?: string;
    link_color?: string;
    button_color?: string;
    button_text_color?: string;
    secondary_bg_color?: string;
  }

  interface TelegramWebApp {
    initData: string;
    initDataUnsafe: TelegramWebAppInitData;
    version: string;
    platform: string;
    colorScheme: "light" | "dark";
    themeParams: TelegramThemeParams;
    ready: () => void;
    expand: () => void;
    close: () => void;
    openLink: (url: string) => void;
    openTelegramLink: (url: string) => void;
    HapticFeedback: TelegramHapticFeedback;
    MainButton: TelegramMainButton;
    BackButton: TelegramBackButton;
    setHeaderColor: (color: string) => void;
    setBackgroundColor: (color: string) => void;
    isVersionAtLeast?: (v: string) => boolean;
  }

  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}
