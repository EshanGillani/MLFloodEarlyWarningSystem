export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const STATUS_CONFIG = {
  NORMAL: {
    label: "NORMAL",
    shortLabel: "Normal",
    gradient: "from-emerald-700 to-emerald-500",
    bgColor: "bg-emerald-500",
    textColor: "text-emerald-400",
    borderColor: "border-emerald-500",
    glowColor: "shadow-emerald-500/20",
    hex: "#10b981",
    icon: "ShieldCheck" as const,
  },
  "FLOOD WATCH": {
    label: "FLOOD WATCH",
    shortLabel: "Watch",
    gradient: "from-amber-700 to-amber-500",
    bgColor: "bg-amber-500",
    textColor: "text-amber-400",
    borderColor: "border-amber-500",
    glowColor: "shadow-amber-500/20",
    hex: "#f59e0b",
    icon: "AlertTriangle" as const,
  },
  "EMERGENCY WARNING": {
    label: "EMERGENCY WARNING",
    shortLabel: "Emergency",
    gradient: "from-red-700 to-red-500",
    bgColor: "bg-red-500",
    textColor: "text-red-400",
    borderColor: "border-red-500",
    glowColor: "shadow-red-500/50",
    hex: "#ef4444",
    icon: "AlertOctagon" as const,
  },
} as const;

export type StatusKey = keyof typeof STATUS_CONFIG;

export const FEATURE_LABELS: Record<string, string> = {
  surface_pressure: "Surface Pressure",
  precipitation: "Precipitation",
  humidity: "Humidity",
  temperature: "Temperature",
  pressure_trend: "Pressure Trend",
  pressure_trend_3h: "Pressure Trend (3h)",
  precip_rolling_6h: "Precip Rolling (6h)",
  precip_rolling_24h: "Precip Rolling (24h)",
  pressure_rolling_12h: "Pressure Rolling (12h)",
  humidity_rolling_6h: "Humidity Rolling (6h)",
};
