import { motion } from "framer-motion";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

export default function ThemeToggle({ className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      aria-pressed={isDark}
      className={`focus-ring relative inline-flex h-8 w-14 items-center rounded-full border transition-colors duration-200 ${className}`}
      style={{
        backgroundColor: "var(--color-bg-sunken)",
        borderColor: "var(--color-border-strong)",
      }}
    >
      <motion.span
        layout
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        className="flex h-6 w-6 items-center justify-center rounded-full"
        style={{
          backgroundColor: "var(--color-accent)",
          marginLeft: isDark ? "calc(100% - 1.5rem - 2px)" : "2px",
        }}
      >
        {isDark ? (
          <Moon size={13} strokeWidth={2.25} color="var(--color-bg-elevated)" />
        ) : (
          <Sun size={13} strokeWidth={2.25} color="var(--color-bg-elevated)" />
        )}
      </motion.span>
    </button>
  );
}
