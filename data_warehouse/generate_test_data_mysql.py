"""
generate_test_data_mysql.py
----------------------------
ينشئ بيانات اختبارية (عملاء، خدمات، طلبات) في قاعدة بيانات MySQL
لنظام إدارة الخدمات الذكي
، مناسبة لتدريب نموذج الذكاء الاصطناعي.
الإصدار: 1.0
تاريخ: أبريل 2026
"""

import sys
import os
import random
from datetime import datetime, timedelta
import logging

# إضافة المسار الرئيسي للمشروع (حسب هيكل الكود)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد مدير قاعدة البيانات من المشروع نفسه
from repositories.database import DatabaseManager
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== الإعدادات ====================
TRAINING_DAYS = 90          # عدد أيام التدريب (يوصى 60-120)
TESTING_DAYS = 21           # عدد أيام الاختبار (يوصى 14-30)
START_DATE = datetime(2024, 1, 1)   # تاريخ البدء (قديم)

# متوسط الطلبات اليومي
AVG_ORDERS_PER_DAY_TRAIN = 7   # ~7 طلب/يوم => ~630 طلب تدريب
AVG_ORDERS_PER_DAY_TEST = 7    # ~147 طلب اختبار

# قائمة الخدمات الأساسية (ستضاف تلقائياً)
DEFAULT_SERVICES = [
    ("تنظيف منزل", 150, 1),
    ("صيانة مكيفات", 200, 1),
    ("سباكة", 100, 1),
    ("كهرباء", 120, 1),
    ("دهان", 300, 1),
    ("تركيب أثاث", 180, 1),
    ("تنظيف سجاد", 80, 1),
    ("نقل عفش", 400, 1),
]

# فئات الخدمات (ستضاف)
DEFAULT_CATEGORIES = ["صيانة", "تركيب", "استشارات", "تنظيف", "نقل", "تصميم"]

# عدد العملاء الوهميين
NUM_CUSTOMERS = 50

# ==================== دوال مساعدة ====================
def get_day_factor(date: datetime) -> float:
    """عامل زيادة/نقصان حسب يوم الأسبوع (محاكاة الواقع)"""
    w = date.weekday()  # 0=الإثنين, 4=الجمعة, 5=السبت
    if w == 4:   # الجمعة
        return 1.6
    elif w == 5: # السبت
        return 0.6
    elif w == 6: # الأحد
        return 0.8
    else:
        return 1.0

def get_hour_factor(hour: int) -> float:
    """عامل حسب الساعة (ذروة صباحاً ومساءً)"""
    if 9 <= hour <= 12:
        return 1.3
    elif 16 <= hour <= 20:
        return 1.4
    elif 22 <= hour or hour <= 5:
        return 0.3
    else:
        return 0.7

def generate_orders_for_date(date: datetime, target_orders: int, customers_ids: list, services_data: list):
    """توليد طلبات ليوم محدد (قائمة من القواميس)"""
    orders = []
    num_orders = max(1, int(target_orders * get_day_factor(date)))
    for _ in range(num_orders):
        customer_id = random.choice(customers_ids)
        hour = random.choices(
            population=list(range(24)),
            weights=[get_hour_factor(h) for h in range(24)],
            k=1
        )[0]
        minute = random.randint(0, 59)
        created_at = datetime(date.year, date.month, date.day, hour, minute)
        
        # اختيار 1-3 خدمات لكل طلب
        num_services = random.randint(1, 3)
        selected = random.sample(services_data, num_services)
        total_amount = 0
        details = []
        for svc in selected:
            qty = random.randint(1, 2)
            price = svc['price']
            line_total = qty * price
            total_amount += line_total
            details.append({
                'service_id': svc['id'],
                'quantity': qty,
                'unit_price': price,
                'total_price': line_total
            })
        orders.append({
            'customer_id': customer_id,
            'created_at': created_at,
            'total_amount': round(total_amount, 2),
            'status': 'completed',   # لبيانات التدريب نعتبرها مكتملة
            'notes': None,
            'details': details
        })
    return orders

