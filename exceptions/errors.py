# -*- coding: utf-8 -*-
"""
exceptions/errors.py
--------------------
جميع الاستثناءات المخصصة لنظام إدارة الخدمات الذكي
.

مُنظمة حسب النطاق:
- أخطاء قاعدة البيانات
- أخطاء التحقق من البيانات
- أخطاء المصادقة والتفويض
- أخطاء نماذج الذكاء الاصطناعي
- أخطاء الملفات

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""


# ══════════════════════════════════════════════
# استثناءات قاعدة البيانات
# ══════════════════════════════════════════════

class DatabaseError(Exception):
    """استثناء أساسي لجميع أخطاء قاعدة البيانات."""
    def __init__(self, message: str = "حدث خطأ في قاعدة البيانات", detail: str = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class DatabaseConnectionError(DatabaseError):
    """يُرفع عند فشل الاتصال بقاعدة البيانات."""
    def __init__(self, detail: str = None):
        super().__init__(message="فشل الاتصال بقاعدة البيانات", detail=detail)


class DatabaseQueryError(DatabaseError):
    """يُرفع عند فشل تنفيذ استعلام SQL."""
    def __init__(self, query: str = "", detail: str = None):
        super().__init__(message="فشل تنفيذ الاستعلام", detail=detail)
        self.query = query


class RecordNotFoundError(DatabaseError):
    """يُرفع عندما لا يتم العثور على سجل محدد."""
    def __init__(self, table: str = "", record_id: int = None):
        self.table = table
        self.record_id = record_id
        msg = f"لم يتم العثور على السجل في جدول {table}"
        if record_id is not None:
            msg += f" بالمعرف {record_id}"
        super().__init__(message=msg)


class DuplicateRecordError(DatabaseError):
    """يُرفع عند محاولة إضافة سجل مكرر."""
    def __init__(self, table: str = "", field: str = "", value: str = ""):
        self.table = table
        self.field = field
        self.value = value
        msg = f"السجل موجود مسبقاً في جدول {table}"
        if field and value:
            msg += f" ({field} = {value})"
        super().__init__(message=msg)


class ForeignKeyViolationError(DatabaseError):
    """يُرفع عند انتهاك قيد المفتاح الأجنبي."""
    def __init__(self, detail: str = None):
        super().__init__(message="لا يمكن تنفيذ العملية بسبب ارتباط بسجلات أخرى", detail=detail)


# ══════════════════════════════════════════════
# استثناءات التحقق من البيانات
# ══════════════════════════════════════════════

class ValidationError(Exception):
    """استثناء أساسي لجميع أخطاء التحقق."""
    def __init__(self, message: str = "بيانات غير صالحة", errors: list = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


class RequiredFieldError(ValidationError):
    """يُرفع عند فقدان حقل مطلوب."""
    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(message=f"الحقل '{field_name}' مطلوب",
                         errors=[{"field": field_name, "error": "required"}])


class InvalidEmailError(ValidationError):
    """يُرفع عند إدخال بريد إلكتروني غير صالح."""
    def __init__(self, email: str):
        self.email = email
        super().__init__(message=f"البريد الإلكتروني '{email}' غير صالح",
                         errors=[{"field": "email", "error": "invalid_format", "value": email}])


class InvalidPhoneError(ValidationError):
    """يُرفع عند إدخال رقم هاتف غير صالح."""
    def __init__(self, phone: str):
        self.phone = phone
        super().__init__(message=f"رقم الهاتف '{phone}' غير صالح",
                         errors=[{"field": "phone", "error": "invalid_format", "value": phone}])


class InvalidPriceError(ValidationError):
    """يُرفع عند إدخال سعر غير صالح."""
    def __init__(self, price):
        self.price = price
        super().__init__(message=f"السعر '{price}' غير صالح. يجب أن يكون رقماً أكبر من صفر",
                         errors=[{"field": "price", "error": "invalid_value", "value": str(price)}])


# ══════════════════════════════════════════════
# استثناءات المصادقة والتفويض
# ══════════════════════════════════════════════

class AuthenticationError(Exception):
    """استثناء أساسي لجميع أخطاء المصادقة."""
    def __init__(self, message: str = "فشل المصادقة"):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    """يُرفع عند إدخال بيانات دخول غير صحيحة."""
    def __init__(self):
        super().__init__(message="اسم المستخدم أو كلمة المرور غير صحيحة")


class AccountLockedError(AuthenticationError):
    """يُرفع عندما يكون الحساب مقفولاً."""
    def __init__(self, remaining_time: int = 0):
        self.remaining_time = remaining_time
        msg = "الحساب مقفل بسبب محاولات فاشلة متعددة"
        if remaining_time > 0:
            msg += f". يرجى المحاولة بعد {remaining_time} ثانية"
        super().__init__(message=msg)


class PermissionDeniedError(AuthenticationError):
    """يُرفع عند عدم وجود صلاحية."""
    def __init__(self, action: str = "", required_role: str = ""):
        self.action = action
        self.required_role = required_role
        msg = "ليس لديك صلاحية لتنفيذ هذه العملية"
        if required_role:
            msg += f". يتطلب دور: {required_role}"
        super().__init__(message=msg)


# ══════════════════════════════════════════════
# استثناءات نماذج الذكاء الاصطناعي
# ══════════════════════════════════════════════

class AIModelError(Exception):
    """استثناء أساسي لأخطاء الذكاء الاصطناعي."""
    def __init__(self, message: str = "حدث خطأ في نموذج الذكاء الاصطناعي"):
        self.message = message
        super().__init__(self.message)


class ModelNotTrainedError(AIModelError):
    """يُرفع عند استخدام نموذج لم يتم تدريبه."""
    def __init__(self):
        super().__init__(message="لا يمكن إجراء التنبؤ. النموذج لم يتم تدريبه بعد.")


class InsufficientDataError(AIModelError):
    """يُرفع عندما تكون البيانات غير كافية."""
    def __init__(self, required: int = 10, available: int = 0):
        self.required = required
        self.available = available
        super().__init__(message=f"البيانات غير كافية. المطلوب: {required}، المتوفر: {available}")


class ModelPerformanceError(AIModelError):
    """يُرفع عندما يكون أداء النموذج منخفضاً."""
    def __init__(self, accuracy: float, threshold: float):
        self.accuracy = accuracy
        self.threshold = threshold
        super().__init__(message=f"أداء النموذج منخفض ({accuracy:.1%}) أقل من العتبة ({threshold:.1%})")


# ══════════════════════════════════════════════
# استثناءات الملفات والبيانات
# ══════════════════════════════════════════════

class FileOperationError(Exception):
    """يُرفع عند فشل عملية على الملفات."""
    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        detail = message
        if file_path:
            detail += f" (الملف: {file_path})"
        super().__init__(detail)


class ExportError(Exception):
    """يُرفع عند فشل عملية التصدير."""
    def __init__(self, format_type: str = "", detail: str = None):
        self.format_type = format_type
        super().__init__(message=f"فشل التصدير بتنسيق {format_type}: {detail or ''}")


class DataImportError(Exception):
    """يُرفع عند فشل عملية الاستيراد."""
    def __init__(self, detail: str = None):
        super().__init__(message=f"فشل الاستيراد: {detail or 'خطأ غير معروف'}")
