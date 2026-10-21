# -*- coding: utf-8 -*-
"""
models/service_category.py
---------------------------
فئة نموذج فئة الخدمة (Service Category Model).

تمثل فئة تصنيف الخدمات في النظام.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ServiceCategory:
    """
    فئة تمثل فئة تصنيف الخدمات.

    Attributes:
        id: المعرف الفريد للفئة.
        name: اسم الفئة (مطلوب).
        description: وصف تفصيلي للفئة.
        created_at: تاريخ ووقت الإنشاء.
    """
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """تنظيف البيانات بعد الإنشاء."""
        if self.name:
            self.name = self.name.strip()

    def to_dict(self) -> dict:
        """تحويل كائن الفئة إلى قاموس."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ServiceCategory':
        """إنشاء كائن فئة من قاموس."""
        created_at = data.get('created_at')
        if created_at is not None:
            if isinstance(created_at, datetime):
                pass  # Already datetime
            else:
                created_at = datetime.fromisoformat(str(created_at))

        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description'),
            created_at=created_at,
        )
