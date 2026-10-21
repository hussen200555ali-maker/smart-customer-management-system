# -*- coding: utf-8 -*-
"""
utils/dialogs.py
---------------
نوافذ إشعارات مخصصة ومحسنة بتصميم حديث وجذاب مع دعم العربية.
الإصدار: 3.0 (تحسين جميع الإشعارات عدا تدريب النموذج)
"""

import customtkinter as ctk
from typing import Optional
import numpy as np

def reshape_text(text: str) -> str:
    """إعادة تشكيل النص العربي لعرضه بشكل صحيح"""
    if not text:
        return ""
    try:
        from bidi.algorithm import get_display
        import arabic_reshaper
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

# ألوان Dark Theme الاحترافية
PRO_COLORS = {
    "primary": "#3b82f6",
    "success": "#10b981",
    "success_dark": "#059669",
    "warning": "#f59e0b",
    "warning_dark": "#d97706",
    "danger": "#ef4444",
    "danger_dark": "#dc2626",
    "info": "#06b6d4",
    "bg_card": "#1e293b",
    "bg_dark": "#0f172a",
    "text_white": "#f8fafc",
    "text_gray": "#94a3b8",
    "border": "#334155",
}

class BaseDialog:
    """نافذة حوار أساسية محسنة"""
    def __init__(self, parent: Optional[ctk.CTk], title: str, width: int = 500, height: int = 300):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.configure(fg_color=PRO_COLORS["bg_dark"])
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        # توسيط النافذة
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)

    def _create_header(self, icon: str, icon_color: str, title: str):
        """إنشاء رأس النافذة بالأيقونة والعنوان"""
        header = ctk.CTkFrame(self.dialog, fg_color="transparent")
        header.pack(fill=ctk.X, padx=25, pady=(25, 15))
        
        icon_label = ctk.CTkLabel(header, text=icon, font=ctk.CTkFont(size=36))
        icon_label.pack(side="right", padx=(15, 0))
        
        title_label = ctk.CTkLabel(
            header, text=reshape_text(title), font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PRO_COLORS["text_white"], anchor="e"
        )
        title_label.pack(side="right", fill=ctk.X, expand=True)
        
        sep = ctk.CTkFrame(self.dialog, height=1, fg_color=PRO_COLORS["border"])
        sep.pack(fill=ctk.X, padx=25, pady=(0, 15))

    def _create_message(self, message: str):
        """إنشاء منطقة الرسالة"""
        container = ctk.CTkFrame(self.dialog, fg_color=PRO_COLORS["bg_card"], corner_radius=12)
        container.pack(fill=ctk.X, padx=25, pady=(0, 20))
        msg_label = ctk.CTkLabel(
            container, text=reshape_text(message), font=ctk.CTkFont(size=15),
            text_color=PRO_COLORS["text_gray"], wraplength=400, justify="right", anchor="e"
        )
        msg_label.pack(padx=20, pady=20)

    def _create_button(self, text: str, command, color: str, hover_color: str):
        """زر موحد"""
        btn = ctk.CTkButton(
            self.dialog, text=reshape_text(text), command=command,
            width=180, height=42, corner_radius=10, fg_color=color,
            hover_color=hover_color, font=ctk.CTkFont(size=15, weight="bold"),
            text_color=PRO_COLORS["text_white"]
        )
        btn.pack(pady=(0, 20))
        return btn

    def _close(self):
        self.dialog.destroy()


class InfoDialog(BaseDialog):
    def __init__(self, parent, title="معلومات", message=""):
        super().__init__(parent, title, 500, 300)
        self._create_header("ℹ️", PRO_COLORS["info"], title)
        self._create_message(message)
        self._create_button("موافق", self._close, PRO_COLORS["primary"], "#2563eb")
        self.dialog.wait_window()


class SuccessDialog(BaseDialog):
    def __init__(self, parent, title="نجاح", message=""):
        super().__init__(parent, title, 500, 300)
        self._create_header("✓", PRO_COLORS["success"], title)
        self._create_message(message)
        self._create_button("موافق", self._close, PRO_COLORS["success"], PRO_COLORS["success_dark"])
        self.dialog.wait_window()


class WarningDialog(BaseDialog):
    def __init__(self, parent, title="تحذير", message=""):
        super().__init__(parent, title, 500, 300)
        self._create_header("⚠️", PRO_COLORS["warning"], title)
        self._create_message(message)
        self._create_button("موافق", self._close, PRO_COLORS["warning"], PRO_COLORS["warning_dark"])
        self.dialog.wait_window()


