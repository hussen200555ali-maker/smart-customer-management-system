# استيراد مكتبة واجهة المستخدم المحسنة
import customtkinter as ctk
# استيراد مربعات الرسائل وخطوط tkinter
from tkinter import messagebox, font as tkfont
# استيراد الأنواع للـ type hints
from typing import Optional, Dict, Any
# استيراد وحدة التسجيل للتسجيل والأخطاء
import logging
# استيراد وحدة معالجة JSON
import json
# استيراد وحدة الخيوط (multithreading)
import threading
# استيراد مدير قاعدة البيانات
from repositories.database import DatabaseManager
# استيراد خوارزمية bidi للتعامل مع النصوص الثنائية
from bidi.algorithm import get_display
# استيراد مكتبة إعادة تشكيل النصوص العربية
import arabic_reshaper
# استيراد وحدة التعامل مع ملفات النظام
import os
# استيراد دوال عرض الرسائل
from utils.dialogs import show_info, show_success, show_warning, show_error, ask_yes_no
# استيراد مساعد التحميل غير المتزامن
from ui.async_helper import LoadingOverlay

# إنشاء logger للتسجيل
logger = logging.getLogger(__name__)


def reshape_text(text: str) -> str:
    """
    إعادة تشكيل النص العربي وعرضه بشكل صحيح من اليمين لليسار
    تستقبل نص وتُعيده مُهيأ للعرض في الواجهة مع دعم الحروف العربية المتصلة
    """
    if not text:  # التحقق من أن النص ليس فارغاً
        return ""
    try:
        # استخدام arabic_reshaper مع إعدادات محسنة للربط
        reshaper = arabic_reshaper.reshape(
            account_for_ligatures=True,  # احتساب الحروف المرتبطة
            support_ligatures=True  # دعم الحروف المتصلة
        )
        reshaped = reshaper.reshape(text)  # إعادة تشكيل النص
        return get_display(reshaped)  # توجيه النص من اليمين لليسار
    except Exception as e:
        logger.error(f"Error reshaping text: {e}")  # تسجيل الخطأ
        return text  # إعادة النص الأصلي في حالة الخطأ

# استيراد خدمات العمل المختلفة
from services.customer_service import CustomerService  # خدمة العملاء
from services.service_service import ServiceService  # خدمة الخدمات
from services.order_service import OrderService  # خدمة الطلبات

# استيراد واجهات المستخدم المختلفة
from ui.customer_ui import CustomerUI  # واجهة العملاء
from ui.service_ui import ServiceUI  # واجهة الخدمات
from ui.order_ui import OrderUI  # واجهة الطلبات
from ui.statistics_ui import StatisticsUI  # واجهة الإحصائيات
from ui.ai_ui import AIUI  # واجهة الذكاء الاصطناعي


