import { motion } from "framer-motion";
import { ScreenFrame } from "../components/ScreenFrame";
import { haptic } from "../lib/telegram";

interface Props {
  onStart: () => void;
}

export function WelcomeScreen({ onStart }: Props) {
  return (
    <ScreenFrame keyName="welcome">
      <motion.div
        className="pill"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        ФЗ-53 · по-отечественному
      </motion.div>

      <motion.h1
        className="text-display hero-title"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
      >
        Русифицируй название ЖК — с размахом и иронией.
      </motion.h1>

      <motion.p
        className="subtitle"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
      >
        В РФ всё серьёзнее с русским языком в рекламе и вывесках. Давай
        пофантазируем, как могли бы звучать западные бренды «по-отечественному».
        Пришли английское название — верну 5 вариантов на русском.
      </motion.p>

      <motion.button
        type="button"
        className="primary-button"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        onClick={() => {
          haptic("light");
          onStart();
        }}
      >
        Начать
      </motion.button>
    </ScreenFrame>
  );
}
