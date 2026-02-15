export interface WeatherData {
  pressure: number;
  precipitation: number;
  humidity: number;
  temperature?: number;
  trend: number;
  timestamp: string;
  data_hour_utc: string;
  data_hour_pk: string;
}

export interface FloodPrediction {
  prediction: number;
  status: string;
  color: string;
  confidence: number;
}

export interface PredictionResponse {
  weather: WeatherData;
  prediction: FloodPrediction;
  last_updated: string;
}

export interface HistoryEntry {
  timestamp: string;
  pressure: number;
  precipitation: number;
  humidity: number;
  temperature?: number;
  trend: number;
  status: string;
  color: string;
  confidence: number;
}

export interface WeatherObservation {
  timestamp: string;
  pressure: number;
  precipitation: number;
  humidity: number;
  temperature: number | null;
}

export interface ModelInfo {
  accuracy: number;
  feature_importances: Record<string, number>;
  n_estimators: number;
  max_depth: number;
  training_timestamp: string | null;
  training_samples: number;
  features: string[];
  data_source: string;
  observation_count: number;
}

export interface DemoScenarioResponse {
  scenario: string;
  weather: WeatherData;
  prediction: FloodPrediction;
  last_updated: string;
}

export type AlertLevel = "normal" | "watch" | "emergency";
