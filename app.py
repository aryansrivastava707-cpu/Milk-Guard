from datetime import datetime
from pathlib import Path
import os
import uuid

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "milkguard_model.joblib"
HISTORY_PATH = BASE_DIR / "data" / "screening_history.csv"

app = Flask(__name__)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None


def get_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run: python train_model.py")
    return joblib.load(MODEL_PATH)


def calculate_gradual_risk(ph, tds, temperature):
    """Calculates risk proportionally instead of hardcoding 94%."""
    ph_risk = 0.0
    tds_risk = 0.0
    temp_risk = 0.0

    # pH Risk (Normal: 6.5 to 6.8)
    if ph < 6.5:
        ph_risk = min(max((6.5 - ph) / (6.5 - 5.0) * 100.0, 0.0), 100.0)
    elif ph > 6.8:
        ph_risk = min(max((ph - 6.8) / (8.5 - 6.8) * 100.0, 0.0), 100.0)

    # TDS Risk (Normal: 600 to 1200 ppm)
    if tds < 600:
        tds_risk = min(max((600.0 - tds) / (600.0 - 200.0) * 100.0, 0.0), 100.0)
    elif tds > 1200:
        tds_risk = min(max((tds - 1200.0) / (2500.0 - 1200.0) * 100.0, 0.0), 100.0)

    # Temperature Risk (Normal: <= 30.0°C)
    if temperature > 30.0:
        temp_risk = min(max((temperature - 30.0) / 15.0 * 100.0, 0.0), 100.0)

    # Weighted: 50% pH + 35% TDS + 15% Temp
    total_risk = (ph_risk * 0.50) + (tds_risk * 0.35) + (temp_risk * 0.15)
    return total_risk / 100.0  # Returns decimal probability (0.0 to 1.0)


def save_history(test_id, sample_id, ph, tds, temperature, result, probability):
    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = pd.DataFrame([{
        "test_id": test_id,
        "sample_id": sample_id,
        "time": test_time,
        "ph": ph,
        "tds": tds,
        "temperature": temperature,
        "result": result,
        "suspicious_probability": round(probability * 100, 1),
    }])
    row.to_csv(HISTORY_PATH, mode="a", index=False, header=not HISTORY_PATH.exists())
    if supabase:
        try:
            supabase.table("milk_tests").insert({
                "id": test_id, "sample_id": sample_id, "test_time": test_time,
                "ph": ph, "tds": tds, "temperature": temperature,
                "result": result, "suspicious_probability": round(probability * 100, 1),
            }).execute()
        except Exception as error:
            print("Supabase save failed:", error)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        values = request.get_json()
        ph = float(values["ph"])
        tds = float(values["tds"])
        temperature = float(values["temperature"])
        
        if not (0 <= ph <= 14 and 0 <= tds <= 5000 and -10 <= temperature <= 100):
            return jsonify(error="Please enter realistic sensor values."), 400

        reasons = []
        if ph < 6.50:
            reasons.append(f"Low pH ({ph}) - Acidic / Curdling risk")
        elif ph > 6.80:
            reasons.append(f"High pH ({ph}) - Abnormal alkaline adulterant")

        if tds > 1200:
            reasons.append(f"High TDS ({int(tds)} ppm) - Unnatural dissolved salts/solids")
        elif tds < 600:
            reasons.append(f"Low TDS ({int(tds)} ppm) - Diluted water detected")

        if temperature > 32.0:
            reasons.append(f"High Temperature ({temperature}°C) - Cold chain breakdown")

        # Dynamic calculated risk
        heuristic_probability = calculate_gradual_risk(ph, tds, temperature)

        # ML Model check
        try:
            model = get_model()
            features = pd.DataFrame([[ph, tds, temperature]], columns=["ph", "tds", "temperature"])
            ml_prob = float(model.predict_proba(features)[0][1])
            probability = max(heuristic_probability, ml_prob)
        except Exception:
            probability = heuristic_probability

        if probability >= 0.40:
            result = "SUSPICIOUS"
            reason_text = " • ".join(reasons) if reasons else "Parameters deviate from normal milk benchmarks."
        else:
            result = "NORMAL"
            reason_text = "All parameters (pH, TDS, Temperature) meet standard dairy benchmarks."

        test_id = str(uuid.uuid4())
        sample_id = str(values.get("sample_id") or f"MG-{test_id[:8].upper()}")[:40]
        save_history(test_id, sample_id, ph, tds, temperature, result, probability)

        report_url = request.url_root.rstrip("/") + f"/report/{test_id}"

        return jsonify(
            result=result, 
            suspicious_probability=round(probability * 100, 1),
            reason=reason_text,
            ph=ph,
            tds=tds,
            temperature=temperature,
            test_id=test_id, 
            sample_id=sample_id, 
            report_url=report_url
        )
    except (KeyError, TypeError, ValueError):
        return jsonify(error="pH, TDS and temperature must be numeric values."), 400
    except FileNotFoundError as error:
        return jsonify(error=str(error)), 500


@app.route("/latest")
def latest():
    if not HISTORY_PATH.exists():
        return jsonify(None)
    rows = pd.read_csv(HISTORY_PATH)
    if rows.empty:
        return jsonify(None)
    return jsonify(rows.iloc[-1].fillna("").to_dict())


@app.route("/report/<test_id>")
def report(test_id):
    record = None
    if supabase:
        try:
            record = supabase.table("milk_tests").select("*").eq("id", test_id).single().execute().data
        except Exception:
            record = None
    if record is None and HISTORY_PATH.exists():
        rows = pd.read_csv(HISTORY_PATH)
        found = rows[rows.get("test_id", pd.Series(dtype=str)).astype(str) == test_id]
        if not found.empty:
            record = found.iloc[-1].fillna("").to_dict()
    if record is None:
        return "Test record not found.", 404
    return render_template("report.html", record=record)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
