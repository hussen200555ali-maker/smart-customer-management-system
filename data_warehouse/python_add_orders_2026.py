"""
add_orders_2026_fixed.py
------------------------
يضيف طلبات من 1 يناير 2026 حتى اليوم الحالي (8 أبريل 2026)
بمعدل 80-150 طلب في اليوم.
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
START_DATE = datetime(2026, 1, 1)    # 1 يناير 2026
MIN_ORDERS_PER_DAY = 80
MAX_ORDERS_PER_DAY = 150

# الخدمات النشطة (حسب قاعدة البيانات)
SERVICES_IDS = [10, 11, 12, 13, 14, 15, 16, 17]

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
    
    num_services = random.choices([1, 2, 3, 4], weights=[0.3, 0.3, 0.25, 0.15])[0]
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
    logger.info("بدء تشغيل سكريبت إضافة طلبات من يناير 2026 حتى اليوم...")
    db = DatabaseManager()
    
    # ========== 1. جلب العملاء ==========
    customers = db.execute_query("SELECT id FROM customers")
    if not customers:
        logger.error("لا يوجد عملاء!")
        return
    customer_ids = [c['id'] for c in customers]
    logger.info(f"عدد العملاء: {len(customer_ids)}")
    
    # ========== 2. جلب الخدمات النشطة باستخدام IN مع العناصر النائبة ==========
    if not SERVICES_IDS:
        logger.error("لا توجد خدمات محددة!")
        return
    
    placeholders = ','.join(['%s'] * len(SERVICES_IDS))
    query = f"SELECT id, price FROM services WHERE is_active = 1 AND id IN ({placeholders})"
    services_db = db.execute_query(query, tuple(SERVICES_IDS))
    
    if not services_db:
        logger.error("لا توجد خدمات نشطة بالمعرفات المحددة!")
        return
    services_list = [{'id': s['id'], 'price': float(s['price'])} for s in services_db]
    logger.info(f"عدد الخدمات: {len(services_list)}")
    
    # ========== 3. تحديد الأيام من 1 يناير 2026 إلى اليوم ==========
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    all_dates = []
    d = START_DATE
    while d <= today:
        all_dates.append(d)
        d += timedelta(days=1)
    logger.info(f"عدد الأيام المطلوب تغطيتها: {len(all_dates)} (من {START_DATE.date()} إلى {today.date()})")
    
    # ========== 4. توليد الطلبات ==========
    all_orders = []
    total_orders = 0
    for dt in all_dates:
        num_orders = random.randint(MIN_ORDERS_PER_DAY, MAX_ORDERS_PER_DAY)
        logger.info(f"توليد {num_orders} طلب ليوم {dt.date()}")
        selected_customers = random.choices(customer_ids, k=num_orders)
        for cid in selected_customers:
            order = generate_order_for_customer(cid, dt, services_list)
            all_orders.append(order)
        total_orders += num_orders
    
    logger.info(f"إجمالي الطلبات المولدة: {total_orders}")
    
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
            if inserted % 500 == 0:
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
    
    # ========== 6. إحصائيات ==========
    total_after = db.execute_query("SELECT COUNT(*) as cnt FROM orders")[0]['cnt']
    logger.info(f"إجمالي الطلبات في قاعدة البيانات الآن: {total_after}")

if __name__ == "__main__":
    main()