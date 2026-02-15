"use client";

import { motion } from "framer-motion";
import { MapPin } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { STATUS_CONFIG, type StatusKey } from "@/lib/constants";

interface KarachiMapProps {
  status: string | null;
  isLoading: boolean;
}

export default function KarachiMap({ status, isLoading }: KarachiMapProps) {
  const statusKey = (status as StatusKey) || "NORMAL";
  const config = STATUS_CONFIG[statusKey] || STATUS_CONFIG["NORMAL"];
  const isEmergency = statusKey === "EMERGENCY WARNING";

  if (isLoading) {
    return (
      <Card className="bg-slate-900/80 border-slate-800">
        <CardContent className="p-5">
          <div className="h-6 w-32 bg-slate-800 rounded animate-pulse mb-4" />
          <div className="h-[300px] bg-slate-800/50 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-900/80 border-slate-800">
      <CardContent className="p-5">
        <h3 className="text-base font-semibold text-slate-200 mb-4">
          Karachi Risk Zone
        </h3>

        <div className="relative h-[300px] flex items-center justify-center overflow-hidden rounded-lg bg-slate-800/50">
          {/* Simplified Karachi map outline */}
          <svg
            viewBox="0 0 400 300"
            className="w-full h-full"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Background grid */}
            <defs>
              <pattern
                id="grid"
                width="20"
                height="20"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 20 0 L 0 0 0 20"
                  fill="none"
                  stroke="rgba(255,255,255,0.03)"
                  strokeWidth="0.5"
                />
              </pattern>
              <radialGradient id="alertGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={config.hex} stopOpacity="0.4" />
                <stop offset="100%" stopColor={config.hex} stopOpacity="0" />
              </radialGradient>
            </defs>

            <rect width="400" height="300" fill="url(#grid)" />

            {/* Karachi coastline (simplified) */}
            <motion.path
              d="M 60 180 Q 80 160, 120 155 Q 160 150, 200 145 Q 240 140, 280 150 Q 320 160, 340 180 L 340 220 Q 320 240, 280 250 Q 240 260, 200 255 Q 160 250, 120 240 Q 80 230, 60 210 Z"
              fill={config.hex}
              fillOpacity={0.15}
              stroke={config.hex}
              strokeWidth="2"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2, ease: "easeInOut" }}
              className={isEmergency ? "animate-pulse" : ""}
            />

            {/* City zones */}
            <circle cx="160" cy="185" r="15" fill={config.hex} fillOpacity="0.2" stroke={config.hex} strokeOpacity="0.4" strokeWidth="1" />
            <text x="160" y="210" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8">Saddar</text>

            <circle cx="220" cy="175" r="18" fill={config.hex} fillOpacity="0.25" stroke={config.hex} strokeOpacity="0.4" strokeWidth="1" />
            <text x="220" y="200" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8">Gulshan</text>

            <circle cx="280" cy="190" r="14" fill={config.hex} fillOpacity="0.2" stroke={config.hex} strokeOpacity="0.4" strokeWidth="1" />
            <text x="280" y="215" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8">Korangi</text>

            <circle cx="120" cy="190" r="12" fill={config.hex} fillOpacity="0.2" stroke={config.hex} strokeOpacity="0.4" strokeWidth="1" />
            <text x="120" y="212" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8">Clifton</text>

            <circle cx="190" cy="160" r="13" fill={config.hex} fillOpacity="0.2" stroke={config.hex} strokeOpacity="0.4" strokeWidth="1" />
            <text x="190" y="152" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8">N. Nazimabad</text>

            {/* Alert glow */}
            <circle cx="200" cy="190" r="80" fill="url(#alertGlow)" className={isEmergency ? "animate-pulse" : ""} />

            {/* Coordinate marker */}
            <circle cx="200" cy="190" r="4" fill="white" />
            <circle cx="200" cy="190" r="8" fill="none" stroke="white" strokeWidth="1" strokeOpacity="0.5" />

            {/* Label */}
            <text x="200" y="270" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="10">
              24.86°N, 67.01°E
            </text>

            {/* Ocean label */}
            <text x="200" y="290" textAnchor="middle" fill="rgba(56,189,248,0.3)" fontSize="9" fontStyle="italic">
              Arabian Sea
            </text>
          </svg>

          {/* Status badge */}
          <div className="absolute top-3 right-3 flex items-center gap-1.5">
            <MapPin className={`h-4 w-4 ${config.textColor}`} />
            <span className={`text-xs font-medium ${config.textColor}`}>
              {config.shortLabel}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
