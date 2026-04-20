import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { useTelegramInit, getWebApp, hapticNotify } from "./lib/telegram";
import {
  fetchSession,
  requestVariants,
  selectVariant,
  type ApiError,
  type SessionState,
  type Variant,
} from "./lib/api";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import { InputScreen } from "./screens/InputScreen";
import { LoadingScreen } from "./screens/LoadingScreen";
import { VariantsScreen } from "./screens/VariantsScreen";
import { SelectedScreen } from "./screens/SelectedScreen";
import { BrandHeader } from "./components/BrandHeader";

type Stage = "welcome" | "input" | "loading" | "variants" | "selected";

const EMPTY_SESSION: SessionState = {
  source_name: null,
  variants: [],
  selected_index: null,
};

export function App() {
  useTelegramInit();

  const [stage, setStage] = useState<Stage>("welcome");
  const [session, setSession] = useState<SessionState>(EMPTY_SESSION);
  const [error, setError] = useState<string | null>(null);
  const [hydrating, setHydrating] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchSession()
      .then((s) => {
        if (cancelled) return;
        setSession(s);
        if (s.selected_index != null && s.variants.length) {
          setStage("selected");
        } else if (s.variants.length) {
          setStage("variants");
        }
      })
      .catch(() => {
        /* нет сессии — остаёмся на welcome */
      })
      .finally(() => !cancelled && setHydrating(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const handleStart = useCallback(() => {
    setStage("input");
  }, []);

  const handleSubmit = useCallback(async (value: string) => {
    setError(null);
    setStage("loading");
    try {
      const res = await requestVariants(value);
      setSession(res.session);
      setStage("variants");
    } catch (e) {
      const err = e as ApiError;
      hapticNotify("error");
      if (err.status === 429) {
        setError("Лимит на сегодня исчерпан. Возвращайся завтра.");
      } else if (err.status === 401) {
        setError("Открой мини-апп через кнопку в Telegram — нужен initData.");
      } else {
        setError(err.message || "Не удалось сгенерировать варианты.");
      }
      setStage("input");
    }
  }, []);

  const handleSelect = useCallback(async (variant: Variant) => {
    setError(null);
    try {
      const s = await selectVariant(variant.index);
      setSession(s);
      hapticNotify("success");
      setStage("selected");
    } catch (e) {
      const err = e as ApiError;
      hapticNotify("error");
      setError(err.message || "Не удалось сохранить выбор.");
    }
  }, []);

  const handleRegen = useCallback(() => {
    setError(null);
    setStage("input");
  }, []);

  const handleBack = useCallback(() => {
    setError(null);
    if (stage === "selected") setStage("variants");
    else if (stage === "variants") setStage("input");
    else if (stage === "input") setStage("welcome");
  }, [stage]);

  useEffect(() => {
    const wa = getWebApp();
    if (!wa) return;
    const back = wa.BackButton;
    if (stage === "welcome" || stage === "loading") {
      back.hide();
      return;
    }
    back.show();
    back.onClick(handleBack);
    return () => back.offClick(handleBack);
  }, [stage, handleBack]);

  const screen = useMemo(() => {
    if (hydrating) return <LoadingScreen label="Загружаю сессию..." />;
    switch (stage) {
      case "welcome":
        return <WelcomeScreen onStart={handleStart} />;
      case "input":
        return (
          <InputScreen
            initialValue={session.source_name ?? ""}
            error={error}
            onSubmit={handleSubmit}
          />
        );
      case "loading":
        return <LoadingScreen label="Генерирую 5 вариантов · 5–10 сек" />;
      case "variants":
        return (
          <VariantsScreen
            sourceName={session.source_name ?? ""}
            variants={session.variants}
            onSelect={handleSelect}
            onRegen={handleRegen}
          />
        );
      case "selected": {
        const picked =
          session.selected_index != null
            ? session.variants[session.selected_index]
            : undefined;
        return (
          <SelectedScreen
            variant={picked}
            sourceName={session.source_name ?? ""}
            onAgain={handleRegen}
          />
        );
      }
    }
  }, [
    hydrating,
    stage,
    session,
    error,
    handleStart,
    handleSubmit,
    handleSelect,
    handleRegen,
  ]);

  return (
    <div className="app-shell">
      <BrandHeader />
      <AnimatePresence mode="wait">{screen}</AnimatePresence>
    </div>
  );
}
