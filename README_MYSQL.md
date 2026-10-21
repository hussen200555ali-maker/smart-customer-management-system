# نظام إدارة العملاء الذكي - Smart Customer Management System
 والذكاء الاصطناعي - إصدار MySQL

## الإصدار 4.0 - دعم MySQL عبر XAMPP

---

## ✅ التعديلات المُنجزة

تم تعديل المشروع الأصلي للعمل مع MySQL بدلاً من SQLite، مع الحفاظ التام على:

- ✅ جميع العمليات تعمل بنفس الطريقة
- ✅ الواجهات بدون أي تغيير
- ✅ التصميم الحالي للواجهات
- ✅ نفس أسماء الملفات والفئات

### الملفات المُعدَّلة:

| الملف | التعديل |
|-------|---------|
| `config.py` | إضافة إعدادات الاتصال بـ MySQL |
| `repositories/database.py` | تغيير من SQLite إلى MySQL |
| `services/backup_service.py` | دعم النسخ الاحتياطي عبر mysqldump |
| `requirements.txt` | إضافة mysql-connector-python |

### الملفات الجديدة:

| الملف | الوصف |
|-------|-------|
| `init_db.sql` | سكربت إنشاء قاعدة البيانات |
| `migrate_to_mysql.py` | أداة ترحيل البيانات من SQLite |

---

## 🚀 خطوات التثبيت

### الخطوة 1: تثبيت XAMPP

#### Windows:
1. تحميل XAMPP من: https://www.apachefriends.org/
2. تثبيت XAMPP في المسار الافتراضي: `C:\xampp`
3. تشغيل XAMPP Control Panel
4. بدء خدمة **MySQL** بالنقر على "Start"

#### Linux:
```bash
sudo chmod +x xampp-linux-x64-*.run
sudo ./xampp-linux-x64-*.run
sudo /opt/lampp/lampp start
```

### الخطوة 2: إنشاء قاعدة البيانات

#### الطريقة 1: عبر phpMyAdmin
1. فتح المتصفح على: http://localhost/phpmyadmin
2. إنشاء قاعدة بيانات جديدة باسم: `service_management`
3. اختيار الترميز: `utf8mb4_unicode_ci`
4. استيراد ملف `init_db.sql`

#### الطريقة 2: عبر سطر الأوامر
```bash
# Windows
C:\xampp\mysql\bin\mysql -u root < init_db.sql

# Linux
sudo /opt/lampp/bin/mysql -u root < init_db.sql
```

### الخطوة 3: تثبيت مكتبات Python

```bash
pip install -r requirements.txt
```

### الخطوة 4: تهيئة الإعدادات

الإعدادات الافتراضية في `config.py`:

```python
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "service_management"
DB_USER = "root"
DB_PASSWORD = ""  # كلمة المرور الافتراضية في XAMPP فارغة
```

أو استخدام متغيرات البيئة:

```bash
# Windows
set DB_HOST=localhost
set DB_NAME=service_management
set DB_USER=root
set DB_PASSWORD=

# Linux/macOS
export DB_HOST=localhost
export DB_NAME=service_management
export DB_USER=root
export DB_PASSWORD=
```

---

## 🔄 ترحيل البيانات من SQLite

إذا كان لديك بيانات في قاعدة SQLite سابقة:

```bash
python migrate_to_mysql.py path/to/service_management.db
```

سيقوم السكربت بنقل جميع البيانات:
- المستخدمين
- العملاء
- الخدمات والفئات
- الطلبات والتفاصيل
- سجل الأنشطة

---

## ▶️ تشغيل النظام

```bash
python main.py
```

### بيانات الدخول الافتراضية
- **اسم المستخدم**: admin
- **كلمة المرور**: admin123

---

## 🔧 المميزات الجديدة

### 1. تجمع الاتصالات (Connection Pool)
```python
DB_POOL_ENABLED = True
DB_POOL_SIZE = 10
```

### 2. إعادة المحاولة التلقائية
- 3 محاولات للاتصال
- تراجع أسي (Exponential Backoff)

### 3. النسخ الاحتياطي المحسَّن
- دعم mysqldump للنسخ الاحتياطي الكامل
- نسخ احتياطي برمجي كبديل

---

## ⚠️ حل المشاكل الشائعة

### خطأ: Can't connect to MySQL server
```
الحل:
1. تأكد من تشغيل خدمة MySQL في XAMPP
2. تحقق من المنفذ (3306)
3. تأكد من عدم وجود جدار ناري يمنع الاتصال
```

### خطأ: Access denied for user
```
الحل:
1. تحقق من اسم المستخدم وكلمة المرور
2. في XAMPP الافتراضي: user=root, password=""
```

### خطأ: Unknown database
```
الحل:
1. تأكد من إنشاء قاعدة البيانات
2. تنفيذ سكربت init_db.sql
```

### خطأ: Arabic characters not displaying correctly
```
الحل:
- التأكد من استخدام utf8mb4
- التحقق من إعداد collation: utf8mb4_unicode_ci
```

---

## 📊 الفروقات بين SQLite و MySQL

| الميزة | SQLite | MySQL |
|--------|--------|-------|
| معامل الاستعلام | `?` | `%s` |
| النصوص | `TEXT` | `VARCHAR(n)` |
| الأرقام العشرية | `REAL` | `DECIMAL(m,n)` |
| المفتاح الأساسي | `INTEGER PRIMARY KEY AUTOINCREMENT` | `INT AUTO_INCREMENT PRIMARY KEY` |
| التجمع | ملف واحد | خادم منفصل |

---

## 📞 الدعم الفني

للمساعدة أو الإبلاغ عن مشاكل:
1. راجع ملفات السجلات في `logs/`
2. تحقق من إعدادات الاتصال
3. تأكد من إصدارات المكتبات

---

**الإصدار**: 4.0 - MySQL  
**تاريخ الإصدار**: أبريل 2026  
**الحالة**: جاهز للإنتاج
