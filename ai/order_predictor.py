# -*- coding: utf-8 -*-
"""
ai/order_predictor.py
---------------------
نموذج ذكاء اصطناعي متقدم للتنبؤ بالطلبات المستقبلية وتحليل الأنماط.

الإصدار: 3.0 - جميع الميزات المتقدمة
تاريخ التحديث: أبريل 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any, Optional
import joblib
import os
import warnings

from config import (
    AI_MODEL_PATH,
    AI_MODELS_DIR,
    AI_MIN_TRAINING_SAMPLES,
    AI_RECOMMENDED_TRAINING_SAMPLES,
    AI_MAX_LAG_DAYS,
    AI_ROLLING_WINDOW_SHORT,
    AI_ROLLING_WINDOW_LONG,
    AI_CUSTOMER_SEGMENTS,
    AI_RECOMMENDATION_TOP_N,
    AI_FORECAST_MONTHS,
    AI_MULTI_STEP_FORECAST_CONFIG,
    AI_AVAILABLE_MODELS,
)

warnings.filterwarnings('ignore', category=FutureWarning)


class AdvancedOrderPredictionModel:
    """
    نموذج ذكاء اصطناعي للتنبؤ بالطلبات المستقبلية
    الإصدار 3.0 - مع جميع الميزات المتقدمة
    """

    def __init__(self, model_type: str = "ensemble"):
        """تهيئة نموذج التنبؤ"""
        self.model_type = model_type
        self.model_path = AI_MODEL_PATH
        self.scaler = None
        self.is_trained = False
        self.training_metrics = {}
        self._feature_names = []
        self._feature_engineer = None
        self._metrics_calculator = None
        self._last_known_values = {}
        self._training_data = None
        self._config = AI_MULTI_STEP_FORECAST_CONFIG.copy()

        # استيراد وإنشاء النماذج
        self._initialize_models()
        
        # تحميل النموذج إذا كان موجوداً
        if os.path.exists(self.model_path):
            try:
                self._load_model()
            except Exception:
                self.is_trained = False
                self._initialize_models()

    def _initialize_models(self):
        """تهيئة النماذج"""
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans
        
        self._ridge = Ridge(alpha=1.0, random_state=42)
        self._rf = RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_split=5,
            min_samples_leaf=2, random_state=42, n_jobs=-1
        )
        self._gb = GradientBoostingRegressor(
            n_estimators=200, max_depth=8, learning_rate=0.05, random_state=42
        )
        self._ensemble = VotingRegressor(
            estimators=[
                ('ridge', Ridge(alpha=1.0, random_state=42)),
                ('rf', RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)),
                ('gb', GradientBoostingRegressor(n_estimators=200, max_depth=8, learning_rate=0.05, random_state=42)),
            ],
            weights=[1, 2, 2]
        )
        self._scaler = StandardScaler()
        
        # استخدام VotingRegressor كالنموذج الرئيسي
        self.model = self._ensemble
        
        # ميزات التأخر
        self._lag_periods = [1, 3, 7, 14, 21, 30, 60, 90]
        self._rolling_windows = [3, 7, 14, 30, 60]

    def _safe_numeric(self, value: Any) -> float:
        """تحويل القيمة إلى رقم بشكل آمن"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(',', ''))
            except ValueError:
                return 0.0
        if isinstance(value, dict):
            # إذا كانت القيمة قواميس، استخرج منها القيمة المناسبة
            return 0.0
        return 0.0

    def prepare_features(self, orders_data: List[Dict]) -> Tuple[np.ndarray, List[str]]:
        """تحضير الميزات المتقدمة من بيانات الطلبات"""
        if not orders_data:
            return np.array([]), []

        df = pd.DataFrame(orders_data)
        
        # ⭐⭐⭐ تحويل الأعمدة المعقدة إلى ميزات رقمية مفيدة ⭐⭐⭐
        
        # 1. عمود service_ids (قائمة أرقام) -> عدد الخدمات في الطلب
        if 'service_ids' in df.columns:
            df['num_services'] = df['service_ids'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            df = df.drop(columns=['service_ids'])
        
        # 2. عمود service_quantities (قائمة أرقام) -> إجمالي الكميات المطلوبة
        if 'service_quantities' in df.columns:
            df['total_quantity'] = df['service_quantities'].apply(
                lambda x: sum(x) if isinstance(x, list) else 0
            )
            df = df.drop(columns=['service_quantities'])
        
        # 3. عمود details (قائمة قواميس) -> عدد التفاصيل + مجموع الأسعار
        if 'details' in df.columns:
            # عدد تفاصيل الطلب
            df['details_count'] = df['details'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            
            # مجموع الأسعار من التفاصيل
            def sum_details_total(details):
                if not isinstance(details, list):
                    return 0.0
                total = 0.0
                for d in details:
                    if isinstance(d, dict) and 'total_price' in d:
                        try:
                            total += float(d.get('total_price', 0))
                        except (ValueError, TypeError):
                            pass
                return total
            
            df['details_total'] = df['details'].apply(sum_details_total)
            df = df.drop(columns=['details'])
        
        # قائمة الأعمدة النصية التي لا يجب تحويلها
        text_cols = ['created_at', 'customer_name', 'customer_phone', 
                     'status', 'notes', 'customer_email', 'customer_address', 
                     'updated_at', 'services_info', 'service_names']
        
        # تنظيف البيانات: التأكد من أن جميع القيم رقمية
        for col in df.columns:
            if col not in text_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # تحويل created_at بشكل آمن
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # إزالة الصفوف التي لا تحتوي على تاريخ صالح
        df = df.dropna(subset=['created_at'])
        
        if len(df) == 0:
            return np.array([]), []

        # تجميع يومي
        daily = df.groupby(df['created_at'].dt.date).agg({
            'id': 'count',
            'customer_id': 'nunique',
        }).reset_index()
        daily.columns = ['date', 'order_count', 'unique_customers']
        daily['date'] = pd.to_datetime(daily['date'])
        daily = daily.sort_values('date').reset_index(drop=True)

        # إضافة الإيرادات اليومية
        if 'total_amount' in df.columns:
            revenue = df.groupby(df['created_at'].dt.date)['total_amount'].sum()
            daily = daily.merge(
                pd.DataFrame({
                    'date': pd.to_datetime(revenue.index),
                    'daily_revenue': revenue.values
                }),
                on='date', how='left'
            )
            daily['daily_revenue'] = daily['daily_revenue'].fillna(0)

        # الميزات الزمنية الأساسية
        daily['year'] = daily['date'].dt.year
        daily['month'] = daily['date'].dt.month
        daily['day'] = daily['date'].dt.day
        daily['day_of_week'] = daily['date'].dt.dayofweek
        daily['day_of_year'] = daily['date'].dt.dayofyear
        daily['week_of_year'] = daily['date'].dt.isocalendar().week.astype(int)
        daily['quarter'] = daily['date'].dt.quarter

        # ميزات خاصة
        daily['is_weekend'] = (daily['day_of_week'] >= 5).astype(int)
        daily['is_month_start'] = daily['date'].dt.is_month_start.astype(int)
        daily['is_month_end'] = daily['date'].dt.is_month_end.astype(int)
        daily['is_friday'] = (daily['day_of_week'] == 4).astype(int)
        daily['is_monday'] = (daily['day_of_week'] == 0).astype(int)

        # الترميز الدوري
        daily['month_sin'] = np.sin(2 * np.pi * daily['month'] / 12)
        daily['month_cos'] = np.cos(2 * np.pi * daily['month'] / 12)
        daily['day_of_week_sin'] = np.sin(2 * np.pi * daily['day_of_week'] / 7)
        daily['day_of_week_cos'] = np.cos(2 * np.pi * daily['day_of_week'] / 7)
        daily['day_of_year_sin'] = np.sin(2 * np.pi * daily['day_of_year'] / 365)
        daily['day_of_year_cos'] = np.cos(2 * np.pi * daily['day_of_year'] / 365)

        # فصول السنة
        def get_season(month):
            if 3 <= month <= 6: return 0
            elif 7 <= month <= 9: return 1
            elif 10 <= month <= 11: return 2
            else: return 3
        daily['season'] = daily['month'].apply(get_season)

        # ميزات التأخر
        for lag in self._lag_periods:
            if lag <= len(daily):
                daily[f'order_count_lag_{lag}'] = daily['order_count'].shift(lag)
                if 'daily_revenue' in daily.columns:
                    daily[f'revenue_lag_{lag}'] = daily['daily_revenue'].shift(lag)

        # المتوسطات المتحركة
        for window in self._rolling_windows:
            if window <= len(daily):
                daily[f'rolling_mean_{window}'] = daily['order_count'].rolling(window=window, min_periods=1).mean()
                daily[f'rolling_std_{window}'] = daily['order_count'].rolling(window=window, min_periods=1).std()
                daily[f'rolling_max_{window}'] = daily['order_count'].rolling(window=window, min_periods=1).max()
                daily[f'rolling_min_{window}'] = daily['order_count'].rolling(window=window, min_periods=1).min()

        # نسب التغيير
        for lag in [1, 7, 14]:
            if f'order_count_lag_{lag}' in daily.columns:
                daily[f'change_{lag}'] = (daily['order_count'] - daily[f'order_count_lag_{lag}']) / (daily[f'order_count_lag_{lag}'] + 1)

        # نسبة اليوم لنفس اليوم في الأسبوع الماضي
        if 'order_count_lag_7' in daily.columns:
            daily['same_day_last_week_ratio'] = daily['order_count'] / (daily['order_count_lag_7'] + 1)

        # ميزات الاتجاه
        if len(daily) > 7:
            x = np.arange(len(daily))
            z = np.polyfit(x, daily['order_count'].fillna(0), 1)
            daily['trend_slope'] = z[0]
            daily['trend_value'] = z[0] * x + z[1]
            daily['deviation_from_trend'] = (daily['order_count'] - daily['trend_value']) / (daily['trend_value'] + 1)

        # ميزات الإيرادات
        if 'daily_revenue' in daily.columns:
            daily['avg_order_value'] = daily['daily_revenue'] / (daily['order_count'] + 1)
            daily['revenue_growth'] = daily['daily_revenue'].pct_change()

        # ترتيب الأيام
        daily['days_since_start'] = (daily['date'] - daily['date'].min()).dt.days

        # حفظ البيانات للتدريب
        self._training_data = daily.copy()

        # تحديد الميزات
        exclude_cols = ['date', 'order_count', 'daily_revenue']
        feature_cols = [c for c in daily.columns if c not in exclude_cols]
        
        # تعبئة القيم المفقودة
        daily[feature_cols] = daily[feature_cols].fillna(0)
        daily[feature_cols] = daily[feature_cols].replace([np.inf, -np.inf], 0)

        features = daily[feature_cols].values.astype(float)
        self._feature_names = feature_cols

        return features, feature_cols

    def train(self, orders_data: List[Dict]) -> Dict[str, float]:
        """تدريب النموذج مع تقييم حقيقي باستخدام TimeSeriesSplit"""
        min_samples = AI_MIN_TRAINING_SAMPLES
        if len(orders_data) < min_samples:
            raise ValueError(
                f"بيانات غير كافية للتدريب. يلزم {min_samples} طلب على الأقل. "
                f"البيانات الحالية: {len(orders_data)}."
            )

        # تحضير الميزات والهدف
        features, feature_names = self.prepare_features(orders_data)
        if len(features) == 0:
            raise ValueError("لا يمكن تحضير الميزات من البيانات المقدمة")
        
        target = self._training_data['order_count'].values
        
        # تطبيع الميزات
        features_scaled = self._scaler.fit_transform(features)
        self.scaler = self._scaler
        
        # تدريب النموذج النهائي على كامل البيانات (للاستخدام الفعلي)
        self.model.fit(features_scaled, target)
        self.is_trained = True
        
        # حفظ آخر القيم (للتوقع المستقبلي)
        last_row = self._training_data.iloc[-1]
        self._last_known_values = {}
        for fname in feature_names:
            if fname in last_row.index:
                val = last_row[fname]
                self._last_known_values[fname] = float(val) if not pd.isna(val) else 0.0
            else:
                self._last_known_values[fname] = 0.0
        
        # ═══════════════════════════════════════════════════════════════
        # تقييم حقيقي باستخدام TimeSeriesSplit (بدون تسرب بيانات)
        # ═══════════════════════════════════════════════════════════════
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
        
        # تحويل إلى numpy array إذا لزم الأمر
        if hasattr(features_scaled, 'toarray'):
            features_array = features_scaled.toarray()
        elif hasattr(features_scaled, 'todense'):
            features_array = np.array(features_scaled.todense())
        else:
            features_array = np.asarray(features_scaled)
        
        data_len = int(features_array.shape[0])
        
        # حساب n_splits و test_size بشكل آمن
        try:
            n_splits_val = min(4, max(1, int(data_len / 20)))
            test_size_val = min(14, max(2, int(data_len / 5)))
        except (TypeError, ValueError):
            n_splits_val = 2
            test_size_val = 2
        
        if data_len < 20:
            # بيانات قليلة جداً - استخدم تقسيم يدوي
            split_idx = int(data_len * 0.8)
            if split_idx < 2:
                split_idx = 2
            train_idx = list(range(split_idx))
            test_idx = list(range(split_idx, data_len))
            splits = [(train_idx, test_idx)]
        else:
            tscv = TimeSeriesSplit(n_splits=n_splits_val, test_size=test_size_val, gap=1)
            splits = list(tscv.split(features_array))
        
        cv_mse, cv_rmse, cv_mae, cv_mape = [], [], [], []
        
        for train_idx, test_idx in splits:
            X_tr, X_te = features_array[train_idx], features_array[test_idx]
            y_tr, y_te = target[train_idx], target[test_idx]
            
            # إنشاء نسخة جديدة من النموذج حسب النوع
            if self.model_type == "linear":
                temp_model = Ridge(alpha=1.0, random_state=42)
            elif self.model_type == "random_forest":
                temp_model = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
            elif self.model_type == "gradient_boosting":
                temp_model = GradientBoostingRegressor(n_estimators=200, max_depth=8, learning_rate=0.05, random_state=42)
            else:  # ensemble
                temp_model = VotingRegressor(estimators=[
                    ('ridge', Ridge(alpha=1.0, random_state=42)),
                    ('rf', RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)),
                    ('gb', GradientBoostingRegressor(n_estimators=200, max_depth=8, learning_rate=0.05, random_state=42))
                ], weights=[1, 2, 2])
            
            temp_model.fit(X_tr, y_tr)
            y_pred = temp_model.predict(X_te)
            
            mse_val = np.mean((y_te - y_pred) ** 2)
            rmse_val = np.sqrt(mse_val)
            mae_val = np.mean(np.abs(y_te - y_pred))
            # MAPE
            mask = y_te != 0
            if mask.any():
                mape_val = np.mean(np.abs((y_te[mask] - y_pred[mask]) / y_te[mask])) * 100
            else:
                mape_val = 0.0
            
            cv_mse.append(mse_val)
            cv_rmse.append(rmse_val)
            cv_mae.append(mae_val)
            cv_mape.append(mape_val)
        
        # المتوسطات النهائية
        mse = float(np.mean(cv_mse)) if cv_mse else 0.0
        rmse = float(np.mean(cv_rmse)) if cv_rmse else 0.0
        mae = float(np.mean(cv_mae)) if cv_mae else 0.0
        mape = float(np.mean(cv_mape)) if cv_mape else 0.0
        
        self.training_metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'cv_score': float(rmse),
            'cv_mean': float(rmse),
            'model_type': self.model_type,
            'features_count': len(feature_names),
            'cv_folds': len(cv_rmse),
            'cv_scores': [float(s) for s in cv_rmse],  # قائمة من RMSE لكل fold
            'data_points': int(len(target)),
            'warning': 'إذا كانت RMSE أقل من 0.5، فالبيانات بسيطة جداً أو أن التقييم لا يزال خاطئاً' if rmse < 0.5 else None
        }
        
        self._save_model()
        return self.training_metrics

    def predict_next_days(self, days: int = 7) -> List[Dict[str, Any]]:
        """التنبؤ بعدد الطلبات للأيام القادمة"""
        if not self.is_trained:
            raise ValueError("يجب تدريب النموذج أولاً")

        predictions = []
        today = datetime.now()
        current_values = self._last_known_values.copy()
        prediction_history = []

        for i in range(1, days + 1):
            future_date = today + timedelta(days=i)

            # تحديث الميزات الزمنية
            current_values['year'] = future_date.year
            current_values['month'] = future_date.month
            current_values['day'] = future_date.day
            current_values['day_of_week'] = future_date.weekday()
            current_values['day_of_year'] = (future_date - datetime(future_date.year, 1, 1)).days
            current_values['week_of_year'] = future_date.isocalendar()[1]
            current_values['quarter'] = (future_date.month - 1) // 3 + 1
            current_values['is_weekend'] = 1 if future_date.weekday() >= 5 else 0
            current_values['is_month_start'] = 1 if future_date.day <= 5 else 0
            current_values['is_month_end'] = 1 if future_date.day >= 25 else 0

            # الميزات الدورية
            current_values['month_sin'] = np.sin(2 * np.pi * future_date.month / 12)
            current_values['month_cos'] = np.cos(2 * np.pi * future_date.month / 12)
            current_values['day_of_week_sin'] = np.sin(2 * np.pi * future_date.weekday() / 7)
            current_values['day_of_week_cos'] = np.cos(2 * np.pi * future_date.weekday() / 7)
            current_values['day_of_year_sin'] = np.sin(2 * np.pi * current_values['day_of_year'] / 365)
            current_values['day_of_year_cos'] = np.cos(2 * np.pi * current_values['day_of_year'] / 365)

            # فصول السنة
            month = future_date.month
            if 3 <= month <= 6: current_values['season'] = 0
            elif 7 <= month <= 9: current_values['season'] = 1
            elif 10 <= month <= 11: current_values['season'] = 2
            else: current_values['season'] = 3

            # تحديث التأخيرات
            if prediction_history:
                current_values['order_count_lag_1'] = prediction_history[-1]
            if i >= 7 and len(prediction_history) >= 7:
                current_values['order_count_lag_7'] = prediction_history[-7]
            if i >= 30 and len(prediction_history) >= 30:
                current_values['order_count_lag_30'] = prediction_history[-30]

            # تحديث المتوسطات المتحركة
            for window in [3, 7, 14, 30]:
                if len(prediction_history) >= window:
                    recent = prediction_history[-window:]
                    current_values[f'rolling_mean_{window}'] = np.mean(recent)
                    current_values[f'rolling_std_{window}'] = np.std(recent)
                    current_values[f'rolling_max_{window}'] = np.max(recent)
                    current_values[f'rolling_min_{window}'] = np.min(recent)

            # بناء الميزات
            feature_values = [current_values.get(name, 0.0) for name in self._feature_names]
            features = np.array([feature_values])

            try:
                features_scaled = self.scaler.transform(features)
            except Exception:
                features_scaled = self.scaler.fit_transform(features)

            # التنبؤ
            predicted_orders = self.model.predict(features_scaled)[0]
            prediction_history.append(predicted_orders)

            # مستوى الثقة
            confidence = max(0.5, 0.95 - (i - 1) * 0.05)

            predictions.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'day_of_week': future_date.strftime('%A'),
                'predicted_orders': max(0, int(round(predicted_orders))),
                'confidence': round(confidence, 2),
                'confidence_lower': max(0, int(round(predicted_orders * (1 - confidence)))),
                'confidence_upper': int(round(predicted_orders * (1 + confidence))),
            })

        return predictions

    def predict_multi_horizon(self) -> Dict[str, List[Dict[str, Any]]]:
        """التنبؤ على عدة آفاق زمنية"""
        horizons = {
            'short_term': 7,
            'medium_term': 30,
            'long_term': 90,
        }

        results = {}
        for name, days in horizons.items():
            try:
                results[name] = self.predict_next_days(days)
            except Exception as e:
                results[name] = []

        return results

    def compare_models(self, orders_data: List[Dict]) -> Dict[str, Dict[str, float]]:
        """مقارنة أداء النماذج المختلفة باستخدام TimeSeriesSplit حقيقي"""
        if len(orders_data) < 50:
            raise ValueError("بيانات غير كافية للمقارنة (يلزم 50 طلباً على الأقل)")

        features, _ = self.prepare_features(orders_data)
        target = self._training_data['order_count'].values
        
        if len(features) < 30:
            return {'error': 'بيانات غير كافية (أيام قليلة)'}
        
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        from sklearn.model_selection import TimeSeriesSplit
        n_splits = min(4, len(features_scaled) // 15)
        test_size = min(10, len(features_scaled) // 6)
        tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size, gap=1)
        
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
        
        model_defs = {
            'linear': Ridge(alpha=1.0, random_state=42),
            'random_forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42),
            'ensemble': VotingRegressor(estimators=[
                ('ridge', Ridge(alpha=1.0, random_state=42)),
                ('rf', RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)),
                ('gb', GradientBoostingRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42))
            ], weights=[1, 2, 2])
        }
        
        results = {}
        for name, model_template in model_defs.items():
            mse_list, rmse_list, mae_list = [], [], []
            for train_idx, test_idx in tscv.split(features_scaled):
                X_tr, X_te = features_scaled[train_idx], features_scaled[test_idx]
                y_tr, y_te = target[train_idx], target[test_idx]
                
                # Clone model for each fold
                from sklearn.base import clone
                model = clone(model_template)
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_te)
                
                mse = np.mean((y_te - y_pred) ** 2)
                rmse = np.sqrt(mse)
                mae = np.mean(np.abs(y_te - y_pred))
                mse_list.append(mse)
                rmse_list.append(rmse)
                mae_list.append(mae)
            
            results[name] = {
                'mse': float(np.mean(mse_list)),
                'rmse': float(np.mean(rmse_list)),
                'mae': float(np.mean(mae_list)),
                'cv_folds': len(mse_list)
            }
        
        return results

    def get_feature_importance(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """الحصول على أهمية الميزات"""
        if not self.is_trained or not hasattr(self._rf, 'feature_importances_'):
            return []

        importances = self._rf.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]

        return [
            {'feature': self._feature_names[i], 'importance': float(importances[i])}
            for i in indices
        ]

    def get_model_info(self) -> Dict[str, Any]:
        """الحصول على معلومات النموذج"""
        info = {
            'is_trained': self.is_trained,
            'model_type': self.model_type,
            'model_path': self.model_path,
            'training_metrics': self.training_metrics,
            'feature_count': len(self._feature_names),
            'available_models': list(AI_AVAILABLE_MODELS.keys()),
            'version': '3.0',
        }
        return info

    def _save_model(self):
        """حفظ النموذج"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'ridge': self._ridge,
            'rf': self._rf,
            'gb': self._gb,
            'ensemble': self._ensemble,
            'is_trained': self.is_trained,
            'model_type': self.model_type,
            'training_metrics': self.training_metrics,
            'feature_names': self._feature_names,
            'last_known_values': self._last_known_values,
            'config': self._config,
        }
        joblib.dump(model_data, self.model_path)

    def _load_model(self):
        """تحميل النموذج"""
        model_data = joblib.load(self.model_path)
        self.model = model_data.get('model', self._ensemble)
        self.scaler = model_data.get('scaler', self._scaler)
        self._ridge = model_data.get('ridge', self._ridge)
        self._rf = model_data.get('rf', self._rf)
        self._gb = model_data.get('gb', self._gb)
        self._ensemble = model_data.get('ensemble', self._ensemble)
        self.is_trained = model_data.get('is_trained', False)
        self.model_type = model_data.get('model_type', self.model_type)
        self.training_metrics = model_data.get('training_metrics', {})
        self._feature_names = model_data.get('feature_names', [])
        self._last_known_values = model_data.get('last_known_values', {})
        self._config = model_data.get('config', self._config)

    # ─────────────────────────────────────────────
    # وظائف التحليل
    # ─────────────────────────────────────────────

    def analyze_popular_services(self, orders_data: List[Dict], top_n: int = 10) -> List[Dict[str, Any]]:
        """تحليل الخدمات الأكثر طلباً"""
        if not orders_data:
            return []

        df = pd.DataFrame(orders_data)
        all_services = []
        service_revenues = {}

        for services_info in df.get('services_info', []):
            if not services_info:
                continue
            for service in str(services_info).split(','):
                parts = service.split('|')
                if len(parts) >= 3 and parts[0].strip():
                    name = parts[0].strip()
                    all_services.append(name)
                    # parts[1] = quantity, parts[2] = unit_price
                    quantity = int(parts[1]) if parts[1] else 1
                    unit_price = float(parts[2]) if parts[2] else 0
                    total_price = quantity * unit_price
                    service_revenues[name] = service_revenues.get(name, 0) + total_price

        from collections import Counter
        counts = Counter(all_services)
        popular = counts.most_common(top_n)

        return [
            {
                'service_name': name,
                'order_count': count,
                'total_revenue': service_revenues.get(name, 0),
                'percentage': round((count / len(all_services)) * 100, 2) if all_services else 0
            }
            for name, count in popular
        ]

    def analyze_weekly_patterns(self, orders_data: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """تحليل أنماط الطلبات حسب أيام الأسبوع"""
        if not orders_data:
            return {}

        df = pd.DataFrame(orders_data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['day_of_week'] = df['created_at'].dt.dayofweek

        days_map = {0: 'الإثنين', 1: 'الثلاثاء', 2: 'الأربعاء', 3: 'الخميس',
                    4: 'الجمعة', 5: 'السبت', 6: 'الأحد'}

        # تجميع حسب اليوم مع حساب عدد الطلبات وإجمالي الإيرادات
        weekly = df.groupby('day_of_week').agg({
            'id': 'count',
            'total_amount': 'sum' if 'total_amount' in df.columns else 'count'
        }).reset_index()
        
        results = {}
        for _, row in weekly.iterrows():
            day = days_map.get(row['day_of_week'], str(row['day_of_week']))
            results[day] = {
                'order_count': int(row['id']),
                'total_amount': float(row.get('total_amount', 0)) if 'total_amount' in df.columns else 0
            }
        return results

    def analyze_hourly_patterns(self, orders_data: List[Dict]) -> Dict[str, Any]:
        """تحليل أنماط الطلبات حسب الساعات"""
        if not orders_data:
            return {}

        df = pd.DataFrame(orders_data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['hour'] = df['created_at'].dt.hour

        # تجميع حسب الساعة مع حساب عدد الطلبات وإجمالي الإيرادات
        agg_dict = {'id': 'count'}
        if 'total_amount' in df.columns:
            agg_dict['total_amount'] = 'sum'
        
        hourly = df.groupby('hour').agg(agg_dict).reset_index()
        peak = hourly.nlargest(3, 'id')['hour'].tolist()

        # إضافة total_amount لكل ساعة
        hourly_stats = []
        for _, row in hourly.iterrows():
            stat = {'hour': int(row['hour']), 'order_count': int(row['id'])}
            if 'total_amount' in row:
                stat['total_amount'] = float(row['total_amount'])
            else:
                stat['total_amount'] = 0
            hourly_stats.append(stat)

        return {
            'hourly_stats': hourly_stats,
            'peak_hours': peak,
            'periods': {
                'morning': int(hourly[hourly['hour'].between(6, 12)]['id'].sum()),
                'afternoon': int(hourly[hourly['hour'].between(12, 18)]['id'].sum()),
                'evening': int(hourly[hourly['hour'].between(18, 24)]['id'].sum()),
                'night': int(hourly[hourly['hour'].between(0, 6)]['id'].sum()),
            }
        }

    def segment_customers(self, orders_data: List[Dict], customers_data: List[Dict] = None,
                           n_segments: int = None) -> Dict[str, Any]:
        """تقسيم العملاء إلى شرائح"""
        try:
            if not orders_data or len(orders_data) < 5:
                return {'error': 'بيانات غير كافية'}
            
            n_segments = n_segments or AI_CUSTOMER_SEGMENTS
            df = pd.DataFrame(orders_data)
            
            if 'customer_id' not in df.columns:
                return {'error': 'لا يوجد معرف العميل'}
            
            has_amount = 'total_amount' in df.columns
            
            # تجميع بيانات العملاء بشكل صحيح
            if has_amount:
                # مع total_amount
                customer_stats = df.groupby('customer_id').agg(
                    order_count=('id', 'count'),
                    total_spending=('total_amount', 'sum')
                ).reset_index()
            else:
                # بدون total_amount
                customer_stats = df.groupby('customer_id').agg(
                    order_count=('id', 'count')
                ).reset_index()
            
            if has_amount and 'total_spending' in customer_stats.columns:
                customer_stats['avg_order_value'] = customer_stats['total_spending'] / customer_stats['order_count']
            
            segment_names = ['عميل ذهبي', 'عميل فضي', 'عميل برونزي', 'عميل جديد']
            segments = {}
            labels = []
            
            for _, row in customer_stats.iterrows():
                count = row['order_count']
                if count >= 10: label = segment_names[0]
                elif count >= 5: label = segment_names[1]
                elif count >= 3: label = segment_names[2]
                else: label = segment_names[3]
                
                segments[str(row['customer_id'])] = {
                    'segment': label,
                    'order_count': int(count),
                    'total_spending': float(row.get('total_spending', 0)),
                    'avg_order_value': float(row.get('avg_order_value', 0)),
                }
                labels.append(label)
            
            from collections import Counter
            return {'segments': segments, 'segment_counts': dict(Counter(labels))}
        except Exception as e:
            return {'error': str(e)}

    def recommend_services(self, customer_id: int, orders_data: List[Dict],
                          top_n: int = None) -> Dict[str, Any]:
        """
        نظام توصيات هجين محسّن:
        - للعملاء الجدد: توصيات شعبية
        - للعملاء الحاليين: توصيات مخصصة (ارتباط + تشابه + شعبية)
        """
        try:
            top_n = top_n or AI_RECOMMENDATION_TOP_N
            if not orders_data:
                return self._get_popular_services_fallback(top_n)
            
            df = pd.DataFrame(orders_data)
            if 'customer_id' not in df.columns or 'services_info' not in df.columns:
                return self._get_popular_services_fallback(top_n)
            
            # ===== 1. استخراج الخدمات وتكراراتها =====
            service_freq = {}
            for info in df['services_info'].dropna():
                for s in str(info).split(','):
                    parts = s.split('|')
                    if parts and parts[0].strip():
                        name = parts[0].strip()
                        service_freq[name] = service_freq.get(name, 0) + 1
            
            if not service_freq:
                return self._get_popular_services_fallback(top_n)
            
            popular_list = sorted(service_freq.items(), key=lambda x: x[1], reverse=True)
            max_pop = popular_list[0][1] if popular_list else 1
            
            # ===== 2. خدمات العميل الحالية =====
            customer_orders = df[df['customer_id'] == customer_id]
            customer_services = set()
            for info in customer_orders['services_info'].dropna():
                for s in str(info).split(','):
                    parts = s.split('|')
                    if parts and parts[0].strip():
                        customer_services.add(parts[0].strip())
            
            # ===== 3. العميل الجديد؟ أرجع شعبية =====
            if not customer_services:
                return {
                    'recommendations': [
                        {'service_name': name, 'confidence': round(count / max_pop, 4), 'source': 'رائج'}
                        for name, count in popular_list[:top_n]
                    ],
                    'reason': 'عميل جديد - توصيات رائجة',
                    'type': 'new_customer'
                }
            
            # ===== 4. حساب الخدمات المرتبطة (Co-occurrence) =====
            co_occurrence = {}
            for info in df['services_info'].dropna():
                services_in_order = []
                for s in str(info).split(','):
                    parts = s.split('|')
                    if parts and parts[0].strip():
                        services_in_order.append(parts[0].strip())
                services_set = set(services_in_order)
                if services_set.intersection(customer_services):
                    for svc in services_set:
                        if svc not in customer_services:
                            co_occurrence[svc] = co_occurrence.get(svc, 0) + 1
            
            # ===== 5. حساب التشابه مع عملاء آخرين (Collaborative) =====
            service_list = sorted(set(service_freq.keys()))
            service_to_idx = {svc: i for i, svc in enumerate(service_list)}
            
            vectors = {}
            for cid, group in df.groupby('customer_id'):
                vec = np.zeros(len(service_list))
                for info in group['services_info'].dropna():
                    for s in str(info).split(','):
                        parts = s.split('|')
                        if parts and parts[0].strip() in service_to_idx:
                            idx = service_to_idx[parts[0].strip()]
                            vec[idx] += 1
                vectors[cid] = vec
            
            collaborative_scores = {}
            if customer_id in vectors:
                target = vectors[customer_id]
                for cid, vec in vectors.items():
                    if cid != customer_id:
                        n1, n2 = np.linalg.norm(target), np.linalg.norm(vec)
                        if n1 > 0 and n2 > 0:
                            sim = np.dot(target, vec) / (n1 * n2)
                            if sim > 0.05:
                                for i, cnt in enumerate(vec):
                                    if cnt > 0 and service_list[i] not in customer_services:
                                        collaborative_scores[service_list[i]] = collaborative_scores.get(service_list[i], 0) + sim * cnt
            
            # ===== 6. دمج جميع المصادر =====
            final_scores = {}
            
            # المصدر 1: الخدمات المرتبطة (وزن 1.5)
            for svc, cnt in co_occurrence.items():
                final_scores[svc] = final_scores.get(svc, 0) + {'score': cnt * 1.5, 'source': 'مرتبطة'}
            
            # المصدر 2: التشابه مع عملاء آخرين (وزن 1.0)
            for svc, score in collaborative_scores.items():
                if svc in final_scores:
                    final_scores[svc]['score'] += score * 1.0
                    final_scores[svc]['source'] = 'مخصصة'
                else:
                    final_scores[svc] = {'score': score * 1.0, 'source': 'مشابهة'}
            
            # المصدر 3: الشعبية (وزن 0.3)
            for svc, freq in service_freq.items():
                if svc not in customer_services and svc not in final_scores:
                    final_scores[svc] = {'score': freq * 0.3, 'source': 'رائج'}
            
            if not final_scores:
                # حتى لو العميل طلب كل الخدمات، أظهر الرائجة
                return {
                    'recommendations': [
                        {'service_name': name, 'confidence': round(count / max_pop, 4), 'source': 'رائج'}
                        for name, count in popular_list[:top_n]
                    ],
                    'reason': 'خدمات رائجة في النظام',
                    'type': 'popular_only'
                }
            # ترتيب النتائج
            sorted_scores = sorted(final_scores.items(), key=lambda x: x[1]['score'], reverse=True)[:top_n]
            max_score = sorted_scores[0][1]['score'] if sorted_scores else 1
            
            recommendations = [
                {
                    'service_name': name,
                    'confidence': round(data['score'] / max_score, 4),
                    'source': data['source']
                }
                for name, data in sorted_scores
            ]
            
            return {
                'recommendations': recommendations,
                'reason': f'تم العثور على {len(recommendations)} توصية مخصصة',
                'type': 'personalized',
                'has_custom': len(collaborative_scores) > 0 or len(co_occurrence) > 0
            }
            
        except Exception as e:
            return self._get_popular_services_fallback(top_n, str(e))

    def _get_popular_services_fallback(self, top_n: int, error: str = None) -> Dict[str, Any]:
        """إرجاع أكثر الخدمات شيوعاً (للعملاء الجدد أو عند الفشل)"""
        try:
            from repositories.database import DatabaseManager
            db = DatabaseManager()
            orders = db.get_orders()
            if not orders:
                return {'recommendations': [], 'reason': 'لا توجد طلبات في النظام'}
            
            df = pd.DataFrame(orders)
            if 'services_info' not in df.columns:
                return {'recommendations': [], 'reason': 'لا توجد معلومات الخدمات'}
            
            all_services = []
            for info in df['services_info'].dropna():
                for s in str(info).split(','):
                    parts = s.split('|')
                    if parts and parts[0].strip():
                        all_services.append(parts[0].strip())
            
            if not all_services:
                return {'recommendations': [], 'reason': 'لا توجد خدمات'}
            
            from collections import Counter
            counter = Counter(all_services)
            most_common = counter.most_common(top_n)
            max_count = most_common[0][1] if most_common else 1
            
            return {
                'recommendations': [
                    {'service_name': name, 'confidence': round(count / max_count, 4), 'source': 'رائج'}
                    for name, count in most_common
                ],
                'reason': f'خدمات رائجة (خطأ: {error})' if error else 'خدمات رائجة',
                'type': 'popular'
            }
        except Exception:
            return {'recommendations': [], 'reason': 'تعذر الحصول على التوصيات'}
    
    def get_customers_with_recommendations(self, orders_data: List[Dict], top_n: int = None) -> List[Dict[str, Any]]:
        """الحصول على قائمة العملاء الذين يمكن给他们 توصيات"""
        try:
            top_n = top_n or AI_RECOMMENDATION_TOP_N
            if not orders_data:
                return []
            
            df = pd.DataFrame(orders_data)
            if 'customer_id' not in df.columns:
                return []
            
            # استخراج الخدمات
            all_services = set()
            for info in df.get('services_info', pd.Series()).dropna():
                for s in str(info).split(','):
                    parts = s.split('|')
                    if parts and parts[0].strip():
                        all_services.add(parts[0].strip())
            
            if not all_services:
                return []
            
            service_list = sorted(all_services)
            
            # بناء vectors
            vectors = {}
            customer_order_counts = {}
            
            for cid, group in df.groupby('customer_id'):
                vec = np.zeros(len(service_list))
                order_count = 0
                for info in group.get('services_info', pd.Series()).dropna():
                    for s in str(info).split(','):
                        parts = s.split('|')
                        if parts and parts[0].strip() in service_list:
                            idx = service_list.index(parts[0].strip())
                            vec[idx] += 1
                            order_count += 1
                vectors[cid] = vec
                customer_order_counts[cid] = order_count
            
            results = []
            
            for cid, target in vectors.items():
                # يحتاج على الأقل طلب واحد
                if np.sum(target) == 0:
                    continue
                
                others = {k: v for k, v in vectors.items() if k != cid}
                if not others:
                    continue
                
                # حساب التشابه
                similarities = []
                for other_cid, vec in others.items():
                    n1, n2 = np.linalg.norm(target), np.linalg.norm(vec)
                    if n1 > 0 and n2 > 0:
                        sim = np.dot(target, vec) / (n1 * n2)
                        if sim > 0.01:
                            similarities.append((other_cid, sim))
                
                if not similarities:
                    continue
                
                # الخدمات المطلوبة
                used = {service_list[i] for i, c in enumerate(target) if c > 0}
                
                # البحث عن خدمات جديدة
                scores = {}
                for sim_cid, sim in similarities[:20]:
                    for i, c in enumerate(others[sim_cid]):
                        if c > 0 and service_list[i] not in used:
                            scores[service_list[i]] = scores.get(service_list[i], 0) + sim * c
                
                if scores:
                    results.append({
                        'customer_id': cid,
                        'order_count': customer_order_counts[cid],
                        'recommendations_count': len(scores),
                        'top_service': max(scores.items(), key=lambda x: x[1])[0] if scores else None
                    })
            
            # ترتيب حسب عدد التوصيات
            results.sort(key=lambda x: x['recommendations_count'], reverse=True)
            return results[:50]  # إرجاع أفضل 50 عميل
            
        except Exception:
            return []

    def forecast_revenue(self, orders_data: List[Dict], months: int = None) -> Dict[str, Any]:
        """التنبؤ بالإيرادات"""
        try:
            months = months or AI_FORECAST_MONTHS
            if not orders_data:
                return {'error': 'لا توجد بيانات'}
            
            df = pd.DataFrame(orders_data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            if 'total_amount' not in df.columns:
                return {'error': 'لا يوجد عمود الإيرادات'}
            
            df['year'] = df['created_at'].dt.year
            df['month'] = df['created_at'].dt.month
            
            monthly = df.groupby(['year', 'month'])['total_amount'].sum().reset_index()
            monthly.columns = ['year', 'month', 'revenue']
            monthly = monthly.sort_values(['year', 'month']).reset_index(drop=True)
            
            if len(monthly) < 2:
                return {'error': 'بيانات شهرية غير كافية'}
            
            historical = [{'year': int(r['year']), 'month': int(r['month']),
                          'revenue': round(float(r['revenue']), 2),
                          'label': f"{int(r['year'])}-{int(r['month']):02d}"}
                         for _, r in monthly.iterrows()]
            
            # تحويل القيم إلى float لتجنب مشاكل Decimal
            revenues = np.array([float(v) for v in monthly['revenue'].values])
            avg_rev = float(np.mean(revenues))
            std_rev = float(np.std(revenues))
            
            growth = []
            for i in range(1, len(revenues)):
                if revenues[i-1] > 0:
                    growth.append((revenues[i] - revenues[i-1]) / revenues[i-1])
            avg_growth = float(np.mean(growth)) if growth else 0.0
            
            last_y, last_m = int(monthly.iloc[-1]['year']), int(monthly.iloc[-1]['month'])
            last_r = float(monthly.iloc[-1]['revenue'])
            
            forecast = []
            for i in range(1, months + 1):
                fm, fy = last_m + i, last_y
                while fm > 12: fm -= 12; fy += 1
                
                pred = last_r * ((1 + avg_growth) ** i)
                w = min(i / months, 0.7)
                pred = pred * (1 - w) + avg_rev * w
                conf = max(0.5, 1.0 - (i - 1) * 0.15)
                
                forecast.append({
                    'year': fy, 'month': fm,
                    'predicted_revenue': round(max(0, pred), 2),
                    'confidence_lower': round(max(0, pred - 1.96 * std_rev), 2),
                    'confidence_upper': round(pred + 1.96 * std_rev, 2),
                    'confidence': round(conf, 2),
                    'label': f"{fy}-{fm:02d}",
                })
            
            return {
                'historical': historical,
                'forecast': forecast,
                'avg_monthly_revenue': round(float(avg_rev), 2),
                'std_revenue': round(float(std_rev), 2),
                'avg_growth_rate': round(float(avg_growth), 4),
            }
        except Exception as e:
            return {'error': str(e)}
