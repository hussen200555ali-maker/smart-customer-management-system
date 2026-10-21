"""
generate_diverse_data_mysql.py
-------------------------------
ينشئ بيانات طلبات غنية ومتنوعة (اتجاه متزايد، موسمية أسبوعية، عشوائية، أيام استثنائية)
مناسبة لتدريب نموذج ذكاء اصطناعي حقيقي.
"""

import sys
import os
import random
import numpy as np
from datetime import datetime, timedelta
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from repositories.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== الإعدادات ====================
TRAINING_DAYS = 120          # أيام التدريب (4 أشهر)
TESTING_DAYS = 30            # أيام الاختبار (شهر)
START_DATE = datetime(2024, 1, 1)

# متوسط الطلبات اليومي الأساسي (سيزيد بالاتجاه)
BASE_AVG_ORDERS = 6

# قوة الاتجاه (زيادة تدريجية)
TREND_STRENGTH = 0.008       # 0.8% زيادة يومية ≈ 30% نمو على 4 أشهر

# قوة الموسمية الأسبوعية (الجمعة ذروة، السبت قاع)
WEEKLY_AMPLITUDE = 0.4       # +/- 40%

# مستوى الضوضاء العشوائية (انحراف معياري نسبي)
NOISE_LEVEL = 0.2            # 20% تقلب

# أيام استثنائية (عطلات، تخفيضات) تزيد الطلبات
SPECIAL_DAYS = [
    ("2024-01-01", 2.2, "رأس السنة"),
    ("2024-03-10", 2.5, "بداية رمضان"),
    ("2024-04-10", 3.0, "عيد الفطر"),
    ("2024-06-15", 2.0, "عطلة منتصف العام"),
    ("2024-09-23", 2.3, "اليوم الوطني"),
    ("2024-12-02", 2.4, "اليوم الوطني الإماراتي"),
]

# ==================== دوال ====================
def get_weekly_factor(weekday):
    """عامل الموسمية الأسبوعية: الجمعة أعلى، السبت أقل"""
    # weekday: 0=الإثنين ... 4=الجمعة, 5=السبت, 6=الأحد
    if weekday == 4:   # الجمعة
        return 1 + WEEKLY_AMPLITUDE * 1.5
    elif weekday == 5: # السبت
        return 1 - WEEKLY_AMPLITUDE
    elif weekday == 6: # الأحد
        return 1 - WEEKLY_AMPLITUDE * 0.5
    elif weekday == 0: # الإثنين
        return 1 + WEEKLY_AMPLITUDE * 0.3
    else:
        return 1 + WEEKLY_AMPLITUDE * 0.1

def get_special_factor(date_str):
    """عامل الأيام الخاصة"""
    for d, factor, _ in SPECIAL_DAYS:
        if d == date_str:
            return factor
    return 1.0

def generate_order_count(date, day_index):
    """توليد عدد الطلبات ليوم معين (رقم حقيقي، غير مقرب)"""
    # 1. الاتجاه الأساسي (زيادة يومية تدريجية)
    trend = 1 + TREND_STRENGTH * day_index
    
    # 2. الموسمية الأسبوعية
    weekly = get_weekly_factor(date.weekday())
    
    # 3. العطلات والأيام الخاصة
    special = get_special_factor(date.strftime("%Y-%m-%d"))
    
    # 4. ضوضاء عشوائية (توزيع لوغاريتمي طبيعي)
    noise = np.random.lognormal(0, NOISE_LEVEL)
    
    # القيمة المتوقعة
    expected = BASE_AVG_ORDERS * trend * weekly * special * noise
    
    # إضافة دفعة عشوائية إضافية لجعل البيانات أكثر تشويشًا
    burst = 1.0
    if random.random() < 0.1:   # 10% من الأيام تكون دفعة مفاجئة
        burst = random.uniform(1.2, 1.8)
    
    raw = expected * burst
    # نضمن ألا تقل عن 0.5
    return max(0.5, raw)

def generate_hourly_distribution(num_orders, date):
    """توزيع الطلبات على الساعات بشكل واقعي"""
    if num_orders < 1:
        return []
    
    # توزيع احتمالي حسب الساعة (ذروة صباحاً ومساءً)
    hours = list(range(24))
    # أوزان: الصباح (9-12) و المساء (16-20) أعلى
    weights = []
    for h in hours:
        if 9 <= h <= 12:
            weights.append(3.0)
        elif 16 <= h <= 20:
            weights.append(3.5)
        elif 21 <= h <= 23:
            weights.append(1.2)
        elif 0 <= h <= 5:
            weights.append(0.3)
        else:
            weights.append(0.8)
    
    # اختيار الساعات بناءً على الأوزان
    selected_hours = random.choices(hours, weights=weights, k=int(round(num_orders)))
    # توزيع الطلبات على هذه الساعات (قد يزيد أو ينقص قليلاً)
    from collections import Counter
    hour_counts = Counter(selected_hours)
    
    result = []
    for hour, count in hour_counts.items():
        for _ in range(count):
            minute = random.randint(0, 59)
            dt = datetime(date.year, date.month, date.day, hour, minute)
            result.append(dt)
    return result

