


# KarachiFloodMLModel
**Live Flood‑Risk Prediction Using Machine Learning and the Open‑Meteo API**  
*A project developed for the Youth Innovation Challenge: Code for Climate at the IPN Summit (Houston, 2025).*

## Overview 
KarachiFloodMLModel is a Python package that predicts **live flood‑risk levels** in Karachi using a trained **Random Forest Machine‑Learning Model**.  

The model analyzes:  
- Atmospheric pressure  
- Precipitation  
- Relative humidity  
- Short‑term pressure trends  

It uses **hourly weather data** from the Open‑Meteo API and **historical flooding data from Karachi** to classify risk into:  
- **NORMAL**  
- **FLOOD WATCH**  
- **EMERGENCY WARNING**

This tool is designed for climate‑resilience projects, early‑warning systems, and real‑time monitoring dashboards.

## Installation

There are **two ways** to install the package:

### **1. Install via PyPI (recommended)**

Open your terminal (Windows PowerShell, macOS Terminal, or Linux shell) and enter:

```bash
pip install karachiFloodMLModel
```

The package and all dependencies will be installed automatically.

### **2. Install from the PyPI website**

1. Visit the project page:  
   https://pypi.org/project/karachiFloodMLModel/#files  
2. Download the `.whl` or `.tar.gz` file  
3. Install manually using:

```bash
pip install <filename>.whl
```

or

```bash
pip install <filename>.tar.gz
```

##  How It Works

1. The package fetches **live hourly weather data** from Open‑Meteo  
2. It extracts the required features:  
   - Surface pressure  
   - Precipitation  
   - Relative humidity  
3. It computes **pressure trend** from recent hours  
4. The Random Forest model processes the features  
5. It outputs:  
   - Flood‑risk label  
   - Confidence score  
   - Raw weather values used in the prediction  


##  Usage Example

```python
from karachiFloodMLModel import FloodPredictor

predictor = FloodPredictor()

result = predictor.get_live_flood_risk()

print("Flood Risk Level:", result["risk"])
print("Confidence:", result["confidence"])
print("Weather Data Used:", result["weather"])
```

**Sample Output:**

```
Flood Risk Level: FLOOD WATCH
Confidence: 0.82
Weather Data Used: {
    'pressure': 1004.2,
    'humidity': 78,
    'precipitation': 2.1,
    'pressure_trend': -1.3
}
```

##  API Requirements

The package automatically calls the **Open‑Meteo API** — no API key required.

If you want to use custom coordinates or override defaults:

```python
predictor = FloodPredictor(lat=24.8607, lon=67.0011)
```

## 🛠️ Troubleshooting

### **pip install fails**
Try upgrading pip:
```bash
pip install --upgrade pip
```

### **SSL or network errors**
Your network may block API calls. Try:
```python
predictor = FloodPredictor(ssl_verify=False)
```

**Model returns None**
This usually means the API returned incomplete data.  
Wait a few minutes and retry — Open‑Meteo updates hourly.

## Contributing

Pull requests are welcome!  
You can contribute by:  
- Improving model accuracy  
- Adding new features (e.g., rainfall intensity, wind speed)  
- Expanding support to other cities  
- Writing documentation or tests  





https://github.com/user-attachments/assets/b218c79b-476f-4a35-b55e-305940b4574b



