import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


class EnergyForecaster:
    """Gradient-Boosting based demand forecasting model."""

    def __init__(self):
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("gbr", GradientBoostingRegressor(
                n_estimators=200, learning_rate=0.05,
                max_depth=4, random_state=42,
            )),
        ])
        self.is_trained = False

    def _build_features(self, df: pd.DataFrame) -> np.ndarray:
        df = df.copy()
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        df["dayofweek"] = pd.to_datetime(df["timestamp"]).dt.dayofweek
        df["month"] = pd.to_datetime(df["timestamp"]).dt.month
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
        df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
        df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
        df["lag_1"] = df["energy_kwh"].shift(1).bfill()
        df["lag_24"] = df["energy_kwh"].shift(24).bfill()
        df["rolling_mean_6"] = df["energy_kwh"].rolling(6, min_periods=1).mean()
        feats = ["hour_sin", "hour_cos", "dow_sin", "dow_cos",
                 "is_weekend", "lag_1", "lag_24", "rolling_mean_6"]
        return df[feats].values

    def train(self, df: pd.DataFrame):
        X = self._build_features(df)
        y = df["energy_kwh"].values
        self.model.fit(X[24:], y[24:])
        self.is_trained = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = self._build_features(df)
        return self.model.predict(X)

    def score(self, df: pd.DataFrame) -> float:
        X = self._build_features(df)
        y = df["energy_kwh"].values
        return float(self.model.score(X[24:], y[24:]))


class AnomalyDetector:
    """Isolation Forest for energy consumption anomaly detection."""

    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=42,
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    def _features(self, df: pd.DataFrame) -> np.ndarray:
        df = df.copy()
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        df["lag_1"] = df["energy_kwh"].shift(1).bfill()
        df["rolling_std"] = df["energy_kwh"].rolling(6, min_periods=1).std().fillna(0)
        df["rolling_mean"] = df["energy_kwh"].rolling(6, min_periods=1).mean()
        df["z_score"] = (df["energy_kwh"] - df["rolling_mean"]) / (df["rolling_std"] + 1e-9)
        feats = ["energy_kwh", "voltage", "power_factor", "hour", "lag_1", "z_score"]
        available = [f for f in feats if f in df.columns]
        return df[available].fillna(0).values

    def train(self, df: pd.DataFrame):
        X = self._features(df)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        X = self._features(df)
        X_scaled = self.scaler.transform(X)
        preds = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        df = df.copy()
        df["anomaly_flag"] = (preds == -1).astype(int)
        df["anomaly_score"] = np.clip((-scores - scores.min()) / (scores.max() - scores.min() + 1e-9), 0, 1)
        return df


def compute_efficiency_score(df: pd.DataFrame) -> float:
    """Returns 0-100 efficiency score based on power factor and usage variance."""
    if df.empty:
        return 75.0
    pf_score = df["power_factor"].mean() * 50 if "power_factor" in df.columns else 40.0
    usage = df["energy_kwh"]
    variance_penalty = min(20, usage.std() / (usage.mean() + 1e-9) * 20)
    score = pf_score + (50 - variance_penalty)
    return round(float(np.clip(score, 0, 100)), 1)


def compute_carbon_intensity(source_df: pd.DataFrame) -> dict:
    """Compute carbon metrics from source breakdown dataframe."""
    total_energy = source_df["energy_mwh"].sum()
    total_co2 = source_df["co2_tonnes"].sum()
    renewable = source_df[source_df["is_renewable"]]["energy_mwh"].sum()
    renewable_pct = round(renewable / (total_energy + 1e-9) * 100, 1)
    intensity = round(total_co2 / (total_energy + 1e-9) * 1000, 2)  # kg/MWh
    sustainability_score = round(min(100, renewable_pct * 1.1), 1)
    return {
        "total_co2_tonnes": round(total_co2, 1),
        "renewable_pct": renewable_pct,
        "carbon_intensity_kg_mwh": intensity,
        "sustainability_score": sustainability_score,
    }
