from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "milkguard_model.joblib"
HISTORY_PATH = BASE_DIR / "data" / "screening_history.csv"

app = Flask(__name__)


def get_model():
    """Load the model only when a prediction is requested."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run: python train_model.py")
    return joblib.load(MODEL_PATH)


def save_history(ph, tds, temperature, result, probability):
    row = pd.DataFrame([{
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ph": ph,
        "tds": tds,
        "temperature": temperature,
        "result": result,
        "suspicious_probability": round(probability * 100, 1),
    }])
    row.to_csv(HISTORY_PATH, mode="a", index=False, header=not HISTORY_PATH.exists())


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
        save_history(ph, tds, temperature, result, probability)

        return jsonify(result=result, suspicious_probability=round(probability * 100, 1))
    except (KeyError, TypeError, ValueError):
        return jsonify(error="pH, TDS and temperature must be numeric values."), 400
    except FileNotFoundError as error:
        return jsonify(error=str(error)), 500


@app.route("/history")
def history():
    if not HISTORY_PATH.exists():
        return jsonify([])
    rows = pd.read_csv(HISTORY_PATH).tail(8).iloc[::-1].fillna("")
    return jsonify(rows.to_dict(orient="records"))


@app.route("/latest")
def latest():
    """Used by the dashboard to show the most recent ESP32 or manual test."""
    if not HISTORY_PATH.exists():
        return jsonify(None)
    rows = pd.read_csv(HISTORY_PATH)
    if rows.empty:
        return jsonify(None)
    return jsonify(rows.iloc[-1].fillna("").to_dict())


if __name__ == "__main__":
    # host=0.0.0.0 allows an ESP32 on the same Wi-Fi network to reach this API.
    app.run(host="0.0.0.0", debug=True)
