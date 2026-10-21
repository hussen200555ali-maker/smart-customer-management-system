# -*- coding: utf-8 -*-
"""
migrate_to_mysql.py
--------------------
سكربت ترحيل البيانات من SQLite إلى MySQL.

يقوم بنقل جميع البيانات من قاعدة SQLite الحالية إلى MySQL.
يدعم:
- المستخدمين
- العملاء
- فئات الخدمات
- الخدمات
- الطلبات وتفاصيلها
- سجل الأنشطة

الإصدار: 4.0
تاريخ التحديث: أبريل 2026
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# استيراد التكوينات
try:
    from config import (
        DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
        DB_CHARSET, DB_COLLATION
    )
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError as e:
    logger.error(f"خطأ في استيراد المكتبات: {e}")
    logger.error("تأكد من تثبيت mysql-connector-python: pip install mysql-connector-python")
    sys.exit(1)


class DataMigrator:
    """فئة ترحيل البيانات من SQLite إلى MySQL."""

    def __init__(self, sqlite_path: str):
        """
        تهيئة المُرحِّل.

        Args:
            sqlite_path: مسار ملف قاعدة SQLite.
        """
        self.sqlite_path = sqlite_path
        self.sqlite_conn = None
        self.mysql_conn = None
        
        # إحصائيات الترحيل
        self.stats = {
            'users': 0,
            'customers': 0,
            'service_categories': 0,
            'services': 0,
            'orders': 0,
            'order_details': 0,
            'activity_log': 0,
        }

    def connect_sqlite(self) -> bool:
        """الاتصال بقاعدة SQLite."""
        try:
            if not os.path.exists(self.sqlite_path):
                logger.error(f"ملف SQLite غير موجود: {self.sqlite_path}")
                return False

            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"تم الاتصال بقاعدة SQLite: {self.sqlite_path}")
            return True

        except sqlite3.Error as e:
            logger.error(f"خطأ في الاتصال بـ SQLite: {e}")
            return False

    def connect_mysql(self) -> bool:
        """الاتصال بقاعدة MySQL."""
        try:
            self.mysql_conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                charset=DB_CHARSET,
                collation=DB_COLLATION,
            )
            
            # التحقق من وجود قاعدة البيانات أو إنشاؤها
            cursor = self.mysql_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET {DB_CHARSET} COLLATE {DB_COLLATION}")
            cursor.execute(f"USE {DB_NAME}")
            cursor.close()
            
            logger.info(f"تم الاتصال بقاعدة MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
            return True

        except MySQLError as e:
            logger.error(f"خطأ في الاتصال بـ MySQL: {e}")
            return False

    def migrate_users(self) -> int:
        """ترحيل المستخدمين."""
        logger.info("بدء ترحيل المستخدمين...")
        
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()

            sqlite_cursor.execute("SELECT * FROM users")
            users = sqlite_cursor.fetchall()

            for user in users:
                try:
                    mysql_cursor.execute("""
                        INSERT INTO users (id, username, password_hash, full_name, role, is_active, created_at, last_login, password_changed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE username=VALUES(username)
                    """, (
                        user['id'],
                        user['username'],
                        user['password_hash'],
                        user['full_name'],
                        user['role'],
                        user['is_active'],
                        user['created_at'],
                        user['last_login'],
                        user.get('password_changed_at', user['created_at'])
                    ))
                    self.stats['users'] += 1
                except MySQLError as e:
                    logger.warning(f"خطأ في ترحيل المستخدم {user['username']}: {e}")

            self.mysql_conn.commit()
            logger.info(f"تم ترحيل {self.stats['users']} مستخدم")
            return self.stats['users']

        except Exception as e:
            logger.error(f"خطأ في ترحيل المستخدمين: {e}")
            return 0

    def migrate_customers(self) -> int:
        """ترحيل العملاء."""
        logger.info("بدء ترحيل العملاء...")
        
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()

            sqlite_cursor.execute("SELECT * FROM customers")
            customers = sqlite_cursor.fetchall()

            for customer in customers:
                try:
                    mysql_cursor.execute("""
                        INSERT INTO customers (id, name, phone, email, address, notes, created_by, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """, (
                        customer['id'],
                        customer['name'],
                        customer['phone'],
                        customer['email'],
                        customer['address'],
                        customer['notes'],
                        customer['created_by'],
                        customer['created_at'],
                        customer['updated_at']
                    ))
                    self.stats['customers'] += 1
                except MySQLError as e:
                    logger.warning(f"خطأ في ترحيل العميل {customer['id']}: {e}")

            self.mysql_conn.commit()
            logger.info(f"تم ترحيل {self.stats['customers']} عميل")
            return self.stats['customers']

        except Exception as e:
            logger.error(f"خطأ في ترحيل العملاء: {e}")
            return 0

    def migrate_service_categories(self) -> int:
        """ترحيل فئات الخدمات."""
        logger.info("بدء ترحيل فئات الخدمات...")
        
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()

            sqlite_cursor.execute("SELECT * FROM service_categories")
            categories = sqlite_cursor.fetchall()

            for category in categories:
                try:
                    mysql_cursor.execute("""
                        INSERT INTO service_categories (id, name, description, created_at)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """, (
                        category['id'],
                        category['name'],
                        category['description'],
                        category['created_at']
                    ))
                    self.stats['service_categories'] += 1
                except MySQLError as e:
                    logger.warning(f"خطأ في ترحيل الفئة {category['id']}: {e}")

            self.mysql_conn.commit()
            logger.info(f"تم ترحيل {self.stats['service_categories']} فئة")
            return self.stats['service_categories']

        except Exception as e:
            logger.error(f"خطأ في ترحيل فئات الخدمات: {e}")
            return 0

    def migrate_services(self) -> int:
        """ترحيل الخدمات."""
        logger.info("بدء ترحيل الخدمات...")
        
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()

            sqlite_cursor.execute("SELECT * FROM services")
            services = sqlite_cursor.fetchall()

            for service in services:
                try:
                    mysql_cursor.execute("""
                        INSERT INTO services (id, name, description, price, category_id, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """, (
                        service['id'],
                        service['name'],
                        service['description'],
                        service['price'],
                        service['category_id'],
                        service['is_active'],
                        service['created_at'],
                        service['updated_at']
                    ))
                    self.stats['services'] += 1
                except MySQLError as e:
                    logger.warning(f"خطأ في ترحيل الخدمة {service['id']}: {e}")

            self.mysql_conn.commit()
            logger.info(f"تم ترحيل {self.stats['services']} خدمة")
            return self.stats['services']

        except Exception as e:
            logger.error(f"خطأ في ترحيل الخدمات: {e}")
            return 0

    def migrate_orders(self) -> int:
        """ترحيل الطلبات."""
        logger.info("بدء ترحيل الطلبات...")
        
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()

            sqlite_cursor.execute("SELECT * FROM orders")
            orders = sqlite_cursor.fetchall()

            for order in orders:
                try:
                    mysql_cursor.execute("""
                        INSERT INTO orders (id, customer_id, status, total_amount, notes, created_by, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE customer_id=VALUES(customer_id)
                    """, (
                        order['id'],
                        order['customer_id'],
                        order['status'],
                        order['total_amount'],
                        order['notes'],
                        order['created_by'],
                        order['created_at'],
                        order['updated_at']
                    ))
                    self.stats['orders'] += 1
                except MySQLError as e:
                    logger.warning(f"خطأ في ترحيل الطلب {order['id']}: {e}")

            self.mysql_conn.commit()
            logger.info(f"تم ترحيل {self.stats['orders']} طلب")
            return self.stats['orders']

        except Exception as e:
            logger.error(f"خطأ في ترحيل الطلبات: {e}")
            return 0

    def migrate_order_details(self) -> int:
        """ترحيل تفاصيل الطلبات."""
        logger.info("بدء ترحيل تفاصيل الطلبات...")
        
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()

            sqlite_cursor.execute("SELECT * FROM order_details")
            details = sqlite_cursor.fetchall()

            for detail in details:
                try:
                    mysql_cursor.execute("""
                        INSERT INTO order_details (id, order_id, service_id, quantity, unit_price, total_price)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE order_id=VALUES(order_id)
                    """, (
                        detail['id'],
                        detail['order_id'],
                        detail['service_id'],
                        detail['quantity'],
                        detail['unit_price'],
                        detail['total_price']
                    ))
                    self.stats['order_details'] += 1
                except MySQLError as e:
                    logger.warning(f"خطأ في ترحيل تفاصيل الطلب {detail['id']}: {e}")

            self.mysql_conn.commit()
            logger.info(f"تم ترحيل {self.stats['order_details']} تفصيل طلب")
            return self.stats['order_details']

        except Exception as e:
            logger.error(f"خطأ في ترحيل تفاصيل الطلبات: {e}")
            return 0

    def migrate_activity_log(self) -> int:
        """ترحيل سجل الأنشطة."""
        logger.info("بدء ترحيل سجل الأنشطة...")
        
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()

            sqlite_cursor.execute("SELECT * FROM activity_log")
            logs = sqlite_cursor.fetchall()

            for log in logs:
                try:
                    mysql_cursor.execute("""
                        INSERT INTO activity_log (id, user_id, action, table_name, record_id, details, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        log['id'],
                        log['user_id'],
                        log['action'],
                        log['table_name'],
                        log['record_id'],
                        log['details'],
                        log['created_at']
                    ))
                    self.stats['activity_log'] += 1
                except MySQLError as e:
                    logger.warning(f"خطأ في ترحيل سجل النشاط {log['id']}: {e}")

            self.mysql_conn.commit()
            logger.info(f"تم ترحيل {self.stats['activity_log']} سجل نشاط")
            return self.stats['activity_log']

        except Exception as e:
            logger.error(f"خطأ في ترحيل سجل الأنشطة: {e}")
            return 0

    def run_migration(self) -> dict:
        """
        تنفيذ الترحيل الكامل.

        Returns:
            قاموس بإحصائيات الترحيل.
        """
        logger.info("=" * 60)
        logger.info("بدء عملية الترحيل من SQLite إلى MySQL")
        logger.info("=" * 60)

        # الاتصال بقواعد البيانات
        if not self.connect_sqlite():
            return self.stats
        if not self.connect_mysql():
            return self.stats

        # تنفيذ الترحيل بالترتيب الصحيح (مراعاة المفاتيح الأجنبية)
        self.migrate_users()
        self.migrate_service_categories()
        self.migrate_services()
        self.migrate_customers()
        self.migrate_orders()
        self.migrate_order_details()
        self.migrate_activity_log()

        # إغلاق الاتصالات
        self.close()

        # عرض الملخص
        logger.info("=" * 60)
        logger.info("ملخص الترحيل:")
        logger.info(f"  - المستخدمين: {self.stats['users']}")
        logger.info(f"  - العملاء: {self.stats['customers']}")
        logger.info(f"  - فئات الخدمات: {self.stats['service_categories']}")
        logger.info(f"  - الخدمات: {self.stats['services']}")
        logger.info(f"  - الطلبات: {self.stats['orders']}")
        logger.info(f"  - تفاصيل الطلبات: {self.stats['order_details']}")
        logger.info(f"  - سجل الأنشطة: {self.stats['activity_log']}")
        logger.info("=" * 60)

        total = sum(self.stats.values())
        logger.info(f"إجمالي السجلات المُرحَّلة: {total}")

        return self.stats

    def close(self):
        """إغلاق الاتصالات."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.mysql_conn:
            self.mysql_conn.close()
        logger.info("تم إغلاق الاتصالات")


def main():
    """نقطة الدخول الرئيسية."""
    # التحقق من وجود مسار ملف SQLite
    if len(sys.argv) > 1:
        sqlite_path = sys.argv[1]
    else:
        # البحث عن ملف قاعدة البيانات الافتراضي
        default_path = os.path.join(os.path.dirname(__file__), "service_management.db")
        if os.path.exists(default_path):
            sqlite_path = default_path
        else:
            print("استخدام: python migrate_to_mysql.py [مسح_ملف_SQLite]")
            print(f"أو تأكد من وجود ملف {default_path}")
            sys.exit(1)

    # تنفيذ الترحيل
    migrator = DataMigrator(sqlite_path)
    stats = migrator.run_migration()

    # التحقق من نجاح الترحيل
    if sum(stats.values()) > 0:
        print("\n✅ تم الترحيل بنجاح!")
        print("يمكنك الآن تشغيل النظام باستخدام MySQL.")
    else:
        print("\n❌ فشل الترحيل!")
        sys.exit(1)


if __name__ == "__main__":
    main()
