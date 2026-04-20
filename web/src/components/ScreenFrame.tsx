import { motion, type Transition } from "framer-motion";
import type { ReactNode } from "react";

const DEFAULT_TRANSITION: Transition = { duration: 0.28, ease: [0.2, 0.8, 0.2, 1] };

interface Props {
  children: ReactNode;
  keyName: string;
}

export function ScreenFrame({ children, keyName }: Props) {
  return (
    <motion.div
      key={keyName}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={DEFAULT_TRANSITION}
      style={{ display: "flex", flexDirection: "column", gap: 16 }}
    >
      {children}
    </motion.div>
  );
}
