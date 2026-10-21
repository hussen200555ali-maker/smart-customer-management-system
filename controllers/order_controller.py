# -*- coding: utf-8 -*-
"""
controllers/order_controller.py
--------------------------------
وحدة تحكم إدارة الطلبات (Order Controller).

الإصدار: 2.1
"""

import logging
from typing import List, Optional

from repositories.database import DatabaseManager
from services.order_service import OrderService
from services.customer_service import CustomerService
from services.service_service import ServiceService
from controllers.base_controller import BaseController
from exceptions import RecordNotFoundError, RequiredFieldError, ValidationError

logger = logging.getLogger(__name__)


class OrderController(BaseController):
    """وحدة تحكم الطلبات."""

    VALID_STATUSES = ["pending", "in_progress", "completed", "cancelled"]

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self._order_service = OrderService(db_manager)
        self._customer_service = CustomerService(db_manager)
        self._service_service = ServiceService(db_manager)

    def create_order(self, customer_id: int, notes: Optional[str] = None,
                    created_by: Optional[int] = None) -> int:
        """إنشاء طلب جديد."""
        customer = self._customer_service.get_customer_by_id(customer_id)
        if not customer:
            raise RecordNotFoundError(table="customers", record_id=customer_id)
        order_id = self._order_service.add_order(customer_id, notes, created_by)
        self.logger.info(f"تم إنشاء طلب رقم: {order_id} للعميل: {customer.name}")
        return order_id

    def add_order_detail(self, order_id: int, service_id: int,
                        quantity: int = 1, created_by: Optional[int] = None) -> bool:
        """إضافة خدمة إلى طلب."""
        order = self._order_service.get_order_by_id(order_id)
        if not order:
            raise RecordNotFoundError(table="orders", record_id=order_id)
        service = self._service_service.get_service_by_id(service_id)
        if not service:
            raise RecordNotFoundError(table="services", record_id=service_id)
        success = self._order_service.add_order_detail(order_id, service_id, quantity, created_by)
        if success:
            self.logger.info(f"تم إضافة خدمة '{service.name}' للطلب رقم {order_id}")
        return success

    def update_order_status(self, order_id: int, status: str,
                           updated_by: Optional[int] = None) -> bool:
        """تحديث حالة طلب."""
        if status not in self.VALID_STATUSES:
            raise ValidationError(
                message=f"الحالة '{status}' غير صالحة. المسموحة: {', '.join(self.VALID_STATUSES)}"
            )
        order = self._order_service.get_order_by_id(order_id)
        if not order:
            raise RecordNotFoundError(table="orders", record_id=order_id)
        old_status = order.status
        success = self._order_service.update_order_status(order_id, status, updated_by)
        if success:
            self.logger.info(f"تحديث حالة الطلب {order_id}: {old_status} → {status}")
        return success

    def get_order(self, order_id: int):
        """الحصول على طلب محدد."""
        order = self._order_service.get_order_by_id(order_id)
        if not order:
            raise RecordNotFoundError(table="orders", record_id=order_id)
        return order

    def search_orders(self, status: Optional[str] = None,
                     customer_id: Optional[int] = None) -> List:
        """البحث عن الطلبات."""
        return self._order_service.get_orders(status, customer_id)

    def get_all_orders(self) -> List:
        """الحصول على جميع الطلبات."""
        return self._order_service.get_orders()

    def get_customer_orders(self, customer_id: int) -> List:
        """الحصول على طلبات عميل محدد."""
        customer = self._customer_service.get_customer_by_id(customer_id)
        if not customer:
            raise RecordNotFoundError(table="customers", record_id=customer_id)
        return self._order_service.get_orders(customer_id=customer_id)
