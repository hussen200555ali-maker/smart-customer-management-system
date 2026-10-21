# -*- coding: utf-8 -*-
"""
ui/statistics_ui.py
-------------------
لوحة الإحصائيات الشاملة - Comprehensive Statistics Dashboard

تعرض لوحة إحصائيات متقدمة تشمل:
- بطاقات KPI رئيسية وثانوية
- تفصيل حالات الطلبات
- 4 رسوم بيانية (إيرادات شهرية، طلبات حسب الحالة، خدمات شائعة، نمو العملاء)
- جدول أفضل العملاء
- جدول أحدث الطلبات
- ملخص النشاط (أكثر الأيام نشاطاً، أكثر الساعات نشاطاً، فئة الخدمات الأكثر طلباً)
- فلاتر نطاق التاريخ

الإصدار: 2.0
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from repositories.database import DatabaseManager
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bidi.algorithm import get_display
import arabic_reshaper
from utils.dialogs import show_info, show_success, show_warning, show_error, ask_yes_no


def reshape_text(text: str) -> str:
    """إعادة تشكيل النص العربي وعرضه بشكل صحيح من اليمين لليسار"""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


# ═══════════════════════════════════════════════════════════════
# ألوان وتكوينات عامة
# ═══════════════════════════════════════════════════════════════

COLORS = {
    'primary': '#4361ee',
    'primary_dark': '#3a56d4',
    'success': '#2ec4b6',
    'warning': '#f77f00',
    'danger': '#ef233c',
    'info': '#3f37c9',
    'text_dark': '#1a1a2e',
    'text_gray': '#6c757d',
    'bg_light': '#f8f9fa',
    'card_border': '#e0e0e0',
    'pending': '#f77f00',
    'in_progress': '#4361ee',
    'completed': '#2ec4b6',
    'cancelled': '#ef233c',
}

STATUS_MAP = {
    'pending': reshape_text('قيد الانتظار'),
    'in_progress': reshape_text('قيد التنفيذ'),
    'completed': reshape_text('مكتمل'),
    'cancelled': reshape_text('ملغي'),
}

MONTH_NAMES_AR = {
    '01': 'يناير', '02': 'فبراير', '03': 'مارس', '04': 'أبريل',
    '05': 'مايو', '06': 'يونيو', '07': 'يوليو', '08': 'أغسطس',
    '09': 'سبتمبر', '10': 'أكتوبر', '11': 'نوفمبر', '12': 'ديسمبر',
}

DAY_NAMES_AR = {
    '0': reshape_text('الأحد'), '1': reshape_text('الاثنين'),
    '2': reshape_text('الثلاثاء'), '3': reshape_text('الأربعاء'),
    '4': reshape_text('الخميس'), '5': reshape_text('الجمعة'),
    '6': reshape_text('السبت'),
}


class StatisticsUI:
    """واجهة لوحة الإحصائيات الشاملة مع دعم كامل للغة العربية RTL"""

    def __init__(self, parent: ctk.CTkFrame, db_manager: DatabaseManager,
                 current_user: Dict[str, Any]):
        self.parent = parent
        self.db_manager = db_manager
        self.current_user = current_user
        self._chart_canvases: List = []
        self._create_ui()
        self._load_statistics()

    # ═══════════════════════════════════════════════════════════
    # بناء الواجهة الرئيسية
    # ═══════════════════════════════════════════════════════════

    def _create_ui(self):
        """إنشاء واجهة المستخدم الكاملة مع دعم RTL"""
        # إطار التمرير الرئيسي
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="transparent",
            orientation="vertical"
        )
        self.scroll_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # ── القسم 1: رأس الصفحة مع فلاتر التاريخ ──
        self._create_header(self.scroll_frame)

        # ── القسم 2: بطاقات KPI الرئيسية (4 بطاقات) ──
        self._create_main_kpi_cards(self.scroll_frame)

        # ── القسم 3: بطاقات KPI الثانوية (4 بطاقات) ──
        self._create_secondary_kpi_cards(self.scroll_frame)

        # ── القسم 4: بطاقة تفصيل حالات الطلبات ──
        self._create_status_breakdown(self.scroll_frame)

        # ── القسم 5: صف الرسوم البيانية الأول (إيرادات شهرية + طلبات حسب الحالة) ──
        self._create_charts_row1(self.scroll_frame)

        # ── القسم 6: صف الرسوم البيانية الثاني (خدمات شائعة + نمو العملاء) ──
        self._create_charts_row2(self.scroll_frame)

        # ── القسم 7: جدول أفضل العملاء ──
        self._create_top_customers_table(self.scroll_frame)

        # ── القسم 8: جدول أحدث الطلبات ──
        self._create_recent_orders_table(self.scroll_frame)

        # ── القسم 9: ملخص النشاط ──
        self._create_activity_summary(self.scroll_frame)

    # ═══════════════════════════════════════════════════════════
    # القسم 1: رأس الصفحة وفلاتر التاريخ
    # ═══════════════════════════════════════════════════════════

    def _create_header(self, parent):
        """إنشاء رأس الصفحة مع العنوان وزر التحديث وفلاتر التاريخ"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill=ctk.X, pady=(0, 15))

        # الصف العلوي: العنوان وزر التحديث
        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(fill=ctk.X, pady=(0, 10))

        title_label = ctk.CTkLabel(
            title_row,
            text=reshape_text("لوحة الإحصائيات الشاملة"),
            font=ctk.CTkFont(family="Cairo", size=26, weight="bold"),
            text_color=COLORS['text_dark']
        )
        title_label.pack(side=ctk.RIGHT, padx=(0, 5))

        refresh_button = ctk.CTkButton(
            title_row,
            text="🔄 تحديث البيانات",
            command=self._load_statistics,
            width=140,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=13, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_dark'],
            corner_radius=8
        )
        refresh_button.pack(side=ctk.LEFT, padx=(5, 0))

        # الصف السفلي: فلاتر التاريخ
        filter_row = ctk.CTkFrame(header_frame, fg_color=COLORS['bg_light'],
                                   corner_radius=10)
        filter_row.pack(fill=ctk.X)

        filter_label = ctk.CTkLabel(
            filter_row,
            text=": تصفية حسب التاريخ 📅",
            font=ctk.CTkFont(family="Cairo", size=13, weight="bold"),
            text_color=COLORS['text_dark']
        )
        filter_label.pack(side=ctk.RIGHT, padx=(15, 5), pady=10)

        from_label = ctk.CTkLabel(
            filter_row,
            text=reshape_text("من:"),
            font=ctk.CTkFont(family="Cairo", size=12),
            text_color=COLORS['text_gray']
        )
        from_label.pack(side=ctk.RIGHT, padx=(10, 2), pady=10)

        self.date_from_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="YYYY-MM-DD",
            width=140,
            height=35,
            justify="center",
            font=ctk.CTkFont(family="Cairo", size=12)
        )
        self.date_from_entry.pack(side=ctk.RIGHT, padx=(5, 10), pady=10)

        to_label = ctk.CTkLabel(
            filter_row,
            text=reshape_text("إلى:"),
            font=ctk.CTkFont(family="Cairo", size=12),
            text_color=COLORS['text_gray']
        )
        to_label.pack(side=ctk.RIGHT, padx=(10, 2), pady=10)

        self.date_to_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="YYYY-MM-DD",
            width=140,
            height=35,
            justify="center",
            font=ctk.CTkFont(family="Cairo", size=12)
        )
        self.date_to_entry.pack(side=ctk.RIGHT, padx=(5, 10), pady=10)

        filter_button = ctk.CTkButton(
            filter_row,
            text="🔍 تطبيق",
            command=self._load_statistics,
            width=90,
            height=35,
            font=ctk.CTkFont(family="Cairo", size=12, weight="bold"),
            fg_color=COLORS['success'],
            hover_color="#25a89c",
            corner_radius=8
        )
        filter_button.pack(side=ctk.RIGHT, padx=(5, 15), pady=10)

        reset_button = ctk.CTkButton(
            filter_row,
            text="↩️ إعادة تعيين",
            command=self._reset_date_filter,
            width=110,
            height=35,
            font=ctk.CTkFont(family="Cairo", size=12),
            fg_color=COLORS['text_gray'],
            hover_color="#5a6268",
            corner_radius=8
        )
        reset_button.pack(side=ctk.RIGHT, padx=(0, 5), pady=10)

    def _reset_date_filter(self):
        """إعادة تعيين فلاتر التاريخ"""
        self.date_from_entry.delete(0, ctk.END)
        self.date_to_entry.delete(0, ctk.END)
        self._load_statistics()

    # ═══════════════════════════════════════════════════════════
    # القسم 2: بطاقات KPI الرئيسية
    # ═══════════════════════════════════════════════════════════

    def _create_main_kpi_cards(self, parent):
        """إنشاء صف بطاقات KPI الرئيسية (4 بطاقات)"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, pady=(0, 15))

        self.card_customers = self._create_kpi_card(
            cards_frame, "👥", reshape_text("إجمالي العملاء"),
            "0", COLORS['primary'], "#eef0ff"
        )
        self.card_services = self._create_kpi_card(
            cards_frame, "🛠️", reshape_text("إجمالي الخدمات"),
            "0", COLORS['info'], "#f0eeff"
        )
        self.card_orders = self._create_kpi_card(
            cards_frame, "📋", reshape_text("إجمالي الطلبات"),
            "0", COLORS['success'], "#eefffe"
        )
        self.card_revenue = self._create_kpi_card(
            cards_frame, "💰", reshape_text("إجمالي الإيرادات"),
            "0 " + reshape_text("ر.س"), COLORS['warning'], "#fff8ee"
        )

    def _create_kpi_card(self, parent, icon: str, title: str,
                         value: str, color: str, bg_color: str) -> dict:
        """إنشاء بطاقة KPI احترافية مع أيقونة وقيمة ومؤشر اتجاه"""
        card = ctk.CTkFrame(
            parent, fg_color=bg_color, corner_radius=15,
            border_width=1, border_color=color
        )
        card.pack(side=ctk.RIGHT, padx=8, fill=ctk.BOTH, expand=True)

        # شريط ملون علوي
        top_bar = ctk.CTkFrame(card, fg_color=color, height=4, corner_radius=0)
        top_bar.pack(fill=ctk.X)
        top_bar.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)

        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill=ctk.X)

        icon_label = ctk.CTkLabel(
            header_row,
            text=icon,
            font=ctk.CTkFont(family="Cairo", size=28)
        )
        icon_label.pack(side=ctk.RIGHT)

        value_label = ctk.CTkLabel(
            header_row,
            text=value,
            font=ctk.CTkFont(family="Cairo", size=22, weight="bold"),
            text_color=color
        )
        value_label.pack(side=ctk.LEFT)

        title_label = ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(family="Cairo", size=12),
            text_color=COLORS['text_gray']
        )
        title_label.pack(pady=(5, 0))

        # مؤشر الاتجاه (initially)
        trend_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(family="Cairo", size=10),
            text_color=COLORS['success']
        )
        trend_label.pack(pady=(2, 0))

        return {
            'icon': icon_label,
            'value': value_label,
            'title': title_label,
            'trend': trend_label,
            'color': color,
        }

    # ═══════════════════════════════════════════════════════════
    # القسم 3: بطاقات KPI الثانوية
    # ═══════════════════════════════════════════════════════════

    def _create_secondary_kpi_cards(self, parent):
        """إنشاء صف بطاقات KPI الثانوية (4 بطاقات)"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, pady=(0, 15))

        self.card_today_orders = self._create_small_kpi_card(
            cards_frame, "📅", reshape_text("طلبات اليوم"),
            "0", COLORS['primary']
        )
        self.card_week_orders = self._create_small_kpi_card(
            cards_frame, "📊", reshape_text("طلبات هذا الأسبوع"),
            "0", COLORS['info']
        )
        self.card_avg_order = self._create_small_kpi_card(
            cards_frame, "💲", reshape_text("متوسط قيمة الطلب"),
            "0 " + reshape_text("ر.س"), COLORS['success']
        )
        self.card_completion_rate = self._create_small_kpi_card(
            cards_frame, "✅", reshape_text("نسبة الإنجاز"),
            "0%", COLORS['warning']
        )

    def _create_small_kpi_card(self, parent, icon: str, title: str,
                               value: str, color: str) -> dict:
        """إنشاء بطاقة KPI صغيرة"""
        card = ctk.CTkFrame(
            parent, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        card.pack(side=ctk.RIGHT, padx=8, fill=ctk.BOTH, expand=True)

        card_header = ctk.CTkFrame(card, fg_color="transparent")
        card_header.pack(fill=ctk.X, padx=15, pady=(12, 5))

        icon_label = ctk.CTkLabel(
            card_header,
            text=icon,
            font=ctk.CTkFont(family="Cairo", size=24)
        )
        icon_label.pack(side=ctk.RIGHT)

        value_label = ctk.CTkLabel(
            card_header,
            text=value,
            font=ctk.CTkFont(family="Cairo", size=20, weight="bold"),
            text_color=color
        )
        value_label.pack(side=ctk.LEFT)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family="Cairo", size=11),
            text_color=COLORS['text_gray']
        )
        title_label.pack(pady=(0, 12))

        return {'icon': icon_label, 'value': value_label, 'title': title_label}

    # ═══════════════════════════════════════════════════════════
    # القسم 4: بطاقة تفصيل حالات الطلبات
    # ═══════════════════════════════════════════════════════════

    def _create_status_breakdown(self, parent):
        """إنشاء بطاقة تفصيل حالات الطلبات مع أشرطة التقدم"""
        breakdown_card = ctk.CTkFrame(
            parent, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        breakdown_card.pack(fill=ctk.X, pady=(0, 15), padx=5)

        card_header = ctk.CTkFrame(breakdown_card, fg_color="transparent")
        card_header.pack(fill=ctk.X, padx=15, pady=(12, 5))

        header_title = ctk.CTkLabel(
            card_header,
            text=reshape_text("📋 تفصيل حالات الطلبات"),
            font=ctk.CTkFont(family="Cairo", size=16, weight="bold"),
            text_color=COLORS['text_dark']
        )
        header_title.pack(side=ctk.RIGHT)

        self.status_total_label = ctk.CTkLabel(
            card_header,
            text=reshape_text("الإجمالي: 0"),
            font=ctk.CTkFont(family="Cairo", size=12),
            text_color=COLORS['text_gray']
        )
        self.status_total_label.pack(side=ctk.LEFT)

        # حاوية أشرطة الحالة
        self.status_bars_container = ctk.CTkFrame(
            breakdown_card, fg_color="transparent"
        )
        self.status_bars_container.pack(fill=ctk.X, padx=15, pady=(0, 15))

        # إنشاء أشرطة الحالة الأربعة
        self.status_progress = {}
        status_configs = [
            ('pending', reshape_text('قيد الانتظار'), COLORS['pending']),
            ('in_progress', reshape_text('قيد التنفيذ'), COLORS['in_progress']),
            ('completed', reshape_text('مكتمل'), COLORS['completed']),
            ('cancelled', reshape_text('ملغي'), COLORS['cancelled']),
        ]

        for status_key, status_label, color in status_configs:
            row = ctk.CTkFrame(self.status_bars_container, fg_color="transparent")
            row.pack(fill=ctk.X, pady=3)

            label = ctk.CTkLabel(
                row,
                text=status_label,
                font=ctk.CTkFont(family="Cairo", size=12),
                text_color=COLORS['text_dark'],
                width=120, anchor="e"
            )
            label.pack(side=ctk.RIGHT, padx=(0, 10))

            count_label = ctk.CTkLabel(
                row,
                text="0",
                font=ctk.CTkFont(family="Cairo", size=12, weight="bold"),
                text_color=color,
                width=50, anchor="e"
            )
            count_label.pack(side=ctk.LEFT, padx=(10, 0))

            pct_label = ctk.CTkLabel(
                row,
                text="(0%)",
                font=ctk.CTkFont(family="Cairo", size=10),
                text_color=COLORS['text_gray'],
                width=60, anchor="e"
            )
            pct_label.pack(side=ctk.LEFT, padx=(5, 0))

            # شريط التقدم
            progress_bar = ctk.CTkProgressBar(
                row, height=20, corner_radius=10,
                fg_color="#f0f0f0", progress_color=color
            )
            progress_bar.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)
            progress_bar.set(0)

            self.status_progress[status_key] = {
                'bar': progress_bar,
                'count_label': count_label,
                'pct_label': pct_label,
            }

    # ═══════════════════════════════════════════════════════════
    # القسم 5: صف الرسوم البيانية الأول
    # ═══════════════════════════════════════════════════════════

    def _create_charts_row1(self, parent):
        """إنشاء صف الرسوم البيانية الأول: الإيرادات الشهرية + الطلبات حسب الحالة"""
        charts_row = ctk.CTkFrame(parent, fg_color="transparent")
        charts_row.pack(fill=ctk.BOTH, expand=True, pady=(0, 15))

        # الرسم البياني 1: الإيرادات الشهرية
        revenue_chart_frame = ctk.CTkFrame(
            charts_row, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        revenue_chart_frame.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=(0, 5))

        revenue_title = ctk.CTkLabel(
            revenue_chart_frame,
            text=reshape_text("💰 الإيرادات الشهرية"),
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color=COLORS['text_dark']
        )
        revenue_title.pack(pady=(10, 5))

        self.revenue_canvas_frame = ctk.CTkFrame(revenue_chart_frame, fg_color="white")
        self.revenue_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))

        # الرسم البياني 2: الطلبات حسب الحالة (دائري)
        status_chart_frame = ctk.CTkFrame(
            charts_row, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        status_chart_frame.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=(5, 0))

        status_title = ctk.CTkLabel(
            status_chart_frame,
            text=reshape_text("📊 الطلبات حسب الحالة"),
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color=COLORS['text_dark']
        )
        status_title.pack(pady=(10, 5))

        self.status_chart_canvas_frame = ctk.CTkFrame(status_chart_frame, fg_color="white")
        self.status_chart_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))

    # ═══════════════════════════════════════════════════════════
    # القسم 6: صف الرسوم البيانية الثاني
    # ═══════════════════════════════════════════════════════════

    def _create_charts_row2(self, parent):
        """إنشاء صف الرسوم البيانية الثاني: الخدمات الأكثر طلباً + نمو العملاء"""
        charts_row = ctk.CTkFrame(parent, fg_color="transparent")
        charts_row.pack(fill=ctk.BOTH, expand=True, pady=(0, 15))

        # الرسم البياني 3: الخدمات الأكثر طلباً
        services_chart_frame = ctk.CTkFrame(
            charts_row, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        services_chart_frame.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=(0, 5))

        services_title = ctk.CTkLabel(
            services_chart_frame,
            text=reshape_text("🛠️ الخدمات الأكثر طلباً"),
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color=COLORS['text_dark']
        )
        services_title.pack(pady=(10, 5))

        self.services_canvas_frame = ctk.CTkFrame(services_chart_frame, fg_color="white")
        self.services_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))

        # الرسم البياني 4: نمو العملاء الشهري
        growth_chart_frame = ctk.CTkFrame(
            charts_row, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        growth_chart_frame.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=(5, 0))

        growth_title = ctk.CTkLabel(
            growth_chart_frame,
            text=reshape_text("👥 نمو العملاء الشهري"),
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color=COLORS['text_dark']
        )
        growth_title.pack(pady=(10, 5))

        self.growth_canvas_frame = ctk.CTkFrame(growth_chart_frame, fg_color="white")
        self.growth_canvas_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))

    # ═══════════════════════════════════════════════════════════
    # القسم 7: جدول أفضل العملاء
    # ═══════════════════════════════════════════════════════════

    def _create_top_customers_table(self, parent):
        """إنشاء جدول أفضل العملاء مع Treeview"""
        table_card = ctk.CTkFrame(
            parent, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        table_card.pack(fill=ctk.BOTH, expand=True, pady=(0, 15), padx=5)

        table_header = ctk.CTkFrame(table_card, fg_color="transparent")
        table_header.pack(fill=ctk.X, padx=15, pady=(12, 5))

        header_title = ctk.CTkLabel(
            table_header,
            text=reshape_text("⭐ أفضل العملاء"),
            font=ctk.CTkFont(family="Cairo", size=16, weight="bold"),
            text_color=COLORS['text_dark']
        )
        header_title.pack(side=ctk.RIGHT)

        # ترتيب الأعمدة من اليمين لليسار
        columns = ("rank", "customer_name", "total_spending", "order_count")
        headings = {
            "rank": reshape_text("#"),
            "customer_name": reshape_text("اسم العميل"),
            "order_count": reshape_text("عدد الطلبات"),
            "total_spending": reshape_text("إجمالي الإنفاق"),
        }
        widths = {"rank": 50, "customer_name": 250, "order_count": 120, "total_spending": 180}

        style = ttk.Style()
        style.configure("TopCustomers.Treeview",
                        background="#f9f9f9",
                        foreground="black",
                        rowheight=38,
                        fieldbackground="#f9f9f9",
                        font=("Cairo", 11))
        style.map("TopCustomers.Treeview",
                  background=[("selected", "#2b5b84")],
                  foreground=[("selected", "white")])
        style.configure("TopCustomers.Treeview.Heading",
                        font=("Cairo", 12, "bold"),
                        background="#e9ecef",
                        foreground="black",
                        relief="flat")
        style.map("TopCustomers.Treeview.Heading",
                  background=[("active", "#dee2e6")])

        table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        table_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.top_customers_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=6,
            style="TopCustomers.Treeview"
        )

        for col in columns:
            self.top_customers_tree.heading(col, text=headings[col], anchor="center")
            self.top_customers_tree.column(col, width=widths[col], minwidth=50, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient=ctk.VERTICAL,
                                  command=self.top_customers_tree.yview)
        self.top_customers_tree.configure(yscrollcommand=scrollbar.set)

        self.top_customers_tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y)

        # ألوان متناوبة
        self.top_customers_tree.tag_configure("Even", background="#f9f9f9")
        self.top_customers_tree.tag_configure("Odd", background="#ffffff")

    # ═══════════════════════════════════════════════════════════
    # القسم 8: جدول أحدث الطلبات
    # ═══════════════════════════════════════════════════════════

    def _create_recent_orders_table(self, parent):
        """إنشاء جدول أحدث الطلبات مع Treeview"""
        table_card = ctk.CTkFrame(
            parent, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        table_card.pack(fill=ctk.BOTH, expand=True, pady=(0, 15), padx=5)

        table_header = ctk.CTkFrame(table_card, fg_color="transparent")
        table_header.pack(fill=ctk.X, padx=15, pady=(12, 5))

        header_title = ctk.CTkLabel(
            table_header,
            text=reshape_text("📋 أحدث الطلبات"),
            font=ctk.CTkFont(family="Cairo", size=16, weight="bold"),
            text_color=COLORS['text_dark']
        )
        header_title.pack(side=ctk.RIGHT)

        # ترتيب الأعمدة من اليمين لليسار
        columns = ("id", "customer_name", "total_amount", "status", "created_at")
        headings = {
            "id": reshape_text("الرقم"),
            "customer_name": reshape_text("العميل"),
            "total_amount": reshape_text("المبلغ"),
            "status": reshape_text("الحالة"),
            "created_at": reshape_text("التاريخ"),
        }
        widths = {
            "id": 60, "customer_name": 220,
            "total_amount": 130, "status": 120, "created_at": 140,
        }

        style = ttk.Style()
        style.configure("Recent.Treeview",
                        background="#f9f9f9",
                        foreground="black",
                        rowheight=38,
                        fieldbackground="#f9f9f9",
                        font=("Cairo", 11))
        style.map("Recent.Treeview",
                  background=[("selected", "#2b5b84")],
                  foreground=[("selected", "white")])
        style.configure("Recent.Treeview.Heading",
                        font=("Cairo", 12, "bold"),
                        background="#e9ecef",
                        foreground="black",
                        relief="flat")
        style.map("Recent.Treeview.Heading",
                  background=[("active", "#dee2e6")])

        table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        table_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.recent_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8,
            style="Recent.Treeview"
        )

        for col in columns:
            self.recent_tree.heading(col, text=headings[col], anchor="center")
            self.recent_tree.column(col, width=widths[col], minwidth=50, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient=ctk.VERTICAL,
                                  command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)

        self.recent_tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y)

        # تنسيق الصفوف حسب الحالة
        self.recent_tree.tag_configure('pending', foreground=COLORS['pending'])
        self.recent_tree.tag_configure('in_progress', foreground=COLORS['in_progress'])
        self.recent_tree.tag_configure('completed', foreground=COLORS['completed'])
        self.recent_tree.tag_configure('cancelled', foreground=COLORS['cancelled'])

    # ═══════════════════════════════════════════════════════════
    # القسم 9: ملخص النشاط
    # ═══════════════════════════════════════════════════════════

    def _create_activity_summary(self, parent):
        """إنشاء بطاقة ملخص النشاط"""
        summary_card = ctk.CTkFrame(
            parent, fg_color="white", corner_radius=12,
            border_width=1, border_color=COLORS['card_border']
        )
        summary_card.pack(fill=ctk.X, pady=(0, 15), padx=5)

        card_header = ctk.CTkFrame(summary_card, fg_color="transparent")
        card_header.pack(fill=ctk.X, padx=15, pady=(12, 5))

        header_title = ctk.CTkLabel(
            card_header,
            text=reshape_text("⚡ ملخص النشاط"),
            font=ctk.CTkFont(family="Cairo", size=16, weight="bold"),
            text_color=COLORS['text_dark']
        )
        header_title.pack(side=ctk.RIGHT)

        # صف عناصر الملخص
        summary_items_frame = ctk.CTkFrame(summary_card, fg_color="transparent")
        summary_items_frame.pack(fill=ctk.X, padx=15, pady=(0, 15))

        # عنصر 1: أكثر الأيام نشاطاً
        self.busiest_day_card = self._create_summary_item(
            summary_items_frame,
            "📅", reshape_text("أكثر الأيام نشاطاً"),
            reshape_text("لم يتم تحديده"), COLORS['primary']
        )

        # عنصر 2: أكثر الساعات نشاطاً
        self.busiest_hour_card = self._create_summary_item(
            summary_items_frame,
            "⏰", reshape_text("أكثر الساعات نشاطاً"),
            reshape_text("لم يتم تحديدها"), COLORS['info']
        )

        # عنصر 3: فئة الخدمات الأكثر طلباً
        self.popular_category_card = self._create_summary_item(
            summary_items_frame,
            "🏷️", reshape_text("فئة الخدمات الأكثر طلباً"),
            reshape_text("لم يتم تحديدها"), COLORS['success']
        )

    def _create_summary_item(self, parent, icon: str, title: str,
                             value: str, color: str) -> dict:
        """إنشاء عنصر ملخص نشاط صغير"""
        item_frame = ctk.CTkFrame(
            parent, fg_color=COLORS['bg_light'], corner_radius=10
        )
        item_frame.pack(side=ctk.RIGHT, padx=8, fill=ctk.BOTH, expand=True)

        icon_label = ctk.CTkLabel(
            item_frame,
            text=icon,
            font=ctk.CTkFont(family="Cairo", size=24)
        )
        icon_label.pack(pady=(12, 5))

        value_label = ctk.CTkLabel(
            item_frame,
            text=value,
            font=ctk.CTkFont(family="Cairo", size=13, weight="bold"),
            text_color=color
        )
        value_label.pack(pady=2)

        title_label = ctk.CTkLabel(
            item_frame,
            text=title,
            font=ctk.CTkFont(family="Cairo", size=10),
            text_color=COLORS['text_gray']
        )
        title_label.pack(pady=(0, 12))

        return {'value': value_label, 'title': title_label}

    # ═══════════════════════════════════════════════════════════
    # تحميل البيانات والإحصائيات
    # ═══════════════════════════════════════════════════════════

    def _get_date_filter(self) -> Optional[str]:
        """الحصول على شرط تصفية التاريخ إذا تم تحديده"""
        date_from = self.date_from_entry.get().strip()
        date_to = self.date_to_entry.get().strip()

        conditions = []
        if date_from:
            conditions.append(f"created_at >= '{date_from}'")
        if date_to:
            conditions.append(f"created_at <= '{date_to} 23:59:59'")

        if conditions:
            return " AND ".join(conditions)
        return None

    def _load_statistics(self):
        """تحميل جميع الإحصائيات وعرضها في اللوحة"""
        try:
            stats = self.db_manager.get_statistics()
            date_filter = self._get_date_filter()

            # تحديث بطاقات KPI الرئيسية
            self._update_main_kpis(stats, date_filter)

            # تحديث بطاقات KPI الثانوية
            self._update_secondary_kpis(stats, date_filter)

            # تحديث تفصيل حالات الطلبات
            self._update_status_breakdown(stats, date_filter)

            # رسم الرسوم البيانية
            self._draw_monthly_revenue_chart(stats, date_filter)
            self._draw_status_pie_chart(stats, date_filter)
            self._draw_popular_services_chart(stats, date_filter)
            self._draw_customer_growth_chart(date_filter)

            # تحميل الجداول
            self._load_top_customers(date_filter)
            self._load_recent_orders(stats.get('recent_orders', []), date_filter)

            # تحديث ملخص النشاط
            self._update_activity_summary(date_filter)

        except Exception as e:
            messagebox.showerror(
                reshape_text("خطأ"),
                reshape_text(f"حدث خطأ أثناء تحميل الإحصائيات: {str(e)}")
            )

    # ── تحديث بطاقات KPI الرئيسية ──

    def _update_main_kpis(self, stats: dict, date_filter: Optional[str]):
        """تحديث بطاقات KPI الرئيسية الأربع"""
        try:
            if date_filter:
                filter_clause = f"WHERE {date_filter}"
                customers_result = self.db_manager.execute_query(
                    f"SELECT COUNT(*) as count FROM customers {filter_clause.replace('created_at', 'customers.created_at')}"
                )
                total_customers = customers_result[0]['count'] if customers_result else 0
            else:
                total_customers = stats['total_customers']

            self.card_customers['value'].configure(text=f"{total_customers:,}")
            self.card_services['value'].configure(text=f"{stats['total_services']:,}")
            self.card_orders['value'].configure(text=f"{stats['total_orders']:,}")
            self.card_revenue['value'].configure(
                text=f"{stats['total_revenue']:,.0f} " + reshape_text("ر.س")
            )
        except Exception:
            pass

    # ── تحديث بطاقات KPI الثانوية ──

    def _update_secondary_kpis(self, stats: dict, date_filter: Optional[str]):
        """تحديث بطاقات KPI الثانوية الأربع"""
        try:
            # طلبات اليوم - MySQL/MariaDB compatible
            today_filter = "WHERE created_at >= DATE(NOW())"
            if date_filter:
                today_filter = f"WHERE {date_filter} AND created_at >= DATE(NOW())"

            today_result = self.db_manager.execute_query(
                f"SELECT COUNT(*) as count FROM orders {today_filter}"
            )
            today_orders = today_result[0]['count'] if today_result else 0
            self.card_today_orders['value'].configure(text=str(today_orders))

            # طلبات هذا الأسبوع - MySQL/MariaDB compatible
            week_filter = "WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
            if date_filter:
                week_filter = f"WHERE {date_filter} AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"

            week_result = self.db_manager.execute_query(
                f"SELECT COUNT(*) as count FROM orders {week_filter}"
            )
            week_orders = week_result[0]['count'] if week_result else 0
            self.card_week_orders['value'].configure(text=str(week_orders))

            # متوسط قيمة الطلب
            total_revenue = stats.get('total_revenue', 0)
            total_orders = stats.get('total_orders', 0)
            avg_order = total_revenue / total_orders if total_orders > 0 else 0
            self.card_avg_order['value'].configure(
                text=f"{avg_order:,.0f} " + reshape_text("ر.س")
            )

            # نسبة الإنجاز
            orders_by_status = stats.get('orders_by_status', {})
            completed = orders_by_status.get('completed', 0)
            total = sum(orders_by_status.values()) if orders_by_status else 0
            completion_rate = (completed / total * 100) if total > 0 else 0
            self.card_completion_rate['value'].configure(text=f"{completion_rate:.1f}%")

        except Exception:
            pass

    # ── تحديث تفصيل حالات الطلبات ──

    def _update_status_breakdown(self, stats: dict, date_filter: Optional[str]):
        """تحديث أشرطة تفصيل حالات الطلبات"""
        try:
            orders_by_status = stats.get('orders_by_status', {})
            total = sum(orders_by_status.values()) if orders_by_status else 0

            self.status_total_label.configure(
                text=reshape_text(f"الإجمالي: {total}")
            )

            for status_key in ['pending', 'in_progress', 'completed', 'cancelled']:
                count = orders_by_status.get(status_key, 0)
                pct = (count / total) if total > 0 else 0

                self.status_progress[status_key]['bar'].set(pct)
                self.status_progress[status_key]['count_label'].configure(
                    text=str(count)
                )
                self.status_progress[status_key]['pct_label'].configure(
                    text=f"({pct * 100:.1f}%)"
                )
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════
    # رسم الرسوم البيانية
    # ═══════════════════════════════════════════════════════════

    def _clear_chart_frame(self, frame):
        """مسح إطار الرسم البياني"""
        for widget in frame.winfo_children():
            widget.destroy()

    def _show_no_data(self, frame):
        """عرض رسالة لا توجد بيانات"""
        self._clear_chart_frame(frame)
        no_data_label = ctk.CTkLabel(
            frame,
            text=reshape_text("لا توجد بيانات"),
            text_color=COLORS['text_gray'],
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        no_data_label.pack(expand=True)
        return False

    def _show_chart_error(self, frame, error_msg: str):
        """عرض رسالة خطأ في الرسم البياني"""
        self._clear_chart_frame(frame)
        error_label = ctk.CTkLabel(
            frame,
            text=reshape_text(f"خطأ في عرض الرسم البياني: {error_msg}"),
            text_color=COLORS['danger'],
            font=ctk.CTkFont(family="Cairo", size=11)
        )
        error_label.pack(expand=True)

    # ── الرسم 1: الإيرادات الشهرية ──

    def _draw_monthly_revenue_chart(self, stats: dict, date_filter: Optional[str]):
        """رسم بياني للإيرادات الشهرية"""
        try:
            query = """
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
                       COALESCE(SUM(total_amount), 0) as revenue
                FROM orders WHERE status = 'completed'
            """
            if date_filter:
                query += f" AND {date_filter}"
            query += " GROUP BY month ORDER BY month LIMIT 12"

            monthly_data = self.db_manager.execute_query(query)

            if not monthly_data:
                self._show_no_data(self.revenue_canvas_frame)
                return

            self._clear_chart_frame(self.revenue_canvas_frame)

            months = []
            revenues = []
            for row in monthly_data:
                month_key = row['month']
                if len(month_key) >= 7:
                    m_part = month_key[5:7]
                    months.append(reshape_text(MONTH_NAMES_AR.get(m_part, m_part)))
                else:
                    months.append(month_key)
                # تحويل إلى float لحل مشكلة Decimal
                revenues.append(float(row['revenue']))

            fig = Figure(figsize=(5, 3.5), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)

            colors_bar = [COLORS['success'] if r >= max(revenues) * 0.5
                          else COLORS['warning'] for r in revenues]
            bars = ax.bar(months, revenues, color=colors_bar, alpha=0.85,
                          edgecolor='#ffffff', linewidth=0.5)

            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{height:,.0f}', ha='center', va='bottom',
                            fontfamily='Cairo', fontsize=8, fontweight='bold')

            ax.set_ylabel(reshape_text('الإيرادات (ر.س)'),
                          fontfamily='Cairo', fontsize=10)
            ax.set_xlabel(reshape_text('الشهر'), fontfamily='Cairo', fontsize=10)
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months, rotation=45, ha='right',
                               fontfamily='Cairo', fontsize=9)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(axis='y', alpha=0.3)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.revenue_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)

        except Exception as e:
            self._show_chart_error(self.revenue_canvas_frame, str(e))

    # ── الرسم 2: الطلبات حسب الحالة (دائري) ──

    def _draw_status_pie_chart(self, stats: dict, date_filter: Optional[str]):
        """رسم بياني دائري للطلبات حسب الحالة"""
        try:
            query = "SELECT status, COUNT(*) as count FROM orders"
            if date_filter:
                query += f" WHERE {date_filter}"
            query += " GROUP BY status"

            status_data = self.db_manager.execute_query(query)

            if not status_data:
                self._show_no_data(self.status_chart_canvas_frame)
                return

            self._clear_chart_frame(self.status_chart_canvas_frame)

            labels = []
            sizes = []
            colors_pie = []

            status_colors = {
                'pending': COLORS['pending'],
                'in_progress': COLORS['in_progress'],
                'completed': COLORS['completed'],
                'cancelled': COLORS['cancelled'],
            }

            for row in status_data:
                status = row['status']
                labels.append(STATUS_MAP.get(status, status))
                # تحويل إلى float لحل مشكلة Decimal
                sizes.append(float(row['count']))
                colors_pie.append(status_colors.get(status, '#6c757d'))

            fig = Figure(figsize=(5, 3.5), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors_pie,
                autopct='%1.1f%%', startangle=90,
                textprops={'fontfamily': 'Cairo', 'fontsize': 10},
                wedgeprops={'edgecolor': 'white', 'linewidth': 2}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            ax.axis('equal')

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.status_chart_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)

        except Exception as e:
            self._show_chart_error(self.status_chart_canvas_frame, str(e))

    # ── الرسم 3: الخدمات الأكثر طلباً ──

    def _draw_popular_services_chart(self, stats: dict, date_filter: Optional[str]):
        """رسم بياني للخدمات الأكثر طلباً"""
        try:
            query = """
                SELECT s.name, COUNT(od.id) as order_count
                FROM services s
                LEFT JOIN order_details od ON s.id = od.service_id
                LEFT JOIN orders o ON od.order_id = o.id
                WHERE s.is_active = 1
            """
            if date_filter:
                query += f" AND o.created_at IS NOT NULL AND {date_filter.replace('created_at', 'o.created_at')}"
            query += " GROUP BY s.id ORDER BY order_count DESC LIMIT 5"

            services_data = self.db_manager.execute_query(query)

            if not services_data or all(s['order_count'] == 0 for s in services_data):
                self._show_no_data(self.services_canvas_frame)
                return

            self._clear_chart_frame(self.services_canvas_frame)

            names = []
            counts = []
            for service in services_data:
                name = reshape_text(service['name'])
                if len(name) > 18:
                    name = name[:18] + '...'
                names.append(name)
                # تحويل إلى float لحل مشكلة Decimal
                counts.append(float(service['order_count']))

            fig = Figure(figsize=(5, 3.5), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)

            bar_colors = ['#4361ee', '#3f37c9', '#2ec4b6', '#f77f00', '#ef233c']
            bars = ax.barh(names, counts, color=bar_colors[:len(names)],
                           alpha=0.85, edgecolor='white', linewidth=0.5)

            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax.text(width + 0.1, bar.get_y() + bar.get_height() / 2.,
                            f'{int(width)}', ha='left', va='center',
                            fontfamily='Cairo', fontsize=9, fontweight='bold')

            ax.set_xlabel(reshape_text('عدد الطلبات'), fontfamily='Cairo', fontsize=10)
            ax.set_ylabel(reshape_text('الخدمة'), fontfamily='Cairo', fontsize=10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(axis='x', alpha=0.3)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.services_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)

        except Exception as e:
            self._show_chart_error(self.services_canvas_frame, str(e))

    # ── الرسم 4: نمو العملاء الشهري ──

    def _draw_customer_growth_chart(self, date_filter: Optional[str]):
        """رسم بياني خطي لنمو العملاء الشهري"""
        try:
            query = """
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
                       COUNT(*) as count
                FROM customers
            """
            if date_filter:
                query += f" WHERE {date_filter.replace('created_at', 'customers.created_at')}"
            query += " GROUP BY month ORDER BY month LIMIT 12"

            growth_data = self.db_manager.execute_query(query)

            if not growth_data:
                self._show_no_data(self.growth_canvas_frame)
                return

            self._clear_chart_frame(self.growth_canvas_frame)

            months = []
            counts = []
            cumulative = []
            total = 0

            for row in growth_data:
                month_key = row['month']
                if len(month_key) >= 7:
                    m_part = month_key[5:7]
                    months.append(reshape_text(MONTH_NAMES_AR.get(m_part, m_part)))
                else:
                    months.append(month_key)
                # تحويل إلى float لحل مشكلة Decimal
                total += float(row['count'])
                counts.append(float(row['count']))
                cumulative.append(float(total))

            fig = Figure(figsize=(5, 3.5), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)

            ax.plot(months, counts, 'o-', color=COLORS['primary'], linewidth=2.5,
                    markersize=8, label=reshape_text('عملاء جدد'), alpha=0.9)
            ax.fill_between(range(len(counts)), counts, alpha=0.1, color=COLORS['primary'])

            ax2 = ax.twinx()
            ax2.plot(months, cumulative, 's--', color=COLORS['success'], linewidth=2,
                     markersize=6, label=reshape_text('الإجمالي التراكمي'), alpha=0.8)

            ax.set_ylabel(reshape_text('عملاء جدد'), fontfamily='Cairo', fontsize=10,
                          color=COLORS['primary'])
            ax2.set_ylabel(reshape_text('الإجمالي التراكمي'), fontfamily='Cairo',
                           fontsize=10, color=COLORS['success'])

            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months, rotation=45, ha='right',
                               fontfamily='Cairo', fontsize=9)

            ax.spines['top'].set_visible(False)
            ax.grid(axis='y', alpha=0.3)

            # دمج وسائل الإيضاح
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left',
                      prop={'family': 'Cairo', 'size': 9})

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.growth_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)

        except Exception as e:
            self._show_chart_error(self.growth_canvas_frame, str(e))

    # ═══════════════════════════════════════════════════════════
    # تحميل البيانات في الجداول
    # ═══════════════════════════════════════════════════════════

    def _load_top_customers(self, date_filter: Optional[str]):
        """تحميل جدول أفضل العملاء"""
        try:
            # مسح الجدول
            for item in self.top_customers_tree.get_children():
                self.top_customers_tree.delete(item)

            query = """
                SELECT c.name as customer_name,
                       COUNT(o.id) as order_count,
                       COALESCE(SUM(CASE WHEN o.status = 'completed' THEN o.total_amount ELSE 0 END), 0) as total_spending
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
            """
            if date_filter:
                query += f" WHERE {date_filter.replace('created_at', 'o.created_at')}"
            query += " GROUP BY c.id ORDER BY total_spending DESC LIMIT 10"

            top_customers = self.db_manager.execute_query(query)

            for i, customer in enumerate(top_customers):
                tag = "Even" if i % 2 == 0 else "Odd"
                self.top_customers_tree.insert(
                    "",
                    ctk.END,
                    values=(
                        i + 1,
                        reshape_text(customer['customer_name']),
                        f"{customer['order_count']}",
                        f"{customer['total_spending']:,.2f} " + reshape_text("ر.س")
                    ),
                    tags=(tag,)
                )

        except Exception as e:
            self._show_no_data_message(self.top_customers_tree, str(e))

    def _load_recent_orders(self, orders: list, date_filter: Optional[str]):
        """تحميل جدول أحدث الطلبات"""
        try:
            # مسح الجدول
            for item in self.recent_tree.get_children():
                self.recent_tree.delete(item)

            # إذا كان هناك فلتر تاريخي، نجلب البيانات من قاعدة البيانات
            if date_filter:
                query = """
                    SELECT o.id, o.status, o.total_amount, o.created_at,
                           c.name as customer_name
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE {date_filter}
                    ORDER BY o.created_at DESC LIMIT 10
                """.format(date_filter=date_filter)
                orders = self.db_manager.execute_query(query)

            for order in orders:
                created_at = ""
                if order.get('created_at'):
                    if isinstance(order['created_at'], datetime):
                        created_at = order['created_at'].strftime("%Y-%m-%d")
                    else:
                        created_at = str(order['created_at'])[:10]

                status_original = order.get('status', '')
                status_display = STATUS_MAP.get(status_original, status_original)
                customer_display = reshape_text(order.get('customer_name', ''))

                tags = [status_original] if status_original in STATUS_MAP else []

                self.recent_tree.insert(
                    "",
                    ctk.END,
                    tags=tags,
                    values=(
                        order.get('id', ''),
                        customer_display,
                        f"{order.get('total_amount', 0):,.2f} " + reshape_text("ر.س"),
                        status_display,
                        created_at
                    )
                )

        except Exception as e:
            self._show_no_data_message(self.recent_tree, str(e))

    def _show_no_data_message(self, tree, error_msg: str):
        """عرض رسالة في الجدول عند عدم وجود بيانات"""
        pass  # الجدول يبقى فارغاً بصمت

    # ═══════════════════════════════════════════════════════════
    # تحديث ملخص النشاط
    # ═══════════════════════════════════════════════════════════

    def _update_activity_summary(self, date_filter: Optional[str]):
        """تحديث بطاقة ملخص النشاط (أكثر الأيام، أكثر الساعات، فئة شائعة)"""
        try:
            base_query = "FROM orders"
            if date_filter:
                base_query += f" WHERE {date_filter}"

            # أكثر الأيام نشاطاً
            busiest_day_result = self.db_manager.execute_query(
                f"SELECT DAYOFWEEK(created_at) as day_of_week, COUNT(*) as count "
                f"{base_query} GROUP BY day_of_week ORDER BY count DESC LIMIT 1"
            )
            if busiest_day_result and busiest_day_result[0]['count'] > 0:
                day_key = busiest_day_result[0]['day_of_week']
                day_name = DAY_NAMES_AR.get(day_key, day_key)
                count = busiest_day_result[0]['count']
                self.busiest_day_card['value'].configure(
                    text=f"{day_name} ({count} " + reshape_text("طلب") + ")"
                )
            else:
                self.busiest_day_card['value'].configure(
                    text=reshape_text("لا توجد بيانات")
                )

            # أكثر الساعات نشاطاً
            busiest_hour_result = self.db_manager.execute_query(
                f"SELECT HOUR(created_at) as hour, COUNT(*) as count "
                f"{base_query} GROUP BY hour ORDER BY count DESC LIMIT 1"
            )
            if busiest_hour_result and busiest_hour_result[0]['count'] > 0:
                hour_str = busiest_hour_result[0]['hour']
                count = busiest_hour_result[0]['count']
                self.busiest_hour_card['value'].configure(
                    text=f"{hour_str}:00 ({count} " + reshape_text("طلب") + ")"
                )
            else:
                self.busiest_hour_card['value'].configure(
                    text=reshape_text("لا توجد بيانات")
                )

            # فئة الخدمات الأكثر طلباً
            popular_category_result = self.db_manager.execute_query("""
                SELECT sc.name as category_name, COUNT(od.id) as order_count
                FROM service_categories sc
                JOIN services s ON sc.id = s.category_id
                JOIN order_details od ON s.id = od.service_id
                JOIN orders o ON od.order_id = o.id
                GROUP BY sc.id ORDER BY order_count DESC LIMIT 1
            """)
            if popular_category_result and popular_category_result[0]['order_count'] > 0:
                cat_name = reshape_text(popular_category_result[0]['category_name'])
                cat_count = popular_category_result[0]['order_count']
                self.popular_category_card['value'].configure(
                    text=f"{cat_name} ({cat_count} " + reshape_text("طلب") + ")"
                )
            else:
                self.popular_category_card['value'].configure(
                    text=reshape_text("لا توجد بيانات")
                )

        except Exception:
            self.busiest_day_card['value'].configure(
                text=reshape_text("لا توجد بيانات")
            )
            self.busiest_hour_card['value'].configure(
                text=reshape_text("لا توجد بيانات")
            )
            self.popular_category_card['value'].configure(
                text=reshape_text("لا توجد بيانات")
            )
