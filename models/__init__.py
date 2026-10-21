# -*- coding: utf-8 -*-
"""
models/__init__.py
------------------
حزمة النماذج (Models) في نظام إدارة الخدمات الذكي
.

تحتوي على فئات البيانات (Data Classes) التي تمثل كيانات النظام المختلفة
مثل العملاء والخدمات والطلبات والمستخدمين. تُستخدم هذه الفئات كطبقة
نقل البيانات (DTO) بين الطبقات المختلفة.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from models.customer import Customer
from models.service import Service
from models.service_category import ServiceCategory
from models.order import Order, OrderDetail
from models.user import User

__all__ = [
    "Customer",
    "Service",
    "ServiceCategory",
    "Order",
    "OrderDetail",
    "User",
]
