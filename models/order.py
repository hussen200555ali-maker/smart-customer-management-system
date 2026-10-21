# -*- coding: utf-8 -*-
"""
models/order.py
---------------
فئات نماذج الطلبات (Order Models).

تحتوي على نموذج الطلب الرئيسي ونموذج تفاصيل الطلب.
تُستخدم ككائنات نقل البيانات (DTO) بين طبقات النظام المختلفة.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Order:
    """
    فئة تمثل بيانات الطلب في النظام.

    Attributes:
        id: المعرف الفريد للطلب.
        customer_id: معرف العميل صاحب الطلب.
        status: حالة الطلب (pending, in_progress, completed, cancelled).
        total_amount: المبلغ الإجمالي للطلب.
        notes: ملاحظات على الطلب.
        created_by: معرف المستخدم المنشئ.
        created_at: تاريخ ووقت الإنشاء.
        updated_at: تاريخ ووقت آخر تحديث.
        customer_name: اسم العميل (يُملأ من Join).
        customer_phone: هاتف العميل (يُملأ من Join).
        customer_email: بريد العميل (يُملأ من Join).
        customer_address: عنوان العميل (يُملأ من Join).
        details: قائمة تفاصيل الطلب.
    """
    id: Optional[int] = None
    customer_id: int = 0
    status: str = "pending"
    total_amount: float = 0.0
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # حقول مضافة من JOIN مع جدول العملاء
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    # تفاصيل الطلب
    details: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    # حقول إضافية تُملأ من معالجة البيانات
    service_names: str = ""
    service_ids: List[int] = field(default_factory=list)
    service_quantities: List[int] = field(default_factory=list)

    @property
    def status_display(self) -> str:
        """إرجاع اسم الحالة بالعربية."""
        status_map = {
            'pending': 'قيد الانتظار',
            'in_progress': 'قيد التنفيذ',
            'completed': 'مكتمل',
            'cancelled': 'ملغي',
        }
        return status_map.get(self.status, self.status)

    def to_dict(self) -> dict:
        """تحويل كائن الطلب إلى قاموس."""
        result = {
            'id': self.id,
            'customer_id': self.customer_id,
            'status': self.status,
            'total_amount': self.total_amount,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'customer_address': self.customer_address,
            'details': self.details or [],
            'service_names': self.service_names,
            'service_ids': self.service_ids,
            'service_quantities': self.service_quantities,
        }
        return result


@dataclass
class OrderDetail:
    """
    فئة تمثل تفاصيل عنصر في الطلب.

    Attributes:
        id: المعرف الفريد لسجل التفاصيل.
        order_id: معرف الطلب المرتبط.
        service_id: معرف الخدمة.
        quantity: الكمية المطلوبة.
        unit_price: السعر الوحدوي للخدمة.
        total_price: السعر الإجمالي (quantity × unit_price).
        service_name: اسم الخدمة (يُملأ من Join).
        service_description: وصف الخدمة (يُملأ من Join).
    """
    id: Optional[int] = None
    order_id: int = 0
    service_id: int = 0
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    service_name: Optional[str] = None
    service_description: Optional[str] = None

    def __post_init__(self):
        """حساب السعر الإجمالي تلقائياً."""
        if self.total_price == 0 and self.quantity > 0 and self.unit_price > 0:
            self.total_price = self.quantity * self.unit_price
