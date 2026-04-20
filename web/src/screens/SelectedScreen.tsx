import { motion } from "framer-motion";
import { ScreenFrame } from "../components/ScreenFrame";
import type { Variant } from "../lib/api";
import { haptic, openTgLink, useMainButton } from "../lib/telegram";

interface Props {
  variant: Variant | undefined;
  sourceName: string;
  onAgain: () => void;
}

const CHANNEL_URL = "https://t.me/analiticada";

export function SelectedScreen({ variant, sourceName, onAgain }: Props) {
  useMainButton({
    text: "Подписаться на @analiticada",
    onClick: () => {
      haptic("light");
      openTgLink(CHANNEL_URL);
    },
  });

  return (
    <ScreenFrame keyName="selected">
      <motion.div
        className="pill"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
      >
        Выбор сохранён
      </motion.div>

      <motion.div
        className="selected-hero"
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
      >
        <p>Из «{sourceName}» получилось</p>
        <h1>{variant?.title ?? "—"}</h1>
        {variant?.rationale && (
          <p style={{ marginTop: 8 }}>{variant.rationale}</p>
        )}
      </motion.div>

      <motion.p
        className="subtitle"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        Готово — теперь нейминг точно пройдёт по духу закона о русском языке.
        Если любишь структурно смотреть на продукты, процессы и системы — у нас
        есть канал про системный анализ.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.28 }}
        style={{ display: "flex", flexDirection: "column", gap: 10 }}
      >
        <button
          type="button"
          className="primary-button"
          onClick={() => {
            haptic("light");
            openTgLink(CHANNEL_URL);
          }}
        >
          Подписаться на @analiticada
        </button>
        <button type="button" className="ghost-button" onClick={onAgain}>
          Сгенерировать ещё
        </button>
      </motion.div>
    </ScreenFrame>
  );
}
