"""
ML Lifespan Predictor
Predicts model remaining useful life and retraining deadline
based on drift metrics from historical reports.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class LifespanPredictor:
    """
    Predicts model lifespan based on drift trajectory.
    
    Uses a weighted scoring model combining:
    - PSI trend (most predictive of distributional shift)
    - KL/JS divergence trajectory
    - Feature drift rate (% drifted features over time)
    - Drift velocity (how fast drift is accelerating)
    """

    # Thresholds for health states
    HEALTH_EXCELLENT = (0.0, 0.15)   # drift score range
    HEALTH_GOOD      = (0.15, 0.30)
    HEALTH_FAIR      = (0.30, 0.50)
    HEALTH_POOR      = (0.50, 0.70)
    HEALTH_CRITICAL  = (0.70, 1.01)

    # Days until retraining recommended based on current drift level
    # These are baseline estimates; adjusted by velocity
    RETRAINING_DAYS = {
        'Excellent': 180,
        'Good':      90,
        'Fair':      45,
        'Poor':      14,
        'Critical':  3,
    }

    def predict_lifespan(
        self,
        current_report: Dict[str, Any],
        historical_reports: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point. Returns full lifespan prediction.

        Args:
            current_report: Latest drift analysis result dict.
            historical_reports: Optional list of past reports (oldest first).

        Returns:
            Dict with health_score, health_label, days_remaining,
            recommended_retrain_date, confidence, velocity, feature_insights.
        """
        drift_score = current_report.get('overall_drift_score', 0.0)
        drift_status = current_report.get('overall_status', 'OK')
        feature_results = current_report.get('feature_results', [])
        drifted_features = current_report.get('drifted_features', 0)
        total_features = current_report.get('total_features', 1)
        warning_features = current_report.get('warning_features', 0)

        # ── 1. Composite health score ───────────────────────────────────────
        health_score = self._compute_health_score(
            drift_score, drifted_features, total_features,
            warning_features, feature_results
        )

        # ── 2. Health label ────────────────────────────────────────────────
        health_label = self._get_health_label(health_score)

        # ── 3. Drift velocity from history ─────────────────────────────────
        velocity, velocity_label = self._compute_velocity(historical_reports, health_score)

        # ── 4. Days remaining (adjusted by velocity) ───────────────────────
        base_days = self.RETRAINING_DAYS[health_label]
        days_remaining = self._adjust_days_by_velocity(base_days, velocity)

        # ── 5. Recommended retrain date ────────────────────────────────────
        recommended_retrain_date = (
            datetime.utcnow() + timedelta(days=days_remaining)
        ).strftime('%Y-%m-%d')

        # ── 6. Confidence ──────────────────────────────────────────────────
        confidence = self._compute_confidence(
            total_features, historical_reports, drift_score
        )

        # ── 7. Feature-level insights ───────────────────────────────────────
        feature_insights = self._feature_insights(feature_results)

        # ── 8. Trend (if history available) ────────────────────────────────
        trend = self._compute_trend(historical_reports, health_score)

        # ── 9. Risk factors ─────────────────────────────────────────────────
        risk_factors = self._identify_risk_factors(
            drift_score, drifted_features, total_features,
            warning_features, velocity, feature_results
        )

        # ── 10. Actionable recommendation ──────────────────────────────────
        recommendation = self._generate_recommendation(
            health_label, days_remaining, velocity_label, risk_factors
        )

        return {
            'health_score': round(health_score, 4),
            'health_label': health_label,
            'health_percentage': round((1.0 - health_score) * 100, 1),
            'days_remaining': days_remaining,
            'recommended_retrain_date': recommended_retrain_date,
            'confidence': round(confidence, 2),
            'velocity': round(velocity, 4),
            'velocity_label': velocity_label,
            'trend': trend,
            'risk_factors': risk_factors,
            'feature_insights': feature_insights,
            'recommendation': recommendation,
            'predicted_at': datetime.utcnow().isoformat() + 'Z',
        }

    # ──────────────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _compute_health_score(
        self,
        drift_score: float,
        drifted_features: int,
        total_features: int,
        warning_features: int,
        feature_results: List[Dict]
    ) -> float:
        """
        Composite health score 0..1 (higher = worse / more drift).
        Weights:
          40% overall drift score (PSI/KL/JS blend)
          30% feature drift ratio
          20% warning ratio
          10% mean PSI of top-5 drifted features
        """
        if total_features == 0:
            return drift_score

        w_drift    = 0.40
        w_feat     = 0.30
        w_warn     = 0.20
        w_psi_top  = 0.10

        feat_ratio = drifted_features / total_features
        warn_ratio = min(warning_features / total_features, 1.0)

        # Top-5 mean PSI (normalised to 0-1 using threshold 0.5 as ceiling)
        sorted_features = sorted(
            feature_results,
            key=lambda f: f.get('psi_score') or 0,
            reverse=True
        )
        top_psi_scores = [
            min((f.get('psi_score') or 0) / 0.5, 1.0)
            for f in sorted_features[:5]
        ]
        avg_top_psi = float(np.mean(top_psi_scores)) if top_psi_scores else drift_score

        health = (
            w_drift   * drift_score +
            w_feat    * feat_ratio  +
            w_warn    * warn_ratio  +
            w_psi_top * avg_top_psi
        )
        return float(np.clip(health, 0.0, 1.0))

    def _get_health_label(self, health_score: float) -> str:
        if health_score < self.HEALTH_EXCELLENT[1]:
            return 'Excellent'
        if health_score < self.HEALTH_GOOD[1]:
            return 'Good'
        if health_score < self.HEALTH_FAIR[1]:
            return 'Fair'
        if health_score < self.HEALTH_POOR[1]:
            return 'Poor'
        return 'Critical'

    def _compute_velocity(
        self,
        historical_reports: Optional[List[Dict]],
        current_score: float
    ):
        """
        Drift velocity: rate of change of health score per day.
        Positive = getting worse, Negative = improving.
        Returns (velocity_float, velocity_label_str).
        """
        if not historical_reports or len(historical_reports) < 2:
            return 0.0, 'Stable'

        # Use last 5 reports at most for velocity
        recent = historical_reports[-5:]
        scores = [r.get('overall_drift_score', 0.0) for r in recent]
        scores.append(current_score)

        if len(scores) < 2:
            return 0.0, 'Stable'

        # Simple linear regression slope
        x = np.arange(len(scores), dtype=float)
        slope = float(np.polyfit(x, scores, 1)[0])

        if slope > 0.02:
            label = 'Accelerating'
        elif slope > 0.005:
            label = 'Increasing'
        elif slope < -0.02:
            label = 'Recovering'
        elif slope < -0.005:
            label = 'Decreasing'
        else:
            label = 'Stable'

        return slope, label

    def _adjust_days_by_velocity(self, base_days: int, velocity: float) -> int:
        """Reduce days if drift is accelerating, increase if recovering."""
        # velocity in drift-score-units per report; scale to impact
        multiplier = 1.0 - (velocity * 5)   # e.g. +0.05/report → 0.75x
        multiplier = float(np.clip(multiplier, 0.25, 2.0))
        adjusted = int(round(base_days * multiplier))
        return max(adjusted, 1)

    def _compute_confidence(
        self,
        total_features: int,
        historical_reports: Optional[List],
        drift_score: float
    ) -> float:
        """
        Confidence 0..1 based on:
        - Number of features analysed (more = higher confidence)
        - How many historical reports available
        - Clarity of drift signal (very high or very low = clearer)
        """
        feature_conf = min(total_features / 20, 1.0)  # saturates at 20 features
        history_conf = min((len(historical_reports) if historical_reports else 0) / 10, 1.0)
        # Signal clarity: extremes are clearer than 0.5
        signal_conf = abs(drift_score - 0.5) * 2

        confidence = 0.50 * feature_conf + 0.30 * history_conf + 0.20 * signal_conf
        return float(np.clip(confidence, 0.1, 0.99))

    def _compute_trend(
        self,
        historical_reports: Optional[List],
        current_score: float
    ) -> Dict[str, Any]:
        if not historical_reports:
            return {'direction': 'unknown', 'data_points': 1}

        scores = [r.get('overall_drift_score', 0.0) for r in historical_reports]
        scores.append(current_score)

        if len(scores) < 2:
            return {'direction': 'stable', 'data_points': len(scores)}

        delta = scores[-1] - scores[-2]
        if delta > 0.02:
            direction = 'worsening'
        elif delta < -0.02:
            direction = 'improving'
        else:
            direction = 'stable'

        return {
            'direction': direction,
            'delta': round(delta, 4),
            'data_points': len(scores),
            'score_history': [round(s, 4) for s in scores],
        }

    def _feature_insights(self, feature_results: List[Dict]) -> Dict[str, Any]:
        """Summarise which features are driving drift the most."""
        drifted = [f for f in feature_results if f.get('drift_status') == 'Drift']
        warning = [f for f in feature_results if f.get('drift_status') == 'Warning']

        top_drifted = sorted(
            drifted,
            key=lambda f: f.get('psi_score') or 0,
            reverse=True
        )[:5]

        return {
            'top_drifted_features': [
                {
                    'name': f['feature_name'],
                    'psi_score': round(f.get('psi_score') or 0, 4),
                    'mean_shift_pct': round(
                        abs(
                            (f.get('current_mean', 0) - f.get('baseline_mean', 0))
                            / max(abs(f.get('baseline_mean', 1)), 1e-9)
                        ) * 100,
                        2
                    ),
                }
                for f in top_drifted
            ],
            'warning_count': len(warning),
            'drift_count': len(drifted),
        }

    def _identify_risk_factors(
        self,
        drift_score: float,
        drifted_features: int,
        total_features: int,
        warning_features: int,
        velocity: float,
        feature_results: List[Dict],
    ) -> List[str]:
        risks = []

        if drift_score > 0.5:
            risks.append('High overall drift score — model predictions likely degraded')
        if total_features > 0 and drifted_features / total_features > 0.4:
            risks.append(f'{drifted_features}/{total_features} features show active drift')
        if velocity > 0.03:
            risks.append('Rapid drift acceleration detected — lifespan may be shorter than estimated')
        if warning_features > drifted_features:
            risks.append('Several features in warning zone — drift may escalate soon')

        high_psi = [
            f for f in feature_results
            if (f.get('psi_score') or 0) > 0.5
        ]
        if high_psi:
            names = ', '.join(f['feature_name'] for f in high_psi[:3])
            risks.append(f'Extreme PSI (>0.5) on: {names}')

        return risks if risks else ['No significant risk factors detected']

    def _generate_recommendation(
        self,
        health_label: str,
        days_remaining: int,
        velocity_label: str,
        risk_factors: List[str],
    ) -> str:
        base = {
            'Excellent': 'Model health is excellent. Continue regular monitoring.',
            'Good':      'Model is healthy. Schedule a routine review within the next few weeks.',
            'Fair':      'Moderate drift detected. Plan for retraining or recalibration soon.',
            'Poor':      'Significant drift observed. Initiate retraining procedures promptly.',
            'Critical':  'CRITICAL: Model is severely degraded. Immediate retraining required.',
        }[health_label]

        urgency = ''
        if velocity_label == 'Accelerating':
            urgency = ' Drift is accelerating — act sooner than the estimated deadline.'
        elif velocity_label == 'Recovering':
            urgency = ' Drift appears to be decreasing; continue monitoring.'

        timeline = f' Estimated days before retraining is required: {days_remaining}.'
        return base + timeline + urgency