# ==================== الوظيفة الرئيسية ====================
def main():
    logger.info("بدء إنشاء البيانات الاختبارية في قاعدة البيانات...")
    
    # 1. الاتصال بقاعدة البيانات
    db = DatabaseManager()
    
    # 2. التأكد من وجود فئات الخدمات والخدمات الأساسية
    #    (إذا كانت موجودة بالفعل، لن يتم تكرارها)
    categories_map = {}
    for cat_name in DEFAULT_CATEGORIES:
        existing = db.execute_query("SELECT id FROM service_categories WHERE name = %s", (cat_name,))
        if existing:
            categories_map[cat_name] = existing[0]['id']
        else:
            cat_id = db.execute_update(
                "INSERT INTO service_categories (name, description) VALUES (%s, %s)",
                (cat_name, f"فئة {cat_name}")
            )
            categories_map[cat_name] = cat_id
            logger.info(f"أضيفت فئة: {cat_name} (id={cat_id})")
    
    # التأكد من وجود الخدمات (إضافة إن لم تكن موجودة)
    services_list = []  # قائمة {'id':, 'name':, 'price':}
    for svc_name, price, cat_idx in DEFAULT_SERVICES:
        cat_name = DEFAULT_CATEGORIES[cat_idx-1]  # الفهرس يبدأ من 1
        cat_id = categories_map[cat_name]
        existing = db.execute_query("SELECT id, price FROM services WHERE name = %s", (svc_name,))
        if existing:
            sid = existing[0]['id']
            # تحديث السعر إذا تغير
            if existing[0]['price'] != price:
                db.execute_update("UPDATE services SET price = %s WHERE id = %s", (price, sid))
            services_list.append({'id': sid, 'name': svc_name, 'price': price})
        else:
            sid = db.execute_update(
                "INSERT INTO services (name, description, price, category_id, is_active) VALUES (%s, %s, %s, %s, 1)",
                (svc_name, f"خدمة {svc_name}", price, cat_id)
            )
            services_list.append({'id': sid, 'name': svc_name, 'price': price})
            logger.info(f"أضيفت خدمة: {svc_name} (id={sid})")
    
    # 3. إنشاء عملاء جدد (إذا كان العدد الحالي أقل من المطلوب)
    existing_customers = db.execute_query("SELECT id FROM customers ORDER BY id")
    if len(existing_customers) < NUM_CUSTOMERS:
        needed = NUM_CUSTOMERS - len(existing_customers)
        for i in range(needed):
            name = f"عميل تجريبي {len(existing_customers)+i+1}"
            phone = f"05{random.randint(10000000, 99999999)}"
            db.execute_update(
                "INSERT INTO customers (name, phone, email, address, notes) VALUES (%s, %s, %s, %s, %s)",
                (name, phone, f"test{random.randint(1,1000)}@example.com", "عنوان وهمي", "بيانات اختبارية")
            )
        logger.info(f"تم إضافة {needed} عميل جديد")
        # تحديث القائمة
        existing_customers = db.execute_query("SELECT id FROM customers")
    
    all_customer_ids = [c['id'] for c in existing_customers]
    logger.info(f"عدد العملاء المتاحين: {len(all_customer_ids)}")
    
    # 4. توليد الطلبات عبر الأيام المتتالية (تدريب + اختبار)
    total_days = TRAINING_DAYS + TESTING_DAYS
    dates = [START_DATE + timedelta(days=i) for i in range(total_days)]
    
    # متوسط الطلبات اليومي
    avg_train = AVG_ORDERS_PER_DAY_TRAIN
    avg_test = AVG_ORDERS_PER_DAY_TEST
    
    # تجميع الطلبات لإدراجها
    all_orders_to_insert = []
    
    for i, dt in enumerate(dates):
        if i < TRAINING_DAYS:
            target_avg = avg_train
        else:
            target_avg = avg_test
        orders_day = generate_orders_for_date(dt, target_avg, all_customer_ids, services_list)
        all_orders_to_insert.extend(orders_day)
    
    logger.info(f"تم توليد {len(all_orders_to_insert)} طلب إجمالي (تدريب+اختبار)")
    
    # 5. إدراج الطلبات بالترتيب (مع تفاصيلها) دون تكرار
    #    نستخدم معاملة (transaction) للتأكد من سلامة البيانات
    conn = db._get_connection()
    cursor = conn.cursor()
    try:
        for order_data in all_orders_to_insert:
            # إدراج الطلب
            cursor.execute("""
                INSERT INTO orders (customer_id, status, total_amount, notes, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                order_data['customer_id'],
                order_data['status'],
                order_data['total_amount'],
                order_data['notes'],
                order_data['created_at']
            ))
            order_id = cursor.lastrowid
            
            # إدراج تفاصيل الطلب
            for detail in order_data['details']:
                cursor.execute("""
                    INSERT INTO order_details (order_id, service_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    order_id,
                    detail['service_id'],
                    detail['quantity'],
                    detail['unit_price'],
                    detail['total_price']
                ))
        conn.commit()
        logger.info(f"تم إدراج جميع الطلبات وتفاصيلها بنجاح.")
    except Exception as e:
        conn.rollback()
        logger.error(f"فشل إدراج الطلبات: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    # 6. عرض إحصائيات سريعة
    stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_orders,
            MIN(created_at) as first_order,
            MAX(created_at) as last_order,
            COUNT(DISTINCT DATE(created_at)) as unique_days
        FROM orders
    """)
    logger.info(f"إحصائيات قاعدة البيانات بعد الإضافة: {stats[0]}")
    
    logger.info("✅ تم الانتهاء من إنشاء البيانات الاختبارية بنجاح.")


if __name__ == "__main__":
    main()