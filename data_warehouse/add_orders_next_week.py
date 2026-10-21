"""
add_orders_next_week.py
------------------------
يضيف طلبات للأيام السبعة القادمة (من اليوم إلى اليوم+6)
عدد الطلبات اليومي: 50-100
يستخدم جميع العملاء (149-228)
تنوع في الخدمات (10-17) والأوقات والأيام
"""

import sys
import os
import random
from datetime import datetime, timedelta
import logging

# إضافة المسار الرئيسي للمشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %level)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== الإعدادات ==========
DAYS_AHEAD = 7                     # عدد الأيام (من اليوم إلى اليوم+6)
MIN_ORDERS_PER_DAY = 50
MAX_ORDERS_PER_DAY = 100

# قائمة العملاء (من الـ dump: 149 إلى 228)
CUSTOMER_IDS = list(range(149, 229))   # 149..228

# الخدمات النشطة (من الـ dump: id 10-17)
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
    """
    ساعة عشوائية مع توزيع يراعي أوقات الذروة:
    - 40% صباحاً (8-12)
    - 40% مساءً (16-20)
    - 20% باقي الساعات (13-15 و 21-22)
    """
    r = random.random()
    if r < 0.4:
        return random.randint(8, 12)
    elif r < 0.8:
        return random.randint(16, 20)
    else:
        return random.choice([13, 14, 15, 21, 22])

def generate_orders_for_date(date, target_orders, customer_list, services_list):
    """توليد قائمة الطلبات ليوم محدد"""
    orders = []
    for _ in range(target_orders):
        customer_id = random.choice(customer_list)
        hour = get_random_hour()
        minute = random.randint(0, 59)
        created_at = date.replace(hour=hour, minute=minute)
        
        # عدد الخدمات لكل طلب: 1-3 (مع احتمال 50% لـ 1 خدمة، 30% لـ 2، 20% لـ 3)
        num_services = random.choices([1,2,3], weights=[0.5,0.3,0.2])[0]
        selected_services = random.sample(services_list, num_services)
        total_amount = 0
        details = []
        for svc in selected_services:
            quantity = random.randint(1, 2)   # كمية 1 أو 2
            line_total = quantity * svc['price']
            total_amount += line_total
            details.append({
                'service_id': svc['id'],
                'quantity': quantity,
                'unit_price': svc['price'],
                'total_price': line_total
            })
        orders.append({
            'customer_id': customer_id,
            'created_at': created_at,
            'total_amount': round(total_amount, 2),
            'status': 'completed',   # يمكن تغييرها إلى 'pending' إذا أردت
            'details': details
        })
    return orders

def main():
    logger.info("بدء إنشاء طلبات للأيام السبعة القادمة...")
    
    # الاتصال بقاعدة البيانات
    db = DatabaseManager()
    
    # جلب قائمة العملاء الفعلية من قاعدة البيانات (قد تكون مختلفة عن النطاق الثابت)
    customers = db.execute_query("SELECT id FROM customers")
    customer_ids = [c['id'] for c in customers]
    if not customer_ids:
        logger.error("لا يوجد عملاء في قاعدة البيانات! قم بإضافة عملاء أولاً.")
        return
    logger.info(f"عدد العملاء المتاحين: {len(customer_ids)}")
    
    # جلب الخدمات النشطة من قاعدة البيانات (للتأكد من الأسعار)
    services_db = db.execute_query("SELECT id, price FROM services WHERE is_active = 1 AND id IN (10,11,12,13,14,15,16,17)")
    if not services_db:
        logger.error("لا توجد خدمات نشطة في قاعدة البيانات!")
        return
    services_list = [{'id': s['id'], 'price': float(s['price'])} for s in services_db]
    logger.info(f"عدد الخدمات النشطة: {len(services_list)}")
    
    # تواريخ الأيام السبعة القادمة
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dates = [today + timedelta(days=i) for i in range(DAYS_AHEAD)]
    
    all_orders = []
    for dt in dates:
        num_orders = random.randint(MIN_ORDERS_PER_DAY, MAX_ORDERS_PER_DAY)
        logger.info(f"توليد {num_orders} طلب ليوم {dt.date()}")
        orders_day = generate_orders_for_date(dt, num_orders, customer_ids, services_list)
        all_orders.extend(orders_day)
    
    logger.info(f"إجمالي الطلبات المولدة: {len(all_orders)}")
    
    # إدراج الطلبات في قاعدة البيانات (مع معاملة واحدة)
    conn = db._get_connection()
    cursor = conn.cursor()
    inserted_orders = 0
    try:
        for order in all_orders:
            cursor.execute("""
                INSERT INTO orders (customer_id, status, total_amount, created_at)
                VALUES (%s, %s, %s, %s)
            """, (order['customer_id'], order['status'], order['total_amount'], order['created_at']))
            order_id = cursor.lastrowid
            for detail in order['details']:
                cursor.execute("""
                    INSERT INTO order_details (order_id, service_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, detail['service_id'], detail['quantity'], detail['unit_price'], detail['total_price']))
            inserted_orders += 1
            if inserted_orders % 100 == 0:
                logger.info(f"تم إدراج {inserted_orders} طلب حتى الآن...")
        conn.commit()
        logger.info(f"✅ تم إدراج {inserted_orders} طلب بنجاح في قاعدة البيانات.")
    except Exception as e:
        conn.rollback()
        logger.error(f"فشل إدراج الطلبات: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    # عرض إحصائيات سريعة
    stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(DISTINCT DATE(created_at)) as unique_days,
            MIN(created_at) as first_date,
            MAX(created_at) as last_date
        FROM orders
        WHERE created_at >= %s
    """, (today,))
    logger.info(f"الإحصائيات بعد الإضافة: {stats[0]}")

if __name__ == "__main__":
    main()