/**
 * Брендовая палитра канала @analiticada.
 * Извлечена из аватарки (см. tools/extract_palette.py).
 * - Доминанты фона: серия тёмно-вишнёвых #1A0620..#3C0E25
 * - Акцент: тёплое золото (группа #997756 на аватарке)
 * - Текст: тёплый кремово-белый
 */
export const brand = {
  bg: "#140418",
  bgDeep: "#090209",
  surface: "#22082A",
  surfaceHi: "#320C36",
  border: "#4A1A44",
  primary: "#D1A66B",
  primaryHi: "#E8C889",
  accent: "#F4D487",
  text: "#FBF3E4",
  muted: "#A58BA8",
  danger: "#E06A6A",
  success: "#6BC289",
} as const;

export type BrandColor = keyof typeof brand;
