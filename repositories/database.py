# -*- coding: utf-8 -*-
"""
repositories/database.py
-------------------------
مدير قاعدة البيانات المركزي (Database Manager) - إصدار MySQL.

يتولى جميع عمليات قاعدة البيانات MySQL بما في ذلك إنشاء الجداول
والفهارس وتنفيذ الاستعلامات مع دعم كامل للغة العربية وتحسينات الأداء
مثل نظام التخزين المؤقت (Cache) وتجمع الاتصالات (Connection Pool).

الإصدار: 4.0 - MySQL
تاريخ التحديث: أبريل 2026
"""

import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib
import secrets
import logging
import time
import os

# استيراد التكوينات
from config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    DB_CHARSET, DB_COLLATION, DB_POOL_ENABLED, DB_POOL_SIZE,
    DB_POOL_MAX_OVERFLOW, DB_TIMEOUT, CACHE_TIMEOUT,
    PASSWORD_HASH_ITERATIONS, PASSWORD_HASH_ALGORITHM,
    get_mysql_config
)


class DatabaseManager:
    """
    فئة مدير قاعدة البيانات المركزي - إصدار MySQL.

    توفر واجهة موحدة لجميع عمليات قاعدة البيانات مع:
    - دعم الصفوف كقواميس (dict)
    - تفعيل المفاتيح الأجنبية (Foreign Keys)
    - نظام تخزين مؤقت لتحسين الأداء
    - تجمع اتصالات (Connection Pool) للوصول المتعدد
    - نظام تسجيل شامل
    - إنشاء تلقائي للجداول والفهارس والبيانات الافتراضية
    - معالجة أخطاء الاتصال مع إعادة المحاولة
    """

    def __init__(self, db_config: Optional[Dict] = None):
        """
        تهيئة مدير قاعدة البيانات MySQL.

        Args:
            db_config: قاموس إعدادات الاتصال (اختياري).
        """
        self.db_config = db_config or get_mysql_config()
        self.cache: Dict[str, Dict] = {}
        self.cache_timeout = CACHE_TIMEOUT
        self.connection_timeout = DB_TIMEOUT
        
        # تجمع الاتصالات
        self._connection_pool = None
        self._pool_enabled = DB_POOL_ENABLED

        # خريطة لربط الاستعلامات بالجداول المتأثرة
        self._query_table_map: Dict[str, str] = {}
        self._build_query_table_map()

        self._setup_logging()
        self._initialize_connection_pool()
        self._initialize_database()

    def _setup_logging(self) -> None:
        """تهيئة نظام التسجيل الخاص بقاعدة البيانات."""
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, f'database_mysql_{datetime.now().strftime("%Y%m%d")}.log')

            self.logger = logging.getLogger('DatabaseManagerMySQL')
            self.logger.setLevel(logging.INFO)

            # إزالة المعالجات السابقة
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        except Exception:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('DatabaseManagerMySQL')

    def _initialize_connection_pool(self) -> None:
        """تهيئة تجمع الاتصالات."""
        if not self._pool_enabled:
            self.logger.info("تجمع الاتصالات معطل - استخدام اتصالات مباشرة")
            return

        try:
            pool_config = {
                'pool_name': 'service_management_pool',
                'pool_size': DB_POOL_SIZE,
                'pool_reset_session': True,
                'host': self.db_config['host'],
                'port': self.db_config['port'],
                'user': self.db_config['user'],
                'password': self.db_config['password'],
                'database': self.db_config['database'],
                'charset': self.db_config['charset'],
                'collation': self.db_config['collation'],
                'autocommit': False,
                'connection_timeout': self.connection_timeout,
            }
            
            self._connection_pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
            self.logger.info(f"تم تهيئة تجمع الاتصالات بنجاح - حجم التجمع: {DB_POOL_SIZE}")
        except MySQLError as e:
            self.logger.error(f"خطأ في تهيئة تجمع الاتصالات: {e}")
            self._pool_enabled = False
            self._connection_pool = None

    def _get_connection(self):
        """
        الحصول على اتصال من التجمع أو إنشاء اتصال جديد.

        Returns:
            كائن اتصال MySQL.
        """
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                if self._pool_enabled and self._connection_pool:
                    conn = self._connection_pool.get_connection()
                else:
                    conn = mysql.connector.connect(**self.db_config)
                
                return conn
            except MySQLError as e:
                self.logger.warning(f"محاولة الاتصال {attempt + 1}/{max_retries} فشلت: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"فشل الاتصال بقاعدة البيانات بعد {max_retries} محاولات")
                    raise ConnectionError(f"فشل الاتصال بقاعدة البيانات: {e}")

    def _build_query_table_map(self) -> None:
        """بناء خريطة تربط أنماط الاستعلامات بالجداول المتأثرة."""
        self._query_table_map = {
            'INSERT INTO customers': 'customers',
            'UPDATE customers': 'customers',
            'DELETE FROM customers': 'customers',
            'INSERT INTO services': 'services',
            'UPDATE services': 'services',
            'DELETE FROM services': 'services',
            'INSERT INTO service_categories': 'service_categories',
            'UPDATE service_categories': 'service_categories',
            'DELETE FROM service_categories': 'service_categories',
            'INSERT INTO orders': 'orders',
            'UPDATE orders': 'orders',
            'DELETE FROM orders': 'orders',
            'INSERT INTO order_details': 'order_details',
            'UPDATE order_details': 'order_details',
            'DELETE FROM order_details': 'order_details',
            'INSERT INTO users': 'users',
            'UPDATE users': 'users',
            'DELETE FROM users': 'users',
            'INSERT INTO activity_log': 'activity_log',
            'UPDATE activity_log': 'activity_log',
        }

    def _invalidate_table_cache(self, table_name: str) -> None:
        """إبطال كاش الاستعلامات المرتبطة بجدول محدد."""
        if not self.cache:
            return

        keys_to_remove = []
        for cache_key in self.cache:
            if table_name in cache_key:
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self.cache[key]

        if keys_to_remove:
            self.logger.debug(f"تم إبطال {len(keys_to_remove)} مدخل كاش للجدول: {table_name}")

    def _detect_affected_tables(self, query: str) -> list:
        """تحديد الجداول المتأثرة باستعلام التحديث."""
        query_upper = query.strip().upper()
        affected = []

        for pattern, table in self._query_table_map.items():
            if pattern.upper() in query_upper:
                if table not in affected:
                    affected.append(table)

        # الارتباطات
        if 'order_details' in affected and 'orders' not in affected:
            affected.append('orders')
        if 'orders' in affected and 'order_details' not in affected:
            affected.append('order_details')
        if 'customers' in affected:
            affected.append('orders')

        return affected

    def test_connection(self) -> Dict[str, Any]:
        """
        اختبار الاتصال بقاعدة البيانات.

        Returns:
            قاموس بنتيجة الاختبار.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            return {
                'success': True,
                'message': 'تم الاتصال بنجاح',
                'server_version': version,
                'database': DB_NAME,
                'host': DB_HOST,
                'pool_enabled': self._pool_enabled,
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'database': DB_NAME,
                'host': DB_HOST,
            }

    def _initialize_database(self) -> None:
        """إنشاء الجداول والفهارس والبيانات الافتراضية."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # ── جدول المستخدمين ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    role ENUM('admin', 'employee', 'viewer') DEFAULT 'employee',
                    is_active TINYINT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # ── جدول العملاء ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(100),
                    address TEXT,
                    notes TEXT,
                    created_by INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # ── جدول فئات الخدمات ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # ── جدول الخدمات ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL,
                    category_id INT,
                    is_active TINYINT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES service_categories(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # ── جدول الطلبات ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
                    total_amount DECIMAL(12, 2) DEFAULT 0,
                    notes TEXT,
                    created_by INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # ── جدول تفاصيل الطلبات ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_details (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    service_id INT NOT NULL,
                    quantity INT DEFAULT 1,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    total_price DECIMAL(12, 2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # ── جدول سجل الأنشطة ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    action VARCHAR(100) NOT NULL,
                    table_name VARCHAR(50),
                    record_id INT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            self._create_indexes(cursor)
            conn.commit()

            self._create_default_admin(conn)
            self._create_default_categories(conn)

            self.logger.info("تم تهيئة قاعدة البيانات MySQL بنجاح")

        except MySQLError as e:
            self.logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
            raise
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def _create_indexes(self, cursor) -> None:
        """إنشاء الفهارس لتحسين أداء الاستعلامات."""
        indexes = [
            "CREATE INDEX idx_users_username ON users(username)",
            "CREATE INDEX idx_users_role ON users(role)",
            "CREATE INDEX idx_users_active ON users(is_active)",
            "CREATE INDEX idx_customers_phone ON customers(phone)",
            "CREATE INDEX idx_customers_email ON customers(email)",
            "CREATE INDEX idx_customers_created_by ON customers(created_by)",
            "CREATE INDEX idx_service_categories_name ON service_categories(name)",
            "CREATE INDEX idx_services_category_id ON services(category_id)",
            "CREATE INDEX idx_services_active ON services(is_active)",
            "CREATE INDEX idx_services_price ON services(price)",
            "CREATE INDEX idx_orders_customer_id ON orders(customer_id)",
            "CREATE INDEX idx_orders_status ON orders(status)",
            "CREATE INDEX idx_orders_created_by ON orders(created_by)",
            "CREATE INDEX idx_orders_created_at ON orders(created_at)",
            "CREATE INDEX idx_order_details_order_id ON order_details(order_id)",
            "CREATE INDEX idx_order_details_service_id ON order_details(service_id)",
            "CREATE INDEX idx_activity_log_user_id ON activity_log(user_id)",
            "CREATE INDEX idx_activity_log_action ON activity_log(action)",
            "CREATE INDEX idx_activity_log_created_at ON activity_log(created_at)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except MySQLError as e:
                if 'Duplicate key name' not in str(e):
                    self.logger.warning(f"خطأ في إنشاء الفهرس: {e}")

    def _create_default_admin(self, conn) -> None:
        """إنشاء مستخدم مدير افتراضي (admin/admin123) إذا لم يكن موجوداً."""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username = 'admin' LIMIT 1"
        )
        admin = cursor.fetchone()
        if admin is None:
            password_hash = self._hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s)
            """, ("admin", password_hash, "المدير العام", "admin"))
            conn.commit()
            self.logger.info("تم إنشاء المستخدم الافتراضي 'admin'")
        elif admin[1] == (
            "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6$"
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ):
            password_hash = self._hash_password("admin123")
            cursor.execute(
                "UPDATE users SET password_hash = %s, "
                "password_changed_at = CURRENT_TIMESTAMP WHERE id = %s",
                (password_hash, admin[0])
            )
            conn.commit()
            self.logger.info("تم إصلاح تجزئة كلمة مرور المدير الافتراضي")

    def _create_default_categories(self, conn) -> None:
        """إضافة فئات خدمات افتراضية إذا كان الجدول فارغاً."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM service_categories")
        if cursor.fetchone()[0] == 0:
            default_categories = [
                ("صيانة", "خدمات الصيانة والإصلاح"),
                ("تركيب", "خدمات التركيب والتشغيل"),
                ("استشارات", "خدمات استشارية وفنية"),
                ("تنظيف", "خدمات التنظيف والتعقيم"),
                ("نقل", "خدمات النقل والتوصيل"),
                ("تصميم", "خدمات التصميم والإبداع"),
            ]
            cursor.executemany(
                "INSERT INTO service_categories (name, description) VALUES (%s, %s)",
                default_categories
            )
            conn.commit()
            self.logger.info("تم إنشاء الفئات الافتراضية")

    # ═══════════════════════════════════════════
    # عمليات كلمة المرور
    # ═══════════════════════════════════════════

    def _hash_password(self, password: str) -> str:
        """تشفير كلمة المرور باستخدام PBKDF2 مع salt عشوائي."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            PASSWORD_HASH_ALGORITHM,
            password.encode('utf-8'),
            salt.encode('utf-8'),
            PASSWORD_HASH_ITERATIONS
        )
        return f"{salt}${pwd_hash.hex()}"

    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """التحقق من صحة كلمة المرور."""
        query = "SELECT * FROM users WHERE username = %s AND is_active = 1"
        result = self.execute_query(query, (username,))
        if not result:
            return None

        user = result[0]
        stored_hash = user['password_hash']
        salt, pwd_hash = stored_hash.split('$')

        new_hash = hashlib.pbkdf2_hmac(
            PASSWORD_HASH_ALGORITHM,
            password.encode('utf-8'),
            salt.encode('utf-8'),
            PASSWORD_HASH_ITERATIONS
        )
        if new_hash.hex() == pwd_hash:
            self.execute_update(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user['id'],)
            )
            return user
        return None

    # ═══════════════════════════════════════════
    # عمليات المستخدمين
    # ═══════════════════════════════════════════

    def add_user(self, username: str, password: str, full_name: str,
                 role: str = 'employee') -> int:
        """إضافة مستخدم جديد."""
        password_hash = self._hash_password(password)
        query = """
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_update(query, (username, password_hash, full_name, role))

    def get_users(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة المستخدمين (بدون كلمات المرور)."""
        query = """
            SELECT id, username, full_name, role, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        """
        return self.execute_query(query)

    # ═══════════════════════════════════════════
    # عمليات العملاء
    # ═══════════════════════════════════════════

    def insert_customer(self, name: str, phone: str, email: str = None,
                       address: str = None, notes: str = None,
                       created_by: int = None) -> int:
        """إضافة عميل جديد."""
        query = """
            INSERT INTO customers (name, phone, email, address, notes, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_update(query, (name, phone, email, address, notes, created_by))

    def get_customers(self, search_term: str = None) -> List[Dict[str, Any]]:
        """الحصول على قائمة العملاء مع إمكانية البحث."""
        if search_term:
            query = """
                SELECT * FROM customers
                WHERE name LIKE %s OR phone LIKE %s OR email LIKE %s
                ORDER BY created_at DESC
            """
            params = (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')
        else:
            query = 'SELECT * FROM customers ORDER BY created_at DESC'
            params = ()
        return self.execute_query(query, params)

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات عميل محدد."""
        query = 'SELECT * FROM customers WHERE id = %s'
        result = self.execute_query(query, (customer_id,))
        return result[0] if result else None

    def update_customer(self, customer_id: int, name: str, phone: str,
                       email: str = None, address: str = None,
                       notes: str = None) -> int:
        """تحديث بيانات عميل."""
        query = """
            UPDATE customers
            SET name = %s, phone = %s, email = %s, address = %s, notes = %s
            WHERE id = %s
        """
        return self.execute_update(query, (name, phone, email, address, notes, customer_id))

    def delete_customer(self, customer_id: int) -> int:
        """حذف عميل."""
        query = 'DELETE FROM customers WHERE id = %s'
        return self.execute_update(query, (customer_id,))

    # ═══════════════════════════════════════════
    # عمليات فئات الخدمات
    # ═══════════════════════════════════════════

    def insert_service_category(self, name: str, description: str = None) -> int:
        """إضافة فئة خدمة جديدة."""
        query = "INSERT INTO service_categories (name, description) VALUES (%s, %s)"
        return self.execute_update(query, (name, description))

    def get_service_categories(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة جميع فئات الخدمات."""
        query = 'SELECT * FROM service_categories ORDER BY name'
        return self.execute_query(query)

    def get_service_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على فئة محددة."""
        query = 'SELECT * FROM service_categories WHERE id = %s'
        result = self.execute_query(query, (category_id,))
        return result[0] if result else None

    def update_service_category(self, category_id: int, name: str,
                                description: str = None) -> int:
        """تحديث بيانات فئة."""
        query = "UPDATE service_categories SET name = %s, description = %s WHERE id = %s"
        return self.execute_update(query, (name, description, category_id))

    def delete_service_category(self, category_id: int) -> int:
        """حذف فئة خدمة."""
        query = 'DELETE FROM service_categories WHERE id = %s'
        return self.execute_update(query, (category_id,))

    # ═══════════════════════════════════════════
    # عمليات الخدمات
    # ═══════════════════════════════════════════

    def insert_service(self, name: str, description: str, price: float,
                      category_id: int = None) -> int:
        """إضافة خدمة جديدة."""
        query = """
            INSERT INTO services (name, description, price, category_id)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_update(query, (name, description, price, category_id))

    def get_services(self, search_term: str = None,
                    category_id: int = None) -> List[Dict[str, Any]]:
        """الحصول على قائمة الخدمات النشطة مع إمكانية التصفية والبحث."""
        query = 'SELECT * FROM services WHERE is_active = 1'
        params = []

        if search_term:
            query += ' AND (name LIKE %s OR description LIKE %s)'
            params.extend([f'%{search_term}%', f'%{search_term}%'])

        if category_id is not None:
            query += ' AND category_id = %s'
            params.append(category_id)

        query += ' ORDER BY created_at DESC'
        return self.execute_query(query, tuple(params))

    def get_service_by_id(self, service_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات خدمة محددة."""
        query = 'SELECT * FROM services WHERE id = %s'
        result = self.execute_query(query, (service_id,))
        return result[0] if result else None

    def update_service(self, service_id: int, name: str, description: str,
                      price: float, category_id: int = None) -> int:
        """تحديث بيانات خدمة."""
        query = """
            UPDATE services
            SET name = %s, description = %s, price = %s, category_id = %s
            WHERE id = %s
        """
        return self.execute_update(query, (name, description, price, category_id, service_id))

    def delete_service(self, service_id: int) -> int:
        """إلغاء تفعيل خدمة (حذف ناعم)."""
        query = 'UPDATE services SET is_active = 0 WHERE id = %s'
        return self.execute_update(query, (service_id,))

    # ═══════════════════════════════════════════
    # عمليات الطلبات
    # ═══════════════════════════════════════════

    def insert_order(self, customer_id: int, notes: str = None,
                    created_by: int = None) -> int:
        """إضافة طلب جديد وإرجاع رقم الطلب."""
        query = """
            INSERT INTO orders (customer_id, notes, created_by)
            VALUES (%s, %s, %s)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (customer_id, notes, created_by))
            conn.commit()
            order_id = cursor.lastrowid
            self.logger.info(f"تم إنشاء طلب جديد رقم: {order_id}")
            return order_id
        finally:
            conn.close()

    def add_order_detail(self, order_id: int, service_id: int,
                        quantity: int, unit_price: float) -> int:
        """إضافة تفاصيل عنصر في الطلب وحساب الإجمالي."""
        total_price = quantity * unit_price
        query = """
            INSERT INTO order_details (order_id, service_id, quantity, unit_price, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """
        result = self.execute_update(query, (order_id, service_id, quantity, unit_price, total_price))

        # تحديث إجمالي الطلب
        self.execute_update("""
            UPDATE orders SET total_amount = (
                SELECT COALESCE(SUM(total_price), 0) FROM order_details WHERE order_id = %s
            )
            WHERE id = %s
        """, (order_id, order_id))

        return result

    def get_orders(self, status: str = None,
                  customer_id: int = None) -> List[Dict[str, Any]]:
        """الحصول على قائمة الطلبات مع معلومات العميل والخدمات."""
        query = """
            SELECT o.*, c.name as customer_name, c.phone as customer_phone,
                   GROUP_CONCAT(CONCAT(s.name, '|', od.quantity, '|', od.unit_price, '|', s.id) SEPARATOR ',') as services_info
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN services s ON od.service_id = s.id
        """
        params = []
        conditions = []

        if status:
            conditions.append('o.status = %s')
            params.append(status)
        if customer_id:
            conditions.append('o.customer_id = %s')
            params.append(customer_id)

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' GROUP BY o.id ORDER BY o.created_at DESC'
        orders = self.execute_query(query, tuple(params))

        # معالجة بيانات الخدمات لكل طلب
        for order in orders:
            if order.get('services_info'):
                services = order['services_info'].split(',')
                order['service_names'] = ', '.join([s.split('|')[0] for s in services if s])
                order['service_ids'] = []
                order['service_quantities'] = []
                for s in services:
                    parts = s.split('|')
                    if len(parts) >= 4:
                        try:
                            order['service_ids'].append(int(parts[3]))
                            order['service_quantities'].append(int(parts[1]))
                        except (ValueError, IndexError):
                            pass
            else:
                order['service_names'] = ''
                order['service_ids'] = []
                order['service_quantities'] = []

        return orders

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات طلب محدد مع تفاصيله."""
        query = """
            SELECT o.*, c.name as customer_name, c.phone as customer_phone,
                   c.email as customer_email, c.address as customer_address
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = %s
        """
        result = self.execute_query(query, (order_id,))
        if result:
            details = self.execute_query("""
                SELECT od.*, s.name as service_name, s.description as service_description
                FROM order_details od
                JOIN services s ON od.service_id = s.id
                WHERE od.order_id = %s
            """, (order_id,))
            result[0]['details'] = details
        return result[0] if result else None

    def update_order_status(self, order_id: int, status: str) -> int:
        """تحديث حالة طلب."""
        query = "UPDATE orders SET status = %s WHERE id = %s"
        return self.execute_update(query, (status, order_id))

    # ═══════════════════════════════════════════
    # الإحصائيات
    # ═══════════════════════════════════════════

    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات شاملة عن النظام."""
        stats = {}

        stats['total_customers'] = self.execute_query(
            'SELECT COUNT(*) as count FROM customers'
        )[0]['count']

        stats['total_services'] = self.execute_query(
            'SELECT COUNT(*) as count FROM services WHERE is_active = 1'
        )[0]['count']

        stats['total_orders'] = self.execute_query(
            'SELECT COUNT(*) as count FROM orders'
        )[0]['count']

        stats['total_revenue'] = self.execute_query("""
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM orders WHERE status = 'completed'
        """)[0]['total']

        status_stats = self.execute_query("""
            SELECT status, COUNT(*) as count FROM orders GROUP BY status
        """)
        stats['orders_by_status'] = {row['status']: row['count'] for row in status_stats}

        stats['popular_services'] = self.execute_query("""
            SELECT s.name, COUNT(od.id) as order_count,
                   COALESCE(SUM(od.total_price), 0) as revenue
            FROM services s
            LEFT JOIN order_details od ON s.id = od.service_id
            WHERE s.is_active = 1
            GROUP BY s.id ORDER BY order_count DESC LIMIT 5
        """)

        stats['monthly_revenue'] = self.execute_query("""
            SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
                   COALESCE(SUM(total_amount), 0) as revenue, COUNT(*) as orders
            FROM orders WHERE status = 'completed'
            GROUP BY month ORDER BY month DESC LIMIT 12
        """)

        stats['recent_orders'] = self.execute_query("""
            SELECT o.id, o.status, o.total_amount, o.created_at,
                   c.name as customer_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            ORDER BY o.created_at DESC LIMIT 10
        """)

        return stats

    # ═══════════════════════════════════════════
    # سجل الأنشطة
    # ═══════════════════════════════════════════

    def log_activity(self, user_id: Optional[int], action: str,
                    table_name: str = None, record_id: int = None,
                    details: str = None) -> None:
        """تسجيل نشاط في سجل الأحداث."""
        query = """
            INSERT INTO activity_log (user_id, action, table_name, record_id, details)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.execute_update(query, (user_id, action, table_name, record_id, details))

    # ═══════════════════════════════════════════
    # عمليات الاستعلام العامة
    # ═══════════════════════════════════════════

    def _get_cache_key(self, query: str, params: tuple) -> str:
        """إنشاء مفتاح cache فريد للاستعلام."""
        return f"{query}_{str(params)}"

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """التحقق من صلاحية مدخل الcache."""
        return time.time() - cache_entry['timestamp'] < self.cache_timeout

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        تنفيذ استعلام SELECT مع دعم التخزين المؤقت.

        Args:
            query: نص استعلام SQL (استخدم %s للمعاملات).
            params: معاملات الاستعلام.

        Returns:
            قائمة من القواميس تمثل نتائج الاستعلام.
        """
        cache_key = self._get_cache_key(query, params)

        if query.strip().upper().startswith('SELECT') and cache_key in self.cache:
            if self._is_cache_valid(self.cache[cache_key]):
                return self.cache[cache_key]['data']
            else:
                del self.cache[cache_key]

        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchall()

            if query.strip().upper().startswith('SELECT'):
                self.cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }

            return result
        except MySQLError as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
            raise
        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        تنفيذ استعلام تحديث/إدراج/حذف.

        Args:
            query: نص استعلام SQL (استخدم %s للمعاملات).
            params: معاملات الاستعلام.

        Returns:
            عدد الصفوف المتأثرة بالعملية أو ID للسجل المُدرج.
        """
        self.logger.info(f"تنفيذ استعلام: {query[:100]}...")
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
            # الحصول على lastrowid للإدراج
            last_id = cursor.lastrowid
            result = cursor.rowcount
            
            self.logger.info(f"عدد الصفوف المتأثرة: {result}, ID: {last_id}")

            # إبطال الكاش
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                affected_tables = self._detect_affected_tables(query)
                if affected_tables:
                    for table in affected_tables:
                        self._invalidate_table_cache(table)
                else:
                    self.cache.clear()

            # إرجاع lastrowid للإدراج، وإلا rowcount
            if query.strip().upper().startswith('INSERT') and last_id:
                return last_id
            return result
        except MySQLError as e:
            conn.rollback()
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
            raise
        finally:
            conn.close()

    def optimize_database(self) -> Dict[str, Any]:
        """
        تحسين قاعدة البيانات MySQL.

        Returns:
            قاموس بنتائج التحسين.
        """
        results = {}
        try:
            self.logger.info("بدء تحسين قاعدة البيانات MySQL...")
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # تحسين جميع الجداول
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"OPTIMIZE TABLE {table_name}")
                self.logger.info(f"تم تحسين الجدول: {table_name}")
            
            # تحديث إحصائيات المحسن
            cursor.execute("ANALYZE TABLE customers, services, orders, order_details, users, activity_log, service_categories")
            
            results['optimize'] = {'success': True, 'tables_optimized': len(tables)}
            results['analyze'] = {'success': True}
            
            # مسح الكاش بعد التحسين
            self.cache.clear()
            
            conn.close()
            self.logger.info("تم تحسين قاعدة البيانات MySQL بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في تحسين قاعدة البيانات: {e}")
            results['error'] = str(e)

        return results

    def close(self):
        """إغلاق تجمع الاتصالات."""
        if self._connection_pool:
            self._connection_pool = None
            self.logger.info("تم إغلاق تجمع الاتصالات")
