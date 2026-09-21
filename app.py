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
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def calculate_gradual_risk(ph, tds, temperature):
    """Calculates risk proportionally based on standard milk thresholds."""
    
    # Extreme Critical Override: extreme poison / spoiled levels
    if ph <= 4.5 or ph >= 10.0 or tds >= 1500 or temperature >= 65.0:
        return 1.0

    ph_risk = 0.0
    tds_risk = 0.0
    temp_risk = 0.0

    # pH Risk (Standard Normal: 6.45 to 6.85)
    if ph < 6.45:
        ph_risk = min(max((6.45 - ph) / (6.45 - 4.50) * 100.0, 0.0), 100.0)
    elif ph > 6.85:
        ph_risk = min(max((ph - 6.85) / (9.50 - 6.85) * 100.0, 0.0), 100.0)

    # TDS Risk (Standard Normal Fresh Milk: 220 to 580 ppm)
    if tds < 220.0:
        tds_risk = min(max((220.0 - tds) / (220.0 - 50.0) * 100.0, 0.0), 100.0)
    elif tds > 580.0:
        tds_risk = min(max((tds - 580.0) / (1200.0 - 580.0) * 100.0, 0.0), 100.0)

    # Temperature Risk (Standard Normal: <= 30.0°C)
    if temperature > 30.0:
        temp_risk = min(max((temperature - 30.0) / 25.0 * 100.0, 0.0), 100.0)

    max_individual_risk = max(ph_risk, tds_risk, temp_risk)
    weighted_risk = (ph_risk * 0.45) + (tds_risk * 0.40) + (temp_risk * 0.15)
    
    final_risk = max(weighted_risk, max_individual_risk)
    return round(final_risk / 100.0, 3)


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
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
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
        values = request.get_json(silent=True) or {}
        ph = float(values["ph"])
        tds = float(values["tds"])
        temperature = float(values["temperature"])
        
        if not (0 <= ph <= 14 and 0 <= tds <= 5000 and -10 <= temperature <= 100):
            return jsonify(error="Please enter realistic sensor values."), 400

        reasons = []
        # Correct Indian Milk Standards (pH 6.45 - 6.85, TDS 220 - 580 ppm, Temp <= 30°C)
        if ph < 6.45:
            reasons.append(f"Low pH ({ph:.2f}) - Acidic / Curdling risk")
        elif ph > 6.85:
            reasons.append(f"High pH ({ph:.2f}) - Alkaline neutralizer / adulterant")

        if tds < 220:
            reasons.append(f"Low TDS ({int(tds)} ppm) - Diluted water detected")
        elif tds > 580:
            reasons.append(f"High TDS ({int(tds)} ppm) - Added salts / chemical adulterants")

        if temperature > 30.0:
            reasons.append(f"High Temperature ({temperature:.1f}°C) - Cold chain breakdown")

        heuristic_probability = calculate_gradual_risk(ph, tds, temperature)

        # ML Model prediction (fallback seamlessly to heuristic if model is absent)
        try:
            model = get_model()
            if model is not None:
                features = pd.DataFrame([[ph, tds, temperature]], columns=["ph", "tds", "temperature"])
                ml_prob = float(model.predict_proba(features)[0][1])
                # Agar saare parameters range ke andar hain, toh synthetic model ki false alert ignore hogi
                if len(reasons) == 0:
                    probability = min(heuristic_probability, 0.10)
                else:
                    probability = max(heuristic_probability, ml_prob)
            else:
                probability = heuristic_probability
        except Exception:
            probability = heuristic_probability

        # Final decision: Agar koi reason nahi mila aur prob < 0.40 hai toh NORMAL
        if len(reasons) == 0 and probability < 0.40:
            result = "NORMAL"
            reason_text = "All parameters (pH, TDS, Temperature) meet standard dairy benchmarks."
        else:
            result = "SUSPICIOUS"
            reason_text = " • ".join(reasons) if reasons else "Parameters deviate from normal milk benchmarks."

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
    except Exception as error:
        return jsonify(error=str(error)), 500


@app.route("/latest")
def latest():
    if not HISTORY_PATH.exists():
        return jsonify(None)
    try:
        rows = pd.read_csv(HISTORY_PATH)
        if rows.empty:
            return jsonify(None)
        return jsonify(rows.iloc[-1].fillna("").to_dict())
    except Exception:
        return jsonify(None)


@app.route("/report/<test_id>")
def report(test_id):
    record = None
    if supabase:
        try:
            record = supabase.table("milk_tests").select("*").eq("id", test_id).single().execute().data
        except Exception:
            record = None
    if record is None and HISTORY_PATH.exists():
        try:
            rows = pd.read_csv(HISTORY_PATH)
            found = rows[rows.get("test_id", pd.Series(dtype=str)).astype(str) == test_id]
            if not found.empty:
                record = found.iloc[-1].fillna("").to_dict()
        except Exception:
            pass
    if record is None:
        return "Test record not found.", 404
    return render_template("report.html", record=record)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
