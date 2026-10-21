# -*- coding: utf-8 -*-
"""
ai/metrics.py
-------------
وحدة مقاييس الأداء المتقدمة والشرح لنظام الذكاء الاصطناعي.
تحتوي على مقاييس خاصة بالسلاسل الزمنية ووظائف التفسير.

الإصدار: 3.0
تاريخ التحديث: أبريل 2026
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from abc import ABC, abstractmethod
import warnings

from config import AI_METRICS_CONFIG, AI_EXPLAINABILITY_CONFIG

warnings.filterwarnings('ignore')


class BaseMetric(ABC):
    """القاعدة المجردة لمقاييس الأداء"""

    @abstractmethod
    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """حساب المقياس"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """الحصول على اسم المقياس"""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class MAEMetric(BaseMetric):
    """متوسط الخطأ المطلق (Mean Absolute Error)"""

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(np.abs(y_true - y_pred)))

    def get_name(self) -> str:
        return "MAE"


class RMSEMetric(BaseMetric):
    """جذر متوسط مربع الخطأ (Root Mean Squared Error)"""

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    def get_name(self) -> str:
        return "RMSE"


class MSEMetric(BaseMetric):
    """متوسط مربع الخطأ (Mean Squared Error)"""

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean((y_true - y_pred) ** 2))

    def get_name(self) -> str:
        return "MSE"


class MAPEMetric(BaseMetric):
    """متوسط نسبة الخطأ المطلق (Mean Absolute Percentage Error)"""

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        # تجنب القسمة على صفر
        mask = y_true != 0
        if not mask.any():
            return 0.0

        return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

    def get_name(self) -> str:
        return "MAPE"


class SMAPEMetric(BaseMetric):
    """الخطأ المطلق المنتظم النسبي (Symmetric MAPE)"""

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
        mask = denominator != 0

        if not mask.any():
            return 0.0

        return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100)

    def get_name(self) -> str:
        return "SMAPE"


class MASEMetric(BaseMetric):
    """الخطأ المطلق المتوسط المقياس (Mean Absolute Scaled Error)"""

    def __init__(self, seasonality: int = 1):
        self.seasonality = seasonality

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        # حساب خطأ التنبؤ
        mae_forecast = np.mean(np.abs(y_true - y_pred))

        # حساب_naive forecast error
        n = len(y_true)
        if n <= self.seasonality:
            return 0.0

        naive_errors = np.abs(y_true[self.seasonality:] - y_true[:-self.seasonality])
        mae_naive = np.mean(naive_errors)

        if mae_naive == 0:
            return 0.0

        return float(mae_forecast / mae_naive)

    def get_name(self) -> str:
        return f"MASE(s={self.seasonality})"


class TheilUMetric(BaseMetric):
    """مقياس Theil's U للخطأ التنبؤي"""

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        n = len(y_true)
        if n < 2:
            return 0.0

        # حساب U
        numerator = np.sum((y_pred[1:] - y_true[1:]) ** 2)
        denominator = np.sum(y_true[1:] ** 2) + np.sum(y_pred[1:] ** 2)

        if denominator == 0:
            return 0.0

        return float(np.sqrt(numerator / denominator))

    def get_name(self) -> str:
        return "Theil_U"


class WithinThresholdMetric(BaseMetric):
    """نسبة التنبؤات ضمن هامش معين"""

    def __init__(self, threshold_percent: float = 15):
        self.threshold = threshold_percent / 100

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        # تجنب القسمة على صفر
        mask = y_true != 0
        if not mask.any():
            return 0.0

        relative_errors = np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])
        within_threshold = np.sum(relative_errors <= self.threshold) / len(y_true) * 100

        return float(within_threshold)

    def get_name(self) -> str:
        return f"Within_{int(self.threshold * 100)}%"


class DirectionalAccuracyMetric(BaseMetric):
    """دقة اتجاه التغيير"""

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        if len(y_true) < 2:
            return 0.0

        # حساب اتجاه التغيير
        true_direction = np.diff(y_true)
        pred_direction = np.diff(y_pred)

        # حساب الدقة
        correct = np.sum(true_direction * pred_direction >= 0)
        total = len(true_direction)

        if total == 0:
            return 0.0

        return float(correct / total * 100)

    def get_name(self) -> str:
        return "Directional_Accuracy"


