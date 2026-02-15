"use client";

import { motion } from "framer-motion";
import { Gauge, CloudRain, Droplets, Thermometer } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { WeatherData } from "@/lib/types";

interface GaugeCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  unit: string;
  color: string;
  min: number;
  max: number;
  thresholds?: { warn: number; danger: number };
}

function GaugeCard({
  icon,
  label,
  value,
  unit,
  color,
  min,
  max,
  thresholds,
}: GaugeCardProps) {
  const percentage = Math.min(
    100,
    Math.max(0, ((value - min) / (max - min)) * 100)
  );

  let barColor = color;
  if (thresholds) {
    if (value >= thresholds.danger) barColor = "bg-red-500";
    else if (value >= thresholds.warn) barColor = "bg-amber-500";
  }

  return (
    <Card className="bg-slate-900/80 border-slate-800">
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className={`p-2 rounded-lg bg-slate-800`}>{icon}</div>
          <span className="text-sm text-slate-400">{label}</span>
        </div>

        <motion.div
          className="text-3xl font-bold text-white mb-1 font-mono"
          key={value}
          initial={{ opacity: 0.5 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {typeof value === "number" ? value.toFixed(1) : "--"}
          <span className="text-base text-slate-500 ml-1">{unit}</span>
        </motion.div>

        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mt-3">
          <motion.div
            className={`h-full rounded-full ${barColor}`}
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>

        <div className="flex justify-between text-xs text-slate-600 mt-1">
          <span>{min}</span>
          <span>{max}</span>
        </div>
      </CardContent>
    </Card>
  );
}

interface WeatherGaugesProps {
  weather: WeatherData | null;
  isLoading: boolean;
}

export default function WeatherGauges({
  weather,
  isLoading,
}: WeatherGaugesProps) {
  if (isLoading || !weather) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-slate-900/80 border-slate-800">
            <CardContent className="p-5">
              <div className="h-6 w-24 bg-slate-800 rounded animate-pulse mb-3" />
              <div className="h-10 w-32 bg-slate-800 rounded animate-pulse mb-3" />
              <div className="h-2 bg-slate-800 rounded animate-pulse" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <GaugeCard
        icon={<Gauge className="h-5 w-5 text-blue-400" />}
        label="Surface Pressure"
        value={weather.pressure}
        unit="hPa"
        color="bg-blue-500"
        min={980}
        max={1020}
        thresholds={{ warn: 1005, danger: 1000 }}
      />
      <GaugeCard
        icon={<CloudRain className="h-5 w-5 text-cyan-400" />}
        label="Precipitation"
        value={weather.precipitation}
        unit="in"
        color="bg-emerald-500"
        min={0}
        max={3}
        thresholds={{ warn: 0.4, danger: 1.0 }}
      />
      <GaugeCard
        icon={<Thermometer className="h-5 w-5 text-orange-400" />}
        label="Temperature"
        value={weather.temperature ?? 0}
        unit="°C"
        color="bg-orange-500"
        min={15}
        max={50}
        thresholds={{ warn: 40, danger: 45 }}
      />
      <GaugeCard
        icon={<Droplets className="h-5 w-5 text-violet-400" />}
        label="Humidity"
        value={weather.humidity}
        unit="%"
        color="bg-violet-500"
        min={0}
        max={100}
      />
    </div>
  );
}