class ErrorDialog(BaseDialog):
    def __init__(self, parent, title="خطأ", message=""):
        super().__init__(parent, title, 500, 300)
        self._create_header("✕", PRO_COLORS["danger"], title)
        self._create_message(message)
        self._create_button("موافق", self._close, PRO_COLORS["danger"], PRO_COLORS["danger_dark"])
        self.dialog.wait_window()


class ConfirmDialog(BaseDialog):
    def __init__(self, parent, title="تأكيد", message=""):
        super().__init__(parent, title, 500, 320)
        self.result = False
        self._create_header("❓", PRO_COLORS["primary"], title)
        self._create_message(message)
        # أزرار نعم/لا
        btn_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))
        no_btn = ctk.CTkButton(
            btn_frame, text=reshape_text("لا"), command=self._on_no,
            width=120, height=42, corner_radius=8, fg_color="#6B6B6B", hover_color="#4A4A4A"
        )
        no_btn.pack(side="right", padx=(10, 0))
        yes_btn = ctk.CTkButton(
            btn_frame, text=reshape_text("نعم"), command=self._on_yes,
            width=120, height=42, corner_radius=8, fg_color=PRO_COLORS["primary"], hover_color="#2563eb"
        )
        yes_btn.pack(side="right")
        self.dialog.wait_window()

    def _on_yes(self):
        self.result = True
        self.dialog.destroy()

    def _on_no(self):
        self.result = False
        self.dialog.destroy()


# دوال مساعدة للاستخدام السريع
def show_info(parent: Optional[ctk.CTk] = None, title: str = "معلومات", message: str = ""):
    InfoDialog(parent, title, message)

def show_success(parent: Optional[ctk.CTk] = None, title: str = "نجاح", message: str = ""):
    SuccessDialog(parent, title, message)

def show_warning(parent: Optional[ctk.CTk] = None, title: str = "تحذير", message: str = ""):
    WarningDialog(parent, title, message)

def show_error(parent: Optional[ctk.CTk] = None, title: str = "خطأ", message: str = ""):
    ErrorDialog(parent, title, message)

def ask_yes_no(parent: Optional[ctk.CTk] = None, title: str = "تأكيد", message: str = "") -> bool:
    return ConfirmDialog(parent, title, message).result


# دوال للتوافق مع messagebox القديم (اختياري)
def showinfo(title: str, message: str, parent: Optional[ctk.CTk] = None):
    InfoDialog(parent, title, message)

def showwarning(title: str, message: str, parent: Optional[ctk.CTk] = None):
    WarningDialog(parent, title, message)

def showerror(title: str, message: str, parent: Optional[ctk.CTk] = None):
    ErrorDialog(parent, title, message)

def askyesno(title: str, message: str, parent: Optional[ctk.CTk] = None) -> bool:
    return ask_yes_no(parent, title, message)


