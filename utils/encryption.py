# -*- coding: utf-8 -*-
"""
utils/encryption.py
-------------------
أدوات التشفير المتقدمة لنظام إدارة الخدمات الذكي
.

توفر تشفير AES-256 للحساسة باستخدام Fernet من مكتبة cryptography.
يتم إنشاء مفتاح التشفير من كلمة مرور رئيسية باستخدام PBKDF2.

الإصدار: 2.2
تاريخ التحديث: أبريل 2026
"""

import os
import base64
import hashlib
import logging
from typing import Optional

from config import ENCRYPTION_KEY_FILE
from exceptions import FileOperationError

logger = logging.getLogger(__name__)

# المحدد الافتراضي لكلمة المرور الرئيسية
_DEFAULT_MASTER_PASSWORD = "ServiceMgmt2026!@#"


class FieldEncryption:
    """
    فئة تشفير الحقول الحساسة.

    توفر:
    - تشفير AES-256 باستخدام Fernet
    - توليد مفتاح من كلمة مرور رئيسية (PBKDF2)
    - تشفير/فك تشفير النصوص العادية
    - تشفير/فك تشفير أرقام الهواتف بشكل محسن
    - تخزين المفتاح بشكل آمن في ملف
    - البيانات المشفرة بصيغة base64 آمنة لتخزينها في قاعدة البيانات
    """

    def __init__(self, master_password: str = None):
        """
        تهيئة خدمة التشفير.

        Args:
            master_password: كلمة المرور الرئيسية (تُستخدم القيمة الافتراضية إذا لم تُحدد).
        """
        self._master_password = master_password or _DEFAULT_MASTER_PASSWORD
        self._fernet = None

        try:
            self._initialize_encryption()
            logger.info("تم تهيئة خدمة التشفير بنجاح")
        except Exception as e:
            logger.error(f"فشل تهيئة خدمة التشفير: {e}")
            raise

    # ═══════════════════════════════════════════
    # التهيئة وإدارة المفاتيح
    # ═══════════════════════════════════════════

    def _initialize_encryption(self) -> None:
        """تهيئة التشفير بتحميل أو إنشاء مفتاح."""
        key = self._load_or_create_key()
        self._fernet = self._create_fernet(key)

    def _load_or_create_key(self) -> bytes:
        """
        تحميل مفتاح التشفير من الملف أو إنشاء مفتاح جديد.

        Returns:
            مفتاح التشفير (32 بايت).
        """
        try:
            if os.path.exists(ENCRYPTION_KEY_FILE):
                # تحميل المفتاح الموجود
                with open(ENCRYPTION_KEY_FILE, 'rb') as f:
                    key = f.read()
                logger.info("تم تحميل مفتاح التشفير من الملف")
                return key
            else:
                # إنشاء مفتاح جديد
                key = self._derive_key(self._master_password)
                self._save_key(key)
                logger.info("تم إنشاء مفتاح تشفير جديد")
                return key

        except Exception as e:
            logger.error(f"خطأ في تحميل/إنشاء مفتاح التشفير: {e}")
            raise FileOperationError(
                message=f"خطأ في إدارة مفتاح التشفير: {str(e)}",
                file_path=ENCRYPTION_KEY_FILE
            )

    def _derive_key(self, password: str, salt: bytes = None) -> bytes:
        """
        اشتقاق مفتاح تشفير من كلمة المرور باستخدام PBKDF2.

        Args:
            password: كلمة المرور الرئيسية.
            salt: القيمة الملحية (يتم إنشاؤها عشوائياً إذا لم تُحدد).

        Returns:
            مفتاح تشفير (32 بايت).
        """
        if salt is None:
            salt = os.urandom(16)

        # اشتقاق مفتاح 32 بايت (256 بت) مناسب لـ Fernet
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations=100000,
            dklen=32
        )
        return key

    def _create_fernet(self, key: bytes):
        """
        إنشاء كائن Fernet من المفتاح.

        Args:
            key: مفتاح التشفير (32 بايت).

        Returns:
            كائن Fernet للتشفير/فك التشفير.
        """
        from cryptography.fernet import Fernet
        # Fernet يتطلب مفتاح 32 بايت مشفر بـ base64
        fernet_key = base64.urlsafe_b64encode(key)
        return Fernet(fernet_key)

    def _save_key(self, key: bytes) -> None:
        """
        حفظ مفتاح التشفير في ملف آمن.

        Args:
            key: مفتاح التشفير.
        """
        try:
            # ضبط صلاحيات الملف (قراءة/كتابة للمالك فقط)
            with open(ENCRYPTION_KEY_FILE, 'wb') as f:
                f.write(key)

            # محاولة ضبط صلاحيات الملف (أنظمة Unix)
            try:
                os.chmod(ENCRYPTION_KEY_FILE, 0o600)
            except (OSError, AttributeError):
                pass

            logger.info("تم حفظ مفتاح التشفير بشكل آمن")

        except Exception as e:
            logger.error(f"خطأ في حفظ مفتاح التشفير: {e}")
            raise FileOperationError(
                message=f"فشل حفظ مفتاح التشفير: {str(e)}",
                file_path=ENCRYPTION_KEY_FILE
            )

    # ═══════════════════════════════════════════
    # عمليات التشفير وفك التشفير
    # ═══════════════════════════════════════════

    def encrypt(self, plaintext: str) -> str:
        """
        تشفير نص عادي.

        Args:
            plaintext: النص المراد تشفيره.

        Returns:
            سلسلة base64 تمثل النص المشفر (آمنة لتخزينها في قاعدة البيانات).
        """
        if not plaintext:
            return ""

        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"فشل تشفير النص: {e}")
            raise ValueError(f"فشل تشفير البيانات: {str(e)}")

    def decrypt(self, ciphertext: str) -> str:
        """
        فك تشفير نص مشفر.

        Args:
            ciphertext: النص المشفر (سلسلة base64).

        Returns:
            النص الأصلي.
        """
        if not ciphertext:
            return ""

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"فشل فك تشفير النص: {e}")
            raise ValueError(f"فشل فك تشفير البيانات: {str(e)}")

    def encrypt_phone(self, phone: str) -> str:
        """
        تشفير رقم هاتف.

        يقوم بتنظيف رقم الهاتف من المسافات والرموز الزائدة قبل التشفير.

        Args:
            phone: رقم الهاتف.

        Returns:
            سلسلة base64 تمثل رقم الهاتف المشفر.
        """
        if not phone:
            return ""

        try:
            # تنظيف رقم الهاتف - إزالة المسافات والشرطات
            cleaned_phone = ''.join(c for c in phone if c.isdigit() or c.startswith('+'))
            return self.encrypt(cleaned_phone)

        except Exception as e:
            logger.error(f"فشل تشفير رقم الهاتف: {e}")
            raise ValueError(f"فشل تشفير رقم الهاتف: {str(e)}")

    def decrypt_phone(self, ciphertext: str) -> str:
        """
        فك تشفير رقم هاتف.

        Args:
            ciphertext: رقم الهاتف المشفر.

        Returns:
            رقم الهاتف الأصلي.
        """
        if not ciphertext:
            return ""

        try:
            return self.decrypt(ciphertext)

        except Exception as e:
            logger.error(f"فشل فك تشفير رقم الهاتف: {e}")
            raise ValueError(f"فشل فك تشفير رقم الهاتف: {str(e)}")

    def is_encrypted(self, value: str) -> bool:
        """
        التحقق مما إذا كانت القيمة مشفرة.

        Args:
            value: القيمة المراد فحصها.

        Returns:
            True إذا كانت القيمة تبدو مشفرة.
        """
        if not value or len(value) < 20:
            return False

        try:
            # محاولة فك التشفير للتحقق
            base64.urlsafe_b64decode(value.encode('utf-8'))
            return True
        except Exception:
            return False

    def change_master_password(self, new_password: str) -> bool:
        """
        تغيير كلمة المرور الرئيسية وإعادة إنشاء المفتاح.

        ملاحظة: تغيير كلمة المرور الرئيسية يتطلب إعادة تشفير جميع البيانات المشفرة.

        Args:
            new_password: كلمة المرور الجديدة.

        Returns:
            True إذا تم التغيير بنجاح.
        """
        try:
            # إنشاء مفتاح جديد من كلمة المرور الجديدة
            new_key = self._derive_key(new_password)
            self._save_key(new_key)

            # إعادة تهيئة Fernet بالمفتاح الجديد
            self._fernet = self._create_fernet(new_key)
            self._master_password = new_password

            logger.info("تم تغيير كلمة المرور الرئيسية بنجاح")
            return True

        except Exception as e:
            logger.error(f"فشل تغيير كلمة المرور الرئيسية: {e}")
            return False
