# MilkGuard – Milk Quality Screening Prototype

MilkGuard is a beginner-friendly B.Tech mini-project. It accepts pH, TDS (or a conductivity-derived TDS value), and temperature readings, then displays a screening result: **NORMAL** or **SUSPICIOUS**. The result currently comes from rule-based threshold checks on the three readings. A Random Forest model is trained in `train_model.py` on synthetic demo data, but it is not yet used by the `/predict` endpoint.

**Live demo:** https://milk-guard.onrender.com (free hosting, the first load can take up to a minute)

**Tech:** Python, Flask, Supabase, scikit-learn (training script), HTML/CSS/JavaScript

> Important: This is a classroom screening prototype. It cannot prove that a named adulterant is present, measure its amount, or replace a food-testing laboratory. Its output is only an indication based on the three entered readings.

## Project structure

```
Milk-Guard/
├── app.py                         # Flask routes, rule-based screening, history saving
├── train_model.py                 # creates demo data and trains a Random Forest (not used by /predict yet)
├── requirements.txt
├── render.yaml                    # Render deployment settings
├── supabase_setup.sql             # database table setup
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

## How the screening works

`/predict` compares the three readings with fixed dairy ranges and calculates a risk score:

- pH: 6.45 to 6.85
- TDS: 220 to 580 ppm
- Temperature: up to 30°C

If the risk score is below 45%, the result is NORMAL. Otherwise it is SUSPICIOUS, and the page lists the readings that were out of range. These ranges are simple project thresholds, not certified food-safety limits.

Each test is saved to a CSV history and, if Supabase is configured, to a `milk_tests` table. Every test also gets a report page at `/report/<test_id>`.

## The training script (demo only)

Note: this section describes `train_model.py`. The live app currently uses the rule-based checks above, not this model.

No real, labelled milk measurements were supplied for this project. Therefore `train_model.py` creates a synthetic/demo dataset of 300 readings with a fixed random seed. The labels are deliberately based on broad out-of-range patterns: unusually acidic pH, unusually high TDS, or unusual temperature. They are **not** evidence for any particular adulterant.

The model is a `RandomForestClassifier`:

```
pH + TDS + temperature  →  one classifier  →  NORMAL / SUSPICIOUS
```

The printed accuracy is only performance against the artificial held-out data, so it must not be used as a real-world accuracy claim.

## Setup and run (Windows)

Open PowerShell inside the `Milk-Guard` folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000` in a browser. Use the readings in `data/demo_samples.csv` to test the form.

To also run the training script, use `python train_model.py`.

Supabase is optional. To save tests there, run `supabase_setup.sql` in your Supabase project and set the `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` environment variables. Never put these keys in the code or commit them to GitHub.

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

The response includes the result label, the risk percentage and the reason. An optional ESP32 skeleton is at `esp32/esp32_example.ino`. Calibrate each sensor first, put both ESP32 and laptop on the same Wi-Fi network, change `serverUrl` to the laptop's local IP, and run Flask so that the network can reach it. Do not expose a local demo server to the public internet.

## Improving the project with real data

1. Collect readings from actual milk samples with calibrated sensors.
2. Have samples independently checked by a lab or established reference test.
3. Store `ph`, `tds`, `temperature`, and the independently determined `label` in a CSV.
4. Update `train_model.py` to load that CSV instead of calling `make_demo_data()`.
5. Retrain, keep a separate test set, connect the trained model to `/predict`, and report limitations honestly.