def main():
    logger.info("بدء إنشاء بيانات تدريب متنوعة وغنية...")
    db = DatabaseManager()
    
    # 1. التأكد من وجود خدمات وعملاء (كما في السكريبت السابق، سنضيف المزيد)
    #    نضيف 100 عميل إن أمكن
    existing_customers = db.execute_query("SELECT id FROM customers")
    if len(existing_customers) < 100:
        needed = 100 - len(existing_customers)
        for i in range(needed):
            name = f"عميل متنوع {len(existing_customers)+i+1}"
            phone = f"05{random.randint(10000000, 99999999)}"
            db.execute_update(
                "INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)",
                (name, phone, f"cust{random.randint(1,10000)}@ex.com", "عنوان تجريبي")
            )
        logger.info(f"أضيف {needed} عميل إضافي")
    
    all_customers = db.execute_query("SELECT id FROM customers")
    customer_ids = [c['id'] for c in all_customers]
    
    # 2. التأكد من وجود خدمات كافية
    services = db.execute_query("SELECT id, price FROM services WHERE is_active=1")
    if len(services) < 5:
        logger.warning("الخدمات قليلة، يرجى تشغيل السكريبت الأساسي أولاً أو إضافة خدمات يدوياً.")
        return
    service_prices = {s['id']: float(s['price']) for s in services}
    service_ids = list(service_prices.keys())
    
    # 3. توليد الطلبات عبر الأيام
    total_days = TRAINING_DAYS + TESTING_DAYS
    all_orders_details = []  # list of tuples (order_dict, list_of_details)
    
    for day_idx in range(total_days):
        current_date = START_DATE + timedelta(days=day_idx)
        # عدد الطلبات لهذا اليوم (قد يكون عشرياً)
        raw_count = generate_order_count(current_date, day_idx)
        # نأخذ الجزء الصحيح مع بعض التوزيع الاحتمالي
        # نستخدم Poisson للتوزيع الصحيح حول المتوسط
        try:
            daily_orders = np.random.poisson(lam=max(0.5, raw_count))
        except:
            daily_orders = max(0, int(round(raw_count)))
        if daily_orders == 0 and raw_count > 0.3:
            daily_orders = 1
        
        # توزيع الساعات
        order_times = generate_hourly_distribution(daily_orders, current_date)
        
        # إنشاء الطلبات
        for order_time in order_times:
            customer_id = random.choice(customer_ids)
            # عدد الخدمات في الطلب (1 إلى 4)
            num_services = random.choices([1,2,3,4], weights=[0.5,0.3,0.15,0.05])[0]
            selected_svcs = random.sample(service_ids, min(num_services, len(service_ids)))
            total_amount = 0.0
            details = []
            for svc_id in selected_svcs:
                qty = random.randint(1, 3)
                price = service_prices[svc_id]
                line_total = qty * price
                total_amount += line_total
                details.append({
                    'service_id': svc_id,
                    'quantity': qty,
                    'unit_price': price,
                    'total_price': line_total
                })
            # إضافة بعض الطلبات التي تحتوي على ملاحظات عشوائية
            notes = random.choice([None, "يرجى الاتصال قبل القدوم", "عاجل", "طلب خاص"]) if random.random()<0.2 else None
            all_orders_details.append({
                'customer_id': customer_id,
                'created_at': order_time,
                'total_amount': round(total_amount, 2),
                'status': 'completed',
                'notes': notes,
                'details': details
            })
    
    logger.info(f"تم توليد {len(all_orders_details)} طلب.")
    
    # 4. إدراج الطلبات في قاعدة البيانات
    conn = db._get_connection()
    cursor = conn.cursor()
    try:
        order_count = 0
        for order_data in all_orders_details:
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
            for det in order_data['details']:
                cursor.execute("""
                    INSERT INTO order_details (order_id, service_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    order_id,
                    det['service_id'],
                    det['quantity'],
                    det['unit_price'],
                    det['total_price']
                ))
            order_count += 1
            if order_count % 500 == 0:
                logger.info(f"تم إدراج {order_count} طلب...")
        conn.commit()
        logger.info(f"تم إدراج جميع الطلبات بنجاح. العدد: {order_count}")
    except Exception as e:
        conn.rollback()
        logger.error(f"فشل الإدراج: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    # 5. إحصائيات سريعة للتحقق من التباين
    stats = db.execute_query("""
        SELECT 
            DATE(created_at) as day,
            COUNT(*) as orders
        FROM orders
        GROUP BY DATE(created_at)
        ORDER BY day
    """)
    if stats:
        counts = [s['orders'] for s in stats]
        logger.info(f"إحصائيات الطلبات اليومية: min={min(counts)}, max={max(counts)}, mean={np.mean(counts):.1f}, std={np.std(counts):.1f}")
        if np.std(counts) < 1.5:
            logger.warning("التباين لا يزال منخفضًا، قد تحتاج إلى زيادة NOISE_LEVEL أو TREND_STRENGTH.")
    
    logger.info("✅ اكتمل إنشاء البيانات المتنوعة.")

if __name__ == "__main__":
    main()