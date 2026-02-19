import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

type ThemeMode = "light" | "dark" | "system";
type ColorVariant = "slate" | "blue" | "emerald";

interface ThemeContextType {
  mode: ThemeMode;
  color: ColorVariant;
  setMode: (mode: ThemeMode) => void;
  setColor: (color: ColorVariant) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(
    () => (localStorage.getItem("theme-mode") as ThemeMode) || "system"
  );
  const [color, setColorState] = useState<ColorVariant>(
    () => (localStorage.getItem("theme-color") as ColorVariant) || "slate"
  );
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = window.document.documentElement;
    
    // Handle dark/light mode
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const shouldBeDark = mode === "dark" || (mode === "system" && systemPrefersDark);
    
    setIsDark(shouldBeDark);
    
    if (shouldBeDark) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    
    // Handle color variant
    root.classList.remove("theme-slate", "theme-blue", "theme-emerald");
    root.classList.add(`theme-${color}`);
  }, [mode, color]);

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      if (mode === "system") {
        const root = window.document.documentElement;
        if (mediaQuery.matches) {
          root.classList.add("dark");
          setIsDark(true);
        } else {
          root.classList.remove("dark");
          setIsDark(false);
        }
      }
    };
    
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mode]);

  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode);
    localStorage.setItem("theme-mode", newMode);
  };

  const setColor = (newColor: ColorVariant) => {
    setColorState(newColor);
    localStorage.setItem("theme-color", newColor);
  };

  return (
    <ThemeContext.Provider value={{ mode, color, setMode, setColor, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
