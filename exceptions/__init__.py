# -*- coding: utf-8 -*-
"""
exceptions/__init__.py
----------------------
نظام معالجة الأخطاء المركزي لنظام إدارة الخدمات الذكي
.

يحتوي على استثناءات مخصصة لكل نوع من الأخطاء في النظام.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from exceptions.errors import (
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
    RecordNotFoundError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    ValidationError,
    RequiredFieldError,
    InvalidEmailError,
    InvalidPhoneError,
    InvalidPriceError,
    AuthenticationError,
    InvalidCredentialsError,
    AccountLockedError,
    PermissionDeniedError,
    AIModelError,
    ModelNotTrainedError,
    InsufficientDataError,
    ModelPerformanceError,
    FileOperationError,
    ExportError,
    DataImportError,
)

__all__ = [
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseQueryError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "ForeignKeyViolationError",
    "ValidationError",
    "RequiredFieldError",
    "InvalidEmailError",
    "InvalidPhoneError",
    "InvalidPriceError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "AccountLockedError",
    "PermissionDeniedError",
    "AIModelError",
    "ModelNotTrainedError",
    "InsufficientDataError",
    "ModelPerformanceError",
    "FileOperationError",
    "ExportError",
    "DataImportError",
]
