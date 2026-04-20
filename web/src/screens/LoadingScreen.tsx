import { motion } from "framer-motion";
import { ScreenFrame } from "../components/ScreenFrame";

interface Props {
  label: string;
}

export function LoadingScreen({ label }: Props) {
  return (
    <ScreenFrame keyName="loading">
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 20,
          padding: "60px 0",
        }}
      >
        <motion.div
          className="loader-ring"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1.1, ease: "linear" }}
        />
        <motion.div
          className="subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 1.6 }}
          style={{ textAlign: "center" }}
        >
          {label}
        </motion.div>
        <SkeletonList />
      </div>
    </ScreenFrame>
  );
}

function SkeletonList() {
  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 10 }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <motion.div
          key={i}
          className="card"
          style={{
            height: 56,
            padding: 0,
            background:
              "linear-gradient(90deg, rgba(74,26,68,0.35) 0%, rgba(74,26,68,0.6) 50%, rgba(74,26,68,0.35) 100%)",
            backgroundSize: "200% 100%",
          }}
          animate={{ backgroundPositionX: ["0%", "200%"] }}
          transition={{
            repeat: Infinity,
            duration: 1.6,
            ease: "linear",
            delay: i * 0.08,
          }}
        />
      ))}
    </div>
  );
}
