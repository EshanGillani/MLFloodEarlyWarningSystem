"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, AlertTriangle, AlertOctagon } from "lucide-react";
import { STATUS_CONFIG, type StatusKey } from "@/lib/constants";
import type { FloodPrediction } from "@/lib/types";

const ICONS = {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
};

function ConfidenceRing({ percentage }: { percentage: number }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center">
      <svg width="128" height="128" className="-rotate-90">
        <circle
          cx="64"
          cy="64"
          r={radius}
          stroke="rgba(255,255,255,0.15)"
          strokeWidth="8"
          fill="none"
        />
        <motion.circle
          cx="64"
          cy="64"
          r={radius}
          stroke="white"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          strokeDasharray={circumference}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <motion.span
          className="text-2xl font-bold text-white"
          key={percentage}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
        >
          {percentage.toFixed(0)}%
        </motion.span>
        <span className="text-xs text-white/60">Confidence</span>
      </div>
    </div>
  );
}

interface HeroAlertProps {
  prediction: FloodPrediction | null;
  lastUpdated: string | null;
  isLoading: boolean;
}

export default function HeroAlert({
  prediction,
  lastUpdated,
  isLoading,
}: HeroAlertProps) {
  const status = prediction?.status as StatusKey | undefined;
  const config = status ? STATUS_CONFIG[status] : STATUS_CONFIG["NORMAL"];
  const IconComponent = ICONS[config.icon];
  const isEmergency = status === "EMERGENCY WARNING";

  if (isLoading) {
    return (
      <div className="relative overflow-hidden rounded-2xl bg-slate-800/50 p-8 h-[200px] md:h-[260px] animate-pulse">
        <div className="h-8 w-48 bg-slate-700 rounded mb-4" />
        <div className="h-12 w-72 bg-slate-700 rounded mb-2" />
        <div className="h-4 w-40 bg-slate-700 rounded" />
      </div>
    );
  }

  return (
    <motion.div
      className={`relative overflow-hidden rounded-2xl p-6 md:p-8 bg-gradient-to-r ${config.gradient} ${
        isEmergency ? "animate-emergency-pulse" : ""
      }`}
      layout
      transition={{ duration: 0.8 }}
    >
      {isEmergency && (
        <div className="absolute inset-0 rounded-2xl border-2 border-red-400 animate-ping opacity-20" />
      )}

      <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-3">
            <IconComponent className="h-5 w-5 text-white/80" />
            <span className="text-sm font-medium text-white/80 uppercase tracking-wider">
              Flood Status
            </span>
          </div>

          <AnimatePresence mode="wait">
            <motion.h1
              key={status}
              className="text-3xl md:text-5xl font-bold text-white mb-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              {config.label}
            </motion.h1>
          </AnimatePresence>

          <p className="text-white/70 text-sm md:text-base">
            Karachi, Pakistan (24.86°N, 67.01°E)
          </p>
          {lastUpdated && (
            <p className="text-white/50 text-xs mt-1">
              Last updated: {new Date(lastUpdated).toLocaleTimeString()}
            </p>
          )}
        </div>

        {prediction && <ConfidenceRing percentage={prediction.confidence} />}
      </div>
    </motion.div>
  );
}
