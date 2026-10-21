# -*- coding: utf-8 -*-
"""
controllers/__init__.py
------------------------
حزمة وحدات التحكم (Controllers) في نمط MVC.

كل وحدة تحكم مسؤولة عن التنسيق بين واجهة المستخدم (View)
وخدمات الأعمال (Services).

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from controllers.base_controller import BaseController
from controllers.auth_controller import AuthController
from controllers.customer_controller import CustomerController
from controllers.service_controller import ServiceController
from controllers.order_controller import OrderController

__all__ = [
    "BaseController",
    "AuthController",
    "CustomerController",
    "ServiceController",
    "OrderController",
]
