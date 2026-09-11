"""Create demo training data and train one MilkGuard screening model.

This is NOT a laboratory adulterant-identification model. The values are
synthetic, chosen only to demonstrate a Normal/Suspicious classification flow.
Replace data/synthetic_milk_data.csv with labelled measurements collected from
your own tested samples before making any real-world claim.
"""
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


def make_demo_data(rows=300):
    """Generate labelled, artificial readings for a classroom demonstration."""
    rng = np.random.default_rng(RANDOM_SEED)
    normal_count = rows // 2
    suspicious_count = rows - normal_count

    normal = pd.DataFrame({
        "ph": rng.normal(6.65, 0.15, normal_count).clip(6.2, 7.1),
        "tds": rng.normal(310, 35, normal_count).clip(220, 390),
        "temperature": rng.normal(27, 3.5, normal_count).clip(18, 35),
        "label": 0,
    })
    # Suspicious samples simulate out-of-range readings, not a named adulterant.
    low_ph = pd.DataFrame({
        "ph": rng.normal(5.7, 0.25, suspicious_count // 3),
        "tds": rng.normal(330, 55, suspicious_count // 3),
        "temperature": rng.normal(28, 5, suspicious_count // 3),
        "label": 1,
    })
    high_tds = pd.DataFrame({
        "ph": rng.normal(6.65, 0.2, suspicious_count // 3),
        "tds": rng.normal(520, 70, suspicious_count // 3),
        "temperature": rng.normal(28, 5, suspicious_count // 3),
        "label": 1,
    })
    unusual_temp = pd.DataFrame({
        "ph": rng.normal(6.65, 0.2, suspicious_count - 2 * (suspicious_count // 3)),
        "tds": rng.normal(310, 45, suspicious_count - 2 * (suspicious_count // 3)),
        "temperature": rng.choice([rng.normal(12, 2), rng.normal(46, 3)], suspicious_count - 2 * (suspicious_count // 3)),
        "label": 1,
    })
    return pd.concat([normal, low_ph, high_tds, unusual_temp], ignore_index=True).sample(frac=1, random_state=RANDOM_SEED)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(exist_ok=True)
    data = make_demo_data()
    data.to_csv(DATA_DIR / "synthetic_milk_data.csv", index=False)

    x = data[["ph", "tds", "temperature"]]
    y = data["label"]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.20,
                                                        random_state=RANDOM_SEED, stratify=y)
    model = RandomForestClassifier(n_estimators=120, max_depth=5,
                                   random_state=RANDOM_SEED)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    print("Demo test accuracy:", round(accuracy_score(y_test, predictions), 3))
    print(classification_report(y_test, predictions, target_names=["Normal", "Suspicious"]))
    joblib.dump(model, MODEL_DIR / "milkguard_model.joblib")
    print("Saved model/milkguard_model.joblib")


if __name__ == "__main__":
    main()
