import pandas as pd
import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class DriftDetector:
    """
    Complete drift detection engine with multiple metrics:
    - PSI (Population Stability Index)
    - KL Divergence
    - Jensen-Shannon Divergence
    - Kolmogorov-Smirnov Test
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins

        self.psi_thresholds = {'low': 0.1, 'medium': 0.25}
        self.kl_thresholds = {'low': 0.1, 'medium': 0.5}
        self.js_thresholds = {'low': 0.1, 'medium': 0.3}

        self.ks_threshold = 0.05

    # ============================================================
    # DATA LOADING
    # ============================================================

    def load_and_merge_csvs(self, file_paths: List[str]) -> pd.DataFrame:
        dfs = []

        for path in file_paths:
            try:
                df = pd.read_csv(path)
                dfs.append(df)
            except Exception as e:
                raise ValueError(f"Error loading {path}: {str(e)}")

        if not dfs:
            raise ValueError("No valid CSV files loaded")

        merged_df = pd.concat(dfs, ignore_index=True)
        return merged_df

    # ============================================================
    # FEATURE ALIGNMENT
    # ============================================================

    def align_features(
        self,
        baseline: pd.DataFrame,
        current: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:

        baseline_numeric = baseline.select_dtypes(include=[np.number]).columns
        current_numeric = current.select_dtypes(include=[np.number]).columns

        common_features = [c for c in baseline_numeric if c in current_numeric]

        if not common_features:
            raise ValueError("No common numeric features found between datasets")

        return baseline[common_features], current[common_features]

    # ============================================================
    # INTERNAL DISTRIBUTION PREP
    # ============================================================

    def _prepare_distributions(
        self,
        baseline: np.ndarray,
        current: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:

        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]

        if len(baseline) == 0 or len(current) == 0:
            return None, None

        min_val = baseline.min()
        max_val = baseline.max()

        if min_val == max_val:
            return None, None

        # IMPORTANT FIX: bins from baseline only
        bins = np.linspace(min_val, max_val, self.n_bins + 1)

        # Clip current to baseline range
        current = np.clip(current, min_val, max_val)

        baseline_counts, _ = np.histogram(baseline, bins=bins)
        current_counts, _ = np.histogram(current, bins=bins)

        epsilon = 1e-10

        # IMPORTANT FIX: proper probability mass
        p = (baseline_counts + epsilon) / baseline_counts.sum()
        q = (current_counts + epsilon) / current_counts.sum()

        return p, q

    # ============================================================
    # PSI
    # ============================================================

    def calculate_psi(
        self,
        baseline: np.ndarray,
        current: np.ndarray
    ) -> float:

        p, q = self._prepare_distributions(baseline, current)

        if p is None:
            return 0.0

        psi = np.sum((q - p) * np.log(q / p))
        return float(psi)

    # ============================================================
    # KL DIVERGENCE
    # ============================================================

    def calculate_kl_divergence(
        self,
        baseline: np.ndarray,
        current: np.ndarray
    ) -> float:

        p, q = self._prepare_distributions(baseline, current)

        if p is None:
            return 0.0

        kl_div = np.sum(p * np.log(p / q))
        return float(kl_div)

    # ============================================================
    # JENSEN-SHANNON DIVERGENCE
    # ============================================================

    def calculate_js_divergence(
        self,
        baseline: np.ndarray,
        current: np.ndarray
    ) -> float:

        p, q = self._prepare_distributions(baseline, current)

        if p is None:
            return 0.0

        js_div = jensenshannon(p, q) ** 2
        return float(js_div)

    # ============================================================
    # KS TEST
    # ============================================================

    def calculate_ks_test(
        self,
        baseline: np.ndarray,
        current: np.ndarray
    ) -> Tuple[float, float]:

        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]

        if len(baseline) == 0 or len(current) == 0:
            return np.nan, np.nan

        statistic, pvalue = stats.ks_2samp(baseline, current)
        return float(statistic), float(pvalue)

    # ============================================================
    # DRIFT STATUS DECISION
    # ============================================================

    def determine_drift_status(
        self,
        psi: float,
        kl: float,
        js: float,
        ks_pvalue: float
    ) -> str:

        drift_indicators = 0
        warning_indicators = 0

        if not np.isnan(psi):
            if psi > self.psi_thresholds['medium']:
                drift_indicators += 1
            elif psi > self.psi_thresholds['low']:
                warning_indicators += 1

        if not np.isnan(kl):
            if kl > self.kl_thresholds['medium']:
                drift_indicators += 1
            elif kl > self.kl_thresholds['low']:
                warning_indicators += 1

        if not np.isnan(js):
            if js > self.js_thresholds['medium']:
                drift_indicators += 1
            elif js > self.js_thresholds['low']:
                warning_indicators += 1

        if not np.isnan(ks_pvalue):
            if ks_pvalue < 0.01:
                drift_indicators += 1
            elif ks_pvalue < self.ks_threshold:
                warning_indicators += 1

        if drift_indicators >= 2:
            return 'Drift'
        elif drift_indicators >= 1 or warning_indicators >= 2:
            return 'Warning'
        else:
            return 'OK'

    # ============================================================
    # MAIN DETECTION PIPELINE
    # ============================================================

    def detect_drift(
        self,
        baseline_paths: List[str],
        current_paths: List[str]
    ) -> Dict[str, Any]:

        baseline_df = self.load_and_merge_csvs(baseline_paths)
        current_df = self.load_and_merge_csvs(current_paths)

        baseline_aligned, current_aligned = self.align_features(
            baseline_df,
            current_df
        )

        feature_results = []
        drift_scores = []

        for feature in baseline_aligned.columns:

            baseline_values = baseline_aligned[feature].values
            current_values = current_aligned[feature].values

            psi = self.calculate_psi(baseline_values, current_values)
            kl = self.calculate_kl_divergence(baseline_values, current_values)
            js = self.calculate_js_divergence(baseline_values, current_values)
            ks_stat, ks_pval = self.calculate_ks_test(
                baseline_values,
                current_values
            )

            drift_status = self.determine_drift_status(
                psi, kl, js, ks_pval
            )

            baseline_mean = float(np.nanmean(baseline_values))
            current_mean = float(np.nanmean(current_values))

            baseline_std = float(np.nanstd(baseline_values))
            current_std = float(np.nanstd(current_values))

            feature_results.append({
                'feature_name': feature,
                'psi_score': psi,
                'kl_divergence': kl,
                'js_divergence': js,
                'ks_statistic': ks_stat,
                'ks_pvalue': ks_pval,
                'drift_status': drift_status,
                'baseline_mean': baseline_mean,
                'current_mean': current_mean,
                'baseline_std': baseline_std,
                'current_std': current_std
            })

            valid_scores = []

            if not np.isnan(psi):
                valid_scores.append(min(psi / 0.5, 1.0))

            if not np.isnan(kl):
                valid_scores.append(min(kl / 1.0, 1.0))

            if not np.isnan(js):
                valid_scores.append(min(js / 0.5, 1.0))

            if valid_scores:
                drift_scores.append(np.mean(valid_scores))

        overall_drift_score = float(np.mean(drift_scores)) if drift_scores else 0.0

        drifted_features = sum(
            1 for r in feature_results if r['drift_status'] == 'Drift'
        )

        warning_features = sum(
            1 for r in feature_results if r['drift_status'] == 'Warning'
        )

        if drifted_features >= len(feature_results) * 0.3:
            overall_status = 'Drift'
        elif (
            drifted_features >= len(feature_results) * 0.1
            or warning_features >= len(feature_results) * 0.3
        ):
            overall_status = 'Warning'
        else:
            overall_status = 'OK'

        return {
            'overall_drift_score': overall_drift_score,
            'overall_status': overall_status,
            'total_features': len(feature_results),
            'drifted_features': drifted_features,
            'warning_features': warning_features,
            'ok_features': len(feature_results) - drifted_features - warning_features,
            'feature_results': feature_results,
            'baseline_samples': len(baseline_df),
            'current_samples': len(current_df)
        }
