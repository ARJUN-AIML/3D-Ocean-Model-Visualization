# 🌊 OceanTwin 3D — Interactive Ocean Model & ML Bias Correction Platform

> **BluePulse — Advanced 3D Ocean Digital Twin & Machine Learning Fusion Engine**

![OceanTwin 3D Platform](https://img.shields.io/badge/OceanTwin%203D-v1.0%20Production-00f2fe?style=for-the-badge&logo=cesium&logoColor=white)
![Next.js 14](https://img.shields.io/badge/Next.js-14.2-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![CesiumJS](https://img.shields.io/badge/CesiumJS-1.120-2D7DD2?style=for-the-badge&logo=cesium&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0.3-FF6F00?style=for-the-badge&logo=xgboost&logoColor=white)
![Groq AI](https://img.shields.io/badge/Groq%20AI-LLM%20Engine-F34B7D?style=for-the-badge&logo=openai&logoColor=white)

---

## 📸 Executive Overview

**OceanTwin 3D** is a production-grade 3D Digital Twin oceanographic platform engineered to visualize, analyze, and correct numerical ocean model predictions in real time. Designed for ocean scientists, marine researchers, and maritime authorities (such as INCOIS), OceanTwin 3D pairs high-performance **CesiumJS 3D rendering** with **XGBoost machine learning bias correction** and **Groq LLM physics insights**.

---

## ✨ Key Features

### 🌊 1. INCOIS-Style Animated Current Particle Streamlines
- **2,000 High-Density Streamlines**: Renders dynamic, vector-driven current particles flowing across the Indian Ocean, Arabian Sea, and Bay of Bengal at 60 FPS.
- **Velocity-Colorized Gradient Trails**: Real-time speed gradients ranging from **Electric Cyan** ($<0.25 \text{ m/s}$) to **Azure Blue**, **Vibrant Amber**, and **Deep Coral Red** ($>0.85 \text{ m/s}$).

### 🗺️ 2. Dynamic 3D Ocean Surface Heatmap Overlays
- **Sea Surface Temperature (SST °C)**: Visualizes thermal zones from cold southern deeps ($<26.5^\circ\text{C}$) to Arabian warm pools and marine heatwaves ($>29.2^\circ\text{C}$).
- **Sea Surface Salinity (PSU)**: Photorealistic water color shifts from **Deep Royal Violet** ($36.0 - 38.5\text{ PSU}$ in the high-evaporation Arabian Sea) to **Electric Cyan** ($31.8 - 33.8\text{ PSU}$ in the river-fed Bay of Bengal).
- **Current Velocity (m/s)** & **Wave Swell Height (m)**: Contiguous surface overlays displaying wave heights ($1.0\text{m} - 5.0\text{m}$) and velocity intensity.

### 🤖 3. XGBoost Machine Learning Bias Correction
- **Model-Observation Fusion**: Trains gradient boosted decision trees on historical Argo float observations matched with numerical model outputs.
- **Spatiotemporal Residual Prediction**: Corrects systemic model errors for temperature and salinity across depth levels from **Surface (0m)** down to **2000m**.
- **Metrics Inspector**: Interactive dashboard displaying **MAE**, **RMSE**, **$R^2$ score**, and **Bias improvement percentage**.

### 🧠 4. Groq LLM Physics Insights Engine
- **Background `.env` API Integration**: Automatically queries Groq LLM models (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) when clicking any ocean location.
- **Context-Aware Oceanographic Analysis**: Translates SST, Salinity, surface currents, and XGBoost predictions into concise domain explanations without requiring manual UI configuration.

### 📍 5. Lagrangian Current Trajectory Drift Simulator
- Physical integration of surface $u, v$ current velocity vectors simulating floating object or spill drift paths over 6h, 12h, 24h, and 48h durations.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Frontend Framework** | **Next.js 14** (App Router) | React 18, TypeScript, Server & Client Components |
| **3D Geospatial Engine** | **CesiumJS 1.120** | WebGL Photorealistic 3D Globe, GPU Primitives, Canvas Particles |
| **Styling & UI** | **Tailwind CSS** | Navy Deep Glassmorphism Theme, Lucide Icons, Custom Design Tokens |
| **Backend API Bridge** | **FastAPI 0.110** | Async Python REST Server, CORS Middleware, OpenAPI Docs |
| **Machine Learning** | **XGBoost & Scikit-Learn** | Joblib Serialized Models, Feature Pipelines, NumPy & Pandas DataFrames |
| **AI LLM Inference** | **Groq API** | `llama-3.3-70b-versatile` & `llama-3.1-8b-instant` Sequential Fallback Engine |

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.10 or higher
- **Package Managers**: `npm` & `pip`

---

### 1. Repository Setup
```bash
git clone https://github.com/ARJUN-AIML/3D-Ocean-Model-Visualization.git
cd 3D-Ocean-Model-Visualization
```

### 2. Backend Setup & Startup
```bash
# Navigate to backend environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install required Python packages
pip install fastapi uvicorn xgboost joblib pandas numpy scikit-learn python-dotenv

# Create root .env file with your Groq API Key
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" >> .env

# Run FastAPI backend server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI interactive documentation will be available at **`http://localhost:8000/docs`**.

---

### 3. Frontend Setup & Startup
```bash
# Open a new terminal window inside the frontend folder
cd frontend

# Install dependencies
npm install

# Run Next.js development server
npm run dev
```
Open [**`http://localhost:3000`**](http://localhost:3000) in your browser to interact with the **OceanTwin 3D** platform.

---

## 📡 REST API Reference

| Endpoint | Method | Parameters | Description |
| :--- | :---: | :--- | :--- |
| `/api/health` | `GET` | — | Returns system status & provenance metadata |
| `/api/bias/predict` | `POST` | `targetVariable`, `depth`, `lat`, `lon` | Executes trained XGBoost bias-correction model |
| `/api/insight` | `GET` | `lat`, `lon`, `variable`, `depth` | Generates live AI insights using Groq API (`.env`) |
| `/api/observations` | `GET` | `instrument_type` | Returns live Argo float observation profiles |
| `/api/heatmap` | `GET` | `variable`, `mode`, `depth` | Fetches spatiotemporal model error points |
| `/api/trajectory` | `POST` | `startLat`, `startLon`, `durationHours` | Runs Lagrangian current particle drift simulation |
| `/api/validation/metrics` | `GET` | `variable` | Returns raw vs XGBoost corrected test metrics |

---

## 👥 Team BluePulse & Allies

OceanTwin 3D is developed and maintained by **Team BluePulse**:

| Member | Role | GitHub Profile |
| :--- | :--- | :--- |
| **Deepa Sri P** | Frontend Developer | [![GitHub](https://img.shields.io/badge/GitHub-dheepa92876--alt-181717?style=flat&logo=github)](https://github.com/dheepa92876-alt) |
| **Buvanesh Raj VS** | Full-Stack Developer | [![GitHub](https://img.shields.io/badge/GitHub-buvanesh080606-181717?style=flat&logo=github)](https://github.com/buvanesh080606) |
| **Arjun S** | Architect Developer | [![GitHub](https://img.shields.io/badge/GitHub-ARJUN--AIML-181717?style=flat&logo=github)](https://github.com/ARJUN-AIML) |
| **Nandhini V** | Data Engineer | [![GitHub](https://img.shields.io/badge/GitHub-NandhiniVR-181717?style=flat&logo=github)](https://github.com/NandhiniVR) |
| **Yuvan Sankar A** | Co-Developer | [![GitHub](https://img.shields.io/badge/GitHub-yuvan2103-181717?style=flat&logo=github)](https://github.com/yuvan2103) |
| **Jayadharshan S** | Co-Developer | [![GitHub](https://img.shields.io/badge/GitHub-jayadharshan332--sys-181717?style=flat&logo=github)](https://github.com/jayadharshan332-sys) |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. Built for scientific research, oceanographic digital twin modeling, and ML model validation.
