# استيراد مكتبة واجهة المستخدم المحسنة
import customtkinter as ctk
# استيراد مربعات الرسائل، الجداول، ومربعات اختيار الملفات من tkinter
from tkinter import messagebox, ttk, filedialog
# استيراد الأنواع للـ type hints
from typing import Optional, Dict, Any, List
# استيراد وحدة التعبيرات النمطية
import re
# استيراد وحدة التعامل مع ملفات النظام
import os
# استيراد وحدة الخيوط للتحميل غير المتزامن
import threading

# استيراد خوارزمية bidi للتعامل مع النصوص الثنائية
from bidi.algorithm import get_display
# استيراد مكتبة إعادة تشكيل النصوص العربية
import arabic_reshaper

# استيراد خدمات العمل المختلفة
from services.order_service import OrderService  # خدمة الطلبات
from services.customer_service import CustomerService  # خدمة العملاء
from services.service_service import ServiceService  # خدمة الخدمات

# استيراد مدير قاعدة البيانات
from repositories.database import DatabaseManager
# استيراد نموذج الطلب
from models.order import Order
# استيراد مولد الفواتير
from utils.invoice_generator import InvoiceGenerator
# استيراد دوال عرض الرسائل
from utils.dialogs import show_info, show_success, show_warning, show_error, ask_yes_no
# استيراد مساعد التحميل غير المتزامن
from ui.async_helper import LoadingOverlay


def reshape_text(text: str) -> str:
    """
    إعادة تشكيل النص العربي وعرضه بشكل صحيح من اليمين لليسار
    تستقبل النص وتُعيده مُهيأ للعرض في الواجهة
    """
    if not text:  # إذا كان النص فارغاً أو None
        return ""  # أعد سلسلة فارغة
    try:  # محاولة معالجة النص
        reshaped = arabic_reshaper.reshape(text)  # أعد تشكيل النص العربي
        return get_display(reshaped)  # أعد توجيه النص من اليمين لليسار
    except Exception as e:  # في حالة حدوث خطأ
        return text  # أعد النص الأصلي بدون معالجة


