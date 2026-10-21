"""
add_orders_for_new_customers.py
--------------------------------
يضيف عملاء جدد وطلباتهم مع تفاصيلها.
كل عميل يحصل على عدد طلبات يتناسب مع الشريحة المستهدفة.
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

# العملاء الجدد المطلوب إضافتهم (مع الشريحة المستهدفة)
NEW_CUSTOMERS = [
    {"name": "عميل جديد 1", "phone": "0500000001", "email": "new1@test.com", "address": "عنوان تجريبي", "target_orders": 1},
    {"name": "عميل جديد 2", "phone": "0500000002", "email": "new2@test.com", "address": "عنوان تجريبي", "target_orders": 2},
    {"name": "عميل برونزي 1", "phone": "0500000003", "email": "bronze1@test.com", "address": "عنوان تجريبي", "target_orders": 3},
    {"name": "عميل برونزي 2", "phone": "0500000004", "email": "bronze2@test.com", "address": "عنوان تجريبي", "target_orders": 4},
    {"name": "عميل فضي 1", "phone": "0500000005", "email": "silver1@test.com", "address": "عنوان تجريبي", "target_orders": 5},
    {"name": "عميل فضي 2", "phone": "0500000006", "email": "silver2@test.com", "address": "عنوان تجريبي", "target_orders": 7},
]

# الخدمات النشطة (id 10-17)
SERVICES_IDS = [10, 11, 12, 13, 14, 15, 16, 17]

def get_random_hour():
    """توزيع واقعي للساعات"""
    r = random.random()
    if r < 0.4:
        return random.randint(8, 12)
    elif r < 0.8:
        return random.randint(16, 20)
    else:
        return random.choice([13, 14, 15, 21, 22])

def generate_order(customer_id, services_list, max_days_ago=30):
    """توليد طلب واحد لعميل بتاريخ عشوائي خلال آخر max_days_ago يوماً"""
    days_ago = random.randint(0, max_days_ago)
    order_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
    hour = get_random_hour()
    minute = random.randint(0, 59)
    created_at = order_date.replace(hour=hour, minute=minute)
    
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
        'created_at': created_at,
        'total_amount': round(total_amount, 2),
        'status': 'completed',
        'details': details
    }

def main():
    logger.info("بدء إضافة العملاء الجدد وطلباتهم...")
    db = DatabaseManager()
    
    # 1. جلب الخدمات النشطة
    placeholders = ','.join(['%s'] * len(SERVICES_IDS))
    query = f"SELECT id, price FROM services WHERE is_active = 1 AND id IN ({placeholders})"
    services_db = db.execute_query(query, tuple(SERVICES_IDS))
    if not services_db:
        logger.error("لا توجد خدمات نشطة!")
        return
    services_list = [{'id': s['id'], 'price': float(s['price'])} for s in services_db]
    logger.info(f"تم جلب {len(services_list)} خدمة.")
    
    # 2. إضافة العملاء الجدد (إذا لم يكونوا موجودين مسبقاً)
    customer_ids = {}
    for cust in NEW_CUSTOMERS:
        # التحقق إذا كان العميل موجوداً بالفعل (برقم الهاتف)
        existing = db.execute_query("SELECT id FROM customers WHERE phone = %s", (cust['phone'],))
        if existing:
            cid = existing[0]['id']
            logger.info(f"العميل {cust['name']} موجود مسبقاً (ID: {cid})")
        else:
            cid = db.execute_update("""
                INSERT INTO customers (name, phone, email, address)
                VALUES (%s, %s, %s, %s)
            """, (cust['name'], cust['phone'], cust['email'], cust['address']))
            logger.info(f"تم إضافة العميل {cust['name']} (ID: {cid})")
        customer_ids[cust['name']] = {'id': cid, 'target_orders': cust['target_orders']}
    
    # 3. إضافة الطلبات وتفاصيلها لكل عميل
    total_orders_added = 0
    for cust_name, info in customer_ids.items():
        cid = info['id']
        target = info['target_orders']
        logger.info(f"إضافة {target} طلب للعميل {cust_name} (ID: {cid})")
        for i in range(target):
            order_data = generate_order(cid, services_list, max_days_ago=30)
            # إدراج الطلب
            order_id = db.execute_update("""
                INSERT INTO orders (customer_id, status, total_amount, created_at)
                VALUES (%s, %s, %s, %s)
            """, (cid, order_data['status'], order_data['total_amount'], order_data['created_at']))
            # إدراج تفاصيل الطلب
            for det in order_data['details']:
                db.execute_update("""
                    INSERT INTO order_details (order_id, service_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, det['service_id'], det['quantity'], det['unit_price'], det['total_price']))
            total_orders_added += 1
        logger.info(f"تمت إضافة {target} طلب للعميل {cust_name}")
    
    logger.info(f"✅ تم إضافة {total_orders_added} طلباً بنجاح.")
    
    # 4. عرض إحصائيات سريعة للعملاء الجدد
    logger.info("إحصائيات العملاء الجدد:")
    for cust_name, info in customer_ids.items():
        cid = info['id']
        count = db.execute_query("SELECT COUNT(*) as cnt FROM orders WHERE customer_id = %s", (cid,))[0]['cnt']
        logger.info(f"  {cust_name} (ID: {cid}): {count} طلب")

if __name__ == "__main__":
    main()