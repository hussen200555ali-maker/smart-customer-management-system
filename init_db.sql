-- ═══════════════════════════════════════════════════════════════════════
-- نظام إدارة الخدمات الذكي والذكاء الاصطناعي
-- سكربت إنشاء قاعدة البيانات MySQL
-- الإصدار: 4.0
-- ═══════════════════════════════════════════════════════════════════════

-- إنشاء قاعدة البيانات
CREATE DATABASE IF NOT EXISTS service_management 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE service_management;

-- ──────────────────────────────────────────────
-- جدول المستخدمين
-- ──────────────────────────────────────────────
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ──────────────────────────────────────────────
-- جدول العملاء
-- ──────────────────────────────────────────────
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ──────────────────────────────────────────────
-- جدول فئات الخدمات
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS service_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ──────────────────────────────────────────────
-- جدول الخدمات
-- ──────────────────────────────────────────────
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ──────────────────────────────────────────────
-- جدول الطلبات
-- ──────────────────────────────────────────────
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ──────────────────────────────────────────────
-- جدول تفاصيل الطلبات
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    service_id INT NOT NULL,
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ──────────────────────────────────────────────
-- جدول سجل الأنشطة
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════
-- الفهارس (Indexes)
-- ═══════════════════════════════════════════════════════════════════════

-- فهارس المستخدمين
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- فهارس العملاء
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_created_by ON customers(created_by);

-- فهارس الخدمات
CREATE INDEX idx_service_categories_name ON service_categories(name);
CREATE INDEX idx_services_category_id ON services(category_id);
CREATE INDEX idx_services_active ON services(is_active);
CREATE INDEX idx_services_price ON services(price);

-- فهارس الطلبات
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_by ON orders(created_by);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- فهارس تفاصيل الطلبات
CREATE INDEX idx_order_details_order_id ON order_details(order_id);
CREATE INDEX idx_order_details_service_id ON order_details(service_id);

-- فهارس سجل الأنشطة
CREATE INDEX idx_activity_log_user_id ON activity_log(user_id);
CREATE INDEX idx_activity_log_action ON activity_log(action);
CREATE INDEX idx_activity_log_created_at ON activity_log(created_at);

-- ═══════════════════════════════════════════════════════════════════════
-- البيانات الافتراضية
-- ═══════════════════════════════════════════════════════════════════════

-- ينشئ التطبيق حساب المدير الافتراضي (admin/admin123) عند التشغيل.

-- إدراج فئات الخدمات الافتراضية
INSERT INTO service_categories (name, description) VALUES
('صيانة', 'خدمات الصيانة والإصلاح'),
('تركيب', 'خدمات التركيب والتشغيل'),
('استشارات', 'خدمات استشارية وفنية'),
('تنظيف', 'خدمات التنظيف والتعقيم'),
('نقل', 'خدمات النقل والتوصيل'),
('تصميم', 'خدمات التصميم والإبداع')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- ═══════════════════════════════════════════════════════════════════════
-- ملاحظات الاستخدام
-- ═══════════════════════════════════════════════════════════════════════
-- 
-- لتنفيذ هذا الملف:
-- 
-- عبر سطر الأوامر (Windows/XAMPP):
-- C:\xampp\mysql\bin\mysql -u root < init_db.sql
-- 
-- عبر سطر الأوامر (Linux/XAMPP):
-- sudo /opt/lampp/bin/mysql -u root < init_db.sql
-- 
-- عبر phpMyAdmin:
-- 1. افتح http://localhost/phpmyadmin
-- 2. اذهب إلى تبويب "SQL"
-- 3. انسخ والصق محتوى هذا الملف
-- 4. اضغط "تنفيذ"
-- 
-- ═══════════════════════════════════════════════════════════════════════
