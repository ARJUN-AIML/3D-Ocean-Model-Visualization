"""
backend/ml/preprocessing/normalization.py
Training-Only Feature Normalization Module.
Calculates mean and standard deviation ONLY from training set and applies parameters to val/test sets.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd


class TrainingFeatureScaler:
    """
    StandardScaler wrapper that enforces fit ONLY on training features.
    Exposes dictionary representation suitable for serializing into ModelMetadata.
    """

    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or []
        self.means: Dict[str, float] = {}
        self.stds: Dict[str, float] = {}
        self.is_fitted: bool = False

    def fit(self, X_train: pd.DataFrame) -> "TrainingFeatureScaler":
        """
        Fits scaler parameters (mean, std) ONLY on training features dataframe.
        """
        self.feature_names = list(X_train.columns)
        self.means = {}
        self.stds = {}

        for col in self.feature_names:
            mean_val = float(X_train[col].mean())
            std_val = float(X_train[col].std())
            # Guard against zero variance
            if np.isnan(std_val) or std_val < 1e-8:
                std_val = 1.0

            self.means[col] = mean_val
            self.stds[col] = std_val

        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms input dataframe using pre-fitted training parameters.
        """
        if not self.is_fitted:
            raise RuntimeError("Scaler must be fit on training data before calling transform.")

        X_scaled = X.copy()
        for col in self.feature_names:
            if col in X_scaled.columns:
                mean_val = self.means[col]
                std_val = self.stds[col]
                X_scaled[col] = (X_scaled[col] - mean_val) / std_val

        return X_scaled

    def fit_transform(self, X_train: pd.DataFrame) -> pd.DataFrame:
        """Fits on training data and returns scaled training set."""
        return self.fit(X_train).transform(X_train)

    def to_dict(self) -> Dict[str, Dict[str, float]]:
        """Exports normalization parameters for metadata registration."""
        return {
            col: {"mean": self.means[col], "std": self.stds[col]}
            for col in self.feature_names
        }

    @classmethod
    def from_dict(cls, param_dict: Dict[str, Dict[str, float]]) -> "TrainingFeatureScaler":
        """Reconstructs scaler instance from metadata dictionary."""
        scaler = cls(feature_names=list(param_dict.keys()))
        for col, stats in param_dict.items():
            scaler.means[col] = stats["mean"]
            scaler.stds[col] = stats["std"]
        scaler.is_fitted = True
        return scaler
