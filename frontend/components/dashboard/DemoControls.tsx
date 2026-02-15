"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, Radio, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

interface DemoControlsProps {
  isActive: boolean;
  scenario: string | null;
  isAutoCycling: boolean;
  onActivate: (scenario: string) => void;
  onDeactivate: () => void;
  onStartAutoCycle: () => void;
  onStopAutoCycle: () => void;
}

const SCENARIO_BUTTONS = [
  { name: "normal", label: "Normal", color: "bg-emerald-600 hover:bg-emerald-500" },
  { name: "watch", label: "Flood Watch", color: "bg-amber-600 hover:bg-amber-500" },
  { name: "emergency", label: "Emergency", color: "bg-red-600 hover:bg-red-500" },
];

export default function DemoControls({
  isActive,
  scenario,
  isAutoCycling,
  onActivate,
  onDeactivate,
  onStartAutoCycle,
  onStopAutoCycle,
}: DemoControlsProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <AnimatePresence>
        {isActive ? (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl p-4 shadow-2xl w-[260px]"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Radio className="h-4 w-4 text-violet-400 animate-pulse" />
                <span className="text-sm font-medium text-white">
                  Demo Mode
                </span>
              </div>
              <button
                onClick={onDeactivate}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-2 mb-3">
              {SCENARIO_BUTTONS.map((btn) => (
                <button
                  key={btn.name}
                  onClick={() => onActivate(btn.name)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-white transition-all ${
                    btn.color
                  } ${
                    scenario === btn.name
                      ? "ring-2 ring-white/30 scale-[1.02]"
                      : "opacity-70 hover:opacity-100"
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>

            <div className="border-t border-slate-800 pt-3 space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full border-slate-700 text-slate-300 hover:bg-slate-800"
                onClick={isAutoCycling ? onStopAutoCycle : onStartAutoCycle}
              >
                {isAutoCycling ? (
                  <>
                    <Pause className="h-3.5 w-3.5 mr-1.5" />
                    Stop Auto-Cycle
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5 mr-1.5" />
                    Auto-Cycle (8s)
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <div
              onClick={() => onActivate("normal")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && onActivate("normal")}
              className="flex items-center gap-2 bg-slate-900/90 backdrop-blur-md border border-slate-700 rounded-full px-4 py-2.5 shadow-lg hover:bg-slate-800/90 transition-colors cursor-pointer"
            >
              <Switch checked={false} className="scale-75 pointer-events-none" />
              <span className="text-sm text-slate-300">Demo Mode</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
