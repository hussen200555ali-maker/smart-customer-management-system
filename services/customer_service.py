# -*- coding: utf-8 -*-
"""
services/customer_service.py
----------------------------
خدمة إدارة العملاء (Customer Business Service).

تُغلف منطق الأعمال المتعلق بالعملاء بما في ذلك التحقق من البيانات
وتحويلها بين الكائنات والقواميس وتسجيل العمليات.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from repositories.database import DatabaseManager
from models.customer import Customer


class CustomerService:
    """
    خدمة إدارة العملاء.

    مسؤولة عن جميع عمليات الأعمال المتعلقة بالعملاء:
    - إضافة وتعديل وحذف العملاء
    - البحث والاستعلام عن العملاء
    - التحقق من صحة البيانات
    - تسجيل العمليات في سجل الأنشطة

    Args:
        db_manager: كائن مدير قاعدة البيانات.
    """

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة خدمة العملاء."""
        self.db_manager = db_manager

    def add_customer(
        self,
        name: str,
        phone: str,
        email: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> int:
        """
        إضافة عميل جديد مع التحقق من البيانات وتسجيل العملية.

        Args:
            name: اسم العميل (مطلوب).
            phone: رقم الهاتف (مطلوب).
            email: البريد الإلكتروني (اختياري).
            address: العنوان (اختياري).
            notes: ملاحظات (اختياري).
            created_by: معرف المستخدم المنشئ.

        Returns:
            معرف العميل المُنشأ.

        Raises:
            ValueError: إذا كان الاسم أو الهاتف فارغين.
        """
        if not name or not name.strip():
            raise ValueError("الاسم مطلوب")
        if not phone or not phone.strip():
            raise ValueError("رقم الهاتف مطلوب")

        result = self.db_manager.insert_customer(
            name.strip(), phone.strip(), email, address, notes, created_by
        )
        if result > 0:
            self.db_manager.log_activity(
                created_by, "إضافة عميل", "customers", result,
                f"إضافة عميل جديد: {name}"
            )
        return result

    def get_customers(self, search_term: Optional[str] = None) -> List[Customer]:
        """
        الحصول على قائمة العملاء مع إمكانية البحث.

        Args:
            search_term: مصطلح البحث (بحث في الاسم والهاتف والبريد).

        Returns:
            قائمة بكائنات العملاء.
        """
        customers_data = self.db_manager.get_customers(search_term)
        return [Customer.from_dict(c) for c in customers_data]

    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """
        الحصول على بيانات عميل محدد بالمعرف.

        Args:
            customer_id: معرف العميل.

        Returns:
            كائن العميل أو None إذا لم يُعثر عليه.
        """
        customer_data = self.db_manager.get_customer_by_id(customer_id)
        if customer_data:
            return Customer.from_dict(customer_data)
        return None

    def update_customer(
        self,
        customer_id: int,
        name: str,
        phone: str,
        email: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
        updated_by: Optional[int] = None
    ) -> bool:
        """
        تحديث بيانات عميل موجود مع التحقق من البيانات.

        Args:
            customer_id: معرف العميل.
            name: الاسم الجديد.
            phone: رقم الهاتف الجديد.
            email: البريد الإلكتروني الجديد.
            address: العنوان الجديد.
            notes: الملاحظات الجديدة.
            updated_by: معرف المستخدم المُعدل.

        Returns:
            True إذا تم التحديث بنجاح.

        Raises:
            ValueError: إذا كان الاسم أو الهاتف فارغين.
        """
        if not name or not name.strip():
            raise ValueError("الاسم مطلوب")
        if not phone or not phone.strip():
            raise ValueError("رقم الهاتف مطلوب")

        affected_rows = self.db_manager.update_customer(
            customer_id, name.strip(), phone.strip(), email, address, notes
        )
        if affected_rows > 0:
            self.db_manager.log_activity(
                updated_by, "تعديل عميل", "customers", customer_id,
                f"تعديل بيانات العميل: {name}"
            )
        return affected_rows > 0

    def delete_customer(self, customer_id: int,
                       deleted_by: Optional[int] = None) -> bool:
        """
        حذف عميل مع تسجيل العملية.

        Args:
            customer_id: معرف العميل.
            deleted_by: معرف المستخدم الحاذف.

        Returns:
            True إذا تم الحذف بنجاح.
        """
        affected_rows = self.db_manager.delete_customer(customer_id)
        if affected_rows > 0:
            self.db_manager.log_activity(
                deleted_by, "حذف عميل", "customers", customer_id,
                f"حذف العميل رقم: {customer_id}"
            )
        return affected_rows > 0
