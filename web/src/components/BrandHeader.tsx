import { motion } from "framer-motion";

export function BrandHeader() {
  return (
    <motion.div
      className="brand-header"
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <span>Аналитикада · Нейминг</span>
    </motion.div>
  );
}