class OrderUI:
    """
    واجهة إدارة الطلبات مع دعم كامل للغة العربية وتحسينات RTL
    تحتوي على جميع وظائف إضافة، تعديل، حذف، وفلاترة الطلبات
    """

    def __init__(self, parent: ctk.CTkFrame, order_service: OrderService,
                 customer_service: CustomerService, service_service: ServiceService,
                 db_manager: DatabaseManager, current_user: Dict[str, Any]):
        """
        تهيئة واجهة الطلبات
        parent: الإطار الأب
        order_service: خدمة إدارة الطلبات
        customer_service: خدمة إدارة العملاء
        service_service: خدمة إدارة الخدمات
        db_manager: مدير قاعدة البيانات
        current_user: المستخدم الحالي
        """
        self.parent = parent  # تخزين الإطار الأب
        self.order_service = order_service  # تخزين خدمة الطلبات
        self.customer_service = customer_service  # تخزين خدمة العملاء
        self.service_service = service_service
        self.db_manager = db_manager
        self.current_user = current_user
        self.customers = []
        self.services = []
        self.invoice_generator = InvoiceGenerator()  # تهيئة مولد الفواتير
        self._create_ui()
        self._load_orders()

    def _create_ui(self):
        """إنشاء واجهة المستخدم مع ترتيب RTL"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # عنوان الصفحة
        title_label = ctk.CTkLabel(
            main_frame,
            text="إدارة الطلبات",
            font=ctk.CTkFont(family="Cairo", size=24, weight="bold"),
            anchor="e"
        )
        title_label.pack(fill=ctk.X, pady=(0, 20))

        # إطار الفلترة
        filter_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        filter_frame.pack(fill=ctk.X, pady=(0, 15))

        # أزرار الإجراءات (على اليمين)
        actions_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        actions_frame.pack(side=ctk.RIGHT)

        add_btn = ctk.CTkButton(
            actions_frame,
            text="➕ إضافة طلب",
            command=self._add_order,
            width=140,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#2ec4b6",
            hover_color="#25a89c"
        )
        add_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        details_btn = ctk.CTkButton(
            actions_frame,
            text="👁️ عرض التفاصيل",
            command=self._view_order_details,
            width=130,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#4361ee",
            hover_color="#3a56d4"
        )
        details_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        update_btn = ctk.CTkButton(
            actions_frame,
            text="🔄 تحديث الحالة",
            command=self._update_order_status,
            width=130,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#f77f00",
            hover_color="#e07000"
        )
        update_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        invoice_btn = ctk.CTkButton(
            actions_frame,
            text="📄 إصدار فاتورة",
            command=self._generate_invoice,
            width=130,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#3f37c9",
            hover_color="#3528b5"
        )
        invoice_btn.pack(side=ctk.RIGHT)

        # عناصر الفلترة (على اليسار)
        filters_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filters_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        # فلترة حسب الحالة
        status_label = ctk.CTkLabel(
            filters_frame,
            text="الحالة:",
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        status_label.pack(side=ctk.LEFT, padx=(0, 5))

        self.status_var = ctk.StringVar(value="الكل")
        status_combo = ctk.CTkComboBox(
            filters_frame,
            values=["الكل", "قيد الانتظار", "قيد التنفيذ", "مكتمل", "ملغي"],
            variable=self.status_var,
            width=130,
            height=40,
            command=self._filter_orders,
            font=ctk.CTkFont(family="Cairo", size=13),
            dropdown_font=ctk.CTkFont(family="Cairo", size=13)
        )
        status_combo.pack(side=ctk.LEFT, padx=(0, 10))

        # فلترة حسب العميل
        customer_label = ctk.CTkLabel(
            filters_frame,
            text="العميل:",
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        customer_label.pack(side=ctk.LEFT, padx=(10, 5))

        self.customer_var = ctk.StringVar(value="الكل")
        self.customer_combo = ctk.CTkComboBox(
            filters_frame,
            values=["الكل"],
            variable=self.customer_var,
            width=180,
            height=40,
            command=self._filter_orders,
            font=ctk.CTkFont(family="Cairo", size=13),
            dropdown_font=ctk.CTkFont(family="Cairo", size=13)
        )
        self.customer_combo.pack(side=ctk.LEFT, padx=(0, 10))

        # فلترة حسب الخدمة
        service_label = ctk.CTkLabel(
            filters_frame,
            text="الخدمة:",
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        service_label.pack(side=ctk.LEFT, padx=(10, 5))

        self.service_var = ctk.StringVar(value="الكل")
        self.service_combo = ctk.CTkComboBox(
            filters_frame,
            values=["الكل"],
            variable=self.service_var,
            width=180,
            height=40,
            command=self._filter_orders,
            font=ctk.CTkFont(family="Cairo", size=13),
            dropdown_font=ctk.CTkFont(family="Cairo", size=13)
        )
        self.service_combo.pack(side=ctk.LEFT)

        # تحميل بيانات الفلاتر
        self._load_customers_list()
        self._load_services_list()

        # جدول الطلبات
        self._create_orders_table(main_frame)

    def _load_customers_list(self):
        """تحميل قائمة العملاء (باستخدام خيط منفصل)"""
        thread = threading.Thread(target=self._load_customers_thread)
        thread.daemon = True
        thread.start()
    
    def _load_customers_thread(self):
        """خيط تحميل العملاء"""
        try:
            customers = self.customer_service.get_customers()
            self.parent.after(0, lambda: self._display_customers_list(customers))
        except:
            pass
    
    def _display_customers_list(self, customers):
        """عرض قائمة العملاء في ComboBox"""
        self.customers = customers
        customers_list = ["الكل"] + [c.name for c in customers]
        self.customer_combo.configure(values=customers_list)

    def _load_services_list(self):
        """تحميل قائمة الخدمات (باستخدام خيط منفصل)"""
        thread = threading.Thread(target=self._load_services_thread)
        thread.daemon = True
        thread.start()
    
    def _load_services_thread(self):
        """خيط تحميل الخدمات"""
        try:
            services = self.service_service.get_services()
            self.parent.after(0, lambda: self._display_services_list(services))
        except:
            pass
    
    def _display_services_list(self, services):
        """عرض قائمة الخدمات في ComboBox"""
        self.services = services
        services_list = ["الكل"] + [s.name for s in services]
        self.service_combo.configure(values=services_list)

    def _create_orders_table(self, parent):

        """
        Create and configure a table (Treeview) to display orders.
        
        Args:
            parent: The parent widget where the table will be placed.
        """
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")  # Create a transparent frame
        table_frame.pack(fill=ctk.BOTH, expand=True)

        # ترتيب الأعمدة من اليمين لليسار
        columns = ("created_at", "status", "total_amount", "quantity", "services", "customer_name", "id")
        headings = {
            "id": "الرقم",
            "customer_name": "العميل",
            "services": "الخدمات",
            "quantity": "الكمية",
            "total_amount": "المبلغ",
            "status": "الحالة",
            "created_at": "التاريخ"
        }
        widths = {
            "id": 50,
            "customer_name": 180,
            "services": 250,
            "quantity": 80,
            "total_amount": 100,
            "status": 100,
            "created_at": 130
        }

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Orders.Treeview",
                        background="#f9f9f9",
                        foreground="black",
                        rowheight=40,
                        fieldbackground="#f9f9f9",
                        font=("Cairo", 12))
        style.map("Orders.Treeview",
                  background=[("selected", "#2b5b84")],
                  foreground=[("selected", "white")])
        style.configure("Orders.Treeview.Heading",
                        font=("Cairo", 13, "bold"),
                        background="#e9ecef",
                        foreground="black",
                        relief="flat")
        style.map("Orders.Treeview.Heading",
                  background=[("active", "#dee2e6")])

        self.orders_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
            style="Orders.Treeview"
        )

        for col in columns:
            self.orders_tree.heading(col, text=headings[col], anchor="center")
            self.orders_tree.column(col, width=widths[col], minwidth=80, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=ctk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)

        self.orders_tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y)

        self.orders_tree.bind("<Double-1>", lambda e: self._view_order_details())

    def _load_orders(self, status: str = None, customer_id: int = None, service_id: int = None):
        """تحميل وعرض الطلبات (باستخدام خيط منفصل)"""
        self._show_loading()
        
        thread = threading.Thread(target=self._load_orders_thread, args=(status, customer_id, service_id))
        thread.daemon = True
        thread.start()
    
    def _show_loading(self):
        """إظهار مؤشر التحميل"""
        self._hide_loading()
        
        self.loading_overlay = ctk.CTkFrame(self.orders_tree.master, fg_color=("white", "#2d2d44"))
        self.loading_overlay.place(relx=0.5, rely=0.5, anchor="center")
        
        self.loading_label = ctk.CTkLabel(
            self.loading_overlay,
            text="جاري التحميل...",
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        self.loading_label.pack(pady=20, padx=30)
        
        self.loading_progress = ctk.CTkProgressBar(
            self.loading_overlay,
            mode="indeterminate",
            width=150
        )
        self.loading_progress.pack(pady=(0, 20))
        self.loading_progress.start()
    
    def _hide_loading(self):
        """إخفاء مؤشر التحميل"""
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            try:
                if hasattr(self, 'loading_progress') and self.loading_progress:
                    self.loading_progress.stop()
                    self.loading_progress.destroy()
                if hasattr(self, 'loading_label') and self.loading_label:
                    self.loading_label.destroy()
                self.loading_overlay.destroy()
            except:
                pass
            self.loading_overlay = None
            self.loading_progress = None
            self.loading_label = None
    
    def _load_orders_thread(self, status: str, customer_id: int, service_id: int):
        """الخيط الذي يقوم بتحميل البيانات"""
        try:
            orders = self.order_service.get_orders(status, customer_id)
            self.parent.after(0, lambda: self._display_orders(orders, service_id))
        except Exception as e:
            self.parent.after(0, lambda: self._hide_loading())
    
    def _display_orders(self, orders, service_id: int = None):
        """عرض الطلبات في الجدول"""
        self._hide_loading()
        
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        status_map = {
            'pending': 'قيد الانتظار',
            'in_progress': 'قيد التنفيذ',
            'completed': 'مكتمل',
            'cancelled': 'ملغي'
        }

        filtered_orders = []
        for order in orders:
            service_names = order.service_names if hasattr(order, 'service_names') else ''
            service_ids = order.service_ids if hasattr(order, 'service_ids') else []

            if service_id and service_id not in service_ids:
                continue
            filtered_orders.append(order)

        for i, order in enumerate(filtered_orders):
            created_at = order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else ""
            status_text = status_map.get(order.status, order.status)

            tags = []
            if i % 2 == 0:
                tags.append("Even")
            else:
                tags.append("Odd")
            if order.status == 'completed':
                tags.append('completed')
            elif order.status == 'cancelled':
                tags.append('cancelled')
            elif order.status == 'in_progress':
                tags.append('in_progress')

            service_quantities = order.service_quantities if hasattr(order, 'service_quantities') else []
            total_quantity = sum(service_quantities) if service_quantities else 0
            
            self.orders_tree.insert(
                "",
                ctk.END,
                tags=tuple(tags),
                values=(
                    created_at,
                    status_text,
                    f"{order.total_amount:.2f} ر.س",
                    str(total_quantity),
                    order.service_names if hasattr(order, 'service_names') else '',
                    reshape_text(order.customer_name),
                    order.id
                )
            )

        self.orders_tree.tag_configure("Even", background="#f9f9f9")
        self.orders_tree.tag_configure("Odd", background="#ffffff")
        self.orders_tree.tag_configure('completed', foreground='#2ec4b6')
        self.orders_tree.tag_configure('cancelled', foreground='#ef233c')
        self.orders_tree.tag_configure('in_progress', foreground='#f77f00')

    def _filter_orders(self, choice=None):
        status_map = {
            'الكل': None,
            'قيد الانتظار': 'pending',
            'قيد التنفيذ': 'in_progress',
            'مكتمل': 'completed',
            'ملغي': 'cancelled'
        }
        status = status_map.get(self.status_var.get())

        customer_id = None
        if self.customer_var.get() != "الكل":
            for c in self.customers:
                if c.name == self.customer_var.get():
                    customer_id = c.id
                    break

        service_id = None
        if self.service_var.get() != "الكل":
            for s in self.services:
                if s.name == self.service_var.get():
                    service_id = s.id
                    break

        self._load_orders(status, customer_id, service_id)

    def _add_order(self):
        dialog = OrderDialog(self.parent, "إضافة طلب جديد",
                             self.customer_service, self.service_service)
        if dialog.result:
            try:
                # إنشاء الطلب
                order_id = self.order_service.add_order(
                    dialog.result["customer_id"],
                    dialog.result.get("notes"),
                    self.current_user['id']
                )
                # إضافة التفاصيل
                for detail in dialog.result["details"]:
                    self.order_service.add_order_detail(
                        order_id,
                        detail["service_id"],
                        detail["quantity"],
                        self.current_user['id']
                    )
                self._load_orders()
                messagebox.showinfo("نجاح", "تم إضافة الطلب بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء إضافة الطلب: {str(e)}", parent=self.parent)
                # للتصحيح: يمكن إزالة التعليق من السطر التالي
                # import traceback; traceback.print_exc()

    def _view_order_details(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار طلب لعرض تفاصيله", parent=self.parent)
            return

        order_id = self.orders_tree.item(selected[0])["values"][-1]
        order = self.order_service.get_order_by_id(order_id)

        if not order:
            messagebox.showerror("خطأ", "لم يتم العثور على الطلب", parent=self.parent)
            return

        status_map = {
            'pending': 'قيد الانتظار',
            'in_progress': 'قيد التنفيذ',
            'completed': 'مكتمل',
            'cancelled': 'ملغي'
        }
        status_text = status_map.get(order.status, order.status)

        # إنشاء نافذة مخصصة لعرض تفاصيل الطلب كفاتورة
        details_window = ctk.CTkToplevel(self.parent)
        details_window.title("فاتورة الطلب")
        details_window.geometry("450x550")
        details_window.resizable(False, False)

        # إطار رئيسي للفاتورة
        main_frame = ctk.CTkFrame(details_window, fg_color="white")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)

        # إطار العنوان
        header_frame = ctk.CTkFrame(main_frame, fg_color="#1a5f7a", height=60)
        header_frame.pack(fill=ctk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        # عنوان الفاتورة
        title_label = ctk.CTkLabel(
            header_frame, 
            text="فاتورة طلب", 
            font=("Cairo", 18, "bold"),
            text_color="white"
        )
        title_label.pack(pady=15)

        # إطار محتوى الفاتورة
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)

        # معلومات العميل والطلب
        customer_frame = ctk.CTkFrame(content_frame, fg_color="#f8f9fa", corner_radius=8)
        customer_frame.pack(fill=ctk.X, pady=(0, 12))

        # رقم الطلب والتاريخ
        order_info_frame = ctk.CTkFrame(customer_frame, fg_color="transparent")
        order_info_frame.pack(fill=ctk.X, padx=12, pady=(10, 5))

        order_id_label = ctk.CTkLabel(
            order_info_frame, 
            text=f"رقم الطلب: #{order.id}", 
            font=("Cairo", 12, "bold"),
            text_color="#1a5f7a",
            anchor="e"
        )
        order_id_label.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

        date_label = ctk.CTkLabel(
            order_info_frame, 
            text=order.created_at.strftime('%Y-%m-%d') if order.created_at else '—', 
            font=("Cairo", 10),
            text_color="#666",
            anchor="e"
        )
        date_label.pack(side=ctk.LEFT)

        # معلومات العميل
        customer_info_frame = ctk.CTkFrame(customer_frame, fg_color="transparent")
        customer_info_frame.pack(fill=ctk.X, padx=12, pady=(5, 10))

        customer_name_label = ctk.CTkLabel(
            customer_info_frame, 
            text=f"العميل: {order.customer_name}", 
            font=("Cairo", 12),
            text_color="#333",
            anchor="e"
        )
        customer_name_label.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

        contact_info = f"{order.customer_phone or ''}"
        if order.customer_email:
            contact_info += f" | {order.customer_email}"

        contact_label = ctk.CTkLabel(
            customer_info_frame, 
            text=contact_info, 
            font=("Cairo", 10),
            text_color="#666",
            anchor="e"
        )
        contact_label.pack(side=ctk.LEFT)

        # جدول الخدمات
        services_frame = ctk.CTkFrame(content_frame, fg_color="white")
        services_frame.pack(fill=ctk.BOTH, expand=True, pady=(0, 12))

        # رأس الجدول
        header_row = ctk.CTkFrame(services_frame, fg_color="#1a5f7a", height=30)
        header_row.pack(fill=ctk.X, pady=(0, 3))
        header_row.pack_propagate(False)

        service_header = ctk.CTkLabel(
            header_row, 
            text="الخدمة", 
            font=("Cairo", 10, "bold"),
            text_color="white",
            width=180
        )
        service_header.pack(side=ctk.RIGHT, padx=8, pady=4)

        qty_header = ctk.CTkLabel(
            header_row, 
            text="الكمية", 
            font=("Cairo", 10, "bold"),
            text_color="white",
            width=50
        )
        qty_header.pack(side=ctk.RIGHT, padx=8, pady=4)

        price_header = ctk.CTkLabel(
            header_row, 
            text="السعر", 
            font=("Cairo", 10, "bold"),
            text_color="white",
            width=70
        )
        price_header.pack(side=ctk.RIGHT, padx=8, pady=4)

        total_header = ctk.CTkLabel(
            header_row, 
            text="المجموع", 
            font=("Cairo", 10, "bold"),
            text_color="white",
            width=70
        )
        total_header.pack(side=ctk.RIGHT, padx=8, pady=4)

        # صفوف الخدمات
        if hasattr(order, 'details') and order.details:
            for i, detail in enumerate(order.details):
                service_name = detail.get('service_name', '')
                qty = detail.get('quantity', 1)
                price = detail.get('unit_price', 0)
                total = detail.get('total_price', qty * price)

                row_bg = "#f8f9fa" if i % 2 == 0 else "white"
                service_row = ctk.CTkFrame(services_frame, fg_color=row_bg, height=30)
                service_row.pack(fill=ctk.X, pady=0)
                service_row.pack_propagate(False)

                service_label = ctk.CTkLabel(
                    service_row, 
                    text=service_name, 
                    font=("Cairo", 10),
                    text_color="#333",
                    anchor="e",
                    width=180
                )
                service_label.pack(side=ctk.RIGHT, padx=8, pady=4)

                qty_label = ctk.CTkLabel(
                    service_row, 
                    text=str(qty), 
                    font=("Cairo", 10),
                    text_color="#333",
                    anchor="center",
                    width=50
                )
                qty_label.pack(side=ctk.RIGHT, padx=8, pady=4)

                price_label = ctk.CTkLabel(
                    service_row, 
                    text=f"{price:.2f}", 
                    font=("Cairo", 10),
                    text_color="#333",
                    anchor="e",
                    width=70
                )
                price_label.pack(side=ctk.RIGHT, padx=8, pady=4)

                total_label = ctk.CTkLabel(
                    service_row, 
                    text=f"{total:.2f}", 
                    font=("Cairo", 10, "bold"),
                    text_color="#1a5f7a",
                    anchor="e",
                    width=70
                )
                total_label.pack(side=ctk.RIGHT, padx=8, pady=4)

        # إجمالي الفاتورة
        total_frame = ctk.CTkFrame(content_frame, fg_color="#f8f9fa", corner_radius=8)
        total_frame.pack(fill=ctk.X, pady=(0, 12))

        total_amount_label = ctk.CTkLabel(
            total_frame, 
            text=f"المجموع الكلي: {order.total_amount:.2f} ر.س", 
            font=("Cairo", 14, "bold"),
            text_color="#1a5f7a"
        )
        total_amount_label.pack(pady=10)

        # الملاحظات
        if order.notes:
            notes_frame = ctk.CTkFrame(content_frame, fg_color="#f8f9fa", corner_radius=8)
            notes_frame.pack(fill=ctk.X, pady=(0, 12))

            notes_title = ctk.CTkLabel(
                notes_frame, 
                text="ملاحظات:", 
                font=("Cairo", 10, "bold"),
                text_color="#666",
                anchor="e"
            )
            notes_title.pack(fill=ctk.X, padx=12, pady=(8, 3))

            notes_text = ctk.CTkLabel(
                notes_frame, 
                text=order.notes, 
                font=("Cairo", 9),
                text_color="#333",
                anchor="e",
                wraplength=400
            )
            notes_text.pack(fill=ctk.X, padx=12, pady=(0, 8))

        # زر الإغلاق
        close_button = ctk.CTkButton(
            content_frame, 
            text="إغلاق", 
            command=details_window.destroy,
            font=("Cairo", 12, "bold"),
            fg_color="#1a5f7a",
            hover_color="#134b61",
            height=30,
            width=100
        )
        close_button.pack(pady=(5, 0))

    def _update_order_status(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار طلب لتحديث حالته", parent=self.parent)
            return

        order_id = self.orders_tree.item(selected[0])["values"][-1]
        dialog = StatusDialog(self.parent, "تحديث حالة الطلب")
        if dialog.result:
            try:
                self.order_service.update_order_status(
                    order_id,
                    dialog.result["status"],
                    self.current_user['id']
                )
                self._load_orders()
                messagebox.showinfo("نجاح", "تم تحديث حالة الطلب بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تحديث الحالة: {str(e)}", parent=self.parent)

    def _generate_invoice(self):
        """إصدار فاتورة للطلب المحدد"""
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار طلب لإصدار فاتورة", parent=self.parent)
            return

        order_id = self.orders_tree.item(selected[0])["values"][-1]
        order = self.order_service.get_order_by_id(order_id)

        if not order:
            messagebox.showerror("خطأ", "لم يتم العثور على الطلب", parent=self.parent)
            return

        status_map = {
            'pending': 'قيد الانتظار',
            'in_progress': 'قيد التنفيذ',
            'completed': 'مكتمل',
            'cancelled': 'ملغي'
        }
        status_text = status_map.get(order.status, order.status)

        # إنشاء نافذة مخصصة للفاتورة
        invoice_window = ctk.CTkToplevel(self.parent)
        invoice_window.title("فاتورة")
        invoice_window.geometry("600x750")
        invoice_window.resizable(False, False)

        # إطار رئيسي للفاتورة
        main_frame = ctk.CTkFrame(invoice_window, fg_color="white")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)

        # إطار العنوان
        header_frame = ctk.CTkFrame(main_frame, fg_color="#1a5f7a", height=80)
        header_frame.pack(fill=ctk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        # عنوان الفاتورة
        title_label = ctk.CTkLabel(
            header_frame,
            text="فاتورة رسمية",
            font=("Cairo", 22, "bold"),
            text_color="white"
        )
        title_label.pack(pady=15)

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text=f"رقم الطلب: #{order.id}",
            font=("Cairo", 12),
            text_color="#e0e0e0"
        )
        subtitle_label.pack(pady=(0, 5))

        # إطار محتوى الفاتورة
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        # معلومات العميل والطلب
        customer_frame = ctk.CTkFrame(content_frame, fg_color="#f8f9fa", corner_radius=10)
        customer_frame.pack(fill=ctk.X, pady=(0, 15))

        # معلومات العميل
        customer_info_frame = ctk.CTkFrame(customer_frame, fg_color="transparent")
        customer_info_frame.pack(fill=ctk.X, padx=15, pady=10)

        customer_name_label = ctk.CTkLabel(
            customer_info_frame,
            text=f"العميل: {order.customer_name}",
            font=("Cairo", 13, "bold"),
            text_color="#1a5f7a",
            anchor="e"
        )
        customer_name_label.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

        if order.customer_phone:
            phone_label = ctk.CTkLabel(
                customer_info_frame,
                text=f"الهاتف: {order.customer_phone}",
                font=("Cairo", 11),
                text_color="#666",
                anchor="e"
            )
            phone_label.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

        # معلومات الطلب
        order_info_frame = ctk.CTkFrame(customer_frame, fg_color="transparent")
        order_info_frame.pack(fill=ctk.X, padx=15, pady=(0, 10))

        date_label = ctk.CTkLabel(
            order_info_frame,
            text=f"التاريخ: {order.created_at.strftime('%Y-%m-%d') if order.created_at else '—'}",
            font=("Cairo", 11),
            text_color="#666",
            anchor="e"
        )
        date_label.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

        status_label = ctk.CTkLabel(
            order_info_frame,
            text=f"الحالة: {status_text}",
            font=("Cairo", 11, "bold"),
            text_color="#2ec4b6" if order.status == 'completed' else "#f77f00",
            anchor="e"
        )
        status_label.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)

        # جدول الخدمات
        services_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10, border_width=2, border_color="#e0e0e0")
        services_frame.pack(fill=ctk.BOTH, expand=True, pady=(0, 15))

        # رأس الجدول
        header_row = ctk.CTkFrame(services_frame, fg_color="#1a5f7a", height=40)
        header_row.pack(fill=ctk.X, pady=(0, 5))
        header_row.pack_propagate(False)

        service_header = ctk.CTkLabel(
            header_row,
            text="الخدمة",
            font=("Cairo", 12, "bold"),
            text_color="white",
            width=250
        )
        service_header.pack(side=ctk.RIGHT, padx=10, pady=8)

        qty_header = ctk.CTkLabel(
            header_row,
            text="الكمية",
            font=("Cairo", 12, "bold"),
            text_color="white",
            width=60
        )
        qty_header.pack(side=ctk.RIGHT, padx=10, pady=8)

        price_header = ctk.CTkLabel(
            header_row,
            text="السعر",
            font=("Cairo", 12, "bold"),
            text_color="white",
            width=80
        )
        price_header.pack(side=ctk.RIGHT, padx=10, pady=8)

        total_header = ctk.CTkLabel(
            header_row,
            text="المجموع",
            font=("Cairo", 12, "bold"),
            text_color="white",
            width=80
        )
        total_header.pack(side=ctk.RIGHT, padx=10, pady=8)

        # صفوف الخدمات
        if hasattr(order, 'details') and order.details:
            for i, detail in enumerate(order.details):
                service_name = detail.get('service_name', '')
                qty = detail.get('quantity', 1)
                price = detail.get('unit_price', 0)
                total = detail.get('total_price', qty * price)

                row_bg = "#f8f9fa" if i % 2 == 0 else "white"
                service_row = ctk.CTkFrame(services_frame, fg_color=row_bg, height=40)
                service_row.pack(fill=ctk.X, pady=0)
                service_row.pack_propagate(False)

                service_label = ctk.CTkLabel(
                    service_row,
                    text=service_name,
                    font=("Cairo", 11),
                    text_color="#333",
                    anchor="e",
                    width=250
                )
                service_label.pack(side=ctk.RIGHT, padx=10, pady=8)

                qty_label = ctk.CTkLabel(
                    service_row,
                    text=str(qty),
                    font=("Cairo", 11),
                    text_color="#333",
                    anchor="center",
                    width=60
                )
                qty_label.pack(side=ctk.RIGHT, padx=10, pady=8)

                price_label = ctk.CTkLabel(
                    service_row,
                    text=f"{price:.2f}",
                    font=("Cairo", 11),
                    text_color="#333",
                    anchor="e",
                    width=80
                )
                price_label.pack(side=ctk.RIGHT, padx=10, pady=8)

                total_label = ctk.CTkLabel(
                    service_row,
                    text=f"{total:.2f}",
                    font=("Cairo", 11, "bold"),
                    text_color="#1a5f7a",
                    anchor="e",
                    width=80
                )
                total_label.pack(side=ctk.RIGHT, padx=10, pady=8)
        else:
            no_data_label = ctk.CTkLabel(
                services_frame,
                text="لا توجد خدمات",
                font=("Cairo", 12),
                text_color="#999",
                anchor="center"
            )
            no_data_label.pack(pady=30)

        # إجمالي الفاتورة
        total_frame = ctk.CTkFrame(content_frame, fg_color="#1a5f7a", corner_radius=10)
        total_frame.pack(fill=ctk.X, pady=(0, 15))

        total_amount_label = ctk.CTkLabel(
            total_frame,
            text=f"المجموع الكلي: {order.total_amount:.2f} ر.س",
            font=("Cairo", 16, "bold"),
            text_color="white"
        )
        total_amount_label.pack(pady=15)

        # الملاحظات
        if order.notes:
            notes_frame = ctk.CTkFrame(content_frame, fg_color="#f8f9fa", corner_radius=10)
            notes_frame.pack(fill=ctk.X, pady=(0, 15))

            notes_title = ctk.CTkLabel(
                notes_frame,
                text="ملاحظات:",
                font=("Cairo", 11, "bold"),
                text_color="#666",
                anchor="e"
            )
            notes_title.pack(fill=ctk.X, padx=15, pady=(10, 5))

            notes_text = ctk.CTkLabel(
                notes_frame,
                text=order.notes,
                font=("Cairo", 10),
                text_color="#333",
                anchor="e",
                wraplength=550
            )
            notes_text.pack(fill=ctk.X, padx=15, pady=(0, 10))

        # أزرار الإجراءات
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=(0, 10))

        print_btn = ctk.CTkButton(
            buttons_frame,
            text="🖨️ طباعة",
            command=lambda: self._print_invoice(invoice_window),
            font=("Cairo", 12, "bold"),
            fg_color="#2ec4b6",
            hover_color="#25a89c",
            height=35,
            width=120
        )
        print_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        close_btn = ctk.CTkButton(
            buttons_frame,
            text="إغلاق",
            command=invoice_window.destroy,
            font=("Cairo", 12, "bold"),
            fg_color="#ef233c",
            hover_color="#d90429",
            height=35,
            width=120
        )
        close_btn.pack(side=ctk.LEFT, padx=(0, 5))

    def _print_invoice(self, window):
        """طباعة الفاتورة"""
        try:
            # الحصول على الطلب المحدد
            selected = self.orders_tree.selection()
            if not selected:
                messagebox.showwarning("تحذير", "الرجاء اختيار طلب للطباعة", parent=window)
                return

            order_id = self.orders_tree.item(selected[0])["values"][-1]
            order = self.order_service.get_order_by_id(order_id)

            if not order:
                messagebox.showerror("خطأ", "لم يتم العثور على الطلب", parent=window)
                return

            # إنشاء مجلد للفواتير إذا لم يكن موجوداً
            invoices_dir = os.path.join(os.path.dirname(__file__), '..', 'invoices')
            os.makedirs(invoices_dir, exist_ok=True)

            # توليد ملف PDF
            filename = f"invoice_{order.id}_{order.created_at.strftime('%Y%m%d_%H%M%S') if order.created_at else 'unknown'}.pdf"
            output_path = os.path.join(invoices_dir, filename)

            self.invoice_generator.generate_invoice(order, output_path)

            # فتح ملف PDF
            import subprocess
            import platform

            if platform.system() == 'Windows':
                os.startfile(output_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', output_path])
            else:  # Linux
                subprocess.run(['xdg-open', output_path])

            messagebox.showinfo("نجاح", "تم إنشاء الفاتورة بنجاح!", parent=window)

        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الطباعة: {str(e)}", parent=window)

    def _export_invoice(self):
        """تصدير الفاتورة"""
        try:
            # الحصول على الطلب المحدد
            selected = self.orders_tree.selection()
            if not selected:
                messagebox.showwarning("تحذير", "الرجاء اختيار طلب لتصدير فاتورته", parent=self.parent)
                return

            order_id = self.orders_tree.item(selected[0])["values"][-1]
            order = self.order_service.get_order_by_id(order_id)

            if not order:
                messagebox.showerror("خطأ", "لم يتم العثور على الطلب", parent=self.parent)
                return

            # طلب مسار حفظ الملف
            filename = f"invoice_{order.id}_{order.created_at.strftime('%Y%m%d_%H%M%S') if order.created_at else 'unknown'}.pdf"
            file_path = filedialog.asksaveasfilename(
                title="حفظ الفاتورة",
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
                initialfile=filename
            )

            if not file_path:
                return

            # توليد ملف PDF
            self.invoice_generator.generate_invoice(order, file_path)

            messagebox.showinfo("نجاح", "تم تصدير الفاتورة بنجاح!", parent=self.parent)

        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التصدير: {str(e)}", parent=self.parent)


class OrderDialog:
    def __init__(self, parent: ctk.CTkFrame, title: str,
                 customer_service: CustomerService, service_service: ServiceService):
        self.result = None
        self.customer_service = customer_service
        self.service_service = service_service

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("650x650")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()

        self._create_ui()
        self._center_window()
        self.dialog.wait_window()

    def _create_ui(self):
        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=20)

        title_label = ctk.CTkLabel(
            container,
            text="إنشاء طلب جديد",
            font=ctk.CTkFont(family="Cairo", size=18, weight="bold"),
            anchor="center"
        )
        title_label.pack(pady=(0, 15))

        # اختيار العميل
        cust_label = ctk.CTkLabel(
            container,
            text="اختر العميل:*",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color="#2b5b84"
        )
        cust_label.pack(fill="x", pady=(0, 5))

        customers = self.customer_service.get_customers()
        self.customer_combo = ctk.CTkComboBox(
            container,
            values=[c.name for c in customers],
            height=40,
            font=ctk.CTkFont(family="Cairo", size=13),
            dropdown_font=ctk.CTkFont(family="Cairo", size=13)
        )
        self.customer_combo.pack(fill="x", pady=(0, 15))

        # اختيار الخدمات
        services_label = ctk.CTkLabel(
            container,
            text="اختر الخدمات (مع الكميات):*",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color="#2b5b84"
        )
        services_label.pack(fill="x", pady=(0, 5))

        services_scroll = ctk.CTkScrollableFrame(container, height=250)
        services_scroll.pack(fill="both", expand=True, pady=(0, 15))

        services = self.service_service.get_services()
        self.service_entries = []

        for service in services:
            frame = ctk.CTkFrame(services_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=2)

            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(
                frame,
                text="",
                variable=var,
                width=20
            )
            chk.pack(side=ctk.RIGHT, padx=(5, 0))

            name_label = ctk.CTkLabel(
                frame,
                text=reshape_text(service.name),
                font=ctk.CTkFont(family="Cairo", size=13),
                anchor="e"
            )
            name_label.pack(side=ctk.RIGHT, padx=(5, 0))

            price_label = ctk.CTkLabel(
                frame,
                text=f"{service.price:.2f} ر.س",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            price_label.pack(side=ctk.RIGHT, padx=(10, 0))

            qty_entry = ctk.CTkEntry(
                frame,
                width=60,
                height=30,
                justify="center",
                font=ctk.CTkFont(size=13),
                placeholder_text="1"
            )
            qty_entry.insert(0, "1")
            qty_entry.pack(side=ctk.LEFT, padx=(5, 0))

            self.service_entries.append({
                'service_id': service.id,
                'name': service.name,
                'price': service.price,
                'var': var,
                'qty_entry': qty_entry
            })

        # ملاحظات
        notes_label = ctk.CTkLabel(
            container,
            text="ملاحظات:",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14),
            text_color="gray"
        )
        notes_label.pack(fill="x", pady=(0, 5))

        self.notes_text = ctk.CTkTextbox(container, height=60, font=ctk.CTkFont(family="Cairo", size=13))
        self.notes_text.pack(fill="x", pady=(0, 15))

        # الأزرار
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="حفظ الطلب",
            command=self._save,
            height=45,
            font=ctk.CTkFont(family="Cairo", size=15, weight="bold"),
            fg_color="#4361ee",
            hover_color="#3a56d4"
        )
        save_btn.pack(side=ctk.RIGHT, padx=(5, 0), expand=True, fill="x")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="إلغاء",
            command=self._cancel,
            height=45,
            font=ctk.CTkFont(family="Cairo", size=15),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side=ctk.LEFT, padx=(0, 5), expand=True, fill="x")

        self.dialog.bind("<Return>", lambda e: self._save())
        self.dialog.bind("<Escape>", lambda e: self._cancel())
        self.customer_combo.focus()

    def _center_window(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")

    def _save(self):
        customer_name = self.customer_combo.get().strip()
        if not customer_name:
            messagebox.showwarning("تحذير", "الرجاء اختيار عميل", parent=self.dialog)
            return

        customers = self.customer_service.get_customers(customer_name)
        if not customers:
            messagebox.showerror("خطأ", "لم يتم العثور على العميل", parent=self.dialog)
            return
        customer_id = customers[0].id

        details = []
        for entry in self.service_entries:
            if entry['var'].get():
                qty_str = entry['qty_entry'].get().strip()
                try:
                    qty = int(qty_str) if qty_str else 1
                    if qty <= 0:
                        qty = 1
                except ValueError:
                    qty = 1
                details.append({
                    'service_id': entry['service_id'],
                    'quantity': qty,
                    'name': entry['name'],
                    'price': entry['price']
                })

        if not details:
            messagebox.showwarning("تحذير", "الرجاء اختيار خدمة واحدة على الأقل", parent=self.dialog)
            return

        notes = self.notes_text.get("1.0", "end-1c").strip() or None

        self.result = {
            "customer_id": customer_id,
            "notes": notes,
            "details": details
        }
        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()


class StatusDialog:
    def __init__(self, parent: ctk.CTkFrame, title: str):
        self.result = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()

        self._create_ui()
        self._center_window()
        self.dialog.wait_window()

    def _create_ui(self):
        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=25)

        title_label = ctk.CTkLabel(
            container,
            text="تحديث حالة الطلب",
            font=ctk.CTkFont(family="Cairo", size=18, weight="bold"),
            anchor="center"
        )
        title_label.pack(pady=(0, 20))

        status_label = ctk.CTkLabel(
            container,
            text="اختر الحالة الجديدة:*",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color="#2b5b84"
        )
        status_label.pack(fill="x", pady=(0, 5))

        self.status_var = ctk.StringVar(value="قيد الانتظار")
        status_combo = ctk.CTkComboBox(
            container,
            values=["قيد الانتظار", "قيد التنفيذ", "مكتمل", "ملغي"],
            variable=self.status_var,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=13),
            dropdown_font=ctk.CTkFont(family="Cairo", size=13)
        )
        status_combo.pack(fill="x", pady=(0, 20))

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="حفظ",
            command=self._save,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            fg_color="#4361ee",
            hover_color="#3a56d4"
        )
        save_btn.pack(side=ctk.RIGHT, padx=(5, 0), expand=True, fill="x")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="إلغاء",
            command=self._cancel,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.pack(side=ctk.LEFT, padx=(0, 5), expand=True, fill="x")

        self.dialog.bind("<Return>", lambda e: self._save())
        self.dialog.bind("<Escape>", lambda e: self._cancel())

    def _center_window(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")

    def _save(self):
        status_map = {
            'قيد الانتظار': 'pending',
            'قيد التنفيذ': 'in_progress',
            'مكتمل': 'completed',
            'ملغي': 'cancelled'
        }
        status = status_map.get(self.status_var.get())
        if not status:
            messagebox.showwarning("تحذير", "الرجاء اختيار حالة", parent=self.dialog)
            return
        self.result = {"status": status}
        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()