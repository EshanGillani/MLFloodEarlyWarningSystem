# Karachi Flood Early Warning System

**Live Flood-Risk Prediction Using Machine Learning and the Open-Meteo API**
*A project developed for the Youth Innovation Challenge: Code for Climate at the IPN Summit (Houston, 2025).*
*Created by Eshan Gillani — [github.com/EshanGillani](https://github.com/EshanGillani)*

Predicts **live flood-risk levels** in Karachi using a trained **Random Forest** model. It pulls
hourly weather data (surface pressure, precipitation, relative humidity) from the
[Open-Meteo API](https://open-meteo.com/), computes a short-term pressure trend, and classifies
the current risk into:

- 🟢 **NORMAL**
- 🟡 **FLOOD WATCH**
- 🔴 **EMERGENCY WARNING**

---

## Requirements

- **Python 3.9+**
- The following packages:

```bash
pip install openmeteo-requests requests-cache retry-requests pandas numpy scikit-learn
```

(Open-Meteo is free and needs **no API key**.)

---

## Run it

Clone the repo and run the script:

```bash
git clone https://github.com/EshanGillani/MLFloodEarlyWarningSystem.git
cd MLFloodEarlyWarningSystem/src/package
python karachi_flood_monitor.py
```

On start it fetches recent Karachi weather, trains the model, and prints the **current
flood status** with the readings behind it:

```
Karachi Live Flood Monitoring System
------------------------------------------------------------
Model trained. Accuracy: 100.0%

============================================================
FLOOD STATUS: NORMAL
============================================================
Check Time (Local System): 2026-06-28 20:29:39.467191
Data Hour (UTC): 2026-06-28 20:00:00+00:00
Data Hour (Pakistan): 2026-06-29 01:00:00+00:00
Pressure: 1000.39
Rain: 0.0
Humidity: 77.2
Trend: -0.50
Confidence: 76.0%
============================================================
```

### Continuous monitoring (optional)

To keep checking on a fixed interval (and append new readings to `flood_log.csv`),
open `karachi_flood_monitor.py` and uncomment the last line:

```python
# for live monitoring every five minutes, uncomment below
monitor_flood_risk(check_interval_minutes=5)
```

Stop it any time with `Ctrl+C`.

---

## How it works

1. Fetches the past ~92 days of **hourly weather** from Open-Meteo and merges it with
   recorded pressure data from Karachi's 2025 floods.
2. Labels each hour (normal / watch / emergency) from precipitation + pressure thresholds,
   then balances the dataset with synthetic examples for each class.
3. Trains a `RandomForestClassifier` on four features: surface pressure, precipitation,
   humidity, and pressure trend.
4. Fetches the **current hour's** live weather and predicts the flood-risk label plus a
   confidence score.

---

## Contributing

Pull requests are welcome: improve model accuracy, add features (rainfall intensity, wind
speed), expand to other cities, or improve documentation and tests.
