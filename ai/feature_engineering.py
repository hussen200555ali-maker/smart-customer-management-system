# -*- coding: utf-8 -*-
"""
ai/feature_engineering.py
-------------------------
وحدة هندسة الميزات المتقدمة لنظام الذكاء الاصطناعي.
تحتوي على جميع الميزات الزمنية والسلوكية والمؤشرية.

الإصدار: 3.0
تاريخ التحديث: أبريل 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from config import (
    AI_LAG_PERIODS,
    AI_ROLLING_WINDOWS,
    AI_SEASONALITY_CONFIG,
    AI_CUSTOMER_BEHAVIOR_CONFIG,
)


class AdvancedFeatureEngineer:
    """مهندس ميزات متقدم لإنتاج ميزات غنية للنماذج"""

    def __init__(self):
        """تهيئة مهندس الميزات"""
        self.feature_names = []
        self.seasonality_config = AI_SEASONALITY_CONFIG
        self.behavior_config = AI_CUSTOMER_BEHAVIOR_CONFIG

    def create_all_features(
        self,
        orders_data: List[Dict],
        customers_data: List[Dict] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        إنشاء جميع الميزات المطلوبة

        Args:
            orders_data: بيانات الطلبات
            customers_data: بيانات العملاء (اختياري)

        Returns:
            DataFrame بالميزات و Series بالهدف
        """
        if not orders_data or len(orders_data) < 10:
            raise ValueError("بيانات غير كافية لإنشاء الميزات")

        # تحويل إلى DataFrame
        df = pd.DataFrame(orders_data)
        df['created_at'] = pd.to_datetime(df['created_at'])

        # إنشاء تاريخ يومى
        daily_df = self._aggregate_to_daily(df)

        # إضافة الميزات الزمنية الأساسية
        daily_df = self._add_temporal_features(daily_df)

        # إضافة ميزات التأخر
        daily_df = self._add_lag_features(daily_df)

        # إضافة المتوسطات المتحركة
        daily_df = self._add_rolling_features(daily_df)

        # إضافة الميزات الموسمية
        daily_df = self._add_seasonality_features(daily_df)

        # إضافة ميزات الاتجاه
        daily_df = self._add_trend_features(daily_df)

        # إضافة ميزات الأسبوع والشهر
        daily_df = self._add_calendar_features(daily_df)

        # إضافة الميزات الإحصائية
        daily_df = self._add_statistical_features(daily_df)

        # إضافة الميزات السلوكية للعملاء
        if customers_data:
            daily_df = self._add_customer_behavior_features(
                df, daily_df, customers_data
            )

        # إضافة ميزات الإيرادات
        if 'total_amount' in df.columns:
            daily_df = self._add_revenue_features(df, daily_df)

        # إضافة ميزات التنبؤ بالوقت
        daily_df = self._add_forecast_horizon_features(daily_df)

        # الهدف هو عدد الطلبات اليومية
        target = daily_df['order_count'].copy()

        # إزالة الأعمدة غير المناسبة
        cols_to_drop = ['date', 'order_count']
        if 'daily_revenue' in daily_df.columns:
            cols_to_drop.append('daily_revenue')

        feature_df = daily_df.drop(columns=cols_to_drop, errors='ignore')

        # تعبئة القيم المفقودة
        feature_df = feature_df.fillna(0)

        # تخزين أسماء الميزات
        self.feature_names = list(feature_df.columns)

        return feature_df, target

    def _aggregate_to_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """تجميع البيانات على مستوى يومي"""
        daily = df.groupby(df['created_at'].dt.date).agg({
            'id': 'count',
            'customer_id': 'nunique',
        }).reset_index()

        daily.columns = ['date', 'order_count', 'unique_customers']
        daily['date'] = pd.to_datetime(daily['date'])

        # إضافة الإيرادات اليومية
        if 'total_amount' in df.columns:
            revenue = df.groupby(df['created_at'].dt.date)['total_amount'].sum()
            daily = daily.merge(
                pd.DataFrame({
                    'date': pd.to_datetime(revenue.index),
                    'daily_revenue': revenue.values
                }),
                on='date',
                how='left'
            )
            daily['daily_revenue'] = daily['daily_revenue'].fillna(0)

        # ترتيب البيانات
        daily = daily.sort_values('date').reset_index(drop=True)

        return daily

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة الميزات الزمنية الأساسية"""
        df = df.copy()

        # الميزات الأساسية
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
        df['quarter'] = df['date'].dt.quarter

        # معلومات اليوم
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        df['is_quarter_start'] = df['date'].dt.is_quarter_start.astype(int)
        df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)

        # ميزات خاصة بالأيام
        df['is_monday'] = (df['day_of_week'] == 0).astype(int)
        df['is_friday'] = (df['day_of_week'] == 4).astype(int)
        df['is_saturday'] = (df['day_of_week'] == 5).astype(int)

        return df

    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة ميزات التأخر المتقدمة"""
        df = df.copy()

        for lag in AI_LAG_PERIODS:
            if lag <= len(df):
                df[f'order_count_lag_{lag}'] = df['order_count'].shift(lag)

                if 'unique_customers' in df.columns:
                    df[f'unique_customers_lag_{lag}'] = df['unique_customers'].shift(lag)

                if 'daily_revenue' in df.columns:
                    df[f'daily_revenue_lag_{lag}'] = df['daily_revenue'].shift(lag)

        # نسبة التغيير
        for lag in [1, 7, 14]:
            if lag < len(df):
                df[f'order_count_change_{lag}'] = (
                    df['order_count'] - df[f'order_count_lag_{lag}']
                ) / (df[f'order_count_lag_{lag}'] + 1)
                df[f'order_count_pct_change_{lag}'] = (
                    df['order_count'] / (df[f'order_count_lag_{lag}'] + 1)
                )

        # نسبة اليوم لنفس اليوم في الأسبوع الماضي
        if 'order_count_lag_7' in df.columns:
            df['same_day_last_week_ratio'] = (
                df['order_count'] / (df['order_count_lag_7'] + 1)
            )

        # نسبة اليوم لنفس اليوم في الشهر الماضي
        if 'order_count_lag_30' in df.columns:
            df['same_day_last_month_ratio'] = (
                df['order_count'] / (df['order_count_lag_30'] + 1)
            )

        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة المتوسطات المتحركة والمتغيرات"""
        df = df.copy()

        for window in AI_ROLLING_WINDOWS:
            if window <= len(df):
                # متوسطات متحركة
                df[f'rolling_mean_{window}'] = (
                    df['order_count'].rolling(window=window, min_periods=1).mean()
                )
                df[f'rolling_median_{window}'] = (
                    df['order_count'].rolling(window=window, min_periods=1).median()
                )

                # انحراف معياري
                df[f'rolling_std_{window}'] = (
                    df['order_count'].rolling(window=window, min_periods=1).std()
                )

                # الحد الأدنى والأقصى
                df[f'rolling_min_{window}'] = (
                    df['order_count'].rolling(window=window, min_periods=1).min()
                )
                df[f'rolling_max_{window}'] = (
                    df['order_count'].rolling(window=window, min_periods=1).max()
                )

                # النطاق
                df[f'rolling_range_{window}'] = (
                    df[f'rolling_max_{window}'] - df[f'rolling_min_{window}']
                )

                # معامل التغير
                df[f'rolling_cv_{window}'] = (
                    df[f'rolling_std_{window}'] / (df[f'rolling_mean_{window}'] + 1)
                )

        # مقارنة المتوسطات
        if 'rolling_mean_7' in df.columns and 'rolling_mean_30' in df.columns:
            df['rolling_mean_ratio_7_30'] = (
                df['rolling_mean_7'] / (df['rolling_mean_30'] + 1)
            )

        # اتجاه المتوسطات
        if 'rolling_mean_7' in df.columns:
            df['rolling_trend'] = (
                df['rolling_mean_7'] - df['rolling_mean_7'].shift(7)
            )

        return df

    def _add_seasonality_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة الميزات الموسمية والعطلات"""
        df = df.copy()

        # الترميز الدوري للوقت (sin/cos)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_year_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['day_of_year_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        df['week_of_year_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
        df['week_of_year_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)

        # فصول السنة
        def get_season(row):
            month = row['month']
            if 3 <= month <= 6:
                return 0  # ربيع
            elif 7 <= month <= 9:
                return 1  # صيف
            elif 10 <= month <= 11:
                return 2  # خريف
            else:
                return 3  # شتاء

        df['season'] = df.apply(get_season, axis=1)

        # إنشاء ميزات عطلة
        df['is_holiday'] = 0
        df['is_ramadan'] = 0
        df['is_eid'] = 0

        # يمكنك إضافة مزيد من العطلات هنا
        # هذه مجرد أمثلة

        return df

    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة ميزات الاتجاه"""
        df = df.copy()

        # ترتيب الأيام
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days

        # اتجاه خطي بسيط
        if len(df) > 7:
            x = np.arange(len(df))
            z = np.polyfit(x, df['order_count'].fillna(0), 1)
            df['trend_slope'] = z[0]
            df['trend_intercept'] = z[1]

            # قيمة الاتجاه المتوقعة
            df['trend_value'] = z[0] * x + z[1]

        # نسبة الطلبات الحالية إلى الاتجاه
        if 'trend_value' in df.columns:
            df['deviation_from_trend'] = (
                df['order_count'] - df['trend_value']
            ) / (df['trend_value'] + 1)

        return df

    def _add_calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة ميزات التقويم"""
        df = df.copy()

        # موقع اليوم في الشهر
        df['day_of_month_normalized'] = df['day'] / 31

        # موقع الأسبوع في الشهر
        df['week_of_month'] = (df['day'] - 1) // 7 + 1

        # موقع اليوم في الأسبوع
        df['position_in_week'] = df['day_of_week'] / 6

        # الأيام المتبقية في الشهر
        days_in_month = df['date'].dt.days_in_month
        df['days_remaining_in_month'] = days_in_month - df['day']

        # نسبة الشهر المنقضية
        df['month_progress'] = df['day'] / days_in_month

        # رقم الأسبوع في الشهر
        df['week_of_month'] = df['date'].dt.isocalendar().week.astype(int) - \
            df['date'].dt.to_period('M').apply(lambda r: r.start_time) \
            .dt.isocalendar().week.astype(int) + 1

        return df

    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة الميزات الإحصائية"""
        df = df.copy()

        # التوزيع
        if len(df) > 30:
            mean = df['order_count'].mean()
            std = df['order_count'].std()
            df['z_score'] = (df['order_count'] - mean) / (std + 1)

            # النسب المئوية
            df['percentile'] = df['order_count'].rank(pct=True)

            # ما إذا كان القيمة متطرفة
            df['is_outlier'] = (np.abs(df['z_score']) > 2).astype(int)

        # نسبة المتوسط
        df['ratio_to_mean'] = df['order_count'] / (df['order_count'].mean() + 1)

        # كمية المعلومات
        df['info_amount'] = np.log1p(df['order_count'])

        return df

    def _add_customer_behavior_features(
        self,
        orders_df: pd.DataFrame,
        daily_df: pd.DataFrame,
        customers_data: List[Dict]
    ) -> pd.DataFrame:
        """إضافة ميزات سلوك العملاء"""
        df = daily_df.copy()
        config = self.behavior_config

        if not config.get('compute_frequency') and \
           not config.get('compute_recency') and \
           not config.get('compute_monetary'):
            return df

        customers_df = pd.DataFrame(customers_data)

        if 'created_at' not in orders_df.columns:
            return df

        # حساب RFM لكل عميل
        orders_df = orders_df.copy()
        orders_df['date_only'] = pd.to_datetime(orders_df['created_at']).dt.date

        rfm_data = []
        for customer_id, group in orders_df.groupby('customer_id'):
            dates = pd.to_datetime(group['created_at'])
            amounts = group['total_amount'] if 'total_amount' in group.columns else [0] * len(group)

            recency = (dates.max() - dates.min()).days if len(dates) > 1 else 0
            frequency = len(group)
            monetary = sum(amounts)

            rfm_data.append({
                'customer_id': customer_id,
                'recency': recency,
                'frequency': frequency,
                'monetary': monetary,
            })

        rfm_df = pd.DataFrame(rfm_data)

        # إضافة ميزات RFM للبيانات اليومية
        if not rfm_df.empty:
            # متوسطات RFM
            daily_df['avg_recency'] = rfm_df['recency'].mean()
            daily_df['avg_frequency'] = rfm_df['frequency'].mean()
            daily_df['avg_monetary'] = rfm_df['monetary'].mean()

            # عدد العملاء النشطين
            daily_df['total_customers'] = len(rfm_df)

            # توزيع الشرائح
            rfm_df['segment'] = pd.cut(
                rfm_df['monetary'],
                bins=[0, rfm_df['monetary'].quantile(0.25),
                      rfm_df['monetary'].quantile(0.5),
                      rfm_df['monetary'].quantile(0.75),
                      float('inf')],
                labels=['bronze', 'silver', 'gold', 'platinum']
            )

            segment_counts = rfm_df['segment'].value_counts()
            for seg in ['bronze', 'silver', 'gold', 'platinum']:
                daily_df[f'customers_{seg}'] = segment_counts.get(seg, 0)

        return df

    def _add_revenue_features(
        self,
        orders_df: pd.DataFrame,
        daily_df: pd.DataFrame
    ) -> pd.DataFrame:
        """إضافة ميزات الإيرادات"""
        df = daily_df.copy()

        if 'total_amount' not in orders_df.columns:
            return df

        # متوسط سعر الطلب
        df['avg_order_value'] = (
            df['daily_revenue'] / (df['order_count'] + 1)
        )

        # مؤشرات نمو الإيرادات
        if len(df) > 1:
            df['revenue_growth'] = df['daily_revenue'].pct_change()
            df['revenue_growth_7d'] = (
                df['daily_revenue'] - df['daily_revenue'].shift(7)
            ) / (df['daily_revenue'].shift(7) + 1)

        return df

    def _add_forecast_horizon_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """إضافة ميزات خاصة بالتحضير للتنبؤ"""
        df = df.copy()

        # ميزات للتمييز بين فترة التدريب والتنبؤ
        df['days_from_reference'] = (
            df['date'] - df['date'].min()
        ).dt.days

        return df

    def get_feature_importance_dataframe(
        self,
        feature_names: List[str],
        importances: np.ndarray,
        top_n: int = 20
    ) -> pd.DataFrame:
        """إنشاء DataFrame لأهمية الميزات"""
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)

        return importance_df.head(top_n)

    def get_feature_groups(self) -> Dict[str, List[str]]:
        """تقسيم الميزات إلى مجموعات"""
        groups = {
            'temporal': [],
            'lag': [],
            'rolling': [],
            'seasonality': [],
            'trend': [],
            'calendar': [],
            'statistical': [],
            'revenue': [],
            'customer': [],
            'other': []
        }

        for name in self.feature_names:
            if any(x in name for x in ['year', 'month', 'day', 'week', 'quarter', 'is_']):
                groups['temporal'].append(name)
            elif 'lag' in name:
                groups['lag'].append(name)
            elif 'rolling' in name:
                groups['rolling'].append(name)
            elif any(x in name for x in ['sin', 'cos', 'season', 'holiday', 'ramadan', 'eid']):
                groups['seasonality'].append(name)
            elif 'trend' in name:
                groups['trend'].append(name)
            elif any(x in name for x in ['week_of_month', 'day_of_month', 'remaining']):
                groups['calendar'].append(name)
            elif any(x in name for x in ['std', 'mean', 'percentile', 'z_score', 'outlier']):
                groups['statistical'].append(name)
            elif 'revenue' in name or 'value' in name:
                groups['revenue'].append(name)
            elif 'customer' in name:
                groups['customer'].append(name)
            else:
                groups['other'].append(name)

        return groups
