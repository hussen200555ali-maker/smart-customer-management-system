# -*- coding: utf-8 -*-
"""
services/order_service.py
-------------------------
خدمة إدارة الطلبات (Order Business Service).

تُغلف منطق الأعمال المتعلق بالطلبات بما في ذلك إنشاء الطلبات
وإدارة التفاصيل وتحديث الحالات.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from repositories.database import DatabaseManager
from models.order import Order


class OrderService:
    """
    خدمة إدارة الطلبات.

    مسؤولة عن جميع عمليات الأعمال المتعلقة بالطلبات:
    - إنشاء طلب جديد مع تفاصيل متعددة
    - إضافة خدمات إلى الطلب
    - تحديث حالة الطلب
    - البحث والاستعلام عن الطلبات

    Args:
        db_manager: كائن مدير قاعدة البيانات.
    """

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة خدمة الطلبات."""
        self.db_manager = db_manager

    def add_order(
        self,
        customer_id: int,
        notes: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> int:
        """
        إنشاء طلب جديد.

        Args:
            customer_id: معرف العميل.
            notes: ملاحظات على الطلب.
            created_by: معرف المستخدم المنشئ.

        Returns:
            معرف الطلب المُنشأ.

        Raises:
            ValueError: إذا لم يتم تحديد معرف العميل.
        """
        if not customer_id:
            raise ValueError("معرف العميل مطلوب")

        result = self.db_manager.insert_order(customer_id, notes, created_by)
        if result > 0:
            self.db_manager.log_activity(
                created_by, "إضافة طلب", "orders", result,
                f"إضافة طلب جديد للعميل رقم: {customer_id}"
            )
        return result

    def add_order_detail(
        self,
        order_id: int,
        service_id: int,
        quantity: int = 1,
        created_by: Optional[int] = None
    ) -> bool:
        """
        إضافة خدمة إلى طلب موجود.

        Args:
            order_id: معرف الطلب.
            service_id: معرف الخدمة.
            quantity: الكمية المطلوبة.
            created_by: معرف المستخدم.

        Returns:
            True إذا تمت الإضافة بنجاح.

        Raises:
            ValueError: إذا كانت الخدمة غير موجودة.
        """
        service = self.db_manager.get_service_by_id(service_id)
        if not service:
            raise ValueError("الخدمة غير موجودة")

        result = self.db_manager.add_order_detail(
            order_id, service_id, quantity, service['price']
        )

        if result > 0 and created_by:
            self.db_manager.log_activity(
                created_by, "إضافة خدمة للطلب", "order_details", None,
                f"إضافة خدمة {service['name']} للطلب رقم {order_id}"
            )

        return result > 0

    def get_orders(self, status: Optional[str] = None,
                  customer_id: Optional[int] = None) -> List[Order]:
        """
        الحصول على قائمة الطلبات مع إمكانية التصفية.

        Args:
            status: تصفية حسب الحالة.
            customer_id: تصفية حسب العميل.

        Returns:
            قائمة بكائنات الطلبات.
        """
        orders_data = self.db_manager.get_orders(status, customer_id)
        return [self._dict_to_order(o) for o in orders_data]

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        الحصول على بيانات طلب محدد مع تفاصيله.

        Args:
            order_id: معرف الطلب.

        Returns:
            كائن الطلب مع التفاصيل أو None.
        """
        order_data = self.db_manager.get_order_by_id(order_id)
        if order_data:
            return self._dict_to_order(order_data)
        return None

    def update_order_status(
        self,
        order_id: int,
        status: str,
        updated_by: Optional[int] = None
    ) -> bool:
        """
        تحديث حالة طلب.

        Args:
            order_id: معرف الطلب.
            status: الحالة الجديدة.
            updated_by: معرف المستخدم المُحدث.

        Returns:
            True إذا تم التحديث بنجاح.

        Raises:
            ValueError: إذا كانت الحالة فارغة.
        """
        if not status:
            raise ValueError("الحالة مطلوبة")

        affected_rows = self.db_manager.update_order_status(order_id, status)
        if affected_rows > 0:
            self.db_manager.log_activity(
                updated_by, "تحديث حالة الطلب", "orders", order_id,
                f"تحديث حالة الطلب إلى: {status}"
            )
        return affected_rows > 0

    def _dict_to_order(self, data: Dict[str, Any]) -> Order:
        """تحويل القاموس إلى كائن طلب."""
        order = Order(
            id=data['id'],
            customer_id=data['customer_id'],
            status=data['status'],
            total_amount=data.get('total_amount', 0),
            notes=data.get('notes'),
            created_at=data['created_at'] if isinstance(data.get('created_at'), datetime) else datetime.fromisoformat(str(data['created_at'])) if data.get('created_at') else None,
            updated_at=data['updated_at'] if isinstance(data.get('updated_at'), datetime) else datetime.fromisoformat(str(data['updated_at'])) if data.get('updated_at') else None,
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            customer_email=data.get('customer_email'),
            service_names=data.get('service_names', ''),
            service_ids=data.get('service_ids', []),
            service_quantities=data.get('service_quantities', []),
            details=data.get('details', []),
        )
        return order
