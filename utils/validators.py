# -*- coding: utf-8 -*-
"""
utils/validators.py
--------------------
دوال التحقق من صحة البيانات (Validation Utilities).

الإصدار: 2.1
"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    التحقق من صحة تنسيق البريد الإلكتروني.

    Args:
        email: البريد الإلكتروني المراد التحقق منه.

    Returns:
        True إذا كان التنسيق صحيحاً.
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    التحقق من صحة رقم الهاتف.

    Args:
        phone: رقم الهاتف المراد التحقق منه.

    Returns:
        True إذا كان الرقم صحيحاً (7-15 رقماً).
    """
    if not phone:
        return False
    digits = re.sub(r'[^\d]', '', phone)
    return 7 <= len(digits) <= 15


def validate_price(price) -> bool:
    """
    التحقق من صحة السعر.

    Args:
        price: القيمة المراد التحقق منها.

    Returns:
        True إذا كان السعر رقماً أكبر من صفر.
    """
    try:
        return float(price) > 0
    except (ValueError, TypeError):
        return False
