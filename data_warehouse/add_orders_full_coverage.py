"""
add_orders_full_coverage.py
----------------------------
يضيف طلبات من الأسبوع السابق حتى يوم غد (7 أيام ماضية + اليوم + غد)
بمعدل 50-100 طلب في اليوم، ويضمن أن كل عميل لديه على الأقل 3 طلبات.
"""

import sys
import os
import random
from datetime import datetime, timedelta
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from repositories.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== الإعدادات ==========
MIN_ORDERS_PER_CUSTOMER = 3
MIN_ORDERS_PER_DAY = 50
MAX_ORDERS_PER_DAY = 100

# الخدمات النشطة (كما في قاعدة البيانات)
SERVICES = [
    {"id": 10, "name": "تنظيف منزل", "price": 150},
    {"id": 11, "name": "صيانة مكيفات", "price": 200},
    {"id": 12, "name": "سباكة", "price": 100},
    {"id": 13, "name": "كهرباء", "price": 120},
    {"id": 14, "name": "دهان", "price": 300},
    {"id": 15, "name": "تركيب أثاث", "price": 180},
    {"id": 16, "name": "تنظيف سجاد", "price": 80},
    {"id": 17, "name": "نقل عفش", "price": 400},
]

# ========== دوال مساعدة ==========
def get_random_hour():
    """توزيع واقعي للساعات (ذروة صباحاً ومساءً)"""
    r = random.random()
    if r < 0.4:
        return random.randint(8, 12)
    elif r < 0.8:
        return random.randint(16, 20)
    else:
        return random.choice([13, 14, 15, 21, 22])

def generate_order_for_customer(customer_id, date, services_list):
    """توليد طلب واحد لعميل محدد في تاريخ معين"""
    hour = get_random_hour()
    minute = random.randint(0, 59)
    created_at = date.replace(hour=hour, minute=minute)
    
    num_services = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
    selected = random.sample(services_list, num_services)
    total_amount = 0
    details = []
    for svc in selected:
        qty = random.randint(1, 2)
        line_total = qty * svc['price']
        total_amount += line_total
        details.append({
            'service_id': svc['id'],
            'quantity': qty,
            'unit_price': svc['price'],
            'total_price': line_total
        })
    return {
        'customer_id': customer_id,
        'created_at': created_at,
        'total_amount': round(total_amount, 2),
        'status': 'completed',
        'details': details
    }

def main():
    logger.info("بدء تشغيل سكريبت تغطية الفترة من الأسبوع السابق حتى يوم غد...")
    db = DatabaseManager()
    
    # ========== 1. جلب البيانات الأساسية ==========
    customers = db.execute_query("SELECT id FROM customers")
    if not customers:
        logger.error("لا يوجد عملاء في قاعدة البيانات!")
        return
    customer_ids = [c['id'] for c in customers]
    logger.info(f"عدد العملاء: {len(customer_ids)}")
    
    # جلب الخدمات النشطة
    services_db = db.execute_query("SELECT id, price FROM services WHERE is_active = 1")
    services_list = [{'id': s['id'], 'price': float(s['price'])} for s in services_db if s['id'] in [10,11,12,13,14,15,16,17]]
    if not services_list:
        logger.error("لا توجد خدمات نشطة!")
        return
    logger.info(f"عدد الخدمات: {len(services_list)}")
    
    # ========== 2. حساب عدد الطلبات الحالي لكل عميل ==========
    current_counts = {}
    for cid in customer_ids:
        cnt = db.execute_query("SELECT COUNT(*) as cnt FROM orders WHERE customer_id = %s", (cid,))[0]['cnt']
        current_counts[cid] = cnt
    
    # العملاء الذين يحتاجون طلبات إضافية
    needy_customers = [cid for cid, cnt in current_counts.items() if cnt < MIN_ORDERS_PER_CUSTOMER]
    logger.info(f"العملاء الذين لديهم أقل من {MIN_ORDERS_PER_CUSTOMER} طلب: {len(needy_customers)}")
    
    if not needy_customers:
        logger.info("جميع العملاء لديهم طلبات كافية. لن تتم إضافة أي طلبات جديدة.")
        return
    
    # ========== 3. تحديد الفترة الزمنية ==========
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=7)   # قبل 7 أيام (الأسبوع السابق)
    end_date = today + timedelta(days=1)      # حتى يوم غد
    dates = []
    d = start_date
    while d <= end_date:
        dates.append(d)
        d += timedelta(days=1)
    logger.info(f"الفترة المطلوب تغطيتها: من {start_date.date()} إلى {end_date.date()} ({len(dates)} يوماً)")
    
    # ========== 4. توليد طلبات لكل يوم ==========
    # سنحاول توزيع الطلبات على needy_customers أولاً، ثم على باقي العملاء لملء العدد المطلوب يومياً
    all_orders = []
    for dt in dates:
        num_orders_today = random.randint(MIN_ORDERS_PER_DAY, MAX_ORDERS_PER_DAY)
        logger.info(f"توليد {num_orders_today} طلب ليوم {dt.date()}")
        
        # قائمة العملاء المتاحين لليوم (نبدأ بالـ needy ثم نكرر)
        available_customers = needy_customers.copy()
        # إذا كان عدد needy أقل من المطلوب، نضيف باقي العملاء (مع إمكانية التكرار)
        while len(available_customers) < num_orders_today:
            available_customers.extend(customer_ids)
        
        # نختار عشوائياً العملاء لليوم (قد يتكرر نفس العميل أكثر من مرة في نفس اليوم)
        selected_customers = random.sample(available_customers, num_orders_today)
        
        for cid in selected_customers:
            order = generate_order_for_customer(cid, dt, services_list)
            all_orders.append(order)
    
    logger.info(f"إجمالي الطلبات المولدة: {len(all_orders)}")
    
    # ========== 5. إدراج الطلبات في قاعدة البيانات ==========
    conn = db._get_connection()
    cursor = conn.cursor()
    inserted = 0
    try:
        for order in all_orders:
            cursor.execute("""
                INSERT INTO orders (customer_id, status, total_amount, created_at)
                VALUES (%s, %s, %s, %s)
            """, (order['customer_id'], order['status'], order['total_amount'], order['created_at']))
            order_id = cursor.lastrowid
            for det in order['details']:
                cursor.execute("""
                    INSERT INTO order_details (order_id, service_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, det['service_id'], det['quantity'], det['unit_price'], det['total_price']))
            inserted += 1
            if inserted % 100 == 0:
                logger.info(f"تم إدراج {inserted} طلب...")
        conn.commit()
        logger.info(f"✅ تم إدراج {inserted} طلب بنجاح.")
    except Exception as e:
        conn.rollback()
        logger.error(f"فشل الإدراج: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    # ========== 6. التحقق من النتيجة ==========
    new_counts = {}
    for cid in needy_customers:
        cnt = db.execute_query("SELECT COUNT(*) as cnt FROM orders WHERE customer_id = %s", (cid,))[0]['cnt']
        new_counts[cid] = cnt
    still_needy = [cid for cid, cnt in new_counts.items() if cnt < MIN_ORDERS_PER_CUSTOMER]
    if still_needy:
        logger.warning(f"لا يزال {len(still_needy)} عميلاً لديهم أقل من {MIN_ORDERS_PER_CUSTOMER} طلب. قد تحتاج إلى تشغيل السكريبت مرة أخرى أو زيادة عدد الطلبات اليومية.")
    else:
        logger.info(f"🎉 جميع العملاء لديهم الآن على الأقل {MIN_ORDERS_PER_CUSTOMER} طلب. مشكلة التوصيات محلولة!")

if __name__ == "__main__":
    main()