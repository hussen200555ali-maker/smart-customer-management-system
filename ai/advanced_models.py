# -*- coding: utf-8 -*-
"""
ai/advanced_models.py
--------------------
وحدة النماذج المتقدمة للذكاء الاصطناعي.
تحتوي على نماذج XGBoost, LightGBM, Prophet, Ensemble, Stacking.

الإصدار: 3.0
تاريخ التحديث: أبريل 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from abc import ABC, abstractmethod
import warnings

from config import (
    AI_XGBOOST_CONFIG,
    AI_LIGHTGBM_CONFIG,
    AI_PROPHET_CONFIG,
    AI_ENSEMBLE_CONFIG,
    AI_STACKING_CONFIG,
    AI_METRICS_CONFIG,
)

warnings.filterwarnings('ignore')


class BaseModel(ABC):
    """النموذج الأساسي المجرد"""

    @abstractmethod
    def fit(self, X, y):
        """تدريب النموذج"""
        pass

    @abstractmethod
    def predict(self, X) -> np.ndarray:
        """التنبؤ"""
        pass

    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """الحصول على معلمات النموذج"""
        pass

    def get_feature_importance(self) -> Optional[np.ndarray]:
        """الحصول على أهمية الميزات"""
        return None


class LinearRegressionModel(BaseModel):
    """نموذج الانحدار الخطي"""

    def __init__(self):
        from sklearn.linear_model import Ridge
        self.model = Ridge(alpha=1.0, random_state=42)
        self.feature_names = []

    def fit(self, X, y):
        self.model.fit(X, y)
        if hasattr(X, 'columns'):
            self.feature_names = list(X.columns)
        return self

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X)

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'linear_regression',
            'coefficients': self.model.coef_.tolist() if hasattr(self.model, 'coef_') else [],
            'intercept': float(self.model.intercept_) if hasattr(self.model, 'intercept_') else 0,
        }

    def get_feature_importance(self) -> np.ndarray:
        if hasattr(self.model, 'coef_'):
            return np.abs(self.model.coef_)
        return None


class RandomForestModel(BaseModel):
    """نموذج الغابة العشوائية"""

    def __init__(self, config: Dict = None):
        from sklearn.ensemble import RandomForestRegressor
        cfg = config or {}
        self.model = RandomForestRegressor(**cfg)
        self.feature_names = []

    def fit(self, X, y):
        self.model.fit(X, y)
        if hasattr(X, 'columns'):
            self.feature_names = list(X.columns)
        return self

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X)

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'random_forest',
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
        }

    def get_feature_importance(self) -> np.ndarray:
        if hasattr(self.model, 'feature_importances_'):
            return self.model.feature_importances_
        return None


class GradientBoostingModel(BaseModel):
    """نموذج التدرج المتصاعد"""

    def __init__(self):
        from sklearn.ensemble import GradientBoostingRegressor
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            random_state=42
        )
        self.feature_names = []

    def fit(self, X, y):
        self.model.fit(X, y)
        if hasattr(X, 'columns'):
            self.feature_names = list(X.columns)
        return self

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X)

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'gradient_boosting',
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'learning_rate': self.model.learning_rate,
        }

    def get_feature_importance(self) -> np.ndarray:
        if hasattr(self.model, 'feature_importances_'):
            return self.model.feature_importances_
        return None


class XGBoostModel(BaseModel):
    """نموذج XGBoost المتقدم"""

    def __init__(self, config: Dict = None):
        self.config = config or AI_XGBOOST_CONFIG.copy()
        self._check_xgboost()

    def _check_xgboost(self):
        """التحقق من وجود XGBoost"""
        try:
            import xgboost as xgb
            self.xgb = xgb
        except ImportError:
            warnings.warn("XGBoost غير متوفر. سيتم استخدام نموذج بديل.")
            self.xgb = None
            raise ImportError("XGBoost غير مثبت. يرجى تثبيته: pip install xgboost")

    def fit(self, X, y):
        if self.xgb is None:
            raise ImportError("XGBoost غير متوفر")

        self.model = self.xgb.XGBRegressor(**self.config)
        self.model.fit(X, y)
        return self

    def predict(self, X) -> np.ndarray:
        if self.model is None:
            raise ValueError("النموذج غير مدرب")
        return self.model.predict(X)

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'xgboost',
            'config': self.config,
        }

    def get_feature_importance(self) -> np.ndarray:
        if hasattr(self.model, 'feature_importances_'):
            return self.model.feature_importances_
        return None


class LightGBMModel(BaseModel):
    """نموذج LightGBM المتقدم"""

    def __init__(self, config: Dict = None):
        self.config = config or AI_LIGHTGBM_CONFIG.copy()
        self._check_lightgbm()

    def _check_lightgbm(self):
        """التحقق من وجود LightGBM"""
        try:
            import lightgbm as lgb
            self.lgb = lgb
        except ImportError:
            warnings.warn("LightGBM غير متوفر. سيتم استخدام نموذج بديل.")
            self.lgb = None
            raise ImportError("LightGBM غير مثبت. يرجى تثبيته: pip install lightgbm")

    def fit(self, X, y):
        if self.lgb is None:
            raise ImportError("LightGBM غير متوفر")

        self.model = self.lgb.LGBMRegressor(**self.config)
        self.model.fit(X, y)
        return self

    def predict(self, X) -> np.ndarray:
        if self.model is None:
            raise ValueError("النموذج غير مدرب")
        return self.model.predict(X)

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'lightgbm',
            'config': self.config,
        }

    def get_feature_importance(self) -> np.ndarray:
        if hasattr(self.model, 'feature_importances_'):
            return self.model.feature_importances_
        return None


class ProphetModel(BaseModel):
    """نموذج Prophet للتنبؤ بالسلاسل الزمنية"""

    def __init__(self, config: Dict = None):
        self.config = config or AI_PROPHET_CONFIG.copy()
        self._check_prophet()

    def _check_prophet(self):
        """التحقق من وجود Prophet"""
        try:
            from prophet import Prophet
            self.Prophet = Prophet
        except ImportError:
            warnings.warn("Prophet غير متوفر. سيتم استخدام نموذج بديل.")
            self.Prophet = None
            raise ImportError("Prophet غير مثبت. يرجى تثبيته: pip install prophet")

    def fit(self, X, y=None):
        """تدريب نموذج Prophet"""
        if self.Prophet is None:
            raise ImportError("Prophet غير متوفر")

        # Prophet يتطلب تنسيقاً خاصاً
        if isinstance(X, pd.DataFrame):
            self.train_df = X.copy()
        else:
            raise ValueError("Prophet يتطلب DataFrame للبيانات")

        # إنشاء نموذج Prophet
        self.model = self.Prophet(
            yearly_seasonality=self.config.get('yearly_seasonality', True),
            weekly_seasonality=self.config.get('weekly_seasonality', True),
            daily_seasonality=self.config.get('daily_seasonality', False),
            seasonality_mode=self.config.get('seasonality_mode', 'multiplicative'),
        )

        # إضافة البيانات
        df = self.train_df.copy()
        df.columns = ['ds', 'y']
        self.model.fit(df)

        return self

    def predict(self, X) -> np.ndarray:
        """التنبؤ"""
        if self.model is None:
            raise ValueError("النموذج غير مدرب")

        if isinstance(X, pd.DataFrame):
            future = X.copy()
            future.columns = ['ds']
        else:
            future = pd.DataFrame({'ds': X})

        forecast = self.model.predict(future)
        return forecast['yhat'].values

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'prophet',
            'config': self.config,
        }

    def get_feature_importance(self) -> Optional[np.ndarray]:
        # Prophet يوفر معلومات مختلفة عن importance
        return None


class EnsembleModel(BaseModel):
    """نموذج تجميع يجمع عدة نماذج"""

    def __init__(self, models: List[BaseModel] = None, config: Dict = None):
        self.config = config or AI_ENSEMBLE_CONFIG.copy()
        self.models = models or []
        self.weights = self.config.get('weights', [1] * len(self.models))

    def add_model(self, model: BaseModel, weight: float = 1.0):
        """إضافة نموذج للمجموعة"""
        self.models.append(model)
        self.weights.append(weight)

    def fit(self, X, y):
        """تدريب جميع النماذج"""
        for model in self.models:
            model.fit(X, y)
        return self

    def predict(self, X) -> np.ndarray:
        """التنبؤ بالمتوسط الموزون"""
        if not self.models:
            raise ValueError("لا توجد نماذج في المجموعة")

        predictions = []
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)

        # حساب المتوسط الموزون
        predictions = np.array(predictions)
        weights = np.array(self.weights)[:len(predictions)]
        weights = weights / weights.sum()

        weighted_pred = np.average(predictions, axis=0, weights=weights)
        return weighted_pred

    def predict_with_uncertainty(self, X) -> Tuple[np.ndarray, np.ndarray]:
        """التنبؤ مع قياس عدم اليقين"""
        if not self.models:
            raise ValueError("لا توجد نماذج في المجموعة")

        predictions = []
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)

        predictions = np.array(predictions)

        # المتوسط
        mean_pred = np.mean(predictions, axis=0)

        # الانحراف المعياري ك medida لعدم اليقين
        std_pred = np.std(predictions, axis=0)

        return mean_pred, std_pred

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'ensemble',
            'models': [m.get_params() for m in self.models],
            'weights': self.weights,
        }

    def get_feature_importance(self) -> Optional[np.ndarray]:
        """متوسط أهمية الميزات من جميع النماذج"""
        importances = []
        for model in self.models:
            imp = model.get_feature_importance()
            if imp is not None:
                importances.append(imp)

        if importances:
            return np.mean(importances, axis=0)
        return None


class StackingModel(BaseModel):
    """نموذج stacking يجمع نواتج نماذج أساسية"""

    def __init__(self, base_models: List[BaseModel] = None, meta_model: BaseModel = None):
        self.base_models = base_models or []
        self.meta_model = meta_model or LinearRegressionModel()

    def add_base_model(self, model: BaseModel):
        """إضافة نموذج أساسي"""
        self.base_models.append(model)

    def fit(self, X, y, cv_folds: int = 5):
        """تدريب بنمط stacking"""
        from sklearn.model_selection import KFold

        n_samples = len(X)
        n_models = len(self.base_models)

        # إنشاء مصفوفة التنبؤات للنموذج meta
        meta_features = np.zeros((n_samples, n_models))

        kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=42)

        # تدريب النماذج الأساسية مع التحقق المتقاطع
        for train_idx, val_idx in kfold.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train = y[train_idx]

            for i, model in enumerate(self.base_models):
                model.fit(X_train, y_train)
                meta_features[val_idx, i] = model.predict(X_val)

        # تدريب النموذج meta على التنبؤات
        self.meta_model.fit(meta_features, y)

        # إعادة تدريب النماذج الأساسية على كامل البيانات
        for model in self.base_models:
            model.fit(X, y)

        return self

    def predict(self, X) -> np.ndarray:
        """التنبؤ باستخدام stacking"""
        if not self.base_models:
            raise ValueError("لا توجد نماذج أساسية")

        meta_features = np.zeros((len(X), len(self.base_models)))

        for i, model in enumerate(self.base_models):
            meta_features[:, i] = model.predict(X)

        return self.meta_model.predict(meta_features)

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'stacking',
            'base_models': [m.get_params() for m in self.base_models],
            'meta_model': self.meta_model.get_params(),
        }


class ModelFactory:
    """مصنع النماذج لإنشاء النماذج بسهولة"""

    _model_classes = {
        'linear': LinearRegressionModel,
        'random_forest': RandomForestModel,
        'gradient_boosting': GradientBoostingModel,
        'xgboost': XGBoostModel,
        'lightgbm': LightGBMModel,
        'prophet': ProphetModel,
    }

    @classmethod
    def create(cls, model_type: str, **kwargs) -> BaseModel:
        """إنشاء نموذج حسب النوع"""
        if model_type not in cls._model_classes:
            raise ValueError(
                f"نوع النموذج '{model_type}' غير مدعوم. "
                f"الأنواع المدعومة: {list(cls._model_classes.keys())}"
            )

        model_class = cls._model_classes[model_type]

        # معالجة خاصة لبعض النماذج
        if model_type == 'random_forest':
            return model_class(config=kwargs.get('config', AI_RANDOM_FOREST_CONFIG))
        elif model_type in ['xgboost', 'lightgbm']:
            return model_class(config=kwargs.get('config'))
        elif model_type == 'prophet':
            return model_class(config=kwargs.get('config', AI_PROPHET_CONFIG))
        else:
            return model_class()

    @classmethod
    def create_ensemble(
        cls,
        model_types: List[str] = None,
        weights: List[float] = None
    ) -> EnsembleModel:
        """إنشاء نموذج تجميع"""
        model_types = model_types or ['linear', 'random_forest', 'xgboost', 'lightgbm']
        weights = weights or [1, 2, 2, 3]

        models = []
        for model_type in model_types:
            try:
                model = cls.create(model_type)
                models.append(model)
            except (ImportError, ValueError) as e:
                warnings.warn(f"تعذر إضافة نموذج {model_type}: {e}")

        return EnsembleModel(models=models, config={'weights': weights[:len(models)]})

    @classmethod
    def create_stacking(
        cls,
        base_model_types: List[str] = None,
        meta_model_type: str = 'linear'
    ) -> StackingModel:
        """إنشاء نموذج stacking"""
        base_model_types = base_model_types or ['random_forest', 'xgboost', 'lightgbm']

        base_models = []
        for model_type in base_model_types:
            try:
                model = cls.create(model_type)
                base_models.append(model)
            except (ImportError, ValueError) as e:
                warnings.warn(f"تعذر إضافة نموذج أساسي {model_type}: {e}")

        meta_model = cls.create(meta_model_type)

        return StackingModel(base_models=base_models, meta_model=meta_model)
