from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
RANDOM_SEED = 42

def make_data(rows=1200):
    rng = np.random.default_rng(RANDOM_SEED)
    half = rows // 2

    # Normal Pure Milk (pH: 6.5 - 6.8 | TDS: 250 - 550 | Temp: 4 - 30 C)
    normal = pd.DataFrame({
        "ph": rng.uniform(6.50, 6.75, half),
        "tds": rng.uniform(260, 520, half),
        "temperature": rng.uniform(4.0, 28.0, half),
        "label": 0
    })

    # Suspicious / Adulterated Categories
    # 1. Acidic / Spoiled (pH < 6.4)
    acidic = pd.DataFrame({
        "ph": rng.uniform(3.5, 6.35, half // 4),
        "tds": rng.uniform(300, 800, half // 4),
        "temperature": rng.uniform(10.0, 38.0, half // 4),
        "label": 1
    })

    # 2. Alkaline / Detergent Adulterated (pH > 6.9)
    alkaline = pd.DataFrame({
        "ph": rng.uniform(7.0, 11.0, half // 4),
        "tds": rng.uniform(400, 950, half // 4),
        "temperature": rng.uniform(10.0, 38.0, half // 4),
        "label": 1
    })

    # 3. High TDS / Added Salts, Urea, Starch (TDS > 600)
    high_tds = pd.DataFrame({
        "ph": rng.uniform(6.4, 7.2, half // 4),
        "tds": rng.uniform(650, 2500, half // 4),
        "temperature": rng.uniform(10.0, 35.0, half // 4),
        "label": 1
    })

    # 4. Diluted with excess water (TDS < 200) or high temp spoilage
    diluted_or_hot = pd.DataFrame({
        "ph": rng.uniform(6.1, 6.9, half - (3 * (half // 4))),
        "tds": rng.uniform(40, 210, half - (3 * (half // 4))),
        "temperature": rng.uniform(32.0, 55.0, half - (3 * (half // 4))),
        "label": 1
    })

    df = pd.concat([normal, acidic, alkaline, high_tds, diluted_or_hot], ignore_index=True)
    return df.sample(frac=1, random_state=RANDOM_SEED)

def main():
    DATA_DIR.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(exist_ok=True)

    data = make_data()
    data.to_csv(DATA_DIR / "synthetic_milk_data.csv", index=False)

    x = data[["ph", "tds", "temperature"]]
    y = data["label"]

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y)

    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=RANDOM_SEED)
    model.fit(x_train, y_train)

    preds = model.predict(x_test)
    print("Test Accuracy:", round(accuracy_score(y_test, preds), 3))
    print(classification_report(y_test, preds, target_names=["Normal", "Suspicious"]))

    joblib.dump(model, MODEL_DIR / "milkguard_model.joblib")
    print("Model saved to model/milkguard_model.joblib")

if __name__ == "__main__":
    main()
