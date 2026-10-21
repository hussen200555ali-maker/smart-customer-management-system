# استيراد مكتبة واجهة المستخدم المحسنة (CustomTkinter)
import customtkinter as ctk
# استيراد وحدة مربعات الرسائل من tkinter
from tkinter import messagebox
# استيراد أنواع البيانات للتعريفات type hints
from typing import Optional, Dict, Any
# استيراد خوارزمية bidi للتعامل مع النصوص الثنائية (RTL)
from bidi.algorithm import get_display
# استيراد مكتبة إعادة تشكيل النصوص العربية
import arabic_reshaper
# استيراد دوال عرض التحذيرات والأخطاء
from utils.dialogs import show_warning, show_error


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
    except:  # في حالة حدوث خطأ
        return text  # أعد النص الأصلي بدون معالجة


class LoginWindow:
    """
    نافذة تسجيل الدخول.
    تُستخدم للتحقق من هوية المستخدم قبل الدخول إلى النظام الرئيسي.
    تستخدم AuthController لفصل منطق المصادقة عن واجهة المستخدم.
    """

    def __init__(self):
        """تهيئة نافذة تسجيل الدخول وإنشاء وحدة التحكم."""
        from repositories.database import DatabaseManager  # استيراد مدير قاعدة البيانات
        from controllers.auth_controller import AuthController  # استيراد وحدة التحكم للمصادقة

        self.db_manager = DatabaseManager()  # إنشاء مدير قاعدة البيانات
        self.auth_controller = AuthController(self.db_manager)  # إنشاء وحدة المصادقة مع قاعدة البيانات
        self.current_user: Optional[Dict[str, Any]] = None  # متغير لتخزين بيانات المستخدم الحالي

        # إعداد النافذة الرئيسية
        self.root = ctk.CTk()  # إنشاء النافذة الرئيسية
        self.root.title("تسجيل الدخول - نظام إدارة العملاء الذكي")  # تعيين عنوان النافذة
        self.root.geometry("450x620")  # تعيين حجم النافذة (العرض x الارتفاع)
        self.root.resizable(False, False)  # منع تغيير حجم النافذة

        # تفعيل دعم اللغة العربية من اليمين لليسار
        self.root.tk.call('tk', 'scaling', 1.0)  # تعيين مقياس العرض

        # مركز النافذة في منتصف الشاشة
        self._center_window()

        # إنشاء واجهة المستخدم
        self._create_ui()

        # تشغيل النافذة
        self.root.mainloop()

    def _center_window(self):
        """توسيط النافذة على الشاشة"""
        self.root.update_idletasks()  # تحديث النافذة للحصول على الأبعاد الصحيحة
        width = self.root.winfo_width()  # الحصول على عرض النافذة
        height = self.root.winfo_height()  # الحصول على ارتفاع النافذة
        # حساب موقع_center (منتصف الشاشة)
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")  # تحريك النافذة للمركز

    def _create_ui(self):
        """إنشاء واجهة المستخدم مع تحسينات بصرية"""
        # إطار رئيسي (طبقة خلفية) - يملأ整个 النافذة
        main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#1a1a2e")
        main_frame.pack(fill=ctk.BOTH, expand=True)

        # إطار التدرج (طبقة متداخلة لإنشاء تأثير تدرج لوني)
        gradient_overlay = ctk.CTkFrame(
            main_frame, corner_radius=0,
            fg_color="#16213e"
        )
        # وضع التدرج في الجزء العلوي من النافذة (45% من الارتفاع)
        gradient_overlay.place(relx=0, rely=0, relwidth=1, relheight=0.45)

        # إطار المحتوى (يحتوي على عناصر الواجهة)
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True)

        # منطقة الشعار والأيقونة (حاوية فارغة)
        logo_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        logo_frame.pack(pady=(40, 5))

        # إطار الشعار الدائري (مربع بزوايا مدورة لخلق شكل دائري)
        logo_circle = ctk.CTkFrame(
            logo_frame,
            width=80,  # العرض
            height=80,  # الارتفاع
            corner_radius=40,  # نصف قطر الزاوية (لإنشاء شكل دائري)
            fg_color="#4361ee",  # لون الخلفية
            border_width=3,  # عرض الحدود
            border_color="#3f37c9"  # لون الحدود
        )
        logo_circle.pack_propagate(False)  # منع изменения الحجم بناءً على المحتوى
        logo_circle.pack()

        #标签 (عرض أيقونة في circle)
        logo_label = ctk.CTkLabel(
            logo_circle,
            text="🏢",  # أيقونة مبنى
            font=ctk.CTkFont(size=36),  # حجم الخط
            text_color="#ffffff"  # لون النص
        )
        logo_label.pack(expand=True)  # توسيع label لملء المساحة المتبقية

        # العنوان الرئيسي (نظام إدارة العملاء الذكي)
        title_label = ctk.CTkLabel(
            content_frame,
            text=reshape_text("نظام إدارة العملاء الذكي"),
            font=ctk.CTkFont(size=28, weight="bold"),  # خط كبير وعريض
            text_color="#ffffff",  # لون النص الأبيض
            anchor="e"  # محاذاة لليمين
        )
        title_label.pack(pady=(15, 5))  # هوامش عمودية

        # العنوان الفرعي (تسجيل الدخول إلى حسابك)
        subtitle_label = ctk.CTkLabel(
            content_frame,
            text=reshape_text("تسجيل الدخول إلى حسابك"),
            font=ctk.CTkFont(size=14),  # خط أصغر
            text_color="#a0a0a0",  # لون رمادي
            anchor="e"  # محاذاة لليمين
        )
        subtitle_label.pack(pady=(0, 25))  # هامش سفلي فقط

        # إطار النموذج مع خلفية داكنة (حاوية للنموذج)
        form_container = ctk.CTkFrame(
            content_frame,
            fg_color="#0f3460",  # لون خلفية داكن
            corner_radius=15,  # زوايا مدورة
            border_width=1,  # حدود
            border_color="#1a1a5e"  # لون الحدود
        )
        form_container.pack(pady=(0, 10), padx=30, fill=ctk.X)  # تعبئة أفقية

        form_frame = ctk.CTkFrame(form_container, fg_color="transparent")  # إطار داخلي شفاف
        form_frame.pack(pady=25, padx=25, fill=ctk.X)

        # عنوان حقل اسم المستخدم
        username_label = ctk.CTkLabel(
            form_frame,
            text=reshape_text("اسم المستخدم"),
            font=ctk.CTkFont(size=13, weight="bold"),  # خط عريض
            text_color="#e0e0e0",  # لون فاتح
            anchor="e"  # محاذاة لليمين
        )
        username_label.pack(fill=ctk.X, pady=(0, 5))  # تعبئة أفقية

        # حقل اسم المستخدم (إدخال النص)
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=reshape_text("أدخل اسم المستخدم"),  # نص تلميح
            width=280,  # العرض
            height=45,  # الارتفاع
            font=ctk.CTkFont(size=14),  # حجم الخط
            justify="right",  # محاذاة النص لليمين
            fg_color="#1a1a2e",  # لون خلفية الحقل
            border_color="#2d2d6e",  # لون الحدود
            text_color="#ffffff",  # لون النص المدخل
            placeholder_text_color="#666666"  # لون نص التلميح
        )
        self.username_entry.pack(pady=(0, 15))  # هوامش

        # عنوان حقل كلمة المرور
        password_label = ctk.CTkLabel(
            form_frame,
            text=reshape_text("كلمة المرور"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e0e0e0",
            anchor="e"
        )
        password_label.pack(fill=ctk.X, pady=(0, 5))

        # حقل كلمة المرور (مع إظهار • بدلاً من النص)
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=reshape_text("أدخل كلمة المرور"),
            width=280,
            height=45,
            show="•",  # إخفاء النص وإظهار نقاط
            font=ctk.CTkFont(size=14),
            justify="right",
            fg_color="#1a1a2e",
            border_color="#2d2d6e",
            text_color="#ffffff",
            placeholder_text_color="#666666"
        )
        self.password_entry.pack(pady=(0, 10))

        # خيار تذكرني (حاوية للخيار)
        remember_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        remember_frame.pack(fill=ctk.X, pady=(0, 15))

        self.remember_var = ctk.BooleanVar(value=False)  # متغير لتخزين حالة الخيار
        remember_checkbox = ctk.CTkCheckBox(
            remember_frame,
            text=reshape_text("تذكرني"),
            variable=self.remember_var,  # ربط المتغير
            font=ctk.CTkFont(size=12),
            text_color="#a0a0a0",
            fg_color="#4361ee",  # لون عند التحديد
            hover_color="#3a56d4",  # لون عند التحويم
            border_color="#4361ee",
            checkbox_width=18,  # عرض الصندوق
            checkbox_height=18  # ارتفاع الصندوق
        )
        remember_checkbox.pack(anchor="e")  # محاذاة لليمين

        # زر تسجيل الدخول
        login_button = ctk.CTkButton(
            form_frame,
            text=reshape_text("تسجيل الدخول"),
            width=280,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#4361ee",  # لون الزر
            hover_color="#3a56d4",  # لون عند التحويم
            corner_radius=10,  # زوايا مدورة
            command=self._login  # دالة الاستجابة للنقر
        )
        login_button.pack(pady=(5, 0))

        # معلومات تسجيل الدخول (للاختبار)
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(pady=15)

        info_label = ctk.CTkLabel(
            info_frame,
            text=reshape_text("👤 المستخدم: admin    🔑 كلمة المرور: admin123"),
            font=ctk.CTkFont(size=11),
            text_color="#555555",
            anchor="center"
        )
        info_label.pack()

        # رقم الإصدار (في أسفل النافذة)
        version_label = ctk.CTkLabel(
            content_frame,
            text="v2.0.0",
            font=ctk.CTkFont(size=10),
            text_color="#3a3a5e",
            anchor="center"
        )
        version_label.pack(side=ctk.BOTTOM, pady=10)  # وضع في الأسفل

        # ربط مفتاح Enter لتسجيل الدخول (اختصار لوحة المفاتيح)
        self.password_entry.bind("<Return>", lambda e: self._login())  # Enter على كلمة المرور
        self.username_entry.bind("<Return>", lambda e: self._login())  # Enter على اسم المستخدم

    def _login(self):
        """تسجيل الدخول باستخدام وحدة التحكم (AuthController)."""
        # الحصول على القيم من حقول الإدخال وإزالة المسافات الزائدة
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        # التحقق من إدخال اسم المستخدم وكلمة المرور
        if not username or not password:
            show_warning(self.root,"تحذير", "الرجاء إدخال اسم المستخدم وكلمة المرور")
            return  # إيقاف الدالة

        try:
            # محاولة تسجيل الدخول من خلال وحدة التحكم
            user = self.auth_controller.login(username, password)
            self.current_user = user  # تخزين بيانات المستخدم
            self.root.destroy()  # إغلاق نافذة تسجيل الدخول
        except Exception as e:
            error_msg = str(e)  # الحصول على رسالة الخطأ
            show_error(self.root, "خطأ", error_msg)  # عرض رسالة الخطأ
            self.password_entry.delete(0, ctk.END)  # مسح حقل كلمة المرور
