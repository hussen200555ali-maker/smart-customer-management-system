# -*- coding: utf-8 -*-
"""
controllers/customer_controller.py
-----------------------------------
وحدة تحكم إدارة العملاء (Customer Controller).

الإصدار: 2.1
"""

import logging
from typing import List, Optional

from repositories.database import DatabaseManager
from services.customer_service import CustomerService
from controllers.base_controller import BaseController
from exceptions import RecordNotFoundError, RequiredFieldError, ValidationError, InvalidEmailError

logger = logging.getLogger(__name__)


class CustomerController(BaseController):
    """وحدة تحكم العملاء."""

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self._service = CustomerService(db_manager)

    def add_customer(self, name: str, phone: str, email: Optional[str] = None,
                    address: Optional[str] = None, notes: Optional[str] = None,
                    created_by: Optional[int] = None) -> int:
        """إضافة عميل جديد مع التحقق."""
        if not name or not name.strip():
            raise RequiredFieldError("الاسم")
        if not phone or not phone.strip():
            raise RequiredFieldError("رقم الهاتف")
        if email and email.strip():
            self._validate_email(email.strip())

        try:
            customer_id = self._service.add_customer(
                name.strip(), phone.strip(),
                email.strip() if email else None,
                address.strip() if address else None,
                notes.strip() if notes else None,
                created_by
            )
            self.logger.info(f"تم إضافة عميل: {name} (المعرف: {customer_id})")
            return customer_id
        except ValueError as e:
            raise ValidationError(str(e))

    def update_customer(self, customer_id: int, name: str, phone: str,
                       email: Optional[str] = None, address: Optional[str] = None,
                       notes: Optional[str] = None, updated_by: Optional[int] = None) -> bool:
        """تعديل بيانات عميل."""
        customer = self._service.get_customer_by_id(customer_id)
        if not customer:
            raise RecordNotFoundError(table="customers", record_id=customer_id)
        if not name or not name.strip():
            raise RequiredFieldError("الاسم")
        if not phone or not phone.strip():
            raise RequiredFieldError("رقم الهاتف")
        if email and email.strip():
            self._validate_email(email.strip())

        success = self._service.update_customer(
            customer_id, name.strip(), phone.strip(),
            email.strip() if email else None,
            address.strip() if address else None,
            notes.strip() if notes else None,
            updated_by
        )
        if success:
            self.logger.info(f"تم تعديل العميل: {name} (المعرف: {customer_id})")
        return success

    def delete_customer(self, customer_id: int, deleted_by: Optional[int] = None) -> bool:
        """حذف عميل."""
        customer = self._service.get_customer_by_id(customer_id)
        if not customer:
            raise RecordNotFoundError(table="customers", record_id=customer_id)
        success = self._service.delete_customer(customer_id, deleted_by)
        if success:
            self.logger.info(f"تم حذف العميل: {customer.name} (المعرف: {customer_id})")
        return success

    def get_customer(self, customer_id: int):
        """الحصول على عميل محدد."""
        customer = self._service.get_customer_by_id(customer_id)
        if not customer:
            raise RecordNotFoundError(table="customers", record_id=customer_id)
        return customer

    def search_customers(self, search_term: Optional[str] = None) -> List:
        """البحث عن العملاء."""
        return self._service.get_customers(search_term)

    def get_all_customers(self) -> List:
        """الحصول على جميع العملاء."""
        return self._service.get_customers()

    @staticmethod
    def _validate_email(email: str) -> None:
        """التحقق من صحة البريد الإلكتروني."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise InvalidEmailError(email)
