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
    """Load the model only when a prediction is requested."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run: python train_model.py")
    return joblib.load(MODEL_PATH)


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
            # Local result still works if internet/database is temporarily unavailable.
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

        model = get_model()
        features = pd.DataFrame([[ph, tds, temperature]],
                                columns=["ph", "tds", "temperature"])
        prediction = int(model.predict(features)[0])
        probability = float(model.predict_proba(features)[0][1])
        result = "SUSPICIOUS" if prediction == 1 else "NORMAL"
        test_id = str(uuid.uuid4())
        sample_id = str(values.get("sample_id") or f"MG-{test_id[:8].upper()}")[:40]
        save_history(test_id, sample_id, ph, tds, temperature, result, probability)

        return jsonify(result=result, suspicious_probability=round(probability * 100, 1),
                       test_id=test_id, sample_id=sample_id,
                       report_url=request.url_root.rstrip("/") + f"/report/{test_id}")
    except (KeyError, TypeError, ValueError):
        return jsonify(error="pH, TDS and temperature must be numeric values."), 400
    except FileNotFoundError as error:
        return jsonify(error=str(error)), 500


@app.route("/latest")
def latest():
    """Used by the dashboard to show the most recent ESP32 or manual test."""
    if not HISTORY_PATH.exists():
        return jsonify(None)
    rows = pd.read_csv(HISTORY_PATH)
    if rows.empty:
        return jsonify(None)
    return jsonify(rows.iloc[-1].fillna("").to_dict())


@app.route("/report/<test_id>")
def report(test_id):
    """A QR opens this single test report; no list of other users' tests is public."""
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
    # host=0.0.0.0 allows an ESP32 on the same Wi-Fi network to reach this API.
    app.run(host="0.0.0.0", debug=True)
