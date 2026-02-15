"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const SCENARIOS = ["normal", "watch", "emergency"] as const;
const CYCLE_INTERVAL = 8000;

export function useDemoMode() {
  const [isActive, setIsActive] = useState(false);
  const [scenario, setScenario] = useState<string | null>(null);
  const [isAutoCycling, setIsAutoCycling] = useState(false);
  const cycleIndexRef = useRef(0);

  const activate = useCallback((scenarioName: string) => {
    setIsActive(true);
    setScenario(scenarioName);
    setIsAutoCycling(false);
  }, []);

  const deactivate = useCallback(() => {
    setIsActive(false);
    setScenario(null);
    setIsAutoCycling(false);
    cycleIndexRef.current = 0;
  }, []);

  const startAutoCycle = useCallback(() => {
    setIsActive(true);
    setIsAutoCycling(true);
    cycleIndexRef.current = 0;
    setScenario(SCENARIOS[0]);
  }, []);

  const stopAutoCycle = useCallback(() => {
    setIsAutoCycling(false);
  }, []);

  useEffect(() => {
    if (!isAutoCycling) return;

    const interval = setInterval(() => {
      cycleIndexRef.current =
        (cycleIndexRef.current + 1) % SCENARIOS.length;
      setScenario(SCENARIOS[cycleIndexRef.current]);
    }, CYCLE_INTERVAL);

    return () => clearInterval(interval);
  }, [isAutoCycling]);

  return {
    isActive,
    scenario,
    isAutoCycling,
    activate,
    deactivate,
    startAutoCycle,
    stopAutoCycle,
    scenarios: SCENARIOS,
  };
}
