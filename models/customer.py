# -*- coding: utf-8 -*-
"""
models/customer.py
------------------
فئة نموذج العميل (Customer Model).

تمثل بيانات العميل في النظام وتُستخدم ككائن نقل البيانات (DTO)
بين طبقة قاعدة البيانات وطبقة الأعمال وطبقة العرض.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Customer:
    """
    فئة تمثل بيانات العميل في النظام.

    Attributes:
        id: المعرف الفريد للعميل (يُولّد تلقائياً من قاعدة البيانات).
        name: اسم العميل الكامل (مطلوب).
        phone: رقم هاتف العميل (مطلوب).
        email: البريد الإلكتروني (اختياري).
        address: العنوان الفعلي (اختياري).
        notes: ملاحظات إضافية حول العميل (اختياري).
        created_by: معرف المستخدم الذي أضاف العميل.
        created_at: تاريخ ووقت إنشاء السجل.
        updated_at: تاريخ ووقت آخر تحديث للسجل.
    """
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """التحقق من البيانات بعد الإنشاء."""
        if self.name:
            self.name = self.name.strip()
        if self.phone:
            self.phone = self.phone.strip()

    def to_dict(self) -> dict:
        """تحويل كائن العميل إلى قاموس."""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Customer':
        """إنشاء كائن عميل من قاموس."""
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')

        if created_at is not None:
            if isinstance(created_at, datetime):
                pass
            else:
                created_at = datetime.fromisoformat(str(created_at))
        
        if updated_at is not None:
            if isinstance(updated_at, datetime):
                pass
            else:
                updated_at = datetime.fromisoformat(str(updated_at))

        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            phone=data.get('phone', ''),
            email=data.get('email'),
            address=data.get('address'),
            notes=data.get('notes'),
            created_by=data.get('created_by'),
            created_at=created_at,
            updated_at=updated_at,
        )
