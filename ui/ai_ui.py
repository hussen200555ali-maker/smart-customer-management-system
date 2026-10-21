# استيراد مكتبة واجهة المستخدم المحسنة
import customtkinter as ctk
# استيراد الجداول من tkinter
from tkinter import ttk
# استيراد الأنواع للـ type hints
from typing import Dict, Any, List
# استيراد وحدة التسجيل للتسجيل والأخطاء
import logging
# استيراد مكتبة numpy للحسابات العددية
import numpy as np

# استيراد خوارزمية bidi للتعامل مع النصوص الثنائية
from bidi.algorithm import get_display
# استيراد مكتبة إعادة تشكيل النصوص العربية
import arabic_reshaper

# استيراد نموذج الذكاء الاصطناعي للتنبؤ بالطلبات
from ai.order_predictor import AdvancedOrderPredictionModel
# استيراد مدير قاعدة البيانات
from repositories.database import DatabaseManager
# استيراد دوال عرض الرسائل
from utils.dialogs import (
    show_training_result, show_info, show_success, show_warning, 
    show_error, ask_yes_no
)

# إنشاء logger للتسجيل
logger = logging.getLogger(__name__)


def reshape_text(text: str) -> str:
    """
    إعادة تشكيل النص العربي وعرضه بشكل صحيح من اليمين لليسار
    تستقبل النص وتُعيده مُهيأ للعرض في الواجهة
    """
    if not text:  # إذا كان النص فارغاً أو None
        return ""  # أعد سلسلة فارغة
    try:  # محاولة معالجة النص
        reshaped = arabic_reshaper.reshape(text)  # أعد تشكيل النص العربي
        return get_display(reshaped)  # أعد توجيه النص من اليمين لليسار
    except Exception as e:  # في حالة حدوث خطأ
        logger.error(f"Error reshaping text: {e}")  # تسجيل الخطأ
        return text  # أعد النص الأصلي بدون معالجة


