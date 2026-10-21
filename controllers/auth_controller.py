# -*- coding: utf-8 -*-
"""
controllers/auth_controller.py
------------------------------
وحدة تحكم المصادقة والتفويض (Authentication Controller).

مسؤولة عن تسجيل الدخول والتحقق من الهوية وإدارة الصلاحيات.
تشمل سياسات كلمات المرور القوية، تتبع محاولات الدخول،
ومنع الهجمات بالقوة الغاشمة مع تراجع أُسي.

الإصدار: 2.2
تاريخ التحديث: أبريل 2026
"""

import logging
import time
import string
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from repositories.database import DatabaseManager
from controllers.base_controller import BaseController
from exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    PermissionDeniedError,
    RequiredFieldError,
    ValidationError,
)
from config import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_UPPERCASE,
    PASSWORD_REQUIRE_LOWERCASE,
    PASSWORD_REQUIRE_DIGIT,
    PASSWORD_REQUIRE_SPECIAL,
    PASSWORD_EXPIRY_DAYS,
)

logger = logging.getLogger(__name__)


class AuthController(BaseController):
    """
    وحدة تحكم المصادقة.

    توفر:
    - تسجيل الدخول والتحقق من البيانات
    - سياسة كلمات مرور قوية (أحرف كبيرة/صغيرة، أرقام، رموز خاصة)
    - تتبع محاولات الدخول الفاشلة مع تراجع أُسي
    - قفل الحسابات بعد محاولات فاشلة متعددة
    - التحقق من انتهاء صلاحية كلمة المرور (90 يوماً)
    - تسجيل سجل الدخول
    - التحقق من الصلاحيات
    - تشفير البيانات الحساسة
    """

    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # ثوان (5 دقائق)
    BACKOFF_BASE = 2  # قاعدة التراجع الأُسي

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة وحدة تحكم المصادقة."""
        super().__init__(db_manager)
        self._failed_attempts: Dict[str, int] = {}
        self._locked_accounts: Dict[str, float] = {}
        self._failed_identifiers: Dict[str, Dict[str, Any]] = {}  # تعقب بالمعرف
        self._current_user: Optional[Dict[str, Any]] = None

    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات المستخدم الحالي."""
        return self._current_user

    @property
    def is_logged_in(self) -> bool:
        """التحقق من وجود مستخدم مسجل الدخول."""
        return self._current_user is not None

    @property
    def current_user_id(self) -> Optional[int]:
        """الحصول على معرف المستخدم الحالي."""
        return self._current_user["id"] if self._current_user else None

    @property
    def current_user_role(self) -> Optional[str]:
        """الحصول على دور المستخدم الحالي."""
        return self._current_user["role"] if self._current_user else None

    @property
    def is_admin(self) -> bool:
        """التحقق مما إذا كان المستخدم الحالي مديراً."""
        return self.current_user_role == "admin"

    # ═══════════════════════════════════════════
    # تسجيل الدخول والخروج
    # ═══════════════════════════════════════════

    def login(self, username: str, password: str,
              identifier: str = None) -> Dict[str, Any]:
        """
        تسجيل الدخول بالتحقق من صحة البيانات.

        Args:
            username: اسم المستخدم.
            password: كلمة المرور.
            identifier: معرف إضافي لتعقب المحاولات (مثل عنوان IP).

        Returns:
            قاموس بيانات المستخدم عند النجاح.

        Raises:
            RequiredFieldError: إذا كانت الحقول فارغة.
            AccountLockedError: إذا كان الحساب مقفولاً.
            InvalidCredentialsError: إذا كانت البيانات غير صحيحة.
            ValidationError: إذا انتهت صلاحية كلمة المرور.
        """
        if not username or not username.strip():
            raise RequiredFieldError("اسم المستخدم")
        if not password or not password.strip():
            raise RequiredFieldError("كلمة المرور")

        username = username.strip()
        client_id = identifier or username
        self._check_account_lock(client_id)
        self._check_exponential_backoff(client_id)

        user = self.db_manager.verify_password(username, password.strip())

        if user:
            # إعادة تعيين عدادات المحاولات الفاشلة
            self._failed_attempts.pop(username, None)
            self._failed_identifiers.pop(client_id, None)
            self._locked_accounts.pop(username, None)

            # التحقق من انتهاء صلاحية كلمة المرور
            self._check_password_expiry(user)

            self._current_user = user

            self._log_operation(
                action="تسجيل دخول",
                table_name="users",
                user_id=user["id"],
                record_id=user["id"],
                details=f"تسجيل دخول ناجح: {username}"
            )
            self.logger.info(f"تسجيل دخول ناجح: {username}")

            # تسجيل في سجل الدخول
            self._record_login_history(user["id"], True)

            return user
        else:
            self._handle_failed_login(username, client_id)
            self._record_login_history(None, False, username=username)
            raise InvalidCredentialsError()

    def logout(self) -> None:
        """تسجيل الخروج وتنظيف الجلسة."""
        if self._current_user:
            self._log_operation(
                action="تسجيل خروج",
                table_name="users",
                user_id=self.current_user_id,
                record_id=self.current_user_id,
                details="تسجيل خروج من النظام"
            )
            self._current_user = None

    # ═══════════════════════════════════════════
    # سياسة كلمات المرور
    # ═══════════════════════════════════════════

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        التحقق من قوة كلمة المرور.

        السياسة:
        - الحد الأدنى 8 أحرف
        - حرف كبير واحد على الأقل
        - حرف صغير واحد على الأقل
        - رقم واحد على الأقل
        - رمز خاص واحد على الأقل

        Args:
            password: كلمة المرور المراد التحقق منها.

        Returns:
            tuple (صالح: bool, رسالة: str)
        """
        if not password or len(password) < PASSWORD_MIN_LENGTH:
            return (
                False,
                f"كلمة المرور يجب أن تكون {PASSWORD_MIN_LENGTH} أحرف على الأقل"
            )

        errors = []

        if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("حرف كبير واحد على الأقل")

        if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("حرف صغير واحد على الأقل")

        if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            errors.append("رقم واحد على الأقل")

        if PASSWORD_REQUIRE_SPECIAL:
            special_chars = set(string.punctuation)
            if not any(c in special_chars for c in password):
                errors.append("رمز خاص واحد على الأقل (!@#$%^&*)")

        if errors:
            return (False, "يجب أن تحتوي على: " + "، ".join(errors))

        # التحقق من أن كلمة المرور ليست ضعيفة شائعة
        common_passwords = [
            'password', '12345678', 'qwerty', 'admin123',
            'letmein', 'welcome', 'monkey', 'master',
            'dragon', 'login', 'princess', 'abc123'
        ]
        if password.lower() in common_passwords:
            return (False, "كلمة المرور ضعيفة جداً وشائعة، يرجى اختيار كلمة أقوى")

        return (True, "كلمة المرور قوية")

    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        تغيير كلمة المرور للمستخدم الحالي.

        Args:
            old_password: كلمة المرور الحالية.
            new_password: كلمة المرور الجديدة.

        Returns:
            True إذا تم التغيير بنجاح.

        Raises:
            RequiredFieldError: إذا كانت الحقول فارغة.
            InvalidCredentialsError: إذا كانت كلمة المرور الحالية غير صحيحة.
            ValidationError: إذا كانت كلمة المرور الجديدة ضعيفة.
        """
        if not old_password:
            raise RequiredFieldError("كلمة المرور الحالية")
        if not new_password:
            raise RequiredFieldError("كلمة المرور الجديدة")

        if not self._current_user:
            raise InvalidCredentialsError()

        # التحقق من كلمة المرور الحالية
        user = self.db_manager.verify_password(
            self._current_user['username'], old_password
        )
        if not user:
            self.logger.warning(
                f"محاولة تغيير كلمة مرور فاشلة: {self._current_user['username']}"
            )
            raise InvalidCredentialsError()

        # التحقق من قوة كلمة المرور الجديدة
        is_valid, message = self.validate_password_strength(new_password)
        if not is_valid:
            raise ValidationError(message=message)

        # التحقق من أن كلمة المرور الجديدة مختلفة عن القديمة
        if old_password == new_password:
            raise ValidationError(message="كلمة المرور الجديدة يجب أن تكون مختلفة عن الحالية")

        # تحديث كلمة المرور في قاعدة البيانات
        password_hash = self.db_manager._hash_password(new_password)
        self.db_manager.execute_update(
            """
            UPDATE users
            SET password_hash = ?, password_changed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (password_hash, self._current_user['id'])
        )

        # تحديث بيانات المستخدم الحالي
        self._current_user['password_changed_at'] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # تسجيل العملية
        self._log_operation(
            action="تغيير كلمة المرور",
            table_name="users",
            user_id=self.current_user_id,
            record_id=self.current_user_id,
            details="تم تغيير كلمة المرور بنجاح"
        )
        self.logger.info(f"تم تغيير كلمة المرور: {self._current_user['username']}")

        return True

    # ═══════════════════════════════════════════
    # سجل الدخول
    # ═══════════════════════════════════════════

    def get_login_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        الحصول على سجل الدخول للمستخدم.

        Args:
            user_id: معرف المستخدم.

        Returns:
            قائمة سجلات الدخول.
        """
        try:
            query = """
                SELECT id, action, details, created_at
                FROM activity_log
                WHERE user_id = ? AND (action = 'تسجيل دخول' OR action = 'محاولة دخول فاشلة')
                ORDER BY created_at DESC
                LIMIT 50
            """
            return self.db_manager.execute_query(query, (user_id,))
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سجل الدخول: {e}")
            return []

    def _record_login_history(self, user_id: Optional[int], success: bool,
                              username: str = None) -> None:
        """
        تسجيل محاولة الدخول في سجل الأنشطة.

        Args:
            user_id: معرف المستخدم (None إذا فشل الدخول).
            success: هل نجح الدخول.
            username: اسم المستخدم (للمحاولات الفاشلة).
        """
        action = "تسجيل دخول" if success else "محاولة دخول فاشلة"
        details = (
            "تسجيل دخول ناجح"
            if success
            else f"محاولة دخول فاشلة: {username or 'مجهول'}"
        )
        try:
            self.db_manager.log_activity(
                user_id=user_id,
                action=action,
                table_name="users",
                details=details
            )
        except Exception as e:
            self.logger.error(f"فشل تسجيل محاولة الدخول: {e}")

    # ═══════════════════════════════════════════
    # التحقق من الصلاحيات
    # ═══════════════════════════════════════════

    def has_permission(self, required_role: str) -> bool:
        """
        التحقق مما إذا كان المستخدم يمتلك الدور المطلوب.

        Args:
            required_role: الدور المطلوب.

        Returns:
            True إذا كان المستخدم يمتلك الصلاحية.
        """
        if not self.is_logged_in:
            return False

        role_hierarchy = {"admin": 3, "employee": 2, "viewer": 1}
        user_level = role_hierarchy.get(self.current_user_role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        return user_level >= required_level

    def get_all_users(self) -> list:
        """
        الحصول على قائمة المستخدمين (للمدراء فقط).

        Returns:
            قائمة بيانات المستخدمين.

        Raises:
            PermissionDeniedError: إذا لم يكن المستخدم مديراً.
        """
        if not self.is_admin:
            raise PermissionDeniedError(
                action="عرض المستخدمين",
                required_role="admin"
            )
        return self.db_manager.get_users()

    # ═══════════════════════════════════════════
    # الحماية من الهجمات
    # ═══════════════════════════════════════════

    def _check_account_lock(self, client_id: str) -> None:
        """التحقق من قفل الحساب مع دعم المعرف الإضافي."""
        if client_id in self._locked_accounts:
            lock_time = self._locked_accounts[client_id]
            elapsed = time.time() - lock_time
            remaining = self.LOCKOUT_DURATION - elapsed

            if remaining > 0:
                raise AccountLockedError(remaining_time=int(remaining))
            else:
                self._locked_accounts.pop(client_id, None)
                self._failed_attempts.pop(client_id, None)
                self._failed_identifiers.pop(client_id, None)

    def _check_exponential_backoff(self, client_id: str) -> None:
        """
        التحقق من التراجع الأُسي (مزيد من التأخير مع كل محاولة فاشلة).

        Args:
            client_id: معرف العميل.

        Raises:
            AccountLockedError: إذا كان لا يزال في فترة التراجع.
        """
        if client_id in self._failed_identifiers:
            info = self._failed_identifiers[client_id]
            attempts = info.get('attempts', 0)
            last_attempt_time = info.get('last_attempt', 0)

            # حساب مدة الانتظار بالتراجع الأُسي: base^attempts
            wait_seconds = (self.BACKOFF_BASE ** min(attempts, 8))  # حد أقصى 256 ثانية

            elapsed = time.time() - last_attempt_time
            remaining = wait_seconds - elapsed

            if remaining > 0:
                raise AccountLockedError(remaining_time=int(remaining))

    def _handle_failed_login(self, username: str, client_id: str) -> None:
        """معالجة محاولة الدخول الفاشلة مع تراجع أُسي."""
        # تحديث عداد المحاولات الفاشلة
        self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
        attempts = self._failed_attempts[username]

        # تحديث معلومات التعقب بالمعرف
        if client_id not in self._failed_identifiers:
            self._failed_identifiers[client_id] = {
                'attempts': 0,
                'last_attempt': 0
            }
        self._failed_identifiers[client_id]['attempts'] += 1
        self._failed_identifiers[client_id]['last_attempt'] = time.time()

        self.logger.warning(
            f"محاولة دخول فاشلة: {username} ({attempts}/{self.MAX_LOGIN_ATTEMPTS})"
            f" - المعرف: {client_id}"
        )

        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            self._locked_accounts[username] = time.time()
            self._locked_accounts[client_id] = time.time()
            self.logger.error(f"تم قفل الحساب: {username}")

    def _check_password_expiry(self, user: Dict[str, Any]) -> None:
        """
        التحقق من انتهاء صلاحية كلمة المرور.

        Args:
            user: بيانات المستخدم.

        Raises:
            ValidationError: إذا انتهت صلاحية كلمة المرور.
        """
        password_changed_at = user.get('password_changed_at')
        if not password_changed_at:
            # إذا لم يكن هناك تاريخ تغيير، نعتبر الحساب قديماً
            return

        try:
            # تحليل تاريخ التغيير
            if password_changed_at is not None:
                if isinstance(password_changed_at, datetime):
                    changed_date = password_changed_at
                elif isinstance(password_changed_at, str):
                    # Try ISO format first, then regular format
                    try:
                        changed_date = datetime.fromisoformat(password_changed_at)
                    except ValueError:
                        changed_date = datetime.strptime(
                            password_changed_at, "%Y-%m-%d %H:%M:%S"
                        )
                else:
                    changed_date = datetime.fromisoformat(str(password_changed_at))
            else:
                changed_date = None

            # حساب الأيام المتبقية
            expiry_date = changed_date + timedelta(days=PASSWORD_EXPIRY_DAYS)
            remaining_days = (expiry_date - datetime.now()).days

            if remaining_days <= 0:
                self.logger.warning(
                    f"انتهت صلاحية كلمة مرور المستخدم: {user['username']}"
                )
                # لا نمنع الدخول ولكن نسجل تحذيراً
                # يمكن للمستخدم تغيير كلمة المرور بعد الدخول
            elif remaining_days <= 14:
                self.logger.info(
                    f"كلمة مرور المستخدم {user['username']} ستنتهي خلال "
                    f"{remaining_days} يوم"
                )

        except (ValueError, TypeError) as e:
            self.logger.warning(f"خطأ في تحليل تاريخ تغيير كلمة المرور: {e}")

    def get_password_status(self, user_id: int = None) -> Dict[str, Any]:
        """
        الحصول على حالة كلمة المرور للمستخدم.

        Args:
            user_id: معرف المستخدم (الافتراضي: المستخدم الحالي).

        Returns:
            قاموس يحتوي على حالة كلمة المرور.
        """
        target_user = self._current_user
        if user_id and self.is_admin:
            users = self.db_manager.execute_query(
                "SELECT id, password_changed_at, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            if users:
                target_user = users[0]

        if not target_user:
            return {"status": "unknown"}

        password_changed_at = target_user.get('password_changed_at')
        created_at = target_user.get('created_at')

        # استخدام تاريخ الإنشاء إذا لم يكن هناك تاريخ تغيير
        reference_date = password_changed_at or created_at

        if not reference_date:
            return {"status": "unknown", "days_remaining": None}

        try:
            if reference_date is not None:
                if isinstance(reference_date, datetime):
                    ref_date = reference_date
                elif isinstance(reference_date, str):
                    try:
                        ref_date = datetime.fromisoformat(reference_date)
                    except ValueError:
                        ref_date = datetime.strptime(reference_date, "%Y-%m-%d %H:%M:%S")
                else:
                    ref_date = datetime.fromisoformat(str(reference_date))
            else:
                ref_date = None

            expiry_date = ref_date + timedelta(days=PASSWORD_EXPIRY_DAYS)
            remaining_days = (expiry_date - datetime.now()).days

            if remaining_days <= 0:
                status = "expired"
            elif remaining_days <= 14:
                status = "expiring_soon"
            else:
                status = "valid"

            return {
                "status": status,
                "days_remaining": remaining_days,
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "last_changed": ref_date.strftime("%Y-%m-%d")
            }

        except (ValueError, TypeError) as e:
            self.logger.error(f"خطأ في حساب حالة كلمة المرور: {e}")
            return {"status": "error"}
