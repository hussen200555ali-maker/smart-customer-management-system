# -*- coding: utf-8 -*-
"""
controllers/base_controller.py
-------------------------------
الفئة الأساسية لجميع وحدات التحكم (Base Controller).

توفر وظائف مشتركة لجميع وحدات التحكم مثل التسجيل والتحقق
من البيانات والتعامل مع الأخطاء بشكل موحد.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

import logging
from typing import Any, Dict, Optional

from repositories.database import DatabaseManager


class BaseController:
    """
    الفئة الأساسية التي ترثها جميع وحدات التحكم.

    توفر:
    - مرجع لمدير قاعدة البيانات
    - نظام تسجيل موحد
    - طرق مساعدة للتحقق من البيانات
    - معالجة الأخطاء الموحدة
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        تهيئة وحدة التحكم الأساسية.

        Args:
            db_manager: كائن مدير قاعدة البيانات.
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    def _validate_required_fields(self, data: Dict[str, Any],
                                   required_fields: list) -> None:
        """
        التحقق من وجود جميع الحقول المطلوبة.

        Args:
            data: قاموس البيانات.
            required_fields: قائمة الحقول المطلوبة.

        Raises:
            ValueError: إذا كان أحد الحقول مفقوداً أو فارغاً.
        """
        missing = []
        for field in required_fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field)

        if missing:
            fields_str = "، ".join(missing)
            raise ValueError(f"الحقول التالية مطلوبة: {fields_str}")

    def _log_operation(
        self,
        action: str,
        table_name: str,
        user_id: Optional[int],
        record_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> None:
        """تسجيل عملية في سجل الأنشطة."""
        try:
            self.db_manager.log_activity(
                user_id=user_id,
                action=action,
                table_name=table_name,
                record_id=record_id,
                details=details
            )
        except Exception as e:
            self.logger.error(f"فشل تسجيل العملية: {e}")
