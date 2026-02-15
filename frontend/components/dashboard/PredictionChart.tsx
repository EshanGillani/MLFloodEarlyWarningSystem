"use client";

import { useEffect, useState } from "react";
import {
  ComposedChart,
  Area,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import type { HistoryEntry } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  NORMAL: "#10b981",
  "FLOOD WATCH": "#f59e0b",
  "EMERGENCY WARNING": "#ef4444",
};

function formatTime(timestamp: string) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

interface PredictionChartProps {
  history: HistoryEntry[] | undefined;
  isLoading: boolean;
}

export default function PredictionChart({
  history,
  isLoading,
}: PredictionChartProps) {
  const [tickCount, setTickCount] = useState(6);

  useEffect(() => {
    function handleResize() {
      setTickCount(window.innerWidth < 500 ? 3 : 6);
    }
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  if (isLoading || !history) {
    return (
      <Card className="bg-slate-900/80 border-slate-800">
        <CardContent className="p-5">
          <div className="h-6 w-48 bg-slate-800 rounded animate-pulse mb-4" />
          <div className="h-[300px] bg-slate-800/50 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  const chartData = history.map((entry) => ({
    ...entry,
    time: formatTime(entry.timestamp),
    statusColor: STATUS_COLORS[entry.status] || "#10b981",
    dotValue: entry.pressure,
  }));

  return (
    <Card className="bg-slate-900/80 border-slate-800">
      <CardContent className="p-5">
        <h3 className="text-base font-semibold text-slate-200 mb-4">
          Prediction History — Last 48 Hours
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.05)"
            />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              interval={Math.floor(chartData.length / tickCount)}
            />
            <YAxis
              yAxisId="pressure"
              orientation="left"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              domain={["dataMin - 5", "dataMax + 5"]}
              label={{
                value: "hPa",
                angle: -90,
                position: "insideLeft",
                style: { fill: "#64748b", fontSize: 11 },
              }}
            />
            <YAxis
              yAxisId="precip"
              orientation="right"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              domain={[0, "dataMax + 0.5"]}
              label={{
                value: "inches",
                angle: 90,
                position: "insideRight",
                style: { fill: "#64748b", fontSize: 11 },
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "8px",
                fontSize: 12,
              }}
              labelStyle={{ color: "#94a3b8" }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={((value: any, name: any) => {
                if (value == null) return ["-", name ?? ""];
                if (name === "precipitation") return [`${Number(value).toFixed(3)} in`, "Rain"];
                if (name === "pressure") return [`${Number(value).toFixed(1)} hPa`, "Pressure"];
                return [value, name ?? ""];
              }) as any}
            />
            <Legend
              wrapperStyle={{ fontSize: 12, color: "#94a3b8" }}
            />
            <Area
              yAxisId="precip"
              type="monotone"
              dataKey="precipitation"
              fill="rgba(34,211,238,0.15)"
              stroke="#22d3ee"
              strokeWidth={1.5}
              name="precipitation"
            />
            <Line
              yAxisId="pressure"
              type="monotone"
              dataKey="pressure"
              stroke="#94a3b8"
              strokeWidth={2}
              dot={false}
              name="pressure"
            />
            <Scatter
              yAxisId="pressure"
              dataKey="dotValue"
              name="status"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              shape={((props: any) => {
                const cx = props.cx as number;
                const cy = props.cy as number;
                const statusColor = props.payload?.statusColor as string;
                return (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={4}
                    fill={statusColor || "#10b981"}
                    stroke="none"
                  />
                );
              }) as any}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
