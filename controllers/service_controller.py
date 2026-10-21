# -*- coding: utf-8 -*-
"""
controllers/service_controller.py
----------------------------------
وحدة تحكم إدارة الخدمات والفئات (Service Controller).

الإصدار: 2.1
"""

import logging
from typing import List, Optional

from repositories.database import DatabaseManager
from services.service_service import ServiceService
from controllers.base_controller import BaseController
from exceptions import RecordNotFoundError, RequiredFieldError, InvalidPriceError

logger = logging.getLogger(__name__)


class ServiceController(BaseController):
    """وحدة تحكم الخدمات والفئات."""

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self._service = ServiceService(db_manager)

    def add_service(self, name: str, description: str = "", price: float = 0,
                   category_id: Optional[int] = None, created_by: Optional[int] = None) -> int:
        """إضافة خدمة جديدة."""
        if not name or not name.strip():
            raise RequiredFieldError("اسم الخدمة")
        if price is None:
            raise RequiredFieldError("السعر")
        try:
            price_val = float(price)
            if price_val <= 0:
                raise InvalidPriceError(price)
        except (ValueError, TypeError):
            raise InvalidPriceError(price)

        sid = self._service.add_service(
            name.strip(), description.strip() if description else None,
            price_val, category_id, created_by
        )
        self.logger.info(f"تم إضافة خدمة: {name} (المعرف: {sid})")
        return sid

    def update_service(self, service_id: int, name: str, description: str = "",
                      price: float = 0, category_id: Optional[int] = None,
                      updated_by: Optional[int] = None) -> bool:
        """تعديل خدمة."""
        service = self._service.get_service_by_id(service_id)
        if not service:
            raise RecordNotFoundError(table="services", record_id=service_id)
        if not name or not name.strip():
            raise RequiredFieldError("اسم الخدمة")
        try:
            price_val = float(price)
            if price_val <= 0:
                raise InvalidPriceError(price)
        except (ValueError, TypeError):
            raise InvalidPriceError(price)

        success = self._service.update_service(
            service_id, name.strip(), description.strip() if description else None,
            price_val, category_id, updated_by
        )
        if success:
            self.logger.info(f"تم تعديل الخدمة: {name} (المعرف: {service_id})")
        return success

    def delete_service(self, service_id: int, deleted_by: Optional[int] = None) -> bool:
        """حذف خدمة."""
        service = self._service.get_service_by_id(service_id)
        if not service:
            raise RecordNotFoundError(table="services", record_id=service_id)
        success = self._service.delete_service(service_id, deleted_by)
        if success:
            self.logger.info(f"تم حذف الخدمة: {service.name} (المعرف: {service_id})")
        return success

    def get_service(self, service_id: int):
        """الحصول على خدمة محددة."""
        service = self._service.get_service_by_id(service_id)
        if not service:
            raise RecordNotFoundError(table="services", record_id=service_id)
        return service

    def search_services(self, search_term: Optional[str] = None,
                       category_id: Optional[int] = None) -> List:
        """البحث عن الخدمات."""
        return self._service.get_services(search_term, category_id)

    def get_all_services(self) -> List:
        """الحصول على جميع الخدمات النشطة."""
        return self._service.get_services()

    def get_all_categories(self) -> List:
        """الحصول على جميع الفئات."""
        return self.db_manager.get_service_categories()

    def add_category(self, name: str, description: Optional[str] = None) -> int:
        """إضافة فئة جديدة."""
        if not name or not name.strip():
            raise RequiredFieldError("اسم الفئة")
        cid = self.db_manager.insert_service_category(name.strip(), description)
        self.logger.info(f"تم إضافة فئة: {name} (المعرف: {cid})")
        return cid

    def update_category(self, category_id: int, name: str,
                       description: Optional[str] = None) -> bool:
        """تعديل فئة."""
        category = self.db_manager.get_service_category_by_id(category_id)
        if not category:
            raise RecordNotFoundError(table="service_categories", record_id=category_id)
        if not name or not name.strip():
            raise RequiredFieldError("اسم الفئة")
        return self.db_manager.update_service_category(category_id, name.strip(), description)

    def delete_category(self, category_id: int) -> bool:
        """حذف فئة."""
        category = self.db_manager.get_service_category_by_id(category_id)
        if not category:
            raise RecordNotFoundError(table="service_categories", record_id=category_id)
        return self.db_manager.delete_service_category(category_id)
