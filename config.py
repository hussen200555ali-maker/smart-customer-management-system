# -*- coding: utf-8 -*-
"""
config.py
---------
ملف التكوينات الموحد لنظام إدارة الخدمات الذكي
 والذكاء الاصطناعي.
الإصدار: 4.0 - دعم MySQL عبر XAMPP

تاريخ التحديث: أبريل 2026
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# مسارات النظام
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
INVOICES_DIR = os.path.join(BASE_DIR, "invoices")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
MODELS_DIR = os.path.join(BASE_DIR, "models")
FONTS_DIR = os.path.join(BASE_DIR, "ui", "assets", "fonts")
AI_MODELS_DIR = os.path.join(BASE_DIR, "ai_models")
DATA_WAREHOUSE_DIR = os.path.join(BASE_DIR, "data_warehouse")

# إنشاء المجلدات إذا لم تكن موجودة
for directory in [MODELS_DIR, AI_MODELS_DIR, DATA_WAREHOUSE_DIR, LOGS_DIR, INVOICES_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# إعدادات قاعدة بيانات MySQL (XAMPP)
# ═══════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────
# إعدادات الاتصال بـ MySQL
# ──────────────────────────────────────────────
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_NAME = os.environ.get("DB_NAME", "service_management")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# إعدادات الترميز للغة العربية
DB_CHARSET = "utf8mb4"
DB_COLLATION = "utf8mb4_unicode_ci"

# ──────────────────────────────────────────────
# إعدادات تجمع الاتصالات (Connection Pool)
# ──────────────────────────────────────────────
DB_POOL_ENABLED = True
DB_POOL_SIZE = 10
DB_POOL_MAX_OVERFLOW = 5

# ──────────────────────────────────────────────
# إعدادات الأداء والتخزين المؤقت
# ──────────────────────────────────────────────
CACHE_TIMEOUT = 300
DB_TIMEOUT = 30

# ──────────────────────────────────────────────
# دالة الحصول على إعدادات الاتصال
# ──────────────────────────────────────────────
def get_mysql_config() -> dict:
    """
    الحصول على قاموس إعدادات الاتصال بـ MySQL.
    
    Returns:
        قاموس يحتوي على جميع إعدادات الاتصال.
    """
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
        "charset": DB_CHARSET,
        "collation": DB_COLLATION,
        "autocommit": False,
        "connection_timeout": DB_TIMEOUT,
    }

# مسار قاعدة البيانات للتوافق مع بعض الدوال
DB_PATH = os.path.join(BASE_DIR, "service_management.db")
FOREIGN_KEYS_ENABLED = True

# ──────────────────────────────────────────────
# إعدادات الأمان
# ──────────────────────────────────────────────
PASSWORD_HASH_ITERATIONS = 100000
PASSWORD_HASH_ALGORITHM = "sha256"
PASSWORD_SALT_LENGTH = 16
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = 300

# ──────────────────────────────────────────────
# إعدادات النظام
# ──────────────────────────────────────────────
APP_TITLE = "نظام إدارة العملاء الذكي - Smart Customer Management System"
APP_VERSION = "3.0"
DEFAULT_LOCALE = "ar_SA"

# ──────────────────────────────────────────────
# إعدادات واجهة المستخدم
# ──────────────────────────────────────────────
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
SIDEBAR_WIDTH = 250

UI_COLORS = {
    "primary": "#4361ee",
    "secondary": "#3f37c9",
    "success": "#2ec4b6",
    "danger": "#ef233c",
    "warning": "#f77f00",
    "dark": "#1a1a2e",
    "light": "#f8f9fa",
    "gray": "#6c757d",
}

# ──────────────────────────────────────────────
# إعدادات الجداول
# ──────────────────────────────────────────────
TABLE_ROW_HEIGHT = 40
TABLE_FONT = ("Cairo", 12)
TABLE_HEADER_FONT = ("Cairo", 13, "bold")
TABLE_EVEN_COLOR = "#f9f9f9"
TABLE_ODD_COLOR = "#ffffff"
TABLE_SELECTED_BG = "#2b5b84"
TABLE_SELECTED_FG = "white"

# ═══════════════════════════════════════════════════════════════════
# إعدادات الذكاء الاصطناعي المتقدمة - الإصدار 3.0
# ═══════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────
# إعدادات النماذج الأساسية
# ──────────────────────────────────────────────
AI_MODEL_PATH = os.path.join(AI_MODELS_DIR, "advanced_order_prediction_model.pkl")
AI_MODEL_PATH_LEGACY = os.path.join(AI_MODELS_DIR, "order_prediction_model.pkl")

# الحد الأدنى لعدد العينات للتدريب - زيد إلى 100 للحصول على نتائج دقيقة
AI_MIN_TRAINING_SAMPLES = 100
AI_RECOMMENDED_TRAINING_SAMPLES = 300
AI_TRAIN_TEST_SPLIT = 0.2
AI_RETRAIN_THRESHOLD = 0.8
AI_PREDICTION_DAYS = 7

# ──────────────────────────────────────────────
# إعدادات هندسة الميزات المتقدمة
# ──────────────────────────────────────────────
AI_MAX_LAG_DAYS = 30
AI_ROLLING_WINDOW_SHORT = 7
AI_ROLLING_WINDOW_LONG = 30

# ميزات التأخر الموسعة
AI_LAG_PERIODS = [1, 3, 7, 14, 21, 30, 60, 90]
AI_ROLLING_WINDOWS = [3, 7, 14, 30, 60]

# ──────────────────────────────────────────────
# إعدادات تقسيم العملاء والتوصيات
# ──────────────────────────────────────────────
AI_CUSTOMER_SEGMENTS = 4
AI_RECOMMENDATION_TOP_N = 5
AI_FORECAST_MONTHS = 3

# ──────────────────────────────────────────────
# إعدادات النماذج المتقدمة
# ──────────────────────────────────────────────
AI_AVAILABLE_MODELS = {
    "linear_regression": True,
    "random_forest": True,
    "gradient_boosting": True,
    "xgboost": True,
    "lightgbm": True,
    "prophet": True,
    "lstm": False,  # يتطلب TensorFlow
    "ensemble": True,
    "stacking": True,
}

# إعدادات الغابة العشوائية
AI_RANDOM_FOREST_CONFIG = {
    "n_estimators": 200,
    "max_depth": 15,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "max_features": "sqrt",
    "random_state": 42,
    "n_jobs": -1,
    "bootstrap": True,
}

# إعدادات XGBoost
AI_XGBOOST_CONFIG = {
    "n_estimators": 300,
    "max_depth": 8,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "random_state": 42,
    "n_jobs": -1,
}

# إعدادات LightGBM
AI_LIGHTGBM_CONFIG = {
    "n_estimators": 300,
    "max_depth": 8,
    "learning_rate": 0.05,
    "num_leaves": 50,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "random_state": 42,
    "n_jobs": -1,
    "verbose": -1,
}

# إعدادات LSTM
AI_LSTM_CONFIG = {
    "sequence_length": 30,
    "lstm_units": [64, 32],
    "dropout": 0.2,
    "dense_units": [16, 8],
    "epochs": 100,
    "batch_size": 32,
    "early_stopping_patience": 10,
}

# إعدادات Prophet
AI_PROPHET_CONFIG = {
    "yearly_seasonality": True,
    "weekly_seasonality": True,
    "daily_seasonality": False,
    "seasonality_mode": "multiplicative",
    "changepoint_prior_scale": 0.05,
    "seasonality_prior_scale": 10.0,
    "holidays_prior_scale": 10.0,
}

# ──────────────────────────────────────────────
# إعدادات النماذج المجمعة (Ensemble)
# ──────────────────────────────────────────────
AI_ENSEMBLE_CONFIG = {
    "voting": "soft",
    "weights": [1, 2, 2, 3],  # [linear, rf, xgb, lgb]
    "models": ["linear", "random_forest", "xgboost", "lightgbm"],
}

AI_STACKING_CONFIG = {
    "base_models": ["random_forest", "xgboost", "lightgbm"],
    "meta_model": "linear",
    "cv_folds": 5,
}

# ──────────────────────────────────────────────
# إعدادات التحقق المتقاطع للسلاسل الزمنية
# ──────────────────────────────────────────────
AI_TIME_SERIES_CV_CONFIG = {
    "n_splits": 5,
    "gap": 7,  # فجوة بين التدريب والاختبار
    "test_size": 30,  # حجم مجموعة الاختبار
}

# ──────────────────────────────────────────────
# إعدادات التنبؤ المستقبلي المتعدد الخطوات
# ──────────────────────────────────────────────
AI_MULTI_STEP_FORECAST_CONFIG = {
    "short_term_days": 7,
    "medium_term_days": 30,
    "long_term_days": 90,
    "max_forecast_horizon": 365,
    "confidence_interval_alpha": 0.95,
    "recursive_prediction": True,
    "direct_prediction": False,
    "stride": 1,
}

# ──────────────────────────────────────────────
# إعدادات التعلم المستمر
# ──────────────────────────────────────────────
AI_CONTINUOUS_LEARNING_CONFIG = {
    "enabled": True,
    "retrain_interval_days": 7,
    "min_new_samples_for_retrain": 50,
    "performance_threshold": 0.85,  # أقل أداء مقبول
    "auto_deploy": False,  # نشر تلقائي أم موافقة يدوية
    "monitoring_window_days": 30,
    "drift_detection_threshold": 0.1,  # حد اكتشاف الانحراف
}

# ──────────────────────────────────────────────
# إعدادات اكتشاف الانحراف
# ──────────────────────────────────────────────
AI_DRIFT_DETECTION_CONFIG = {
    "method": "population_stability_index",  # أو "wasserstein" أو "kl_divergence"
    "psi_threshold": 0.2,
    "window_size": 100,
    "check_interval": 7,
}

# ──────────────────────────────────────────────
# إعدادات التفسير (Explainability)
# ──────────────────────────────────────────────
AI_EXPLAINABILITY_CONFIG = {
    "enabled": True,
    "methods": ["shap", "lime", "permutation"],
    "shap_sample_size": 100,
    "lime_sample_size": 1000,
    "n_permutations": 10,
    "top_features_display": 10,
}

# ──────────────────────────────────────────────
# إعدادات معالجة اللغة الطبيعية
# ──────────────────────────────────────────────
AI_NLP_CONFIG = {
    "enabled": False,  # يتطلب نماذج عربية متخصصة
    "sentiment_analysis": True,
    "keyword_extraction": True,
    "text_classification": True,
    "embedding_model": "arabert",  # أو "sentence_transformers"
}

# ──────────────────────────────────────────────
# إعدادات البيانات الموسمية والعطلات
# ──────────────────────────────────────────────
AI_SEASONALITY_CONFIG = {
    # عطلات عربية وإسلامية
    "arab_holidays": [
        {"name": "رمضان", "month": 3, "day": 1, "duration": 30},
        {"name": "عيد الفطر", "month": 10, "day": 1, "duration": 3},
        {"name": "عيد الأضحى", "month": 12, "day": 10, "duration": 4},
        {"name": "رأس السنة الهجرية", "month": 1, "day": 1, "duration": 1},
        {"name": "المولد النبوي", "month": 3, "day": 12, "duration": 1},
    ],
    # عطلات رسمية (يمكن تخصيصها حسب الدولة)
    "official_holidays": [
        {"name": "رأس السنة الميلادية", "month": 1, "day": 1},
        {"name": "عيد الاستقلال", "month": 3, "day": 6},
        {"name": "يوم الأرض", "month": 4, "day": 30},
        {"name": "يوم العمال", "month": 5, "day": 1},
        {"name": "عيد الاستقلال", "month": 11, "day": 18},
    ],
    # فصول السنة
    "seasons": {
        "spring": {"start_month": 3, "start_day": 20, "end_month": 6, "end_day": 20},
        "summer": {"start_month": 6, "start_day": 21, "end_month": 9, "end_day": 22},
        "autumn": {"start_month": 9, "start_day": 23, "end_month": 12, "end_day": 20},
        "winter": {"start_month": 12, "start_day": 21, "end_month": 3, "end_day": 19},
    },
    # أيام خاصة بالنشاط
    "special_days": [
        {"name": "الجمعة البيضاء", "day_of_week": 4, "week_of_month": -1},
        {"name": "الاثنين الإلكتروني", "day_of_week": 0, "week_of_month": -1},
        {"name": "الصيف促销", "month": 7, "day_range": (1, 31)},
        {"name": "الربيع促销", "month": 4, "day_range": (1, 15)},
    ],
}

# ──────────────────────────────────────────────
# إعدادات الميزات السلوكية للعملاء
# ──────────────────────────────────────────────
AI_CUSTOMER_BEHAVIOR_CONFIG = {
    "compute_ltv": True,  # Lifetime Value
    "compute_recency": True,
    "compute_frequency": True,
    "compute_monetary": True,
    "rfm_weight_recency": 0.25,
    "rfm_weight_frequency": 0.25,
    "rfm_weight_monetary": 0.50,
    "churn_threshold_days": 90,
    "high_value_threshold_percentile": 80,
}

# ──────────────────────────────────────────────
# إعدادات تنبؤ الإيرادات
# ──────────────────────────────────────────────
AI_REVENUE_FORECAST_CONFIG = {
    "forecast_horizons": [30, 60, 90, 180, 365],
    "confidence_levels": [0.80, 0.90, 0.95],
    "include_scenarios": True,  # متفائل، متشائم، أساسي
    "growth_rate_cap": 0.5,  # حد أقصى لمعدل النمو
    "seasonal_adjustment": True,
}

# ──────────────────────────────────────────────
# إعدادات التصنيف والتوصية
# ──────────────────────────────────────────────
AI_CLASSIFICATION_CONFIG = {
    "similarity_threshold": 0.5,
    "min_similar_customers": 5,
    "collaborative_filtering": True,
    "content_based_filtering": True,
    "hybrid_weight": 0.5,  # وزن المرشح التعاوني مقابل المحتوى
}

# ──────────────────────────────────────────────
# إعدادات مقاييس الأداء
# ──────────────────────────────────────────────
AI_METRICS_CONFIG = {
    "primary_metrics": ["mae", "rmse", "mape"],
    "time_series_metrics": ["mase", "theil_u", "smape"],
    "business_metrics": ["within_threshold_pct", "directional_accuracy"],
    "threshold_percentage": 0.15,  # 15% من القيمة الفعلية
}

# ──────────────────────────────────────────────
# إعدادات التسجيل والمراقبة
# ──────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

AI_LOGGING_CONFIG = {
    "log_predictions": True,
    "log_feature_importance": True,
    "log_drift_alerts": True,
    "log_retrain_events": True,
    "alert_thresholds": {
        "accuracy_drop": 0.1,  # تنبيه عند انخفاض الدقة 10%
        "drift_detected": 0.2,
        "low_sample_count": 50,
    },
}

# ──────────────────────────────────────────────
# إعدادات الاستيراد والتصدير
# ──────────────────────────────────────────────
EXPORT_FORMATS = ["csv", "excel", "json"]
IMPORT_MAX_FILE_SIZE = 10 * 1024 * 1024

# ──────────────────────────────────────────────
# إعدادات الفواتير
# ──────────────────────────────────────────────
INVOICE_NUMBER_FORMAT = "invoice_{order_id}_{date}_{time}"
INVOICE_DATE_FORMAT = "%Y%m%d"
INVOICE_TIME_FORMAT = "%H%M%S"

# ──────────────────────────────────────────────
# إعدادات النسخ الاحتياطي
# ──────────────────────────────────────────────
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
BACKUP_MAX_COPIES = 7
BACKUP_AUTO_ENABLED = True
BACKUP_AUTO_INTERVAL_HOURS = 24

# ──────────────────────────────────────────────
# إعدادات الأمان المتقدمة
# ──────────────────────────────────────────────
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_EXPIRY_DAYS = 90
ENCRYPTION_KEY_FILE = os.path.join(BASE_DIR, ".encryption_key")

# ──────────────────────────────────────────────
# إعدادات أداء قاعدة البيانات
# ──────────────────────────────────────────────
# ملاحظة: تم نقل إعدادات الأداء إلى إعدادات MySQL أعلاه
