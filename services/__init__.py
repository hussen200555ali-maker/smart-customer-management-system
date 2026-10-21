# -*- coding: utf-8 -*-
"""
services/__init__.py
--------------------
حزمة خدمات الأعمال (Business Services) في نظام إدارة الخدمات الذكي
.

تحتوي على منطق الأعمال الرئيسي للنظام. كل خدمة مسؤولة عن
مجال عمل محدد وتوفر واجهة عالية المستوى لوحدات التحكم.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from services.customer_service import CustomerService
from services.service_service import ServiceService
from services.order_service import OrderService

__all__ = [
    "CustomerService",
    "ServiceService",
    "OrderService",
]