# ==================== نافذة نتائج تدريب النموذج (لم يتم تعديلها) ====================
class TrainingResultDialog(BaseDialog):
    """نافذة نتائج تدريب الذكاء الاصطناعي المحسنة الاحترافية (بدون تغيير)"""
    
    COLORS = {
        "primary": "#4361ee",
        "success": "#10b981",
        "success_dark": "#059669",
        "bg_card": "#1e293b",
        "bg_dark": "#0f172a",
        "text_white": "#f8fafc",
        "text_gray": "#94a3b8",
        "border": "#334155",
        "accent": "#3b82f6"
    }
    
    def __init__(self, parent: Optional[ctk.CTk] = None, title: str = "نتائج التدريب", metrics: dict = None):
        super().__init__(parent, title, 650, 550)
        self.dialog.geometry("650x550")
        self.dialog.configure(fg_color=self.COLORS["bg_dark"])
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (550 // 2)
        self.dialog.geometry(f"650x550+{x}+{y}")
        
        self._create_header_training()
        self._create_success_bar()
        self._create_metrics_cards(metrics)
        self._create_close_button()
        self.dialog.wait_window()
    
    def _create_header_training(self):
        header = ctk.CTkFrame(self.dialog, fg_color="transparent")
        header.pack(fill=ctk.X, padx=25, pady=(25, 15))
        icon = ctk.CTkLabel(header, text="✓", font=ctk.CTkFont(size=50, weight="bold"), text_color=self.COLORS["success"])
        icon.pack(side="right", padx=(15, 0))
        text_frame = ctk.CTkFrame(header, fg_color="transparent")
        text_frame.pack(side="right", fill=ctk.BOTH, expand=True)
        title_label = ctk.CTkLabel(text_frame, text=reshape_text("تم تدريب النموذج بنجاح! 🎉"),
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.COLORS["text_white"], anchor="e")
        title_label.pack(anchor="e", pady=(0, 5))
        subtitle_label = ctk.CTkLabel(text_frame, text=reshape_text("Model training completed successfully"),
            font=ctk.CTkFont(size=14), text_color=self.COLORS["text_gray"], anchor="e")
        subtitle_label.pack(anchor="e")
    
    def _create_success_bar(self):
        bar_container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        bar_container.pack(fill=ctk.X, padx=25, pady=(0, 20))
        bar_bg = ctk.CTkFrame(bar_container, fg_color=self.COLORS["bg_card"], height=8, corner_radius=4)
        bar_bg.pack(fill=ctk.X)
        bar_fill = ctk.CTkFrame(bar_bg, fg_color=self.COLORS["success"], height=8, corner_radius=4)
        bar_fill.pack(side="right", fill=ctk.X, expand=True, padx=2, ipady=2)
    
    def _create_metrics_cards(self, metrics):
        if not metrics:
            return
        cards_scroll = ctk.CTkScrollableFrame(self.dialog, fg_color="transparent",
            scrollbar_button_color=self.COLORS["primary"], scrollbar_button_hover_color=self.COLORS["accent"])
        cards_scroll.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        metrics_config = [
            {"key": "mse", "label": "متوسط الخطأ التربيعي", "short": "MSE", "icon": "📊", "desc": "Mean Squared Error - كلما كان أقل كان أفضل", "color": "#ef4444"},
            {"key": "rmse", "label": "جذر متوسط الخطأ", "short": "RMSE", "icon": "📈", "desc": "Root MSE - قياس الانحراف الفعلي", "color": "#f97316"},
            {"key": "mae", "label": "متوسط الخطأ المطلق", "short": "MAE", "icon": "📉", "desc": "Mean Absolute Error - متوسط الفرق", "color": "#eab308"},
            {"key": "cv_scores", "label": "درجة التحقق", "short": "CV", "icon": "🎯", "desc": "Cross-validation score", "color": "#22c55e"},
            {"key": "features_count", "label": "عدد الميزات", "short": "Features", "icon": "🔢", "desc": "عدد المتغيرات المستخدمة", "color": "#3b82f6"}
        ]
        
        row = None
        for i, config in enumerate(metrics_config):
            if i % 2 == 0:
                row = ctk.CTkFrame(cards_scroll, fg_color="transparent")
                row.pack(fill=ctk.X, pady=(0, 10))
            self._create_metric_card(row, config, metrics)
    
    def _create_metric_card(self, parent, config: dict, metrics: dict):
        value = None
        if config["key"] == "cv_scores":
            cv = metrics.get("cv_scores")
            if cv is not None:
                value = f"{abs(np.mean(cv)):.4f}"
            else:
                value = "N/A"
        elif config["key"] == "features_count":
            value = str(metrics.get("features_count", 0))
        else:
            value = f"{metrics.get(config['key'], 0):.4f}"
        
        card = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_card"], corner_radius=12, border_width=1, border_color=self.COLORS["border"])
        card.pack(side="right", fill=ctk.BOTH, expand=True, padx=(0, 8), pady=0)
        
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill=ctk.X, padx=15, pady=(12, 0))
        icon_label = ctk.CTkLabel(top_row, text=config["icon"], font=ctk.CTkFont(size=20))
        icon_label.pack(side="right", padx=(0, 8))
        title_label = ctk.CTkLabel(top_row, text=reshape_text(config["label"]), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLORS["text_white"], anchor="e")
        title_label.pack(side="right", fill=ctk.X, expand=True)
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=config["color"], anchor="center")
        value_label.pack(pady=(10, 5))
        desc_label = ctk.CTkLabel(card, text=reshape_text(config["desc"]), font=ctk.CTkFont(size=11), text_color=self.COLORS["text_gray"], anchor="center")
        desc_label.pack(pady=(0, 12))
    
    def _create_close_button(self):
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=25, pady=(10, 20))
        close_button = ctk.CTkButton(button_frame, text=reshape_text("إغلاق"), command=self.dialog.destroy,
            width=200, height=45, corner_radius=12, fg_color=self.COLORS["success"],
            hover_color=self.COLORS["success_dark"], font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS["text_white"])
        close_button.pack()


def show_training_result(parent: Optional[ctk.CTk] = None, metrics: dict = None):
    """إظهار نافذة نتائج التدريب (بدون تغيير)"""
    TrainingResultDialog(parent, "نتائج التدريب", metrics)