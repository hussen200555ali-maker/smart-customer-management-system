# -*- coding: utf-8 -*-
"""
models/user.py
--------------
فئة نموذج المستخدم (User Model).

تمثل بيانات المستخدم في النظام وتشمل معلومات المصادقة والتفويض.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    فئة تمثل بيانات المستخدم في النظام.

    Attributes:
        id: المعرف الفريد للمستخدم.
        username: اسم المستخدم للدخول (فريد).
        password_hash: تجزئة كلمة المرور المشفّرة.
        full_name: الاسم الكامل للمستخدم.
        role: دور المستخدم (admin, employee, viewer).
        is_active: حالة تفعيل الحساب (1=مفعّل، 0=معطّل).
        created_at: تاريخ ووقت إنشاء الحساب.
        last_login: تاريخ ووقت آخر تسجيل دخول.
    """
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = "employee"
    is_active: int = 1
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    @property
    def is_admin(self) -> bool:
        """التحقق مما إذا كان المستخدم مديراً."""
        return self.role == "admin"

    @property
    def role_display(self) -> str:
        """إرجاع اسم الدور بالعربية."""
        role_map = {
            'admin': 'مدير',
            'employee': 'موظف',
            'viewer': 'مشاهد',
        }
        return role_map.get(self.role, self.role)

    def to_dict(self) -> dict:
        """تحويل كائن المستخدم إلى قاموس (بدون كلمة المرور)."""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'role_display': self.role_display,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
