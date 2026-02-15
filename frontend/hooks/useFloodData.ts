"use client";

import useSWR from "swr";
import { fetcher, apiUrl } from "@/lib/api";
import type {
  PredictionResponse,
  HistoryEntry,
  ModelInfo,
  DemoScenarioResponse,
  WeatherObservation,
} from "@/lib/types";

export function useFloodData(demoScenario?: string | null) {
  const url = demoScenario
    ? apiUrl(`/api/demo/scenario/${demoScenario}`)
    : apiUrl("/api/predict");

  const { data, error, isLoading, mutate } = useSWR<
    PredictionResponse | DemoScenarioResponse
  >(url, fetcher, {
    refreshInterval: demoScenario ? 0 : 15000,
    revalidateOnFocus: true,
    dedupingInterval: 5000,
  });

  return { data, error, isLoading, refresh: mutate };
}

export function usePredictionHistory() {
  const { data, error, isLoading } = useSWR<HistoryEntry[]>(
    apiUrl("/api/predict/history?hours=48"),
    fetcher,
    { refreshInterval: 300000 }
  );
  return { history: data, error, isLoading };
}

export function useWeatherObservations(hours: number = 48) {
  const { data, error, isLoading } = useSWR<WeatherObservation[]>(
    apiUrl(`/api/weather/observations?hours=${hours}`),
    fetcher,
    { refreshInterval: 300000 }
  );
  return { observations: data, error, isLoading };
}

export function useModelInfo() {
  const { data, error, isLoading, mutate } = useSWR<ModelInfo>(
    apiUrl("/api/model/info"),
    fetcher,
    { revalidateOnFocus: false }
  );
  return { modelInfo: data, error, isLoading, refresh: mutate };
}