class MetricsCalculator:
    """حاسبة المقاييس الشاملة"""

    def __init__(self, config: Dict = None):
        self.config = config or AI_METRICS_CONFIG.copy()
        self.metrics = self._initialize_metrics()

    def _initialize_metrics(self) -> Dict[str, BaseMetric]:
        """تهيئة المقاييس"""
        metrics = {}

        # المقاييس الأساسية
        for metric_name in self.config.get('primary_metrics', ['mae', 'rmse', 'mape']):
            if metric_name == 'mae':
                metrics['mae'] = MAEMetric()
            elif metric_name == 'rmse':
                metrics['rmse'] = RMSEMetric()
            elif metric_name == 'mape':
                metrics['mape'] = MAPEMetric()

        # مقاييس السلاسل الزمنية
        for metric_name in self.config.get('time_series_metrics', ['mase', 'theil_u', 'smape']):
            if metric_name == 'mase':
                metrics['mase'] = MASEMetric(seasonality=7)
            elif metric_name == 'theil_u':
                metrics['theil_u'] = TheilUMetric()
            elif metric_name == 'smape':
                metrics['smape'] = SMAPEMetric()

        # المقاييس التجارية
        for metric_name in self.config.get('business_metrics', ['within_threshold_pct']):
            if metric_name == 'within_threshold_pct':
                threshold = self.config.get('threshold_percentage', 0.15) * 100
                metrics['within_threshold_pct'] = WithinThresholdMetric(threshold)
            elif metric_name == 'directional_accuracy':
                metrics['directional_accuracy'] = DirectionalAccuracyMetric()

        return metrics

    def calculate_all(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """حساب جميع المقاييس"""
        results = {}

        for name, metric in self.metrics.items():
            try:
                results[name] = metric.calculate(y_true, y_pred)
            except Exception as e:
                warnings.warn(f"خطأ في حساب {name}: {e}")
                results[name] = np.nan

        return results

    def calculate_primary(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """حساب المقاييس الأساسية فقط"""
        results = {}
        for name in ['mae', 'rmse', 'mape']:
            if name in self.metrics:
                try:
                    results[name] = self.metrics[name].calculate(y_true, y_pred)
                except Exception:
                    results[name] = np.nan
        return results

    def calculate_for_forecast_horizons(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        horizon_size: int = 1
    ) -> Dict[str, Dict[str, float]]:
        """حساب المقاييس لكل أفق تنبؤ"""
        n = len(y_true)
        results = {}

        for horizon in [1, 7, 14, 30]:
            start_idx = horizon - 1
            if start_idx >= n:
                continue

            y_true_h = y_true[start_idx::horizon_size]
            y_pred_h = y_pred[start_idx::horizon_size]

            if len(y_true_h) > 0:
                results[f'horizon_{horizon}'] = self.calculate_all(y_true_h, y_pred_h)

        return results


class ModelEvaluator:
    """مقيّم النماذج"""

    def __init__(self, metrics_calculator: MetricsCalculator = None):
        self.metrics_calc = metrics_calculator or MetricsCalculator()

    def cross_validate_time_series(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        n_splits: int = 5,
        gap: int = 7,
        test_size: int = 30
    ) -> Dict[str, Any]:
        """
        التحقق المتقاطع للسلاسل الزمنية

        Args:
            model: النموذج المراد تقييمه
            X: الميزات
            y: الهدف
            n_splits: عدد التقسيمات
            gap: الفجوة بين التدريب والاختبار
            test_size: حجم مجموعة الاختبار

        Returns:
            قاموس بالنتائج
        """
        from sklearn.model_selection import TimeSeriesSplit

        n = len(y)
        if n < test_size * 2:
            raise ValueError("بيانات غير كافية للتحقق المتقاطع")

        tscv = TimeSeriesSplit(n_splits=n_splits, gap=gap, test_size=test_size)

        fold_results = []
        feature_importances = []

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            try:
                # تدريب النموذج
                model.fit(X_train, y_train)

                # التنبؤ
                y_pred = model.predict(X_test)

                # حساب المقاييس
                metrics = self.metrics_calc.calculate_all(y_test, y_pred)

                # الحصول على feature importance
                importance = model.get_feature_importance()
                if importance is not None:
                    feature_importances.append(importance)

                fold_results.append({
                    'fold': fold + 1,
                    'train_size': len(train_idx),
                    'test_size': len(test_idx),
                    'metrics': metrics,
                })

            except Exception as e:
                warnings.warn(f"خطأ في fold {fold + 1}: {e}")
                continue

        # تجميع النتائج
        aggregated = self._aggregate_fold_results(fold_results)
        aggregated['feature_importance'] = np.mean(feature_importances, axis=0) if feature_importances else None
        aggregated['folds'] = fold_results

        return aggregated

    def _aggregate_fold_results(
        self,
        fold_results: List[Dict]
    ) -> Dict[str, Any]:
        """تجميع نتائج الـ folds"""
        if not fold_results:
            return {}

        # استخراج أسماء المقاييس
        metric_names = list(fold_results[0]['metrics'].keys())

        aggregated = {}
        for metric_name in metric_names:
            values = [fold['metrics'][metric_name] for fold in fold_results]
            aggregated[f'{metric_name}_mean'] = np.mean(values)
            aggregated[f'{metric_name}_std'] = np.std(values)
            aggregated[f'{metric_name}_min'] = np.min(values)
            aggregated[f'{metric_name}_max'] = np.max(values)

        return aggregated

    def compare_models(
        self,
        models: Dict[str, BaseMetric],
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: int = 5
    ) -> pd.DataFrame:
        """مقارنة أداء عدة نماذج"""
        results = []

        for name, model in models.items():
            try:
                cv_results = self.cross_validate_time_series(model, X, y, n_splits=cv_folds)
                row = {'model': name}
                row.update({k: v for k, v in cv_results.items() if not k.endswith('_folds')})
                results.append(row)
            except Exception as e:
                warnings.warn(f"خطأ في تقييم {name}: {e}")
                results.append({'model': name, 'error': str(e)})

        return pd.DataFrame(results)


class DriftDetector:
    """كاشف انحراف البيانات"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.baseline_data = None
        self.baseline_stats = None

    def set_baseline(self, data: np.ndarray):
        """تعيين خط الأساس"""
        self.baseline_data = data
        self.baseline_stats = {
            'mean': np.mean(data),
            'std': np.std(data),
            'median': np.median(data),
            'q25': np.percentile(data, 25),
            'q75': np.percentile(data, 75),
        }

    def calculate_psi(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        حساب Population Stability Index (PSI)

        Args:
            expected: البيانات المتوقعة (خط الأساس)
            actual: البيانات الفعلية
            n_bins: عدد الأوعية

        Returns:
            قيمة PSI
        """
        # تحديد حدود الأوعية
        breakpoints = np.percentile(expected, np.linspace(0, 100, n_bins + 1))

        # حساب التوزيعات
        expected_counts = np.histogram(expected, bins=breakpoints)[0]
        actual_counts = np.histogram(actual, bins=breakpoints)[0]

        # تحويل إلى نسب
        expected_pct = expected_counts / len(expected)
        actual_pct = actual_counts / len(actual)

        # تجنب القسمة على صفر
        expected_pct = np.where(expected_pct == 0, 0.0001, expected_pct)
        actual_pct = np.where(actual_pct == 0, 0.0001, actual_pct)

        # حساب PSI
        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))

        return float(psi)

    def detect_drift(
        self,
        new_data: np.ndarray,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """اكتشاف الانحراف"""
        if self.baseline_stats is None:
            raise ValueError("لم يتم تعيين خط الأساس")

        psi = self.calculate_psi(self.baseline_data, new_data)

        return {
            'psi': psi,
            'drift_detected': psi > threshold,
            'severity': 'low' if psi < 0.1 else ('medium' if psi < 0.2 else 'high'),
            'recommendation': 'إعادة تدريب' if psi > threshold else 'النموذج الحالي كافٍ',
        }

    def calculate_drift_over_time(
        self,
        historical_data: np.ndarray,
        window_size: int = 30
    ) -> List[Dict[str, Any]]:
        """حساب الانحراف عبر الوقت"""
        n = len(historical_data)
        results = []

        # استخدام أول window كخط أساس
        baseline = historical_data[:window_size]

        for i in range(window_size, n, window_size):
            window = historical_data[max(0, i - window_size):i]
            psi = self.calculate_psi(baseline, window)
            drift = self.detect_drift(window, threshold=self.config.get('psi_threshold', 0.2))

            results.append({
                'window_start': i - window_size,
                'window_end': i,
                'psi': psi,
                'drift_detected': drift['drift_detected'],
                'severity': drift['severity'],
            })

        return results
