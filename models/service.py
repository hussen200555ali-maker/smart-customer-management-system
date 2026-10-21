# -*- coding: utf-8 -*-
"""
models/service.py
-----------------
فئة نموذج الخدمة (Service Model).

تمثل بيانات الخدمة المقدمة في النظام وتُستخدم ككائن نقل البيانات (DTO).

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Service:
    """
    فئة تمثل بيانات الخدمة في النظام.

    Attributes:
        id: المعرف الفريد للخدمة.
        name: اسم الخدمة (مطلوب).
        description: وصف تفصيلي للخدمة.
        price: سعر الخدمة بالوحدة (مطلوب، أكبر من صفر).
        category_id: معرف فئة الخدمة المرتبطة.
        is_active: حالة تفعيل الخدمة (1=مفعّلة، 0=معطّلة).
        created_at: تاريخ ووقت إنشاء السجل.
        updated_at: تاريخ ووقت آخر تحديث.
    """
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    price: float = 0.0
    category_id: Optional[int] = None
    is_active: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """التحقق من البيانات بعد الإنشاء."""
        if self.name:
            self.name = self.name.strip()
        if isinstance(self.price, str):
            try:
                self.price = float(self.price)
            except ValueError:
                self.price = 0.0

    def to_dict(self) -> dict:
        """تحويل كائن الخدمة إلى قاموس."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category_id': self.category_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Service':
        """إنشاء كائن خدمة من قاموس."""
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
            description=data.get('description'),
            price=float(data.get('price', 0)),
            category_id=data.get('category_id'),
            is_active=data.get('is_active', 1),
            created_at=created_at,
            updated_at=updated_at,
        )
