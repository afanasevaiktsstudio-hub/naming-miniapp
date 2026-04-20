import { motion } from "framer-motion";
import { ScreenFrame } from "../components/ScreenFrame";
import type { Variant } from "../lib/api";
import { haptic, useMainButton } from "../lib/telegram";

interface Props {
  sourceName: string;
  variants: Variant[];
  onSelect: (variant: Variant) => void;
  onRegen: () => void;
}

export function VariantsScreen({ sourceName, variants, onSelect, onRegen }: Props) {
  useMainButton({
    text: "Хочу ещё варианты",
    onClick: () => {
      haptic("light");
      onRegen();
    },
  });

  return (
    <ScreenFrame keyName="variants">
      <motion.div
        className="pill"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {sourceName || "Варианты"}
      </motion.div>
      <h2 className="text-display hero-title">Выбери вариант</h2>
      <p className="subtitle">
        Тапни на карточку, если понравилось. Или попроси ещё 5 вариантов кнопкой снизу.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {variants.map((v, idx) => (
          <motion.button
            key={`${v.index}-${v.title}`}
            className="variant-card"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 + idx * 0.08, duration: 0.32 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              haptic("medium");
              onSelect(v);
            }}
          >
            <span className="variant-index">{idx + 1}</span>
            <span className="variant-body">
              <span className="variant-title">{v.title}</span>
              {(v.rationale || v.translit) && (
                <span className="variant-rationale">
                  {v.translit ? `(${v.translit}) ` : ""}
                  {v.rationale ?? ""}
                </span>
              )}
            </span>
          </motion.button>
        ))}
      </div>

      <button type="button" className="ghost-button" onClick={onRegen}>
        Попробовать ещё 5 вариантов
      </button>
    </ScreenFrame>
  );
}
