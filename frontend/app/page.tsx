"use client";

import { ShieldAlert, Radio } from "lucide-react";
import HeroAlert from "@/components/dashboard/HeroAlert";
import WeatherGauges from "@/components/dashboard/WeatherGauges";
import WeatherCharts from "@/components/dashboard/WeatherCharts";
import PredictionChart from "@/components/dashboard/PredictionChart";
import KarachiMap from "@/components/dashboard/KarachiMap";
import ModelInfo from "@/components/dashboard/ModelInfo";
import DemoControls from "@/components/dashboard/DemoControls";
import {
  useFloodData,
  usePredictionHistory,
  useWeatherObservations,
  useModelInfo,
} from "@/hooks/useFloodData";
import { useDemoMode } from "@/hooks/useDemoMode";

function LiveIndicator() {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
      </span>
      <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">
        Live
      </span>
    </div>
  );
}

export default function Dashboard() {
  const demo = useDemoMode();
  const { data, isLoading } = useFloodData(
    demo.isActive ? demo.scenario : null
  );
  const { history, isLoading: historyLoading } = usePredictionHistory();
  const { observations, isLoading: obsLoading } = useWeatherObservations(48);
  const {
    modelInfo,
    isLoading: modelLoading,
    refresh: refreshModel,
  } = useModelInfo();

  const weather = data?.weather ?? null;
  const prediction = data?.prediction ?? null;
  const lastUpdated = data?.last_updated ?? null;

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800/60 px-4 md:px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-7 w-7 text-blue-400" />
            <div>
              <h1 className="text-lg md:text-xl font-bold text-white">
                Karachi Flood Early Warning System
              </h1>
              <p className="text-xs md:text-sm text-slate-500">
                ML-Powered Real-Time Monitoring
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {demo.isActive && (
              <div className="flex items-center gap-1.5 text-violet-400">
                <Radio className="h-3.5 w-3.5 animate-pulse" />
                <span className="text-xs font-medium">DEMO</span>
              </div>
            )}
            {!demo.isActive && <LiveIndicator />}
          </div>
        </div>
      </header>

      {/* Dashboard content */}
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-6 space-y-5">
        {/* Row 1: Hero Alert */}
        <HeroAlert
          prediction={prediction}
          lastUpdated={lastUpdated}
          isLoading={isLoading}
        />

        {/* Row 2: Weather Gauges (4 cards) */}
        <WeatherGauges weather={weather} isLoading={isLoading} />

        {/* Row 3: Weather Time-Series Charts + Map */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2">
            <WeatherCharts observations={observations} isLoading={obsLoading} />
          </div>
          <KarachiMap
            status={prediction?.status ?? null}
            isLoading={isLoading}
          />
        </div>

        {/* Row 4: Prediction History */}
        <PredictionChart history={history} isLoading={historyLoading} />

        {/* Row 5: Model Info */}
        <ModelInfo
          modelInfo={modelInfo}
          isLoading={modelLoading}
          onRetrained={refreshModel}
        />
      </div>

      {/* Floating Demo Controls */}
      <DemoControls
        isActive={demo.isActive}
        scenario={demo.scenario}
        isAutoCycling={demo.isAutoCycling}
        onActivate={demo.activate}
        onDeactivate={demo.deactivate}
        onStartAutoCycle={demo.startAutoCycle}
        onStopAutoCycle={demo.stopAutoCycle}
      />
    </main>
  );
}