class MainWindow:
    """النافذة الرئيسية للتطبيق - تحتوي على القائمة الجانبية وجميع الواجهات"""

    def __init__(self, root: ctk.CTk, current_user: Dict[str, Any]):
        """تهيئة النافذة الرئيسية"""
        self.root = root  # تخزين النافذة الرئيسية
        self.current_user = current_user  # تخزين بيانات المستخدم الحالي
        
        # تعيين عنوان النافذة مع اسم المستخدم
        self.root.title(reshape_text(f"نظام إدارة العملاء الذكي - {current_user['full_name']}"))
        self.root.geometry("1200x800")  # تعيين حجم افتراضي
        
        # تفعيل دعم اللغة العربية (RTL)
        self.root.tk.call('tk', 'scaling', 1.0)
        
        # محاولة تكبير النافذة لملء الشاشة (يعمل على Windows)
        try:
            self.root.state('zoomed')  # وضع التكبير
        except Exception:
            # إذا فشل، استخدم حجم أكبر
            self.root.geometry("1400x900")
        
        # تهيئة قاعدة البيانات والخدمات (للاستخدام في الواجهات المختلفة)
        self.db_manager = DatabaseManager()
        self.customer_service = CustomerService(self.db_manager)
        self.service_service = ServiceService(self.db_manager)
        self.order_service = OrderService(self.db_manager)
        self.ai_ui = None  # تهيئة واجهة الذكاء الاصطناعي
        
        # إعدادات الألوان
        self.dark_mode = False
        self._load_appearance_preference()
        self._setup_colors()
        
        # إنشاء واجهة المستخدم
        self._create_ui()
        
        # عرض الصفحة الافتراضية
        self._show_statistics()

    def _setup_colors(self):
        """إعداد الألوان"""
        if self.dark_mode:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        if self.dark_mode:
            self.colors = {
                'primary': '#4361ee',
                'secondary': '#3f37c9',
                'success': '#2ec4b6',
                'danger': '#ef233c',
                'warning': '#f77f00',
                'dark': '#1a1a2e',
                'light': '#2d2d44',
                'gray': '#a0a0a0'
            }
        else:
            self.colors = {
                'primary': '#4361ee',
                'secondary': '#3f37c9',
                'success': '#2ec4b6',
                'danger': '#ef233c',
                'warning': '#f77f00',
                'dark': '#1a1a2e',
                'light': '#f8f9fa',
                'gray': '#6c757d'
            }
        
        # إعداد خطوط Cairo
        self._setup_fonts()

    def _setup_fonts(self):
        """إعداد وتسجيل خطوط Cairo"""
        # الحصول على مسار مجلد الخطوط (موجود في ui/assets/fonts)
        fonts_dir = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
        
        # تسجيل خطوط Cairo المختلفة
        cairo_fonts = {
            'Cairo-Regular': os.path.join(fonts_dir, 'Cairo-Regular.ttf'),
            'Cairo-Bold': os.path.join(fonts_dir, 'Cairo-Bold.ttf'),
            'Cairo-Medium': os.path.join(fonts_dir, 'Cairo-Medium.ttf'),
            'Cairo-Light': os.path.join(fonts_dir, 'Cairo-Light.ttf'),
            'Cairo-SemiBold': os.path.join(fonts_dir, 'Cairo-SemiBold.ttf'),
            'Cairo-ExtraBold': os.path.join(fonts_dir, 'Cairo-ExtraBold.ttf'),
            'Cairo-Black': os.path.join(fonts_dir, 'Cairo-Black.ttf'),
            'Cairo-ExtraLight': os.path.join(fonts_dir, 'Cairo-ExtraLight.ttf')
        }
        
        # تسجيل الخطوط في النظام
        for font_name, font_path in cairo_fonts.items():
            if os.path.exists(font_path):
                try:
                    self.root.tk.call('font', 'create', font_name, '-file', font_path)
                except Exception as e:
                    logger.warning(f"فشل تسجيل الخط {font_name}: {e}")
        
        # تعيين الخطوط الافتراضية للواجهة
        self.fonts = {
            'title': ('Cairo-Bold', 20),
            'subtitle': ('Cairo-SemiBold', 16),
            'body': ('Cairo-Regular', 12),
            'small': ('Cairo-Regular', 10),
            'button': ('Cairo-Medium', 14)
        }

    def _create_ui(self):
        """إنشاء واجهة المستخدم"""
        # إطار الشبكة الرئيسي
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # إنشاء الشريط الجانبي
        self._create_sidebar()
        
        # إنشاء منطقة المحتوى الرئيسية
        self._create_content_area()

    def _create_sidebar(self):
        """إنشاء الشريط الجانبي"""
        # إطار الشريط الجانبي
        sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0, fg_color=self.colors['dark'])
        sidebar.grid(row=0, column=1, sticky="nsew")
        
        # عنوان النظام
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_frame.pack(pady=20, padx=20, fill=ctk.X)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=reshape_text("نظام إدارة العملاء الذكي"),
            font=ctk.CTkFont(family="Cairo-Bold", size=20),
            text_color="#ffffff",
            anchor="e"
        )
        title_label.pack()
        
        # معلومات المستخدم
        user_frame = ctk.CTkFrame(sidebar, fg_color="#2d2d44", corner_radius=10)
        user_frame.pack(pady=(0, 20), padx=20, fill=ctk.X)
        
        user_label = ctk.CTkLabel(
            user_frame,
            text=reshape_text(f"مرحباً، {self.current_user['full_name']}"),
            font=ctk.CTkFont(family="Cairo-Regular", size=12),
            text_color="#a0a0a0",
            anchor="e"
        )
        user_label.pack(pady=10)
        
        role_label = ctk.CTkLabel(
            user_frame,
            text=reshape_text(f"الدور: {self._get_role_name(self.current_user['role'])}"),
            font=ctk.CTkFont(family="Cairo-Regular", size=10),
            text_color="#666666",
            anchor="e"
        )
        role_label.pack(pady=(0, 10))
        
        # أزرار التنقل
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(pady=10, padx=20, fill=ctk.BOTH, expand=True)
        
        # زر الإحصائيات
        self.btn_statistics = ctk.CTkButton(
            nav_frame,
            text=reshape_text("📊  الإحصائيات"),
            command=self._show_statistics,
            fg_color="transparent",
            border_width=0,
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff",
            hover_color="#3f37c9",
            anchor="e"
        )
        self.btn_statistics.pack(pady=5, fill=ctk.X)
        
        # زر العملاء
        self.btn_customers = ctk.CTkButton(
            nav_frame,
            text=reshape_text("👥  إدارة العملاء"),
            command=self._show_customers,
            fg_color="transparent",
            border_width=0,
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff",
            hover_color="#3f37c9",
            anchor="e"
        )
        self.btn_customers.pack(pady=5, fill=ctk.X)
        
        # زر الخدمات
        self.btn_services = ctk.CTkButton(
            nav_frame,
            text=reshape_text("🛠 ️إدارة الخدمات"),
            command=self._show_services,
            fg_color="transparent",
            border_width=0,
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff",
            hover_color="#3f37c9",
            anchor="e"
        )
        self.btn_services.pack(pady=5, fill=ctk.X)
        
        # زر الطلبات
        self.btn_orders = ctk.CTkButton(
            nav_frame,
            text=reshape_text("📋  إدارة الطلبات"),
            command=self._show_orders,
            fg_color="transparent",
            border_width=0,
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff",
            hover_color="#3f37c9",
            anchor="e"
        )
        self.btn_orders.pack(pady=5, fill=ctk.X)
        
        # زر الذكاء الاصطناعي
        self.btn_ai = ctk.CTkButton(
            nav_frame,
            text=reshape_text("🤖  الذكاء الاصطناعي"),
            command=self._show_ai,
            fg_color="transparent",
            border_width=0,
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff",
            hover_color="#3f37c9",
            anchor="e"
        )
        self.btn_ai.pack(pady=5, fill=ctk.X)
        
        # زر استيراد وتصدير البيانات
        self.btn_import_export = ctk.CTkButton(
            nav_frame,
            text=reshape_text("📁  استيراد/تصدير"),
            command=self._show_import_export,
            fg_color="transparent",
            border_width=0,
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff",
            hover_color="#3f37c9",
            anchor="e"
        )
        self.btn_import_export.pack(pady=5, fill=ctk.X)
        
        # زر المستخدمين (للمدير فقط)
        if self.current_user['role'] == 'admin':
            self.btn_users = ctk.CTkButton(
                nav_frame,
                text="👤  إدارة المستخدمين",
                command=self._show_users,
                fg_color="transparent",
                border_width=0,
                height=45,
                font=ctk.CTkFont(family="Cairo-Medium", size=14),
                text_color="#ffffff",
                hover_color="#3f37c9",
                anchor="e"
            )
            self.btn_users.pack(pady=5, fill=ctk.X)

            # زر النسخ الاحتياطي (للمدير فقط)
            self.btn_backup = ctk.CTkButton(
                nav_frame,
                text=reshape_text("💾  النسخ الاحتياطي"),
                command=self._show_backup,
                fg_color="transparent",
                border_width=0,
                height=45,
                font=ctk.CTkFont(family="Cairo-Medium", size=14),
                text_color="#ffffff",
                hover_color="#3f37c9",
                anchor="e"
            )
            self.btn_backup.pack(pady=5, fill=ctk.X)
        
        # زر تبديل الوضع الداكن
        self.dark_mode_button = ctk.CTkButton(
            nav_frame,
            text=reshape_text("🌙  الوضع الداكن"),
            command=self._toggle_dark_mode,
            fg_color="transparent",
            border_width=0,
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff",
            hover_color="#3f37c9",
            anchor="e"
        )
        self.dark_mode_button.pack(pady=5, fill=ctk.X)

        # زر الخروج
        exit_button = ctk.CTkButton(
            nav_frame,
            text="🚪  خروج",
            command=self._exit_app,
            fg_color="#ef233c",
            hover_color="#d90429",
            height=40,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            text_color="#ffffff"
        )
        exit_button.pack(pady=20, fill=ctk.X, side=ctk.BOTTOM)

    def _create_content_area(self):
        """إنشاء منطقة المحتوى الرئيسية"""
        # إطار المحتوى
        self.content_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=self.colors['light'])
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # إطار لعرض المحتوى المختلف
        self.main_content = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.main_content.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

    def _clear_content(self):
        """مسح المحتوى الحالي"""
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def _get_role_name(self, role: str) -> str:
        """الحصول على اسم الدور"""
        roles = {
            'admin': 'مدير',
            'employee': 'موظف',
            'viewer': 'مشاهد'
        }
        return roles.get(role, role)

    def _show_statistics(self):
        """عرض صفحة الإحصائيات"""
        self._clear_content()
        self._highlight_button(self.btn_statistics)
        statistics_ui = StatisticsUI(
            self.main_content,
            self.db_manager,
            self.current_user
        )

    def _show_customers(self):
        """عرض صفحة إدارة العملاء"""
        self._clear_content()
        self._highlight_button(self.btn_customers)
        customer_ui = CustomerUI(
            self.main_content,
            self.customer_service,
            self.db_manager,
            self.current_user
        )

    def _show_services(self):
        """عرض صفحة إدارة الخدمات"""
        self._clear_content()
        self._highlight_button(self.btn_services)
        service_ui = ServiceUI(
            self.main_content,
            self.service_service,
            self.db_manager,
            self.current_user
        )

    def _show_orders(self):
        """عرض صفحة إدارة الطلبات"""
        self._clear_content()
        self._highlight_button(self.btn_orders)
        order_ui = OrderUI(
            self.main_content,
            self.order_service,
            self.customer_service,
            self.service_service,
            self.db_manager,
            self.current_user
        )

    def _show_ai(self):
        """عرض صفحة الذكاء الاصطناعي"""
        self._clear_content()
        self._highlight_button(self.btn_ai)
        self.ai_ui = AIUI(
            self.main_content,
            self.db_manager
        )

    def _show_import_export(self):
        """عرض صفحة استيراد وتصدير البيانات"""
        self._clear_content()
        self._highlight_button(self.btn_import_export)
        from ui.import_export_ui import ImportExportUI
        import_export_ui = ImportExportUI(
            self.main_content,
            self.db_manager,
            self.current_user
        )

    def _show_users(self):
        """عرض صفحة إدارة المستخدمين"""
        self._clear_content()
        if hasattr(self, 'btn_users'):
            self._highlight_button(self.btn_users)
        from ui.users_ui import UsersUI
        users_ui = UsersUI(
            self.main_content,
            self.db_manager,
            self.current_user
        )

    def _highlight_button(self, button: ctk.CTkButton):
        """تمييز الزر النشط"""
        buttons = [
            self.btn_statistics, self.btn_customers, 
            self.btn_services, self.btn_orders, self.btn_ai,
            self.btn_import_export
        ]
        if hasattr(self, 'btn_users'):
            buttons.append(self.btn_users)
        if hasattr(self, 'btn_backup'):
            buttons.append(self.btn_backup)
        
        for btn in buttons:
            btn.configure(fg_color="transparent")
        
        button.configure(fg_color=self.colors['primary'])

    def _show_backup(self):
        """عرض صفحة النسخ الاحتياطي"""
        self._clear_content()
        if hasattr(self, 'btn_backup'):
            self._highlight_button(self.btn_backup)
        from ui.backup_ui import BackupUI
        backup_ui = BackupUI(
            self.main_content,
            self.db_manager,
            self.current_user
        )

    def _toggle_dark_mode(self):
        """تبديل بين الوضع الفاتح والداكن"""
        self.dark_mode = not self.dark_mode
        self._save_appearance_preference()
        self._setup_colors()

        # تحديث نص الزر
        if self.dark_mode:
            self.dark_mode_button.configure(text=reshape_text("☀️  الوضع الفاتح"))
        else:
            self.dark_mode_button.configure(text=reshape_text("🌙  الوضع الداكن"))

        # تحديث لون منطقة المحتوى
        self.content_frame.configure(fg_color=self.colors['light'])

        # إعادة عرض الصفحة الحالية لتحديث الألوان
        self._show_statistics()

    def _load_appearance_preference(self):
        """تحميل تفضيل الوضع من ملف الإعدادات"""
        try:
            pref_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'appearance.json')
            if os.path.exists(pref_path):
                with open(pref_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.dark_mode = data.get('dark_mode', False)
        except Exception as e:
            logger.warning(f"خطأ في تحميل تفضيل المظهر: {e}")

    def _save_appearance_preference(self):
        """حفظ تفضيل الوضع في ملف الإعدادات"""
        try:
            pref_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'appearance.json')
            os.makedirs(os.path.dirname(pref_path), exist_ok=True)
            with open(pref_path, 'w', encoding='utf-8') as f:
                json.dump({'dark_mode': self.dark_mode}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"خطأ في حفظ تفضيل المظهر: {e}")

    def _exit_app(self):
        """خروج من التطبيق"""
        if messagebox.askyesno("تأكيد الخروج", "هل تريد الخروج من التطبيق؟"):
            self.db_manager.log_activity(
                self.current_user['id'],
                "تسجيل خروج",
                "users",
                self.current_user['id'],
                "تسجيل خروج من النظام"
            )
            self.root.destroy()
