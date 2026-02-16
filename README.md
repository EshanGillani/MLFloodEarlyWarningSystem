


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

## Demo
I've developed a front-end that's deployed (frontend through Vercel and backend through Railway)
You can visit it here: https://ml-flood-early-warning-system.vercel.app/

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
   - Map of area around the site.

## Contributing

Pull requests are welcome!  
You can contribute by:  
- Improving model accuracy  
- Adding new features (e.g., rainfall intensity, wind speed)  
- Expanding support to other cities  
- Writing documentation or tests  









