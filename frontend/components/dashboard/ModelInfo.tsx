"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Brain, RefreshCw, Database } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { FEATURE_LABELS } from "@/lib/constants";
import { apiUrl } from "@/lib/api";
import type { ModelInfo as ModelInfoType } from "@/lib/types";

interface ModelInfoProps {
  modelInfo: ModelInfoType | undefined;
  isLoading: boolean;
  onRetrained: () => void;
}

export default function ModelInfo({
  modelInfo,
  isLoading,
  onRetrained,
}: ModelInfoProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isRetraining, setIsRetraining] = useState(false);

  const handleRetrain = async () => {
    setIsRetraining(true);
    try {
      await fetch(apiUrl("/api/model/retrain"), { method: "POST" });
      onRetrained();
    } finally {
      setIsRetraining(false);
    }
  };

  if (isLoading || !modelInfo) {
    return (
      <Card className="bg-slate-900/80 border-slate-800">
        <CardContent className="p-5">
          <div className="h-6 w-48 bg-slate-800 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  const maxImportance = Math.max(...Object.values(modelInfo.feature_importances));

  const dataSourceLabel =
    modelInfo.data_source === "database" ? "Time Series DB" : "Legacy";

  return (
    <Card className="bg-slate-900/80 border-slate-800">
      <CardContent className="p-0">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between p-5 text-left hover:bg-slate-800/30 transition-colors rounded-xl"
        >
          <div className="flex items-center gap-3">
            <Brain className="h-5 w-5 text-violet-400" />
            <span className="font-semibold text-slate-200">
              Model Information
            </span>
            <span className="text-sm text-slate-500">
              Random Forest — {modelInfo.accuracy}% accuracy
            </span>
          </div>
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-5 w-5 text-slate-500" />
          </motion.div>
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="px-5 pb-5 space-y-5 border-t border-slate-800 pt-4">
                {/* Accuracy */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-400">Test Accuracy</span>
                    <span className="font-mono text-white">
                      {modelInfo.accuracy}%
                    </span>
                  </div>
                  <Progress value={modelInfo.accuracy} className="h-2" />
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="text-xs text-slate-500">Trees</div>
                    <div className="text-lg font-mono text-white">
                      {modelInfo.n_estimators}
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="text-xs text-slate-500">Max Depth</div>
                    <div className="text-lg font-mono text-white">
                      {modelInfo.max_depth}
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="text-xs text-slate-500">Samples</div>
                    <div className="text-lg font-mono text-white">
                      {modelInfo.training_samples}
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="text-xs text-slate-500">Features</div>
                    <div className="text-lg font-mono text-white">
                      {modelInfo.features.length}
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="text-xs text-slate-500 flex items-center gap-1">
                      <Database className="h-3 w-3" /> Data Source
                    </div>
                    <div className="text-sm font-mono text-white">
                      {dataSourceLabel}
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="text-xs text-slate-500">Observations</div>
                    <div className="text-lg font-mono text-white">
                      {modelInfo.observation_count?.toLocaleString() ?? "—"}
                    </div>
                  </div>
                </div>

                {/* Feature importances */}
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-3">
                    Feature Importance
                  </h4>
                  <div className="space-y-2.5">
                    {Object.entries(modelInfo.feature_importances)
                      .sort(([, a], [, b]) => b - a)
                      .map(([feature, importance]) => (
                        <div key={feature}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-400">
                              {FEATURE_LABELS[feature] || feature}
                            </span>
                            <span className="font-mono text-slate-300">
                              {(importance * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <motion.div
                              className="h-full bg-violet-500 rounded-full"
                              initial={{ width: 0 }}
                              animate={{
                                width: `${(importance / maxImportance) * 100}%`,
                              }}
                              transition={{ duration: 0.8, ease: "easeOut" }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Retrain button */}
                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs text-slate-600">
                    Last trained:{" "}
                    {modelInfo.training_timestamp
                      ? new Date(
                          modelInfo.training_timestamp
                        ).toLocaleString()
                      : "Unknown"}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRetrain}
                    disabled={isRetraining}
                    className="border-slate-700 text-slate-300 hover:bg-slate-800"
                  >
                    <RefreshCw
                      className={`h-3.5 w-3.5 mr-1.5 ${
                        isRetraining ? "animate-spin" : ""
                      }`}
                    />
                    {isRetraining ? "Retraining..." : "Retrain Model"}
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
