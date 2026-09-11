# MilkGuard – Smart Milk Quality & Adulteration Detection System

MilkGuard is a beginner-friendly B.Tech mini-project. It accepts pH, TDS (or a conductivity-derived TDS value), and temperature readings, then uses **one machine-learning classification model** to display a screening result: **NORMAL** or **SUSPICIOUS**.

> Important: This is a classroom screening prototype. It cannot prove that a named adulterant is present, measure its amount, or replace a food-testing laboratory. Its ML output is only an indication based on the three entered readings.

## Project structure

```
milkguard/
├── app.py                         # Flask routes and prediction API
├── train_model.py                 # creates demo data and trains ONE model
├── requirements.txt
├── README.md
├── data/
│   ├── demo_samples.csv            # small set of values for testing
│   └── synthetic_milk_data.csv     # made after training; documented demo data
├── model/
│   └── milkguard_model.joblib      # saved after training
├── templates/index.html            # website page
├── static/style.css
├── static/script.js
└── esp32/esp32_example.ino         # optional future sensor connection
```

## How the demo dataset works

No real, labelled milk measurements were supplied for this project. Therefore `train_model.py` creates a synthetic/demo dataset of 300 readings with a fixed random seed. The labels are deliberately based on broad out-of-range patterns: unusually acidic pH, unusually high TDS, or unusual temperature. They are **not** evidence for any particular adulterant.

The model is a `RandomForestClassifier`. It is one model, trained with three input columns:

```
pH + TDS + temperature  →  one classifier  →  NORMAL / SUSPICIOUS
```

The printed accuracy is only performance against the artificial held-out data, so it must not be used as a real-world accuracy claim.

## Setup and run (Windows)

Open PowerShell inside the `milkguard` folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train_model.py
python app.py
```

Then open `http://127.0.0.1:5000` in a browser. Use the readings in `data/demo_samples.csv` to test the form.

If PowerShell blocks virtual-environment activation, run this once in that PowerShell window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## API and ESP32 connection

The page itself calls this Flask endpoint. The ESP32 can call the same endpoint; the dashboard checks for a newest reading every five seconds and displays it automatically:

```text
POST /predict
Content-Type: application/json
{"ph": 6.65, "tds": 310, "temperature": 27.0}
```

The response includes the label and its model probability. An optional ESP32 skeleton is at `esp32/esp32_example.ino`. Calibrate each sensor first, put both ESP32 and laptop on the same Wi-Fi network, change `serverUrl` to the laptop's local IP, and run Flask so that the network can reach it (for example change the final line of `app.py` to `app.run(host="0.0.0.0", debug=True)`). Do not expose this demo server to the public internet.

## Improving the project with real data

1. Collect readings from actual milk samples with calibrated sensors.
2. Have samples independently checked by a lab or established reference test.
3. Store `ph`, `tds`, `temperature`, and the independently determined `label` in a CSV.
4. Update `train_model.py` to load that CSV instead of calling `make_demo_data()`.
5. Retrain, keep a separate test set, and report limitations honestly.

## Make the website public (Render)

The project includes `render.yaml` for deployment. First create a GitHub account and upload this project folder to a new repository (do not upload `.venv`). Then:

1. Sign in to [Render](https://render.com/) using GitHub.
2. Click **New** → **Web Service** and select the MilkGuard GitHub repository.
3. Select the **Free** plan and click **Create Web Service**.
4. Render uses `pip install -r requirements.txt` to build and `gunicorn app:app` to start the app.
5. When deployment finishes, copy the `https://...onrender.com` URL and share it.

The free service can sleep after inactivity and takes a short time to wake up on the next visit. A public deployment is a demo site: do not store personal or sensitive test data in it.

## Suggested team division

| Member | Responsibility |
|---|---|
| 1 | ESP32 and sensor wiring/calibration |
| 2 | Data collection and model training |
| 3 | Flask website and API |
| 4 | Testing, report, poster and presentation |

## Short project explanation

MilkGuard takes three easy-to-measure milk parameters. The frontend sends them to a Python Flask backend. Flask passes the values to a saved Random Forest classification model. The backend returns a Normal/Suspicious screening label, shows it on the page, and saves the test in a small CSV history. In a later hardware version, ESP32 can send the same JSON readings directly to `/predict`.

## Viva points

1. **Why only one model?** One classifier can learn the combined effect of all three sensor readings. Separate models are unnecessary for this binary screening task.
2. **Why Random Forest?** It is understandable, works with small tabular datasets, and can learn simple non-linear boundaries.
3. **What are the inputs and output?** Inputs are pH, TDS and temperature; output is Normal or Suspicious.
4. **What does TDS indicate?** It is an indirect measure related to dissolved solids/conductivity; it is not an adulterant-specific test.
5. **Why temperature?** Sensor readings and milk handling can vary with temperature, so it adds context.
6. **What is synthetic data?** Artificial data created from stated assumptions for demonstrating the software pipeline. It is not experimental evidence.
7. **What is the limitation?** The system cannot name or quantify adulterants and needs labelled, calibrated real samples for validation.
8. **How will ESP32 connect?** It reads calibrated sensors and sends JSON over Wi-Fi to the Flask `/predict` endpoint.
