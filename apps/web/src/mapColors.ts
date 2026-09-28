export function moistureFill(value: number | null, threshold?: number | null): string {
  if (value == null) return "#c9c2b3";
  const line = threshold ?? 45;
  if (value < line) return "#b85a1a";
  if (value < line + 8) return "#c9a227";
  return "#2f6f54";
}

export function riskFill(level: string): string {
  if (level === "high") return "#b42318";
  if (level === "medium") return "#b86e12";
  return "#2f6f54";
}
