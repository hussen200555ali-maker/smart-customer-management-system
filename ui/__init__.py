# -*- coding: utf-8 -*-
"""
ui/__init__.py
--------------
حزمة واجهة المستخدم (User Interface).

تحتوي على جميع نوافذ وواجهات النظام المبنية باستخدام CustomTkinter.

الإصدار: 2.1
"""

from ui.main_window import MainWindow
from ui.login_window import LoginWindow
from ui.customer_ui import CustomerUI
from ui.service_ui import ServiceUI
from ui.order_ui import OrderUI
from ui.statistics_ui import StatisticsUI
from ui.ai_ui import AIUI
from ui.users_ui import UsersUI
from ui.import_export_ui import ImportExportUI

__all__ = [
    "MainWindow",
    "LoginWindow",
    "CustomerUI",
    "ServiceUI",
    "OrderUI",
    "StatisticsUI",
    "AIUI",
    "UsersUI",
    "ImportExportUI",
]
