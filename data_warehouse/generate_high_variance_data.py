"""
generate_high_variance_data.py
-------------------------------
يولد بيانات طلبات ذات تباين كبير (2-20 طلب/يوم) لتدريب النموذج.
"""

import sys, os, random, numpy as np
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from repositories.database import DatabaseManager

TRAIN_DAYS = 120
TEST_DAYS = 30
START_DATE = datetime(2024, 1, 1)

# توزيع واسع للطلبات اليومية: متوسط 8 لكن انحراف معياري 5
def daily_orders_count(date):
    base = np.random.normal(8, 5)  # انحراف معياري 5 ← يتراوح بين 0 و 20 غالباً
    # تأثير يوم الجمعة
    if date.weekday() == 4:
        base *= 1.6
    elif date.weekday() == 5:
        base *= 0.5
    return max(1, int(round(base)))

# عوامل الساعة (كما هي)
def hour_factor(h):
    if 9 <= h <= 12: return 1.4
    if 17 <= h <= 21: return 1.5
    if h <= 5: return 0.3
    return 0.7

db = DatabaseManager()
customers = db.execute_query("SELECT id FROM customers")
if len(customers) < 20:
    for i in range(50):
        db.execute_update("INSERT INTO customers (name, phone) VALUES (%s, %s)",
                          (f"عميل تباين {i}", f"05{random.randint(10000000,99999999)}"))
customers = db.execute_query("SELECT id FROM customers")
cust_ids = [c['id'] for c in customers]

services = db.execute_query("SELECT id, price FROM services WHERE is_active=1")
if not services:
    print("لا توجد خدمات، قم بتشغيل سكريبت الخدمات أولاً")
    sys.exit()
services = [{'id': s['id'], 'price': float(s['price'])} for s in services]

all_orders = []
for i in range(TRAIN_DAYS + TEST_DAYS):
    dt = START_DATE + timedelta(days=i)
    n_orders = daily_orders_count(dt)
    for _ in range(n_orders):
        cust = random.choice(cust_ids)
        hour = random.choices(range(24), weights=[hour_factor(h) for h in range(24)])[0]
        minute = random.randint(0,59)
        created = dt.replace(hour=hour, minute=minute)
        num_sv = random.choices([1,2,3,4], weights=[0.4,0.3,0.2,0.1])[0]
        selected = random.sample(services, num_sv)
        total = 0
        details = []
        for sv in selected:
            qty = random.randint(1,3)
            line = qty * sv['price']
            total += line
            details.append((sv['id'], qty, sv['price'], line))
        all_orders.append((cust, created, round(total,2), details))

# إدراج
conn = db._get_connection()
cursor = conn.cursor()
for cust, created, total, dets in all_orders:
    cursor.execute("INSERT INTO orders (customer_id, status, total_amount, created_at) VALUES (%s, 'completed', %s, %s)",
                   (cust, total, created))
    oid = cursor.lastrowid
    for sid, qty, up, tp in dets:
        cursor.execute("INSERT INTO order_details (order_id, service_id, quantity, unit_price, total_price) VALUES (%s,%s,%s,%s,%s)",
                       (oid, sid, qty, up, tp))
conn.commit()
cursor.close()
conn.close()
print(f"تم إضافة {len(all_orders)} طلباً بتوزيع واسع.")