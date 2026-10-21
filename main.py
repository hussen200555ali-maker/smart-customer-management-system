# -*- coding: utf-8 -*-
"""
main.py
-------
نقطة الدخول الرئيسية لنظام إدارة الخدمات الذكي
 والذكاء الاصطناعي (الإصدار 2.1).

يُهيئ بيئة التطبيق ويُشغّل واجهة تسجيل الدخول. عند نجاح تسجيل الدخول
يُنشئ مدير قاعدة البيانات ووحدات التحكم ويُمررها إلى النافذة الرئيسية.

البنية المعمارية:
    MVC (Model-View-Controller) مع طبقة مستودعات إضافية.

المسارات:
    models/          → نماذج البيانات (Data Classes)
    repositories/    → مستودعات قاعدة البيانات (Database Access)
    services/        → خدمات الأعمال (Business Logic)
    controllers/     → وحدات التحكم (Controllers)
    ui/              → واجهة المستخدم (Views/GUI)
    ai/              → نماذج الذكاء الاصطناعي
    utils/           → أدوات مساعدة
    exceptions/      → استثناءات مخصصة

الإصدار: 2.1
تاريخ الإنشاء: مارس 2026
تاريخ التحديث: أبريل 2026
"""

import os
import sys
import logging

# التأكد من وجود مجلدات النظام
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "invoices"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)

# تهيئة التسجيل الأساسي
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    نقطة الدخول الرئيسية للتطبيق.

    تُهيئ بيئة التطبيق ثم تُشغّل نافذة تسجيل الدخول.
    عند نجاح تسجيل الدخول، تُنشئ جميع مكونات النظام وتفتح النافذة الرئيسية.

    Flow:
        1. تشغيل نافذة تسجيل الدخول (LoginWindow)
        2. التحقق من بيانات المستخدم عبر AuthController
        3. إنشاء النافذة الرئيسية (MainWindow) مع جميع المكونات
        4. تشغيل الحلقة الرئيسية للتطبيق
    """
    try:
        logger.info("بدء تشغيل نظام إدارة الخدمات الذكي")

        # ── الخطوة 1: تشغيل نافذة تسجيل الدخول ──
        from ui.login_window import LoginWindow
        login_window = LoginWindow()

        # ── الخطوة 2: التحقق من تسجيل الدخول ──
        if login_window.current_user:
            # ── الخطوة 3: إنشاء النافذة الرئيسية ──
            import customtkinter as ctk
            from ui.main_window import MainWindow

            main_root = ctk.CTk()
            app = MainWindow(main_root, login_window.current_user)
            main_root.mainloop()
        else:
            logger.info("لم يتم تسجيل الدخول. تم إغلاق التطبيق.")

    except ImportError as e:
        logger.critical(f"خطأ في استيراد مكتبة مطلوبة: {e}")
        logger.critical("تأكد من تثبيت جميع المتطلبات: pip install -r requirements.txt")
        raise
    except Exception as e:
        logger.critical(f"خطأ حرج في تشغيل التطبيق: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
