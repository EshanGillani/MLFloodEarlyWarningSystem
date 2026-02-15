"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  AreaChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import type { WeatherObservation } from "@/lib/types";

function formatTime(timestamp: string) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(timestamp: string) {
  const date = new Date(timestamp);
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

const TOOLTIP_STYLE = {
  backgroundColor: "#1e293b",
  border: "1px solid #334155",
  borderRadius: "8px",
  fontSize: 12,
};

interface MiniChartProps {
  title: string;
  data: { time: string; value: number | null }[];
  color: string;
  fillColor: string;
  unit: string;
  domain?: [number | string, number | string];
  isArea?: boolean;
  tickCount: number;
}

function MiniChart({
  title,
  data,
  color,
  fillColor,
  unit,
  domain,
  isArea,
  tickCount,
}: MiniChartProps) {
  return (
    <Card className="bg-slate-900/80 border-slate-800">
      <CardContent className="p-4">
        <h4 className="text-sm font-medium text-slate-400 mb-3">{title}</h4>
        <ResponsiveContainer width="100%" height={160}>
          {isArea ? (
            <AreaChart data={data}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
              />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                tick={{ fontSize: 10 }}
                interval={Math.max(0, Math.floor(data.length / tickCount))}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 10 }}
                domain={domain}
                width={45}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={{ color: "#94a3b8" }}
                formatter={(value: number) => [
                  `${value != null ? Number(value).toFixed(3) : "-"} ${unit}`,
                  title,
                ]}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={color}
                fill={fillColor}
                strokeWidth={1.5}
              />
            </AreaChart>
          ) : (
            <LineChart data={data}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
              />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                tick={{ fontSize: 10 }}
                interval={Math.max(0, Math.floor(data.length / tickCount))}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 10 }}
                domain={domain}
                width={45}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={{ color: "#94a3b8" }}
                formatter={(value: number) => [
                  `${value != null ? Number(value).toFixed(1) : "-"} ${unit}`,
                  title,
                ]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

interface WeatherChartsProps {
  observations: WeatherObservation[] | undefined;
  isLoading: boolean;
}

export default function WeatherCharts({
  observations,
  isLoading,
}: WeatherChartsProps) {
  const [tickCount, setTickCount] = useState(6);

  useEffect(() => {
    function handleResize() {
      setTickCount(window.innerWidth < 500 ? 3 : 6);
    }
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  if (isLoading || !observations) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-slate-900/80 border-slate-800">
            <CardContent className="p-4">
              <div className="h-5 w-32 bg-slate-800 rounded animate-pulse mb-3" />
              <div className="h-[160px] bg-slate-800/50 rounded animate-pulse" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const chartData = observations.map((obs) => ({
    time: formatTime(obs.timestamp),
    date: formatDate(obs.timestamp),
    pressure: obs.pressure,
    precipitation: obs.precipitation,
    temperature: obs.temperature,
    humidity: obs.humidity,
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <MiniChart
        title="Pressure (hPa)"
        data={chartData.map((d) => ({ time: d.time, value: d.pressure }))}
        color="#3b82f6"
        fillColor="rgba(59,130,246,0.15)"
        unit="hPa"
        domain={["dataMin - 2", "dataMax + 2"]}
        tickCount={tickCount}
      />
      <MiniChart
        title="Precipitation (inches)"
        data={chartData.map((d) => ({
          time: d.time,
          value: d.precipitation,
        }))}
        color="#22d3ee"
        fillColor="rgba(34,211,238,0.15)"
        unit="in"
        domain={[0, "dataMax + 0.1"]}
        isArea
        tickCount={tickCount}
      />
      <MiniChart
        title="Temperature (°C)"
        data={chartData.map((d) => ({ time: d.time, value: d.temperature }))}
        color="#f97316"
        fillColor="rgba(249,115,22,0.15)"
        unit="°C"
        domain={["dataMin - 2", "dataMax + 2"]}
        tickCount={tickCount}
      />
      <MiniChart
        title="Humidity (%)"
        data={chartData.map((d) => ({ time: d.time, value: d.humidity }))}
        color="#8b5cf6"
        fillColor="rgba(139,92,246,0.15)"
        unit="%"
        domain={[0, 100]}
        tickCount={tickCount}
      />
    </div>
  );
}
