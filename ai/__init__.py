# -*- coding: utf-8 -*-
"""
ai/__init__.py
--------------
حزمة نماذج الذكاء الاصطناعي (AI Models).

تحتوي على نماذج التنبؤ بالطلبات وتحليل الأنماط والميزات المتقدمة.

الإصدار: 3.0
تاريخ التحديث: أبريل 2026
"""

from ai.order_predictor import AdvancedOrderPredictionModel
from ai.feature_engineering import AdvancedFeatureEngineer
from ai.advanced_models import (
    ModelFactory,
    EnsembleModel,
    StackingModel,
    LinearRegressionModel,
    RandomForestModel,
    GradientBoostingModel,
)
from ai.metrics import (
    MetricsCalculator,
    ModelEvaluator,
    DriftDetector,
)

__all__ = [
    # النموذج الرئيسي
    "AdvancedOrderPredictionModel",
    
    # معالجة الميزات
    "AdvancedFeatureEngineer",
    
    # النماذج المتقدمة
    "ModelFactory",
    "EnsembleModel",
    "StackingModel",
    "LinearRegressionModel",
    "RandomForestModel",
    "GradientBoostingModel",
    
    # المقاييس
    "MetricsCalculator",
    "ModelEvaluator",
    "DriftDetector",
]

__version__ = "3.0"
