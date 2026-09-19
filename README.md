# 🥛 MilkGuard – Smart Milk Quality Screening System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-RandomForest-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Hardware](https://img.shields.io/badge/IoT-ESP32%20Ready-E7352C?style=flat&logo=espressif&logoColor=white)](https://www.espressif.com/)

**MilkGuard** is an IoT and Machine Learning-based milk quality screening solution. It evaluates crucial physical parameters—**pH**, **TDS / Conductivity**, and **Temperature**—in real time to classify sample conditions into binary screening states: **NORMAL (PURE MILK)** or **SUSPICIOUS (ADULTERATED / SPOILED)**.

---

> ⚠️ **Disclaimer:** This system is engineered as an educational proof-of-concept / rapid screening prototype. It flags parameter deviations indicating spoilage or abnormal adulteration patterns, but does not replace standard laboratory food safety assays (e.g., FSSAI compliance testing).

---

## 📌 Key Capabilities

- **Real-Time Multi-Sensor Verification:** Continuous monitoring of chemical and physical thresholds (pH: 6.45–6.85, TDS: 220–580 ppm, Temp: ≤ 30°C).
- **Proportional Risk Evaluation:** Multi-layer scoring with critical overrides for extreme adulterant detection.
- **Dynamic Certificate & QR Generation:** Instant generation of public audit certificates and downloadable QR access codes for test verification.
- **RESTful Sensor Pipeline:** Seamless ESP32 wireless integration via JSON payload transmission over HTTP POST.

---

## 🏗️ System Architecture
