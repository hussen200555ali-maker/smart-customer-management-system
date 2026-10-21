# -*- coding: utf-8 -*-
"""
services/service_service.py
---------------------------
خدمة إدارة الخدمات (Service Business Service).

تُغلف منطق الأعمال المتعلق بالخدمات وفئاتها.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from typing import List, Optional, Dict, Any

from repositories.database import DatabaseManager
from models.service import Service


class ServiceService:
    """
    خدمة إدارة الخدمات.

    مسؤولة عن جميع عمليات الأعمال المتعلقة بالخدمات:
    - إضافة وتعديل وحذف الخدمات
    - البحث والتصفية حسب الفئة
    - التحقق من صحة البيانات

    Args:
        db_manager: كائن مدير قاعدة البيانات.
    """

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة خدمة الخدمات."""
        self.db_manager = db_manager

    def add_service(
        self,
        name: str,
        description: Optional[str] = None,
        price: float = 0.0,
        category_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> int:
        """
        إضافة خدمة جديدة مع التحقق من البيانات.

        Args:
            name: اسم الخدمة (مطلوب).
            description: وصف الخدمة.
            price: سعر الخدمة (مطلوب، أكبر من صفر).
            category_id: معرف الفئة.
            created_by: معرف المستخدم المنشئ.

        Returns:
            معرف الخدمة المُنشأة.

        Raises:
            ValueError: إذا كان الاسم فارغاً أو السعر غير صالح.
        """
        if not name or not name.strip():
            raise ValueError("اسم الخدمة مطلوب")
        if price is None or price <= 0:
            raise ValueError("يجب تحديد سعر صحيح أكبر من صفر")

        result = self.db_manager.insert_service(
            name.strip(), description, float(price), category_id
        )
        if result > 0:
            self.db_manager.log_activity(
                created_by, "إضافة خدمة", "services", result,
                f"إضافة خدمة جديدة: {name}"
            )
        return result

    def get_services(self, search_term: Optional[str] = None,
                    category_id: Optional[int] = None) -> List[Service]:
        """
        الحصول على قائمة الخدمات النشطة مع إمكانية التصفية.

        Args:
            search_term: مصطلح البحث.
            category_id: معرف الفئة للتصفية.

        Returns:
            قائمة بكائنات الخدمات.
        """
        services_data = self.db_manager.get_services(search_term, category_id)
        return [Service.from_dict(s) for s in services_data]

    def get_service_by_id(self, service_id: int) -> Optional[Service]:
        """
        الحصول على خدمة محددة بالمعرف.

        Args:
            service_id: معرف الخدمة.

        Returns:
            كائن الخدمة أو None.
        """
        service_data = self.db_manager.get_service_by_id(service_id)
        if service_data:
            return Service.from_dict(service_data)
        return None

    def update_service(
        self,
        service_id: int,
        name: str,
        description: Optional[str] = None,
        price: float = 0.0,
        category_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> bool:
        """
        تحديث بيانات خدمة موجودة.

        Args:
            service_id: معرف الخدمة.
            name: الاسم الجديد.
            description: الوصف الجديد.
            price: السعر الجديد.
            category_id: معرف الفئة الجديد.
            updated_by: معرف المستخدم المُعدل.

        Returns:
            True إذا تم التحديث بنجاح.
        """
        if not name or not name.strip():
            raise ValueError("اسم الخدمة مطلوب")
        if price is None or price <= 0:
            raise ValueError("يجب تحديد سعر صحيح أكبر من صفر")

        affected_rows = self.db_manager.update_service(
            service_id, name.strip(), description, float(price), category_id
        )
        if affected_rows > 0:
            self.db_manager.log_activity(
                updated_by, "تعديل خدمة", "services", service_id,
                f"تعديل بيانات الخدمة: {name}"
            )
        return affected_rows > 0

    def delete_service(self, service_id: int,
                      deleted_by: Optional[int] = None) -> bool:
        """
        حذف خدمة (إلغاء التفعيل).

        Args:
            service_id: معرف الخدمة.
            deleted_by: معرف المستخدم الحاذف.

        Returns:
            True إذا تم الحذف بنجاح.
        """
        affected_rows = self.db_manager.delete_service(service_id)
        if affected_rows > 0:
            self.db_manager.log_activity(
                deleted_by, "حذف خدمة", "services", service_id,
                f"حذف الخدمة رقم: {service_id}"
            )
        return affected_rows > 0