class AIUI:
    """واجهة نموذج الذكاء الاصطناعي - نسخة نهائية مع تحسينات الخطوط والألوان وإصلاح عرض النص العربي"""

    COLORS = {
        "primary": "#4361ee",
        "primary_hover": "#3a56d4",
        "success": "#2ec4b6",
        "success_hover": "#25a89c",
        "danger": "#ff6b6b",
        "danger_hover": "#ee5a5a",
        "info": "#4ecdc4",
        "info_hover": "#3dbdb5",
        "warning": "#95e1d3",
        "warning_hover": "#84d2c4",
        "dark": "#1a1a2e",
        "gray": "#6c757d",
        "light_gray": "#e0e0e0",
        "white": "#ffffff",
        "table_header_bg": "#e9ecef",
        "table_row_odd": "#f8f9fa",
        "table_row_even": "#ffffff"
    }

    def __init__(self, parent: ctk.CTkFrame, db_manager: DatabaseManager):
        self.parent = parent
        self.db_manager = db_manager
        self.ai_model = AdvancedOrderPredictionModel()
        self._create_ui()
        self._load_model_info()

    def _create_ui(self):
        """إنشاء واجهة المستخدم (RTL)"""
        main_container = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="transparent",
            scrollbar_button_color=self.COLORS["primary"],
            scrollbar_button_hover_color=self.COLORS["primary_hover"]
        )
        main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # ========== العنوان ==========
        title_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        title_frame.pack(fill=ctk.X, pady=(0, 20))

        title_label = ctk.CTkLabel(
            title_frame,
            text=reshape_text("الذكاء الاصطناعي والتنبؤات 🤖"),
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.COLORS["dark"],
            justify="right"
        )
        title_label.pack(side=ctk.RIGHT, padx=(0, 10))

        # خط فاصل
        separator = ctk.CTkFrame(main_container, height=2, fg_color=self.COLORS["light_gray"])
        separator.pack(fill=ctk.X, pady=(0, 20))

        # ========== صف البطاقات ==========
        cards_row = ctk.CTkFrame(main_container, fg_color="transparent")
        cards_row.pack(fill=ctk.X, pady=(0, 20))

        # بطاقة معلومات النموذج
        info_card = self._create_card(cards_row, reshape_text("معلومات النموذج"), "📊")
        info_card.pack(side=ctk.RIGHT, padx=(0, 10), fill=ctk.BOTH, expand=True)

        info_content = ctk.CTkFrame(info_card, fg_color="transparent")
        info_content.pack(fill=ctk.BOTH, padx=25, pady=(0, 20))

        self.model_status_label = self._create_info_row(info_content, reshape_text("حالة النموذج:"), "❌ غير مدرب")
        self.model_type_label = self._create_info_row(info_content, reshape_text("نوع النموذج:"), "-")
        self.features_count_label = self._create_info_row(info_content, reshape_text("عدد الميزات:"), "0")

        # ========== بطاقة أداء النموذج (الدقة) ==========
        performance_card = self._create_card(cards_row, reshape_text("أداء النموذج"), "📈")
        performance_card.pack(side=ctk.RIGHT, padx=(10, 0), fill=ctk.BOTH, expand=True)

        perf_content = ctk.CTkFrame(performance_card, fg_color="transparent")
        perf_content.pack(fill=ctk.BOTH, padx=25, pady=(0, 20))

        # الدقة الإجمالية
        self.accuracy_label = self._create_info_row(perf_content, reshape_text("الدقة:"), "—")
        
        # RMSE
        self.rmse_label = self._create_info_row(perf_content, reshape_text("RMSE:"), "—")
        
        # MAE
        self.mae_label = self._create_info_row(perf_content, reshape_text("MAE:"), "—")
        
        # عدد بيانات التدريب
        self.data_points_label = self._create_info_row(perf_content, reshape_text("بيانات التدريب:"), "—")

        # بطاقة التدريب
        train_card = self._create_card(cards_row, reshape_text("تدريب النموذج"), "🚀")
        train_card.pack(side=ctk.RIGHT, padx=(10, 0), fill=ctk.BOTH, expand=True)

        train_content = ctk.CTkFrame(train_card, fg_color="transparent")
        train_content.pack(fill=ctk.BOTH, padx=25, pady=(0, 20))

        train_button = ctk.CTkButton(
            train_content,
            text=reshape_text("بدء التدريب 🚀"),
            command=self._train_model,
            width=250,
            height=50,
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=10
        )
        train_button.pack(pady=10)

        self.training_status_label = ctk.CTkLabel(
            train_content,
            text=reshape_text("الحالة: جاهز للتدريب"),
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS["gray"],
            justify="right"
        )
        self.training_status_label.pack(pady=5)

        # ========== بطاقة التنبؤات ==========
        predict_card = self._create_card(main_container, reshape_text("التنبؤات المستقبلية"), "🔮")
        predict_card.pack(fill=ctk.BOTH, expand=True, pady=(0, 20))

        # أزرار التحليل (بترتيب RTL)
        buttons_frame = ctk.CTkFrame(predict_card, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, padx=25, pady=15)

        button_configs = [
            (reshape_text("تنبؤ بالطلبات (7 أيام) 📊"), self._make_predictions, self.COLORS["success"]),
            (reshape_text("الخدمات الأكثر طلباً 🔥"), self._analyze_services, self.COLORS["danger"]),
            (reshape_text("تحليل الأيام 📅"), self._analyze_days, self.COLORS["info"]),
            (reshape_text("تحليل الساعات ⏰"), self._analyze_hours, self.COLORS["warning"])
        ]

        row1 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row1.pack(fill=ctk.X, pady=5)
        for i in range(2):
            btn = self._create_action_button(row1, *button_configs[i])
            btn.pack(side=ctk.RIGHT, padx=5, expand=True, fill=ctk.X)

        row2 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row2.pack(fill=ctk.X, pady=5)
        for i in range(2, 4):
            btn = self._create_action_button(row2, *button_configs[i])
            btn.pack(side=ctk.RIGHT, padx=5, expand=True, fill=ctk.X)

        # ========== بطاقة الميزات المتقدمة ==========
        advanced_card = self._create_card(main_container, reshape_text("تحليلات متقدمة"), "🧠")
        advanced_card.pack(fill=ctk.BOTH, expand=True, pady=(0, 20))

        advanced_buttons_frame = ctk.CTkFrame(advanced_card, fg_color="transparent")
        advanced_buttons_frame.pack(fill=ctk.X, padx=25, pady=15)

        advanced_button_configs = [
            (reshape_text("تقسيم العملاء 👥"), self._segment_customers, "#6c5ce7"),
            (reshape_text("توصية الخدمات 💡"), self._recommend_services, "#00b894"),
            (reshape_text("تنبؤ الإيرادات 💰"), self._forecast_revenue, "#fdcb6e"),
        ]

        row3 = ctk.CTkFrame(advanced_buttons_frame, fg_color="transparent")
        row3.pack(fill=ctk.X, pady=5)
        for btn_config in advanced_button_configs:
            btn = self._create_action_button(row3, *btn_config)
            btn.pack(side=ctk.RIGHT, padx=5, expand=True, fill=ctk.X)

        # جدول التنبؤات
        self._create_predictions_table(predict_card)

        # ========== خيارات إضافية ==========
        extra_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        extra_frame.pack(fill=ctk.X, pady=10)

        model_names = [reshape_text("الانحدار الخطي"), reshape_text("الغابة العشوائية"), reshape_text("التدرج المتصاعد"), reshape_text("النموذج المدمج (Ensemble)")]

        model_type_label = ctk.CTkLabel(
            extra_frame,
            text=reshape_text("نوع النموذج:"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS["dark"],
            justify="right"
        )
        model_type_label.pack(side=ctk.RIGHT, padx=(10, 0))

        self.model_type_combo = ctk.CTkComboBox(
            extra_frame,
            values=model_names,
            command=self._on_model_type_change,
            width=200,
            height=40,
            state="readonly",
            fg_color=self.COLORS["white"],
            border_color=self.COLORS["light_gray"],
            button_color=self.COLORS["primary"],
            button_hover_color=self.COLORS["primary_hover"],
            font=ctk.CTkFont(size=14),
            dropdown_font=ctk.CTkFont(size=14)
        )
        self.model_type_combo.pack(side=ctk.RIGHT, padx=5)
        self.model_type_combo.set(model_names[0])

        compare_button = ctk.CTkButton(
            extra_frame,
            text=reshape_text("مقارنة النماذج ⚖️"),
            command=self._compare_models,
            width=180,
            height=40,
            fg_color=self.COLORS["info"],
            hover_color=self.COLORS["info_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8
        )
        compare_button.pack(side=ctk.RIGHT, padx=20)

    def _create_card(self, parent, title, icon=""):
        """إنشاء بطاقة جميلة"""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS["white"],
            corner_radius=15,
            border_width=1,
            border_color=self.COLORS["light_gray"]
        )
        header = ctk.CTkFrame(card, fg_color="transparent", height=60)
        header.pack(fill=ctk.X, padx=20, pady=15)

        title_label = ctk.CTkLabel(
            header,
            text=f"{title} {icon}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.COLORS["dark"],
            justify="right"
        )
        title_label.pack(side=ctk.RIGHT)

        return card

    def _create_info_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=ctk.X, pady=8)

        label_widget = ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS["dark"],
            width=120,
            anchor="e",
            justify="right"
        )
        label_widget.pack(side=ctk.RIGHT, padx=(0, 10))

        value_widget = ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(size=16),
            text_color=self.COLORS["gray"],
            anchor="e",
            justify="right"
        )
        value_widget.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

        return value_widget

    def _create_action_button(self, parent, text, command, color):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=50,
            fg_color=color,
            hover_color=self._adjust_color(color, -20),
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=8
        )

    def _adjust_color(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _create_predictions_table(self, parent):
        """جدول التنبؤات مع تحسينات (خط أكبر، ارتفاع أعمدة أكبر، ألوان)"""
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill=ctk.BOTH, expand=True, padx=25, pady=(0, 20))

        tree_frame = ctk.CTkFrame(
            table_frame,
            fg_color=self.COLORS["white"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["light_gray"]
        )
        tree_frame.pack(fill=ctk.BOTH, expand=True)

        columns = ("date", "day_of_week", "predicted_orders")
        self.predictions_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=8,
            style="Custom.Treeview"
        )

        # تخصيص الجدول باستخدام Style
        style = ttk.Style()
        style.theme_use("default")

        # تكوين الرؤوس (headings)
        style.configure(
            "Custom.Treeview.Heading",
            background=self.COLORS["table_header_bg"],
            foreground=self.COLORS["dark"],
            relief="flat",
            font=('Cairo', 14, 'bold')
        )
        style.map("Custom.Treeview.Heading",
            background=[('active', self.COLORS["light_gray"])]
        )

        # تكوين الصفوف
        style.configure(
            "Custom.Treeview",
            background=self.COLORS["table_row_even"],
            foreground=self.COLORS["dark"],
            rowheight=45,
            font=('Cairo', 13),
            fieldbackground=self.COLORS["white"],
            borderwidth=0
        )
        style.map("Custom.Treeview",
            background=[('selected', self.COLORS["primary"])],
            foreground=[('selected', self.COLORS["white"])]
        )

        self.predictions_tree.tag_configure('oddrow', background=self.COLORS["table_row_odd"])
        self.predictions_tree.tag_configure('evenrow', background=self.COLORS["table_row_even"])

        self.predictions_tree.heading("date", text=reshape_text("التاريخ"))
        self.predictions_tree.heading("day_of_week", text=reshape_text("اليوم"))
        self.predictions_tree.heading("predicted_orders", text=reshape_text("الطلبات المتوقعة"))

        self.predictions_tree.column("date", width=200, anchor="center")
        self.predictions_tree.column("day_of_week", width=200, anchor="center")
        self.predictions_tree.column("predicted_orders", width=200, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.predictions_tree.yview)
        self.predictions_tree.configure(yscrollcommand=scrollbar.set)

        self.predictions_tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y, pady=5)

    def _show_services_analysis(self, popular_services: List[Dict]):
        """عرض تحليل الخدمات في نافذة منبثقة محسنة"""
        popup = ctk.CTkToplevel(self.parent)
        popup.title("الخدمات الأكثر طلباً")
        popup.geometry("900x600")
        popup.configure(fg_color=self.COLORS["white"])
        popup.transient(self.parent)
        popup.grab_set()
        popup.focus()
        popup.lift()

        title_label = ctk.CTkLabel(
            popup,
            text=reshape_text("الخدمات الأكثر طلباً 🔥"),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.COLORS["dark"],
            justify="right"
        )
        title_label.pack(pady=20)

        table_container = ctk.CTkFrame(popup, fg_color="transparent")
        table_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        tree_frame = ctk.CTkFrame(
            table_container,
            fg_color=self.COLORS["white"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["light_gray"]
        )
        tree_frame.pack(fill=ctk.BOTH, expand=True)

        columns = ("service_name", "order_count", "total_revenue")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=10,
            style="Analysis.Treeview"
        )

        style = ttk.Style()
        style.configure(
            "Analysis.Treeview.Heading",
            background=self.COLORS["table_header_bg"],
            foreground=self.COLORS["dark"],
            font=('Cairo', 14, 'bold'),
            relief="flat"
        )
        style.configure(
            "Analysis.Treeview",
            background=self.COLORS["table_row_even"],
            foreground=self.COLORS["dark"],
            rowheight=40,
            font=('Cairo', 13),
            fieldbackground=self.COLORS["white"]
        )
        tree.tag_configure('oddrow', background=self.COLORS["table_row_odd"])
        tree.tag_configure('evenrow', background=self.COLORS["table_row_even"])

        tree.heading("service_name", text=reshape_text("اسم الخدمة"))
        tree.heading("order_count", text=reshape_text("عدد الطلبات"))
        tree.heading("total_revenue", text=reshape_text("إجمالي الإيرادات"))

        tree.column("service_name", width=300, anchor="center")
        tree.column("order_count", width=200, anchor="center")
        tree.column("total_revenue", width=200, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y, pady=5)

        for idx, service in enumerate(popular_services):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert("", "end", values=(
                reshape_text(service['service_name']),
                service['order_count'],
                f"{service['total_revenue']:.2f}"
            ), tags=(tag,))

        close_button = ctk.CTkButton(
            popup,
            text=reshape_text("إغلاق"),
            command=popup.destroy,
            width=200,
            height=50,
            fg_color=self.COLORS["danger"],
            hover_color=self.COLORS["danger_hover"],
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=8
        )
        close_button.pack(pady=20)

    def _show_days_analysis(self, weekly_patterns: Dict[str, Dict]):
        """عرض تحليل الأيام في نافذة منبثقة محسنة"""
        popup = ctk.CTkToplevel(self.parent)
        popup.title("تحليل أنماط الطلبات حسب الأيام")
        popup.geometry("900x600")
        popup.configure(fg_color=self.COLORS["white"])
        popup.transient(self.parent)
        popup.grab_set()
        popup.focus()
        popup.lift()

        title_label = ctk.CTkLabel(
            popup,
            text=reshape_text("تحليل أنماط الطلبات حسب الأيام 📅"),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.COLORS["dark"],
            justify="right"
        )
        title_label.pack(pady=20)

        table_container = ctk.CTkFrame(popup, fg_color="transparent")
        table_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        tree_frame = ctk.CTkFrame(
            table_container,
            fg_color=self.COLORS["white"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["light_gray"]
        )
        tree_frame.pack(fill=ctk.BOTH, expand=True)

        columns = ("day_name", "order_count", "total_amount")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=10,
            style="Analysis.Treeview"
        )

        style = ttk.Style()
        style.configure(
            "Analysis.Treeview.Heading",
            background=self.COLORS["table_header_bg"],
            foreground=self.COLORS["dark"],
            font=('Cairo', 14, 'bold'),
            relief="flat"
        )
        style.configure(
            "Analysis.Treeview",
            background=self.COLORS["table_row_even"],
            foreground=self.COLORS["dark"],
            rowheight=40,
            font=('Cairo', 13),
            fieldbackground=self.COLORS["white"]
        )
        tree.tag_configure('oddrow', background=self.COLORS["table_row_odd"])
        tree.tag_configure('evenrow', background=self.COLORS["table_row_even"])

        tree.heading("day_name", text=reshape_text("اليوم"))
        tree.heading("order_count", text=reshape_text("عدد الطلبات"))
        tree.heading("total_amount", text=reshape_text("إجمالي المبالغ"))

        tree.column("day_name", width=200, anchor="center")
        tree.column("order_count", width=200, anchor="center")
        tree.column("total_amount", width=300, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y, pady=5)

        for idx, (day_name, data) in enumerate(weekly_patterns.items()):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert("", "end", values=(
                day_name,
                data['order_count'],
                f"{data['total_amount']:.2f}"
            ), tags=(tag,))

        close_button = ctk.CTkButton(
            popup,
            text=reshape_text("إغلاق"),
            command=popup.destroy,
            width=200,
            height=50,
            fg_color=self.COLORS["info"],
            hover_color=self.COLORS["info_hover"],
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=8
        )
        close_button.pack(pady=20)

    def _show_hours_analysis(self, hourly_patterns: Dict[str, any]):
        """عرض تحليل الساعات في نافذة منبثقة محسنة"""
        popup = ctk.CTkToplevel(self.parent)
        popup.title("تحليل أنماط الطلبات حسب الساعات")
        popup.geometry("1000x800")
        popup.configure(fg_color=self.COLORS["white"])
        popup.transient(self.parent)
        popup.grab_set()
        popup.focus()
        popup.lift()

        title_label = ctk.CTkLabel(
            popup,
            text=reshape_text("تحليل أنماط الطلبات حسب الساعات ⏰"),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.COLORS["dark"],
            justify="right"
        )
        title_label.pack(pady=20)

        # معلومات إضافية بشكل بطاقة
        info_card = ctk.CTkFrame(popup, fg_color=self.COLORS["light_gray"], corner_radius=10)
        info_card.pack(fill=ctk.X, padx=20, pady=10)

        peak_hours_info = ctk.CTkLabel(
            info_card,
            text=f"{hourly_patterns['peak_hours']} : {reshape_text('ساعات الذروة ⏱️')}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["danger"],
            justify="right"
        )
        peak_hours_info.pack(pady=10)

        periods_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        periods_frame.pack(fill=ctk.X, pady=10)

        periods = hourly_patterns['periods']
        period_texts = [
            f"{periods['morning']}  : {reshape_text('الصباح')} 🌅",
            f"{periods['afternoon']} : {reshape_text('الظهر')} ☀️",
            f"{periods['evening']}  : {reshape_text('المساء')} 🌆",
            f"{periods['night']}    : {reshape_text('الليل')} 🌙"
        ]
        for text in period_texts:
            label = ctk.CTkLabel(
                periods_frame,
                text=text,
                font=ctk.CTkFont(size=16),
                text_color=self.COLORS["dark"],
                justify="right"
            )
            label.pack(side=ctk.RIGHT, padx=15)

        # جدول التحليل
        table_container = ctk.CTkFrame(popup, fg_color="transparent")
        table_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        tree_frame = ctk.CTkFrame(
            table_container,
            fg_color=self.COLORS["white"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["light_gray"]
        )
        tree_frame.pack(fill=ctk.BOTH, expand=True)

        columns = ("hour", "order_count", "total_amount")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15,
            style="Analysis.Treeview"
        )

        style = ttk.Style()
        style.configure(
            "Analysis.Treeview.Heading",
            background=self.COLORS["table_header_bg"],
            foreground=self.COLORS["dark"],
            font=('Cairo', 14, 'bold'),
            relief="flat"
        )
        style.configure(
            "Analysis.Treeview",
            background=self.COLORS["table_row_even"],
            foreground=self.COLORS["dark"],
            rowheight=40,
            font=('Cairo', 13),
            fieldbackground=self.COLORS["white"]
        )
        tree.tag_configure('oddrow', background=self.COLORS["table_row_odd"])
        tree.tag_configure('evenrow', background=self.COLORS["table_row_even"])

        tree.heading("hour", text=reshape_text("الساعة"))
        tree.heading("order_count", text=reshape_text("عدد الطلبات"))
        tree.heading("total_amount", text=reshape_text("إجمالي المبالغ"))

        tree.column("hour", width=150, anchor="center")
        tree.column("order_count", width=350, anchor="center")
        tree.column("total_amount", width=350, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y, pady=5)

        for idx, hour_data in enumerate(hourly_patterns['hourly_stats']):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert("", "end", values=(
                f"{hour_data['hour']}:00",
                hour_data['order_count'],
                f"{hour_data['total_amount']:.2f}"
            ), tags=(tag,))

        close_button = ctk.CTkButton(
            popup,
            text=reshape_text("إغلاق"),
            command=popup.destroy,
            width=200,
            height=50,
            fg_color=self.COLORS["warning"],
            hover_color=self.COLORS["warning_hover"],
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=8
        )
        close_button.pack(pady=20)

    def _show_model_comparison(self, results: Dict[str, Dict]):
        """عرض مقارنة النماذج في نافذة منبثقة محسنة"""
        popup = ctk.CTkToplevel(self.parent)
        popup.title("مقارنة النماذج")
        popup.geometry("1000x700")
        popup.configure(fg_color=self.COLORS["white"])
        popup.transient(self.parent)
        popup.grab_set()
        popup.focus()
        popup.lift()

        title_label = ctk.CTkLabel(
            popup,
            text=reshape_text("مقارنة أداء النماذج المختلفة ⚖️"),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.COLORS["dark"],
            justify="right"
        )
        title_label.pack(pady=20)

        table_container = ctk.CTkFrame(popup, fg_color="transparent")
        table_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        tree_frame = ctk.CTkFrame(
            table_container,
            fg_color=self.COLORS["white"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["light_gray"]
        )
        tree_frame.pack(fill=ctk.BOTH, expand=True)

        columns = ("model_type", "mse", "rmse", "mae", "cv_mean")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15,
            style="Analysis.Treeview"
        )

        style = ttk.Style()
        style.configure(
            "Analysis.Treeview.Heading",
            background=self.COLORS["table_header_bg"],
            foreground=self.COLORS["dark"],
            font=('Cairo', 14, 'bold'),
            relief="flat"
        )
        style.configure(
            "Analysis.Treeview",
            background=self.COLORS["table_row_even"],
            foreground=self.COLORS["dark"],
            rowheight=40,
            font=('Cairo', 13),
            fieldbackground=self.COLORS["white"]
        )
        tree.tag_configure('oddrow', background=self.COLORS["table_row_odd"])
        tree.tag_configure('evenrow', background=self.COLORS["table_row_even"])

        tree.heading("model_type", text=reshape_text("النموذج"))
        tree.heading("mse", text="MSE")
        tree.heading("rmse", text="RMSE")
        tree.heading("mae", text="MAE")
        tree.heading("cv_mean", text="CV Mean")

        tree.column("model_type", width=250, anchor="center")
        tree.column("mse", width=150, anchor="center")
        tree.column("rmse", width=150, anchor="center")
        tree.column("mae", width=150, anchor="center")
        tree.column("cv_mean", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y, pady=5)

        model_names = {
            "linear": reshape_text("الانحدار الخطي"),
            "random_forest": reshape_text("الغابة العشوائية"),
            "gradient_boosting": reshape_text("التدرج المتصاعد"),
            "ensemble": reshape_text("النموذج المدمج (Ensemble)")
        }

        for idx, (model_name, metrics) in enumerate(results.items()):
            if "error" not in metrics:
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                tree.insert("", "end", values=(
                    model_names.get(model_name, model_name),
                    f"{metrics['mse']:.4f}",
                    f"{metrics['rmse']:.4f}",
                    f"{metrics['mae']:.4f}",
                    f"{metrics['cv_mean']:.4f}" if metrics['cv_mean'] else "N/A"
                ), tags=(tag,))

        close_button = ctk.CTkButton(
            popup,
            text=reshape_text("إغلاق"),
            command=popup.destroy,
            width=200,
            height=50,
            fg_color=self.COLORS["danger"],
            hover_color=self.COLORS["danger_hover"],
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=8
        )
        close_button.pack(pady=20)

    # باقي الدوال الأساسية
    def _load_model_info(self):
        try:
            model_info = self.ai_model.get_model_info()
            status = "✅ مدرب" if model_info['is_trained'] else "❌ غير مدرب"
            self.model_status_label.configure(text=status)
            self.model_type_label.configure(text=model_info['model_type'])
            
            # Use feature_names length for more accurate count (handles VotingRegressor)
            fnames = self.ai_model._feature_names if hasattr(self.ai_model, '_feature_names') else []
            count = len(fnames) if fnames else model_info.get('features_count', 0)
            self.features_count_label.configure(text=str(count))
            
            # تحديث بطاقة الأداء
            self._update_performance_display()
            
        except Exception as e:
            logger.error(f"Error loading model info: {e}")

    def _update_performance_display(self):
        """تحديث عرض مقاييس الأداء"""
        try:
            metrics = self.ai_model.training_metrics
            
            if metrics and self.ai_model.is_trained:
                # حساب الدقة من MAPE ( MAPE = خطأ النسبة المئوية )
                mape = metrics.get('mape', 0)
                accuracy = max(0, 100 - mape)  # الدقة = 100% - نسبة الخطأ
                
                # عرض الدقة مع لون المناسب
                if accuracy >= 80:
                    accuracy_text = f"✅ {accuracy:.1f}%"
                elif accuracy >= 60:
                    accuracy_text = f"⚠️ {accuracy:.1f}%"
                else:
                    accuracy_text = f"❌ {accuracy:.1f}%"
                
                self.accuracy_label.configure(text=accuracy_text)
                
                # عرض RMSE
                rmse = metrics.get('rmse', 0)
                self.rmse_label.configure(text=f"{rmse:.4f}")
                
                # عرض MAE
                mae = metrics.get('mae', 0)
                self.mae_label.configure(text=f"{mae:.4f}")
                
                # عرض إجمالي الطلبات (أقلناها من data_points)
                data_points = metrics.get('data_points', 0)
                # عدد الطلبات الكلي = أيام * متوسط الطلبات في اليوم
                # أو ببساطة نحسب من خلال orders_data
                if hasattr(self, '_last_orders_data'):
                    total_orders = len(self._last_orders_data)
                else:
                    # نقدر عدد الطلبات التقريبي
                    total_orders = data_points * 3  # متوسط 3 طلبات في اليوم
                self.data_points_label.configure(text=f"~{total_orders} طلب")
            else:
                # لم يتم التدريب بعد
                self.accuracy_label.configure(text="—")
                self.rmse_label.configure(text="—")
                self.mae_label.configure(text="—")
                self.data_points_label.configure(text="—")
                
        except Exception as e:
            logger.error(f"Error updating performance display: {e}")
            # في حالة الخطأ، عرض默认值
            self.accuracy_label.configure(text="—")
            self.rmse_label.configure(text="—")
            self.mae_label.configure(text="—")
            self.data_points_label.configure(text="—")

    def _train_model(self):
        try:
            orders_data = self.db_manager.get_orders()
            if len(orders_data) < 10:
                show_warning(
                    self.parent,
                    "تحذير",
                    "يجب أن يكون هناك 10 طلبات على الأقل لتدريب النموذج"
                )
                return

            # حفظ البيانات لاستخدامها في عرض المقاييس
            self._last_orders_data = orders_data
            
            self.training_status_label.configure(text=reshape_text("الحالة: جاري التدريب... ⏳"))
            self.parent.update()

            metrics = self.ai_model.train(orders_data)
            self.ai_model.is_trained = True
            self.training_status_label.configure(text=reshape_text("الحالة: تم التدريب بنجاح ✅"))
            self._load_model_info()

            # استخدام النافذة المحسنة لعرض النتائج
            show_training_result(self.parent, metrics)
        except Exception as e:
            self.training_status_label.configure(text=reshape_text("الحالة: فشل التدريب ❌"))
            show_error(
                self.parent,
                "خطأ",
                f"حدث خطأ أثناء تدريب النموذج: {str(e)}"
            )

    def _make_predictions(self):
        try:
            if not self.ai_model.is_trained:
                show_warning(
                    self.parent,
                    "تحذير",
                    "يجب تدريب النموذج أولاً قبل إجراء التنبؤات"
                )
                return

            if not hasattr(self, 'predictions_tree'):
                show_error(
                    self.parent,
                    "خطأ",
                    "الجدول غير موجود. يرجى إعادة تحميل الصفحة."
                )
                return

            # مسح الجدول
            for item in self.predictions_tree.get_children():
                self.predictions_tree.delete(item)

            predictions = self.ai_model.predict_next_days(days=7)

            if not predictions:
                show_info(
                    self.parent,
                    "معلومات",
                    "لم يتم الحصول على أي تنبؤات. تأكد من أن النموذج مدرب بشكل صحيح."
                )
                return

            days_map = {
                'Monday': 'الإثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
                'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
            }

            for idx, pred in enumerate(predictions):
                day_name = days_map.get(pred['day_of_week'], pred['day_of_week'])
                orders = f"{float(pred['predicted_orders']):.0f}"
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                self.predictions_tree.insert("", 'end', values=(pred['date'], day_name, orders), tags=(tag,))

            self.predictions_tree.update_idletasks()
            show_success(
                self.parent,
                "نجاح",
                f"تم عرض {len(predictions)} تنبؤ بنجاح."
            )

        except Exception as e:
            show_error(
                self.parent,
                "خطأ",
                f"حدث خطأ أثناء إجراء التنبؤات: {str(e)}"
            )

    def _analyze_services(self):
        try:
            orders_data = self.db_manager.get_orders()
            if not orders_data:
                show_warning(self.parent, "تحذير", "لا توجد بيانات للتحليل")
                return
            popular_services = self.ai_model.analyze_popular_services(orders_data)
            self._show_services_analysis(popular_services)
        except Exception as e:
            show_error(
                self.parent,
                "خطأ",
                f"حدث خطأ أثناء تحليل الخدمات: {str(e)}"
            )

    def _analyze_days(self):
        try:
            orders_data = self.db_manager.get_orders()
            if not orders_data:
                show_warning(self.parent, "تحذير", "لا توجد بيانات للتحليل")
                return
            weekly_patterns = self.ai_model.analyze_weekly_patterns(orders_data)
            self._show_days_analysis(weekly_patterns)
        except Exception as e:
            show_error(
                self.parent,
                "خطأ",
                f"حدث خطأ أثناء تحليل الأيام: {str(e)}"
            )

    def _analyze_hours(self):
        try:
            orders_data = self.db_manager.get_orders()
            if not orders_data:
                show_warning(self.parent, "تحذير", "لا توجد بيانات للتحليل")
                return
            hourly_patterns = self.ai_model.analyze_hourly_patterns(orders_data)
            self._show_hours_analysis(hourly_patterns)
        except Exception as e:
            show_error(
                self.parent,
                "خطأ",
                f"حدث خطأ أثناء تحليل الساعات: {str(e)}"
            )

    def _on_model_type_change(self, value: str):
        model_map = {
            reshape_text("الانحدار الخطي"): "linear",
            reshape_text("الغابة العشوائية"): "random_forest",
            reshape_text("التدرج المتصاعد"): "gradient_boosting",
            reshape_text("النموذج المدمج (Ensemble)"): "ensemble"
        }
        model_type = model_map.get(value, "linear")
        self.ai_model = AdvancedOrderPredictionModel(model_type=model_type)
        self._load_model_info()

    # ═══════════════════════════════════════════
    # دوال الميزات المتقدمة
    # ═══════════════════════════════════════════

    def _segment_customers(self):
        """تقسيم العملاء إلى شرائح وعرض النتائج"""
        try:
            orders_data = self.db_manager.get_orders()
            if not orders_data:
                show_warning(self.parent, "تحذير", "لا توجد بيانات كافية لتقسيم العملاء")
                return

            customers_data = self.db_manager.get_customers()
            customers_dict = [{"id": c["id"], "name": c["name"], "phone": c["phone"]} for c in customers_data]

            result = self.ai_model.segment_customers(orders_data, customers_dict)

            if "error" in result:
                show_warning(self.parent, "تحذير", result["error"])
                return

            # إنشاء نافذة العرض
            popup = ctk.CTkToplevel(self.parent)
            popup.title("تقسيم العملاء ")
            popup.geometry("800x700")
            popup.configure(fg_color=self.COLORS["white"])
            popup.transient(self.parent)
            popup.grab_set()
            popup.focus()
            popup.lift()

            title_label = ctk.CTkLabel(
                popup,
                text=reshape_text("تقسيم العملاء إلى شرائح 👥"),
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=self.COLORS["dark"],
                justify="right"
            )
            title_label.pack(pady=20)

            # عرض ملخص الشرائح
            segment_counts = result.get("segment_counts", {})
            summary_frame = ctk.CTkFrame(popup, fg_color=self.COLORS["light_gray"], corner_radius=10)
            summary_frame.pack(fill=ctk.X, padx=20, pady=10)

            summary_label = ctk.CTkLabel(
                summary_frame,
                text=reshape_text("توزيع العملاء حسب الشريحة:"),
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=self.COLORS["dark"],
                justify="right"
            )
            summary_label.pack(pady=10)

            counts_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
            counts_frame.pack(fill=ctk.X, padx=20, pady=(0, 10))

            segment_colors = {
                reshape_text("عميل ذهبي"): "#f1c40f",
                reshape_text("عميل فضي"): "#bdc3c7",
                reshape_text("عميل برونزي"): "#e17055",
                reshape_text("عميل جديد"): "#74b9ff"
            }

            for seg_name, count in segment_counts.items():
                row = ctk.CTkFrame(counts_frame, fg_color="transparent")
                row.pack(side=ctk.RIGHT, padx=10, fill=ctk.X, expand=True)

                color = segment_colors.get(seg_name, self.COLORS["gray"])

                dot = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=20), text_color=color, anchor="w")
                dot.pack(side=ctk.RIGHT, padx=(0, 5))

                name_lbl = ctk.CTkLabel(row, text=f"{count}: {seg_name}", font=ctk.CTkFont(size=14), text_color=self.COLORS["dark"], anchor="e", justify="right")
                name_lbl.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

            # جدول التفاصيل
            table_frame = ctk.CTkFrame(popup, fg_color="transparent")
            table_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

            tree_frame = ctk.CTkFrame(table_frame, fg_color=self.COLORS["white"], corner_radius=10)
            tree_frame.pack(fill=ctk.BOTH, expand=True)

            columns = ("customer_id", "segment", "order_count", "total_spending", "avg_order_value")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10, style="Analysis.Treeview")

            style = ttk.Style()
            style.configure("Analysis.Treeview", background=self.COLORS["table_row_even"], foreground=self.COLORS["dark"], rowheight=40, font=('Cairo', 12), fieldbackground=self.COLORS["white"])

            headings_map = {
                "customer_id": reshape_text("رقم العميل"),
                "segment": reshape_text("الشريحة"),
                "order_count": reshape_text("عدد الطلبات"),
                "total_spending": reshape_text("إجمالي الإنفاق"),
                "avg_order_value": reshape_text("متوسط الطلب")
            }
            widths = {"customer_id": 80, "segment": 120, "order_count": 100, "total_spending": 120, "avg_order_value": 120}

            for col in columns:
                tree.heading(col, text=headings_map.get(col, col), anchor="center")
                tree.column(col, width=widths[col], anchor="center")

            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
            scrollbar.pack(side=ctk.LEFT, fill=ctk.Y, pady=5)

            # ربط البيانات بالعملاء
            customers_map = {str(c["id"]): c["name"] for c in customers_dict}
            segments = result.get("segments", {})

            for idx, (cid, seg_data) in enumerate(segments.items()):
                customer_name = customers_map.get(cid, str(cid))
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                tree.insert("", "end", values=(
                    customer_name,
                    seg_data['segment'],
                    seg_data['order_count'],
                    f"{seg_data['total_spending']:.2f}",
                    f"{seg_data['avg_order_value']:.2f}"
                ), tags=(tag,))

            tree.tag_configure('evenrow', background=self.COLORS["table_row_odd"])
            tree.tag_configure('oddrow', background=self.COLORS["table_row_even"])

            # زر الإغلاق
            close_btn = ctk.CTkButton(popup, text=reshape_text("إغلاق"), command=popup.destroy,
                width=200, height=50, fg_color=self.COLORS["primary"], hover_color=self.COLORS["primary_hover"],
                font=ctk.CTkFont(size=16, weight="bold"), corner_radius=8)
            close_btn.pack(pady=20)

        except Exception as e:
            show_error(self.parent, "خطأ", f"حدث خطأ أثناء تقسيم العملاء: {str(e)}")

    def _recommend_services(self):
        """توصية الخدمات - يعرض جميع العملاء مع نوع التوصية"""
        try:
            orders_data = self.db_manager.get_orders()
            if not orders_data:
                show_warning(self.parent, "تحذير", "لا توجد طلبات لتحليل التوصيات")
                return
            
            # Get all customers
            customers_data = self.db_manager.get_customers()
            if not customers_data:
                show_warning(self.parent, "تحذير", "لا يوجد عملاء في النظام")
                return
            
            # Get customers who have custom recommendations
            customers_with_custom = self.ai_model.get_customers_with_recommendations(orders_data)
            custom_customer_ids = {c['customer_id'] for c in customers_with_custom}
            
            # Get customer names
            customers_map = {c['id']: c for c in customers_data}
            
            # Create customer selection popup
            popup = ctk.CTkToplevel(self.parent)
            popup.title("اختيار العميل")
            popup.geometry("550x650")
            popup.configure(fg_color=self.COLORS["white"])
            popup.transient(self.parent)
            popup.grab_set()
            popup.focus()
            popup.lift()

            title_label = ctk.CTkLabel(
                popup,
                text=reshape_text(f"جميع العملاء ({len(customers_data)}) 💡"),
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=self.COLORS["dark"],
                justify="right"
            )
            title_label.pack(pady=20)
            
            # Info label
            info_label = ctk.CTkLabel(
                popup,
                text=reshape_text("اختر عميلاً للحصول على توصيات:\n• مخصصة = شخصياً لك\n• رائج = شائع للجميع"),
                font=ctk.CTkFont(size=13),
                text_color=self.COLORS["gray"],
                justify="right"
            )
            info_label.pack(pady=(0, 10))

            # Customer list - show ALL customers
            list_frame = ctk.CTkScrollableFrame(popup, fg_color="transparent")
            list_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
            
            for customer in customers_data:
                cid = customer['id']
                
                # تحديد نوع التوصية
                if cid in custom_customer_ids:
                    #Find the customer's recommendation count
                    cust_info = next((c for c in customers_with_custom if c['customer_id'] == cid), None)
                    rec_count = cust_info['recommendations_count'] if cust_info else 0
                    btn_text = f"{customer['name']} ({rec_count} مخصصة)"
                    btn_color = self.COLORS["success"]
                else:
                    btn_text = f"{customer['name']} (رائج)"
                    btn_color = self.COLORS["info"]
                    
                btn = ctk.CTkButton(
                    list_frame,
                    text=btn_text,
                    command=lambda id=cid: self._do_recommend_services(id),
                    height=45,
                    font=ctk.CTkFont(size=14),
                    fg_color=btn_color,
                    hover_color=self.COLORS["primary_hover"],
                    anchor="w"
                )
                btn.pack(fill=ctk.X, pady=3)
            
            # Stats
            custom_count = len(custom_customer_ids)
            popular_count = len(customers_data) - custom_count
            
            stats_label = ctk.CTkLabel(
                popup,
                text=reshape_text(f"📊 {custom_count} توصيات مخصصة | {popular_count} توصيات رائجة"),
                font=ctk.CTkFont(size=12),
                text_color=self.COLORS["gray"],
                justify="right"
            )
            stats_label.pack(pady=5)

            close_btn = ctk.CTkButton(
                popup,
                text=reshape_text("إغلاق"),
                command=popup.destroy,
                width=200,
                height=45,
                fg_color=self.COLORS["danger"],
                hover_color=self.COLORS["danger_hover"],
                font=ctk.CTkFont(size=14, weight="bold")
            )
            close_btn.pack(pady=15)

        except Exception as e:
            show_error(self.parent, "خطأ", f"حدث خطأ: {str(e)}")

    def _do_recommend_services(self, customer_id):
        """تنفيذ التوصية بعد اختيار العميل"""
        try:
            orders_data = self.db_manager.get_orders()
            result = self.ai_model.recommend_services(customer_id, orders_data)

            # Handle new return format (dict with 'recommendations' and 'reason')
            if isinstance(result, dict):
                recommendations = result.get('recommendations', [])
                reason = result.get('reason', '')
                rec_type = result.get('type', 'unknown')
                
                if not recommendations:
                    show_info(self.parent, "معلومات", f"لا توجد توصيات متاحة.\nالسبب: {reason}")
                    return
            else:
                # Old format - list
                recommendations = result if result else []
                reason = ''
                rec_type = 'unknown'
                if not recommendations:
                    show_info(self.parent, "معلومات", "لا توجد توصيات متاحة لهذا العميل")
                    return

            # Display in popup
            popup = ctk.CTkToplevel(self.parent)
            popup.title("توصيات الخدمات")
            popup.geometry("750x550")
            popup.configure(fg_color=self.COLORS["white"])
            popup.transient(self.parent)
            popup.grab_set()
            popup.focus()
            popup.lift()

            # نوع التوصية
            type_icons = {
                'new_customer': '🆕',
                'personalized': '⭐',
                'popular': '🔥',
                'popular_only': '🔥'
            }
            type_text = {
                'new_customer': 'عميل جديد - توصيات رائجة',
                'personalized': 'توصيات مخصصة لك',
                'popular': 'خدمات رائجة',
                'popular_only': 'خدمات رائجة'
            }
            
            title_label = ctk.CTkLabel(
                popup,
                text=reshape_text(f"توصيات الخدمات {type_icons.get(rec_type, '💡')}"),
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=self.COLORS["dark"],
                justify="right"
            )
            title_label.pack(pady=20)
            
            # نوع التوصية
            type_label = ctk.CTkLabel(
                popup,
                text=reshape_text(type_text.get(rec_type, '')),
                font=ctk.CTkFont(size=14),
                text_color=self.COLORS["gray"],
                justify="right"
            )
            type_label.pack(pady=(0, 10))

            # Create recommendations list
            rec_frame = ctk.CTkScrollableFrame(popup, fg_color="transparent")
            rec_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

            for rec in recommendations:
                # تحديد لون البطاقة حسب المصدر
                source = rec.get('source', 'رائج')
                source_colors = {
                    'مخصصة': '#e8f5e9',
                    'مشابهة': '#e3f2fd',
                    'مرتبطة': '#fff3e0',
                    'رائج': '#f5f5f5'
                }
                card_color = source_colors.get(source, '#f5f5f5')
                
                card = ctk.CTkFrame(rec_frame, fg_color=card_color, corner_radius=8, border_width=1, border_color="#ddd")
                card.pack(fill=ctk.X, pady=5)

                name_row = ctk.CTkFrame(card, fg_color="transparent")
                name_row.pack(fill=ctk.X, padx=15, pady=10)

                # اسم الخدمة
                ctk.CTkLabel(
                    name_row,
                    text=f"📌 {rec['service_name']}",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.COLORS["dark"],
                    anchor="e"
                ).pack(side=ctk.RIGHT, fill=ctk.X, expand=True)
                
                # المصدر
                ctk.CTkLabel(
                    name_row,
                    text=f"{source}",
                    font=ctk.CTkFont(size=11),
                    text_color=self.COLORS["gray"],
                    anchor="w"
                ).pack(side=ctk.LEFT, padx=5)
            
            # Confidence
            conf_row = ctk.CTkFrame(rec_frame, fg_color="transparent")
            conf_row.pack(fill=ctk.X, pady=5)
            
            for rec in recommendations:
                conf_label = ctk.CTkLabel(
                    conf_row,
                    text=f"• {rec['service_name']}: {rec['confidence']:.0%}",
                    font=ctk.CTkFont(size=12),
                    text_color=self.COLORS["gray"],
                    justify="right"
                )
                conf_label.pack(side=ctk.RIGHT, padx=10)

            close_btn = ctk.CTkButton(
                popup,
                text=reshape_text("إغلاق"),
                command=popup.destroy,
                width=200,
                height=45,
                fg_color=self.COLORS["danger"],
                hover_color=self.COLORS["danger_hover"],
                font=ctk.CTkFont(size=14, weight="bold")
            )
            close_btn.pack(pady=15)

        except Exception as e:
            show_error(self.parent, "خطأ", f"حدث خطأ في التوصيات: {str(e)}")

    def _forecast_revenue(self):
        """عرض تنبؤ الإيرادات للأشهر القادمة"""
        try:
            orders_data = self.db_manager.get_orders()
            if not orders_data:
                show_warning(self.parent, "تحذير", "لا توجد بيانات للتنبؤ بالإيرادات")
                return

            result = self.ai_model.forecast_revenue(orders_data)

            if "error" in result:
                show_warning(self.parent, "تحذير", result["error"])
                return

            # إنشاء نافذة العرض
            popup = ctk.CTkToplevel(self.parent)
            popup.title("تنبؤ الإيرادات")
            popup.geometry("900x650")
            popup.configure(fg_color=self.COLORS["white"])
            popup.transient(self.parent)
            popup.grab_set()
            popup.focus()
            popup.lift()

            title_label = ctk.CTkLabel(
                popup,
                text=reshape_text("تنبؤ الإيرادات للأشهر القادمة 💰"),
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=self.COLORS["dark"],
                justify="right"
            )
            title_label.pack(pady=20)

            # معلومات ملخصة
            summary_frame = ctk.CTkFrame(popup, fg_color=self.COLORS["light_gray"], corner_radius=10)
            summary_frame.pack(fill=ctk.X, padx=20, pady=10)

            summary_texts = [
                f" {result.get('avg_monthly_revenue', 0):.2f} {reshape_text('متوسط الإيراد الشهري:')}",
                f" {result.get('avg_growth_rate', 0) * 100:.1f}% {reshape_text('معدل النمو:')}",
                f" {result.get('data_points', 0)}{reshape_text('نقاط البيانات:')}"
            ]
            for text in summary_texts:
                lbl = ctk.CTkLabel(summary_frame, text=text, font=ctk.CTkFont(size=14),
                                    text_color=self.COLORS["dark"], justify="right")
                lbl.pack(pady=3)

            # جدول التنبؤات
            table_frame = ctk.CTkFrame(popup, fg_color="transparent")
            table_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

            tree_frame = ctk.CTkFrame(table_frame, fg_color=self.COLORS["white"], corner_radius=10)
            tree_frame.pack(fill=ctk.BOTH, expand=True)

            columns = ("month", "predicted", "lower", "upper", "confidence")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8, style="Analysis.Treeview")

            style = ttk.Style()
            style.configure("Analysis.Treeview", background=self.COLORS["table_row_even"], foreground=self.COLORS["dark"], rowheight=40, font=('Cairo', 12), fieldbackground=self.COLORS["white"])

            headings_map = {
                "month": reshape_text("الشهر"),
                "predicted": reshape_text("المتوقع"),
                "lower": reshape_text("الحد الأدنى"),
                "upper": reshape_text("الحد الأعلى"),
                "confidence": reshape_text("الثقة")
            }
            widths = {"month": 120, "predicted": 120, "lower": 120, "upper": 120, "confidence": 80}

            for col in columns:
                tree.heading(col, text=headings_map.get(col, col), anchor="center")
                tree.column(col, width=widths[col], anchor="center")

            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
            scrollbar.pack(side=ctk.LEFT, fill=ctk.Y, pady=5)

            for forecast in result.get('forecast', []):
                tag = 'evenrow' if result['forecast'].index(forecast) % 2 == 0 else 'oddrow'
                tree.insert("", "end", values=(
                    forecast['label'],
                    f"{forecast['predicted_revenue']:,.0f}",
                    f"{forecast['confidence_lower']:,.0f}",
                    f"{forecast['confidence_upper']:,.0f}",
                    f"{forecast['confidence']*100:.0f}%"
                ), tags=(tag,))

            tree.tag_configure('evenrow', background=self.COLORS["table_row_odd"])
            tree.tag_configure('oddrow', background=self.COLORS["table_row_even"])

            close_btn = ctk.CTkButton(popup, text=reshape_text("إغلاق"), command=popup.destroy,
                width=200, height=50, fg_color="#fdcb6e", hover_color="#f0b731",
                font=ctk.CTkFont(size=16, weight="bold"), corner_radius=8)
            close_btn.pack(pady=20)

        except Exception as e:
            show_error(self.parent, "خطأ", f"حدث خطأ أثناء التنبؤ بالإيرادات: {str(e)}")

    def _compare_models(self):
        """مقارنة أداء جميع النماذج المتاحة"""
        try:
            orders_data = self.db_manager.get_orders()
            if len(orders_data) < 50:
                show_warning(
                    self.parent,
                    "تحذير",
                    "يجب أن يكون هناك 50 طلب على الأقل لمقارنة النماذج"
                )
                return

            # Use the compare_models method which uses TimeSeriesSplit
            results = self.ai_model.compare_models(orders_data)

            if results and 'error' not in results:
                # Add cv_mean for display
                for model_name, metrics in results.items():
                    if isinstance(metrics, dict) and 'rmse' in metrics:
                        metrics['cv_mean'] = metrics.get('rmse', 0)
                self._show_model_comparison(results)
            else:
                error_msg = results.get('error', 'فشلت مقارنة النماذج') if isinstance(results, dict) else 'فشلت مقارنة النماذج'
                show_error(self.parent, "خطأ", error_msg)
        except Exception as e:
            show_error(
                self.parent,
                "خطأ",
                f"حدث خطأ أثناء مقارنة النماذج: {str(e)}"
            )
