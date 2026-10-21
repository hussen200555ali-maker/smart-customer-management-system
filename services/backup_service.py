# -*- coding: utf-8 -*-
"""
services/backup_service.py
--------------------------
خدمة النسخ الاحتياطي لقاعدة بيانات MySQL.

توفر وظائف النسخ الاحتياطي التلقائي واليدوي باستخدام mysqldump
مع ضغط الملفات والحفاظ على آخر نسخ احتياطية.

الإصدار: 4.0 - MySQL
تاريخ التحديث: أبريل 2026
"""

import os
import zipfile
import subprocess
import logging
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any

from config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    BACKUP_DIR, BACKUP_MAX_COPIES,
    BACKUP_AUTO_ENABLED, BACKUP_AUTO_INTERVAL_HOURS
)
from exceptions import FileOperationError

logger = logging.getLogger(__name__)


class BackupService:
    """
    خدمة النسخ الاحتياطي لـ MySQL.

    توفر:
    - نسخ احتياطي يدوي باستخدام mysqldump
    - نسخ احتياطي تلقائي مجدول
    - استعادة من نسخة احتياطية
    - حذف النسخ القديمة تلقائياً
    - ضغط الملفات باستخدام zipfile
    """

    def __init__(self, db_name: str = None, backup_dir: str = None):
        """
        تهيئة خدمة النسخ الاحتياطي.

        Args:
            db_name: اسم قاعدة البيانات.
            backup_dir: مجلد حفظ النسخ الاحتياطية.
        """
        self.db_host = DB_HOST
        self.db_port = DB_PORT
        self.db_name = db_name or DB_NAME
        self.db_user = DB_USER
        self.db_password = DB_PASSWORD
        self.backup_dir = backup_dir or BACKUP_DIR
        self.max_copies = BACKUP_MAX_COPIES
        self._auto_backup_timer: Optional[threading.Timer] = None
        self._auto_backup_enabled = BACKUP_AUTO_ENABLED
        self._auto_backup_interval = BACKUP_AUTO_INTERVAL_HOURS * 3600
        self._next_backup_time: Optional[datetime] = None

        # إنشاء مجلد النسخ الاحتياطية
        os.makedirs(self.backup_dir, exist_ok=True)

        logger.info("تم تهيئة خدمة النسخ الاحتياطي MySQL بنجاح")

    # ═══════════════════════════════════════════
    # عمليات النسخ الاحتياطي
    # ═══════════════════════════════════════════

    def create_backup(self, backup_type: str = "يدوي") -> str:
        """
        إنشاء نسخة احتياطية جديدة باستخدام mysqldump.

        Args:
            backup_type: نوع النسخة ('يدوي' أو 'تلقائي').

        Returns:
            مسار ملف النسخة الاحتياطية.

        Raises:
            FileOperationError: إذا فشل إنشاء النسخة.
        """
        try:
            # إنشاء اسم الملف
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            logger.info(f"بدء إنشاء نسخة احتياطية: {backup_filename} (النوع: {backup_type})")

            # إنشاء ملف SQL باستخدام mysqldump
            sql_content = self._create_mysqldump()

            # إنشاء ملف ZIP مضغوط
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # إضافة ملف SQL
                sql_filename = f"{self.db_name}_{timestamp}.sql"
                zipf.writestr(sql_filename, sql_content)

                # إضافة ملف البيانات الوصفية
                metadata = self._create_metadata(backup_type)
                zipf.writestr("backup_metadata.txt", metadata)

            # التحقق من نجاح إنشاء الملف
            file_size = os.path.getsize(backup_path)
            logger.info(f"تم إنشاء النسخة الاحتياطية بنجاح: {backup_filename} (الحجم: {self._format_size(file_size)})")

            # تنظيف النسخ القديمة
            self._cleanup_old_backups()

            # تسجيل العملية
            self._log_backup_operation(backup_path, backup_type, "إنشاء")

            return backup_path

        except FileOperationError:
            raise
        except Exception as e:
            logger.error(f"فشل إنشاء النسخة الاحتياطية: {e}")
            raise FileOperationError(
                message=f"فشل إنشاء النسخة الاحتياطية: {str(e)}",
                file_path=self.backup_dir
            )

    def _create_mysqldump(self) -> str:
        """
        إنشاء محتوى SQL باستخدام mysqldump أو برمجياً.

        Returns:
            محتوى ملف SQL.
        """
        # محاولة استخدام mysqldump أولاً
        mysqldump_path = self._find_mysqldump()
        
        if mysqldump_path:
            try:
                cmd = [
                    mysqldump_path,
                    f"--host={self.db_host}",
                    f"--port={self.db_port}",
                    f"--user={self.db_user}",
                    f"--password={self.db_password}",
                    "--single-transaction",
                    "--routines",
                    "--triggers",
                    "--add-drop-table",
                    "--complete-insert",
                    self.db_name
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.warning(f"mysqldump فشل: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.warning("انتهت مهلة mysqldump")
            except Exception as e:
                logger.warning(f"خطأ في mysqldump: {e}")

        # إذا فشل mysqldump، إنشاء نسخة برمجياً
        return self._create_programmatic_backup()

    def _find_mysqldump(self) -> Optional[str]:
        """
        البحث عن مسار mysqldump.

        Returns:
            مسار mysqldump أو None.
        """
        # مسارات محتملة لـ mysqldump
        possible_paths = [
            "mysqldump",  # في PATH
            "/usr/bin/mysqldump",  # Linux
            "/usr/local/bin/mysqldump",  # macOS
            "/opt/lampp/bin/mysqldump",  # XAMPP Linux
            "C:\\xampp\\mysql\\bin\\mysqldump.exe",  # XAMPP Windows
            "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysqldump.exe",
            "C:\\Program Files\\MySQL\\MySQL Server 5.7\\bin\\mysqldump.exe",
        ]

        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except Exception:
                continue

        return None

    def _create_programmatic_backup(self) -> str:
        """
        إنشاء نسخة احتياطية برمجياً باستخدام Python.

        Returns:
            محتوى ملف SQL.
        """
        import mysql.connector
        
        sql_lines = [
            f"-- MySQL Backup",
            f"-- Database: {self.db_name}",
            f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"--",
            f"SET NAMES utf8mb4;",
            f"SET FOREIGN_KEY_CHECKS = 0;",
            "",
        ]

        try:
            conn = mysql.connector.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # الحصول على قائمة الجداول
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                # هيكل الجدول
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table = cursor.fetchone()[1]
                sql_lines.append(f"\n-- Table: {table}")
                sql_lines.append(f"DROP TABLE IF EXISTS `{table}`;")
                sql_lines.append(f"{create_table};")

                # بيانات الجدول
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                
                if rows:
                    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                    columns = [col[0] for col in cursor.fetchall()]
                    columns_str = ", ".join([f"`{col}`" for col in columns])
                    
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                val_str = str(val).replace("\\", "\\\\").replace("'", "\\'")
                                values.append(f"'{val_str}'")
                        
                        values_str = ", ".join(values)
                        sql_lines.append(f"INSERT INTO `{table}` ({columns_str}) VALUES ({values_str});")

            sql_lines.append("\nSET FOREIGN_KEY_CHECKS = 1;")
            
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"خطأ في النسخ الاحتياطي البرمجي: {e}")
            raise

        return "\n".join(sql_lines)

    def restore_backup(self, backup_path: str) -> bool:
        """
        استعادة قاعدة البيانات من نسخة احتياطية.

        Args:
            backup_path: مسار ملف النسخة الاحتياطية.

        Returns:
            True إذا نجحت الاستعادة.

        Raises:
            FileOperationError: إذا فشلت الاستعادة.
        """
        try:
            if not os.path.exists(backup_path):
                raise FileOperationError(
                    message="ملف النسخة الاحتياطية غير موجود",
                    file_path=backup_path
                )

            if not zipfile.is_zipfile(backup_path):
                raise FileOperationError(
                    message="ملف النسخة الاحتياطية تالف أو ليس بتنسيق ZIP",
                    file_path=backup_path
                )

            logger.info(f"بدء استعادة من نسخة احتياطية: {os.path.basename(backup_path)}")

            # إنشاء نسخة احتياطية للحالة الحالية
            try:
                self.create_backup(backup_type="قبل_الاستعادة")
            except Exception:
                pass

            # استخراج ملف SQL
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                sql_files = [f for f in zipf.namelist() if f.endswith('.sql')]
                
                if not sql_files:
                    raise FileOperationError(
                        message="لا يوجد ملف SQL في النسخة الاحتياطية",
                        file_path=backup_path
                    )

                sql_content = zipf.read(sql_files[0]).decode('utf-8')

            # تنفيذ الاستعادة
            self._restore_from_sql(sql_content)

            logger.info("تمت استعادة قاعدة البيانات بنجاح")
            self._log_backup_operation(backup_path, "يدوي", "استعادة")

            return True

        except FileOperationError:
            raise
        except Exception as e:
            logger.error(f"فشل استعادة النسخة الاحتياطية: {e}")
            raise FileOperationError(
                message=f"فشل استعادة النسخة الاحتياطية: {str(e)}",
                file_path=backup_path
            )

    def _restore_from_sql(self, sql_content: str) -> bool:
        """
        استعادة قاعدة البيانات من محتوى SQL.

        Args:
            sql_content: محتوى ملف SQL.

        Returns:
            True إذا نجحت الاستعادة.
        """
        import mysql.connector
        
        # محاولة استخدام mysql client
        mysql_path = self._find_mysql_client()
        
        if mysql_path:
            try:
                # إنشاء ملف مؤقت
                temp_sql = os.path.join(self.backup_dir, "temp_restore.sql")
                with open(temp_sql, 'w', encoding='utf-8') as f:
                    f.write(sql_content)

                cmd = [
                    mysql_path,
                    f"--host={self.db_host}",
                    f"--port={self.db_port}",
                    f"--user={self.db_user}",
                    f"--password={self.db_password}",
                    self.db_name
                ]

                with open(temp_sql, 'r', encoding='utf-8') as f:
                    result = subprocess.run(cmd, stdin=f, capture_output=True, timeout=300)

                os.remove(temp_sql)

                if result.returncode == 0:
                    return True
                else:
                    logger.warning(f"mysql client فشل: {result.stderr}")

            except Exception as e:
                logger.warning(f"خطأ في mysql client: {e}")

        # استعادة برمجية
        return self._restore_programmatically(sql_content)

    def _find_mysql_client(self) -> Optional[str]:
        """البحث عن مسار mysql client."""
        possible_paths = [
            "mysql",
            "/usr/bin/mysql",
            "/opt/lampp/bin/mysql",
            "C:\\xampp\\mysql\\bin\\mysql.exe",
        ]

        for path in possible_paths:
            try:
                subprocess.run([path, "--version"], capture_output=True, timeout=5)
                return path
            except Exception:
                continue

        return None

    def _restore_programmatically(self, sql_content: str) -> bool:
        """استعادة برمجية من محتوى SQL."""
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        try:
            # تقسيم الاستعلامات
            statements = sql_content.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logger.warning(f"خطأ في تنفيذ استعلام: {e}")
            
            conn.commit()
            return True
            
        finally:
            cursor.close()
            conn.close()

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة النسخ الاحتياطية المتاحة."""
        backups = []

        try:
            if not os.path.exists(self.backup_dir):
                return backups

            for filename in sorted(os.listdir(self.backup_dir), reverse=True):
                if not filename.endswith('.zip'):
                    continue

                filepath = os.path.join(self.backup_dir, filename)

                try:
                    backup_info = {
                        "filename": filename,
                        "path": filepath,
                        "size": os.path.getsize(filepath),
                        "size_formatted": self._format_size(os.path.getsize(filepath)),
                        "created_at": datetime.fromtimestamp(
                            os.path.getctime(filepath)
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "تلقائي"
                    }

                    # قراءة نوع النسخة من البيانات الوصفية
                    try:
                        with zipfile.ZipFile(filepath, 'r') as zipf:
                            if 'backup_metadata.txt' in zipf.namelist():
                                metadata = zipf.read('backup_metadata.txt').decode('utf-8')
                                for line in metadata.split('\n'):
                                    if line.startswith('type='):
                                        backup_info["type"] = line.split('=')[1].strip()
                    except Exception:
                        pass

                    backups.append(backup_info)

                except Exception as e:
                    logger.warning(f"تعذرت قراءة معلومات النسخة {filename}: {e}")
                    continue

            return backups

        except Exception as e:
            logger.error(f"خطأ في الحصول على قائمة النسخ الاحتياطية: {e}")
            return backups

    def delete_backup(self, backup_path: str) -> bool:
        """حذف نسخة احتياطية."""
        try:
            if not os.path.exists(backup_path):
                raise FileOperationError(
                    message="ملف النسخة الاحتياطية غير موجود",
                    file_path=backup_path
                )

            os.remove(backup_path)
            logger.info(f"تم حذف النسخة الاحتياطية: {os.path.basename(backup_path)}")

            self._log_backup_operation(backup_path, "يدوي", "حذف")

            return True

        except FileOperationError:
            raise
        except Exception as e:
            logger.error(f"فشل حذف النسخة الاحتياطية: {e}")
            raise FileOperationError(
                message=f"فشل حذف النسخة الاحتياطية: {str(e)}",
                file_path=backup_path
            )

    # ═══════════════════════════════════════════
    # النسخ الاحتياطي التلقائي
    # ═══════════════════════════════════════════

    def schedule_auto_backup(self, interval_hours: float = None) -> None:
        """جدولة النسخ الاحتياطي التلقائي."""
        self.stop_auto_backup()

        if interval_hours is not None:
            self._auto_backup_interval = interval_hours * 3600

        self._auto_backup_enabled = True
        self._next_backup_time = datetime.now()

        logger.info(f"تم تفعيل النسخ الاحتياطي التلقائي كل {self._auto_backup_interval / 3600:.1f} ساعة")

        self._start_auto_backup_timer()

    def stop_auto_backup(self) -> None:
        """إيقاف النسخ الاحتياطي التلقائي."""
        self._auto_backup_enabled = False
        self._next_backup_time = None

        if self._auto_backup_timer is not None:
            self._auto_backup_timer.cancel()
            self._auto_backup_timer = None
            logger.info("تم إيقاف النسخ الاحتياطي التلقائي")

    def is_auto_backup_enabled(self) -> bool:
        """التحقق مما إذا كان النسخ الاحتياطي التلقائي مفعلاً."""
        return self._auto_backup_enabled

    def get_next_backup_time(self) -> Optional[str]:
        """الحصول على وقت النسخة الاحتياطية التالية."""
        return self._next_backup_time.strftime("%Y-%m-%d %H:%M:%S") if self._next_backup_time else None

    # ═══════════════════════════════════════════
    # طرق مساعدة داخلية
    # ═══════════════════════════════════════════

    def _start_auto_backup_timer(self) -> None:
        """بدء مؤقت النسخ الاحتياطي التلقائي."""
        if not self._auto_backup_enabled:
            return

        self._auto_backup_timer = threading.Timer(
            self._auto_backup_interval,
            self._auto_backup_callback
        )
        self._auto_backup_timer.daemon = True
        self._auto_backup_timer.start()

        self._next_backup_time = datetime.fromtimestamp(
            datetime.now().timestamp() + self._auto_backup_interval
        )

    def _auto_backup_callback(self) -> None:
        """دالة الاستدعاء للنسخ الاحتياطي التلقائي."""
        try:
            if self._auto_backup_enabled:
                logger.info("بدء النسخ الاحتياطي التلقائي المجدول")
                self.create_backup(backup_type="تلقائي")

                if self._auto_backup_enabled:
                    self._start_auto_backup_timer()

        except Exception as e:
            logger.error(f"فشل النسخ الاحتياطي التلقائي: {e}")
            if self._auto_backup_enabled:
                self._start_auto_backup_timer()

    def _cleanup_old_backups(self) -> int:
        """تنظيف النسخ الاحتياطية القديمة."""
        deleted_count = 0

        try:
            if not os.path.exists(self.backup_dir):
                return 0

            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".zip"):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_files.append((filepath, os.path.getctime(filepath)))

            backup_files.sort(key=lambda x: x[1], reverse=True)

            for filepath, _ in backup_files[self.max_copies:]:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"تم حذف نسخة احتياطية قديمة: {os.path.basename(filepath)}")
                except Exception as e:
                    logger.warning(f"فشل حذف النسخة القديمة: {e}")

        except Exception as e:
            logger.error(f"خطأ في تنظيف النسخ القديمة: {e}")

        return deleted_count

    def _create_metadata(self, backup_type: str) -> str:
        """إنشاء ملف البيانات الوصفية للنسخة الاحتياطية."""
        metadata_lines = [
            f"timestamp={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"type={backup_type}",
            f"database={self.db_name}",
            f"host={self.db_host}",
            f"app_version=4.0-mysql",
        ]
        return "\n".join(metadata_lines)

    def _log_backup_operation(self, backup_path: str, backup_type: str, operation: str) -> None:
        """تسجيل عملية النسخ الاحتياطي."""
        try:
            logger.info(
                f"عملية نسخ احتياطي - {operation}: "
                f"{os.path.basename(backup_path)} (النوع: {backup_type})"
            )
        except Exception as e:
            logger.error(f"فشل تسجيل عملية النسخ الاحتياطي: {e}")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """تنسيق حجم الملف بشكل مقروء."""
        if size_bytes == 0:
            return "0 بايت"

        units = ["بايت", "كيلوبايت", "ميغابايت", "غيغابايت"]
        unit_index = 0
        size = float(size_bytes)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"
