# -*- coding: utf-8 -*-
"""
services/import_export_service.py
----------------------------------
خدمات استيراد وتصدير البيانات.

تحتوي على:
- DataImporterService: استيراد البيانات من ملفات Excel و CSV
- DataExporterService: تصدير البيانات إلى ملفات Excel و CSV

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

import pandas as pd
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from repositories.database import DatabaseManager


class DataImporterService:
    """فئة استيراد البيانات من ملفات Excel و CSV"""

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة مستورد البيانات

        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db_manager = db_manager

    def import_customers_from_file(self, file_path: str, created_by: int = None) -> Dict[str, Any]:
        """استيراد العملاء من ملف Excel أو CSV

        Args:
            file_path: مسار الملف
            created_by: معرف المستخدم المنشئ

        Returns:
            قاموس يحتوي على نتيجة الاستيراد
        """
        try:
            # قراءة الملف
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {'success': False, 'message': 'نوع الملف غير مدعوم'}

            # التحقق من الأعمدة المطلوبة
            required_columns = ['name', 'phone']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {'success': False, 'message': f'الأعمدة المطلوبة مفقودة: {", ".join(missing_columns)}'}

            # استيراد البيانات
            imported_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    name = str(row.get('name', '')).strip()
                    phone = str(row.get('phone', '')).strip()
                    email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None
                    address = str(row.get('address', '')).strip() if pd.notna(row.get('address')) else None
                    notes = str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else None

                    if name and phone:
                        self.db_manager.insert_customer(
                            name=name,
                            phone=phone,
                            email=email if email != 'nan' else None,
                            address=address if address != 'nan' else None,
                            notes=notes if notes != 'nan' else None,
                            created_by=created_by
                        )
                        imported_count += 1
                    else:
                        error_count += 1
                        errors.append(f"الصف {index + 2}: الاسم أو الهاتف فارغ")

                except Exception as e:
                    error_count += 1
                    errors.append(f"الصف {index + 2}: {str(e)}")

            # تسجيل لنشاط
            self.db_manager.log_activity(
                created_by,
                "استيراد عملاء",
                "customers",
                None,
                f"استيراد {imported_count} عميل من الملف"
            )

            return {
                'success': True,
                'imported': imported_count,
                'errors': error_count,
                'error_details': errors[:10]  # إظهار أول 10 أخطاء فقط
            }

        except Exception as e:
            return {'success': False, 'message': f'حدث خطأ أثناء قراءة الملف: {str(e)}'}

    def import_services_from_file(self, file_path: str, created_by: int = None) -> Dict[str, Any]:
        """استيراد الخدمات من ملف Excel أو CSV

        Args:
            file_path: مسار الملف
            created_by: معرف المستخدم المنشئ

        Returns:
            قاموس يحتوي على نتيجة الاستيراد
        """
        try:
            # قراءة الملف
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {'success': False, 'message': 'نوع الملف غير مدعوم'}

            # التحقق من الأعمدة المطلوبة
            required_columns = ['name', 'price']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {'success': False, 'message': f'الأعمدة المطلوبة مفقودة: {", ".join(missing_columns)}'}

            # الحصول على الفئات الموجودة
            categories = self.db_manager.get_service_categories()
            category_map = {cat['name']: cat['id'] for cat in categories}

            # استيراد البيانات
            imported_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    name = str(row.get('name', '')).strip()
                    price = row.get('price')
                    description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None
                    category_name = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None

                    if name and price:
                        # البحث عن معرف الفئة
                        category_id = None
                        if category_name and category_name != 'nan' and category_name in category_map:
                            category_id = category_map[category_name]

                        self.db_manager.insert_service(
                            name=name,
                            description=description if description != 'nan' else None,
                            price=float(price),
                            category_id=category_id
                        )
                        imported_count += 1
                    else:
                        error_count += 1
                        errors.append(f"الصف {index + 2}: الاسم أو السعر فارغ")

                except Exception as e:
                    error_count += 1
                    errors.append(f"الصف {index + 2}: {str(e)}")

            # تسجيل النشاط
            self.db_manager.log_activity(
                created_by,
                "استيراد خدمات",
                "services",
                None,
                f"استيراد {imported_count} خدمة من الملف"
            )

            return {
                'success': True,
                'imported': imported_count,
                'errors': error_count,
                'error_details': errors[:10]
            }

        except Exception as e:
            return {'success': False, 'message': f'حدث خطأ أثناء قراءة الملف: {str(e)}'}

    def import_orders_from_file(self, file_path: str, created_by: int = None) -> Dict[str, Any]:
        """استيراد الطلبات من ملف Excel أو CSV

        Args:
            file_path: مسار الملف
            created_by: معرف المستخدم المنشئ

        Returns:
            قاموس يحتوي على نتيجة الاستيراد
        """
        try:
            # قراءة الملف
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {'success': False, 'message': 'نوع الملف غير مدعوم'}

            # التحقق من الأعمدة المطلوبة
            required_columns = ['customer_name', 'service_name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {'success': False, 'message': f'الأعمدة المطلوبة مفقودة: {", ".join(missing_columns)}'}

            # استيراد البيانات
            imported_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    customer_name = str(row.get('customer_name', '')).strip()
                    service_name = str(row.get('service_name', '')).strip()
                    notes = str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else None
                    status = str(row.get('status', 'pending')).strip()

                    if customer_name and service_name:
                        # البحث عن العميل - جلب كل العملاء والبحث بالمطابقة التامة
                        all_customers = self.db_manager.get_customers()
                        customers = None
                        for c in all_customers:
                            if c['name'] == customer_name:
                                customers = [c]
                                break
                        if not customers:
                            error_count += 1
                            errors.append(f"الصف {index + 2}: العميل '{customer_name}' غير موجود")
                            continue
                        customer_id = customers[0]['id']

                        # البحث عن الخدمة - جلب كل الخدمات والبحث بالمطابقة التامة
                        all_services = self.db_manager.get_services()
                        services = None
                        for s in all_services:
                            if s['name'] == service_name:
                                services = [s]
                                break
                        if not services:
                            error_count += 1
                            errors.append(f"الصف {index + 2}: الخدمة '{service_name}' غير موجودة")
                            continue
                        service_id = services[0]['id']

                        # إنشاء الطلب
                        order_id = self.db_manager.insert_order(
                            customer_id=customer_id,
                            notes=notes if notes != 'nan' else None,
                            created_by=created_by
                        )

                        # إضافة تفاصيل الطلب
                        self.db_manager.add_order_detail(
                            order_id=order_id,
                            service_id=service_id,
                            quantity=int(row.get('quantity', 1)),
                            unit_price=services[0]['price']
                        )

                        # تحديث الحالة إذا تم تحديدها
                        if status and status != 'nan':
                            status_map = {
                                'pending': 'pending',
                                'in_progress': 'in_progress',
                                'completed': 'completed',
                                'cancelled': 'cancelled'
                            }
                            if status.lower() in status_map:
                                self.db_manager.update_order_status(order_id, status_map[status.lower()])

                        imported_count += 1
                    else:
                        error_count += 1
                        errors.append(f"الصف {index + 2}: اسم العميل أو الخدمة فارغ")

                except Exception as e:
                    error_count += 1
                    errors.append(f"الصف {index + 2}: {str(e)}")

            # تسجيل النشاط
            self.db_manager.log_activity(
                created_by,
                "استيراد طلبات",
                "orders",
                None,
                f"استيراد {imported_count} طلب من الملف"
            )

            return {
                'success': True,
                'imported': imported_count,
                'errors': error_count,
                'error_details': errors[:10]
            }

        except Exception as e:
            return {'success': False, 'message': f'حدث خطأ أثناء قراءة الملف: {str(e)}'}


class DataExporterService:
    """فئة تصدير البيانات إلى ملفات Excel و CSV"""

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة مصدر البيانات

        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db_manager = db_manager

    def export_customers(self, file_path: str, format: str = 'xlsx') -> bool:
        """تصدير العملاء إلى ملف

        Args:
            file_path: مسار الملف
            format: تنسيق الملف (xlsx أو csv)

        Returns:
            True إذا نجح التصدير
        """
        try:
            customers = self.db_manager.get_customers()

            if not customers:
                return False

            # تحويل البيانات إلى DataFrame
            data = []
            for customer in customers:
                data.append({
                    'الاسم': customer['name'],
                    'الهاتف': customer['phone'],
                    'البريد الإلكتروني': customer.get('email', ''),
                    'العنوان': customer.get('address', ''),
                    'ملاحظات': customer.get('notes', ''),
                    'تاريخ الإضافة': customer.get('created_at', '')
                })

            df = pd.DataFrame(data)

            # حفظ الملف
            if format == 'csv':
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(file_path, index=False)

            return True

        except Exception:
            return False

    def export_services(self, file_path: str, format: str = 'xlsx') -> bool:
        """تصدير الخدمات إلى ملف

        Args:
            file_path: مسار الملف
            format: تنسيق الملف (xlsx أو csv)

        Returns:
            True إذا نجح التصدير
        """
        try:
            services = self.db_manager.get_services()

            if not services:
                return False

            # الحصول على الفئات
            categories = self.db_manager.get_service_categories()
            category_map = {cat['id']: cat['name'] for cat in categories}

            # تحويل البيانات إلى DataFrame
            data = []
            for service in services:
                data.append({
                    'اسم الخدمة': service['name'],
                    'الوصف': service.get('description', ''),
                    'السعر': service['price'],
                    'الفئة': category_map.get(service.get('category_id'), ''),
                    'تاريخ الإضافة': service.get('created_at', '')
                })

            df = pd.DataFrame(data)

            # حفظ الملف
            if format == 'csv':
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(file_path, index=False)

            return True

        except Exception:
            return False

    def export_orders(self, file_path: str, format: str = 'xlsx') -> bool:
        """تصدير الطلبات إلى ملف

        Args:
            file_path: مسار الملف
            format: تنسيق الملف (xlsx أو csv)

        Returns:
            True إذا نجح التصدير
        """
        try:
            orders = self.db_manager.get_orders()

            if not orders:
                return False

            # تحويل البيانات إلى DataFrame
            data = []
            status_map = {
                'pending': 'قيد الانتظار',
                'in_progress': 'قيد التنفيذ',
                'completed': 'مكتمل',
                'cancelled': 'ملغي'
            }

            for order in orders:
                data.append({
                    'رقم الطلب': order['id'],
                    'اسم العميل': order.get('customer_name', ''),
                    'المبلغ الإجمالي': order.get('total_amount', 0),
                    'الحالة': status_map.get(order.get('status', ''), order.get('status', '')),
                    'ملاحظات': order.get('notes', ''),
                    'تاريخ الإنشاء': order.get('created_at', '')
                })

            df = pd.DataFrame(data)

            # حفظ الملف
            if format == 'csv':
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(file_path, index=False)

            return True

        except Exception:
            return False


# ==========================================
# أسماء مستعارة للتوافق مع واجهة المستخدم
# ==========================================
DataImporter = DataImporterService
DataExporter = DataExporterService


def create_template_files() -> Dict[str, str]:
    """إنشاء ملفات قالب للاستيراد
    
    Returns:
        قاموس بمسارات الملفات المنشأة
    """
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    created_files = {}
    
    # قالب العملاء
    customers_template = pd.DataFrame([
        {'name': 'اسم العميل', 'phone': '05xxxxxxxx', 'email': 'email@example.com', 'address': 'العنوان', 'notes': 'ملاحظات'}
    ])
    customers_path = os.path.join(templates_dir, 'قالب_العملاء.csv')
    customers_template.to_csv(customers_path, index=False, encoding='utf-8-sig')
    created_files['customers'] = customers_path
    
    # قالب الخدمات
    services_template = pd.DataFrame([
        {'name': 'اسم الخدمة', 'price': 100.0, 'description': 'وصف الخدمة', 'category': 'فئة الخدمة'}
    ])
    services_path = os.path.join(templates_dir, 'قالب_الخدمات.csv')
    services_template.to_csv(services_path, index=False, encoding='utf-8-sig')
    created_files['services'] = services_path
    
    # قالب الطلبات
    orders_template = pd.DataFrame([
        {'customer_name': 'اسم العميل', 'service_name': 'اسم الخدمة', 'quantity': 1, 'status': 'pending', 'notes': 'ملاحظات'}
    ])
    orders_path = os.path.join(templates_dir, 'قالب_الطلبات.csv')
    orders_template.to_csv(orders_path, index=False, encoding='utf-8-sig')
    created_files['orders'] = orders_path
    
    return created_files