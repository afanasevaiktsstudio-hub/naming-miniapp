import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ScreenFrame } from "../components/ScreenFrame";
import { haptic, useMainButton } from "../lib/telegram";

interface Props {
  initialValue: string;
  error: string | null;
  onSubmit: (value: string) => void;
}

const MAX_LENGTH = 64;

export function InputScreen({ initialValue, error, onSubmit }: Props) {
  const [value, setValue] = useState(initialValue);
  const trimmed = value.trim();
  const canSubmit = trimmed.length >= 2 && trimmed.length <= MAX_LENGTH;

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  useMainButton(
    canSubmit
      ? {
          text: "Сгенерировать 5 вариантов",
          onClick: () => {
            haptic("medium");
            onSubmit(trimmed);
          },
        }
      : {
          text: "Введи название",
          onClick: () => undefined,
          active: false,
        }
  );

  const handleLocalSubmit = () => {
    if (!canSubmit) return;
    haptic("medium");
    onSubmit(trimmed);
  };

  return (
    <ScreenFrame keyName="input">
      <motion.h2
        className="text-display hero-title"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        Английское название ЖК
      </motion.h2>
      <p className="subtitle">
        Например, <em>Riverside</em>, <em>Skyline</em> или <em>Eco Village</em>.
        До {MAX_LENGTH} символов.
      </p>
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <input
          className="input-field"
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value.slice(0, MAX_LENGTH))}
          placeholder="Riverside, Skyline, Eco Village..."
          autoFocus
          autoComplete="off"
          spellCheck={false}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleLocalSubmit();
          }}
        />
        <div className="text-muted" style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{trimmed.length}/{MAX_LENGTH}</span>
          <span>Латиница, без спецсимволов лучше</span>
        </div>
        <button
          type="button"
          className="primary-button"
          disabled={!canSubmit}
          onClick={handleLocalSubmit}
        >
          Сгенерировать
        </button>
      </div>
      {error && (
        <motion.div
          className="error-banner"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {error}
        </motion.div>
      )}
    </ScreenFrame>
  );
}
