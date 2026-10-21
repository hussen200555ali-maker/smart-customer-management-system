# ui/customer_ui.py - واجهة إدارة العملاء

# استيراد مكتبة واجهة المستخدم المحسنة
import customtkinter as ctk
# استيراد الجداول من tkinter
from tkinter import ttk
# استيراد الأنواع للـ type hints
from typing import Optional, Dict, Any
# استيراد وحدة التعبيرات النمطية
import re
# استيراد وحدة الخيوط للتحميل غير المتزامن
import threading

# استيراد خوارزمية bidi للتعامل مع النصوص الثنائية
from bidi.algorithm import get_display
# استيراد مكتبة إعادة تشكيل النصوص العربية
import arabic_reshaper

# استيراد خدمة العملاء
from services.customer_service import CustomerService
# استيراد مدير قاعدة البيانات
from repositories.database import DatabaseManager
# استيراد نموذج العميل
from models.customer import Customer
# استيراد دوال عرض الرسائل
from utils.dialogs import show_success, show_error, show_warning, ask_yes_no
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


class CustomerUI:
    """واجهة إدارة العملاء مع دعم كامل للغة العربية وتحسينات RTL"""
    def __init__(self, parent: ctk.CTkFrame, customer_service: CustomerService,
                 db_manager: DatabaseManager, current_user: Dict[str, Any]):
        self.parent = parent
        self.customer_service = customer_service
        self.db_manager = db_manager
        self.current_user = current_user

        self._create_ui()
        self._load_customers()

    def _create_ui(self):
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # العنوان
        title_label = ctk.CTkLabel(
            main_frame,
            text="إدارة العملاء",
            font=ctk.CTkFont(family="Cairo", size=24, weight="bold"),
            anchor="e"
        )
        title_label.pack(fill=ctk.X, pady=(0, 20))

        # شريط الأدوات
        toolbar_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        toolbar_frame.pack(fill=ctk.X, pady=(0, 15))

        # أزرار الإجراءات (تظهر على اليمين)
        actions_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        actions_frame.pack(side=ctk.RIGHT)

        add_btn = ctk.CTkButton(
            actions_frame,
            text="➕ إضافة عميل",
            command=self._add_customer,
            width=140,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        add_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️ تعديل",
            command=self._edit_customer,
            width=100,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#2b5b84",
            hover_color="#1f4569"
        )
        edit_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️ حذف",
            command=self._delete_customer,
            width=100,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#b33c3c",
            hover_color="#8f2e2e"
        )
        delete_btn.pack(side=ctk.RIGHT)

        # البحث
        search_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        search_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 ابحث بالاسم أو رقم الهاتف...",
            width=300,
            height=40,
            justify="right",
            font=ctk.CTkFont(family="Cairo", size=13)
        )
        self.search_entry.pack(side=ctk.LEFT, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._search_customers())

        search_btn = ctk.CTkButton(
            search_frame,
            text="بحث",
            width=80,
            height=40,
            command=self._search_customers,
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        search_btn.pack(side=ctk.LEFT)

        # جدول العملاء
        self._create_customers_table(main_frame)

    def _create_customers_table(self, parent):
        """إنشاء جدول عرض العملاء مع تحسينات المظهر (ارتفاع صفوف أكبر، ألوان متناوبة)"""
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill=ctk.BOTH, expand=True)

        columns = ("created_at", "address", "email", "phone", "name", "id")
        headings = {
            "id": "المعرف",
            "name": "الاسم",
            "phone": "الهاتف",
            "email": "البريد الإلكتروني",
            "address": "العنوان",
            "created_at": "تاريخ الإضافة"
        }
        widths = {
            "id": 60,
            "name": 180,
            "phone": 120,
            "email": 200,
            "address": 220,
            "created_at": 130
        }

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                        background="#f9f9f9",
                        foreground="black",
                        rowheight=40,
                        fieldbackground="#f9f9f9",
                        font=("Cairo", 12))
        style.map("Custom.Treeview",
                  background=[("selected", "#2b5b84")],
                  foreground=[("selected", "white")])
        style.configure("Custom.Treeview.Heading",
                        font=("Cairo", 13, "bold"),
                        background="#e9ecef",
                        foreground="black",
                        relief="flat")
        style.map("Custom.Treeview.Heading",
                  background=[("active", "#dee2e6")])
        style.configure("Even.Treeview", background="#f9f9f9")
        style.configure("Odd.Treeview", background="#ffffff")

        self.customers_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
            style="Custom.Treeview"
        )

        for col in columns:
            self.customers_tree.heading(col, text=headings[col], anchor="center")
            self.customers_tree.column(col, width=widths[col], minwidth=80, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=ctk.VERTICAL, command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)

        self.customers_tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y)

        self.customers_tree.bind("<Double-1>", lambda e: self._edit_customer())

    def _load_customers(self, search_term: str = None):
        """تحميل العملاء وعرضهم في الجدول (باستخدام خيط منفصل)"""
        # إظهار مؤشر التحميل
        self._show_loading()
        
        # تشغيل التحميل في خيط منفصل
        thread = threading.Thread(target=self._load_customers_thread, args=(search_term,))
        thread.daemon = True
        thread.start()
    
    def _show_loading(self):
        """إظهار مؤشر التحميل"""
        # حذف أي تحميل سابق
        self._hide_loading()
        
        # إنشاء طبقة التحميل
        self.loading_overlay = ctk.CTkFrame(self.customers_tree.master, fg_color=("white", "#2d2d44"))
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
    
    def _load_customers_thread(self, search_term: str):
        """الخيط الذي يقوم بتحميل البيانات"""
        try:
            customers = self.customer_service.get_customers(search_term)
            # تحديث الواجهة في الخيط الرئيسي
            self.parent.after(0, lambda: self._display_customers(customers))
        except Exception as e:
            self.parent.after(0, lambda: self._hide_loading())
    
    def _display_customers(self, customers):
        """عرض العملاء في الجدول"""
        # إخفاء التحميل
        self._hide_loading()
        
        # مسح الجدول
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # إضافة البيانات
        for i, customer in enumerate(customers):
            name_display = reshape_text(customer.name)
            address_display = reshape_text(customer.address) if customer.address else "—"
            email_display = customer.email if customer.email else "—"
            created_at = customer.created_at.strftime("%Y-%m-%d") if customer.created_at else ""

            tag = "Even" if i % 2 == 0 else "Odd"

            self.customers_tree.insert(
                "",
                ctk.END,
                values=(
                    created_at,
                    address_display,
                    email_display,
                    customer.phone,
                    name_display,
                    customer.id
                ),
                tags=(tag,)
            )

        self.customers_tree.tag_configure("Even", background="#f9f9f9")
        self.customers_tree.tag_configure("Odd", background="#ffffff")

    def _search_customers(self):
        search_text = self.search_entry.get().strip()
        self._load_customers(search_text if search_text else None)

    def _add_customer(self):
        dialog = CustomerDialog(self.parent, "إضافة عميل جديد")
        if dialog.result:
            try:
                self.customer_service.add_customer(
                    name=dialog.result["name"],
                    phone=dialog.result["phone"],
                    email=dialog.result.get("email"),
                    address=dialog.result.get("address"),
                    notes=dialog.result.get("notes"),
                    created_by=self.current_user['id']
                )
                self._load_customers()
                show_success(self.parent, "نجاح", "تم إضافة العميل بنجاح")
            except Exception as e:
                show_error(self.parent, "خطأ", f"حدث خطأ أثناء الإضافة: {str(e)}")

    def _edit_customer(self):
        selected = self.customers_tree.selection()
        if not selected:
            show_warning(self.parent, "تحذير", "الرجاء اختيار عميل للتعديل")
            return

        values = self.customers_tree.item(selected[0])["values"]
        customer_id = values[-1]

        customer = self.customer_service.get_customer_by_id(customer_id)
        if not customer:
            show_error(self.parent, "خطأ", "لم يتم العثور على العميل")
            return

        dialog = CustomerDialog(self.parent, "تعديل بيانات العميل", customer)
        if dialog.result:
            try:
                self.customer_service.update_customer(
                    customer_id=customer_id,
                    name=dialog.result["name"],
                    phone=dialog.result["phone"],
                    email=dialog.result.get("email"),
                    address=dialog.result.get("address"),
                    notes=dialog.result.get("notes"),
                    updated_by=self.current_user['id']
                )
                self._load_customers()
                show_success(self.parent, "نجاح", "تم تحديث بيانات العميل بنجاح")
            except Exception as e:
                show_error(self.parent, "خطأ", f"حدث خطأ أثناء التعديل: {str(e)}")

    def _delete_customer(self):
        selected = self.customers_tree.selection()
        if not selected:
            show_warning(self.parent, "تحذير", "الرجاء اختيار عميل للحذف")
            return

        values = self.customers_tree.item(selected[0])["values"]
        customer_id = values[-1]
        customer_name = values[-2]

        confirm = ask_yes_no(self.parent, "تأكيد الحذف",
                             f"هل أنت متأكد من حذف العميل: {customer_name}؟\nلا يمكن التراجع عن هذا الإجراء.")
        if confirm:
            try:
                self.customer_service.delete_customer(customer_id, self.current_user['id'])
                self._load_customers()
                show_success(self.parent, "نجاح", "تم حذف العميل بنجاح")
            except Exception as e:
                show_error(self.parent, "خطأ", f"حدث خطأ أثناء الحذف: {str(e)}")


class CustomerDialog:
    """نافذة حوار محسنة لإضافة/تعديل العملاء مع دعم العربية"""

    @staticmethod
    def _set_textbox_text_rtl(textbox, text):
        """Set text in textbox with RTL support"""
        textbox.delete("1.0", "end")
        if text:
            textbox.insert("1.0", text)
            textbox.tag_configure("rtl", justify="right", font=ctk.CTkFont(family="Cairo", size=13))
            textbox.tag_add("rtl", "1.0", "end")

    def __init__(self, parent: ctk.CTkFrame, title: str, customer: Optional[Customer] = None):
        self.result = None
        self.customer = customer

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("550x650")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()

        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=25)

        def create_entry(parent, label_text, placeholder, initial_value="", required=False):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", pady=(5, 10))

            label = ctk.CTkLabel(
                frame,
                text=label_text,
                anchor="e",
                font=ctk.CTkFont(family="Cairo", size=14, weight="bold" if required else "normal"),
                text_color=("#2b5b84" if required else "gray")
            )
            label.pack(fill="x", pady=(0, 3))

            entry = ctk.CTkEntry(
                frame,
                height=40,
                justify="right",
                font=ctk.CTkFont(family="Cairo", size=13),
                placeholder_text=placeholder
            )
            if initial_value:
                entry.insert(0, initial_value)
            entry.pack(fill="x")

            if not required:
                hint = ctk.CTkLabel(
                    frame,
                    text="(اختياري)",
                    anchor="e",
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                )
                hint.pack(anchor="e")

            return entry

        self.name_entry = create_entry(
            container,
            "الاسم الكامل:*",
            "مثال: محمد أحمد السيد",
            customer.name if customer else "",
            required=True
        )

        self.phone_entry = create_entry(
            container,
            "رقم الهاتف:*",
            "مثال: 0501234567",
            customer.phone if customer else "",
            required=True
        )

        self.email_entry = create_entry(
            container,
            "البريد الإلكتروني:",
            "example@domain.com",
            customer.email if customer else "",
            required=False
        )

        self.address_entry = create_entry(
            container,
            "العنوان:",
            "المدينة، الحي، الشارع",
            customer.address if customer else "",
            required=False
        )

        notes_frame = ctk.CTkFrame(container, fg_color="transparent")
        notes_frame.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(
            notes_frame,
            text="ملاحظات إضافية:",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14),
            text_color="gray"
        ).pack(fill="x", pady=(0, 3))

        self.notes_entry = ctk.CTkTextbox(
            notes_frame,
            height=80,
            font=ctk.CTkFont(family="Cairo", size=13)
        )
        if customer and customer.notes:
            CustomerDialog._set_textbox_text_rtl(self.notes_entry, customer.notes)
        self.notes_entry.pack(fill="x")

        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(30, 0))

        save_btn = ctk.CTkButton(
            buttons_frame,
            text="حفظ",
            command=self._save,
            height=45,
            font=ctk.CTkFont(family="Cairo", size=15, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838"
        )
        save_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="إلغاء",
            command=self._cancel,
            height=45,
            font=ctk.CTkFont(family="Cairo", size=15),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        self.dialog.bind("<Escape>", lambda e: self._cancel())
        self.dialog.bind("<Return>", lambda e: self._save())
        self.name_entry.focus()

        self.dialog.wait_window()

    def _validate_phone(self, phone):
        """التحقق من صحة رقم الهاتف"""
        phone = re.sub(r'[\s\-]+', '', phone)
        patterns = [
            r'^01\d{6}$',
            r'^\d{9}$',
            r'^\+967\d{9}$',
            r'^009665\d{9}$',
            r'^\d{6}$',
            r'^\d{6}$'
        ]
        return any(re.match(p, phone) for p in patterns)

    def _save(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()

        if not name:
            show_warning(self.dialog, "تحذير", "الرجاء إدخال اسم العميل")
            self.name_entry.focus()
            return
        if not phone:
            show_warning(self.dialog, "تحذير", "الرجاء إدخال رقم الهاتف")
            self.phone_entry.focus()
            return

        if not self._validate_phone(phone):
            result = ask_yes_no(self.dialog, "تأكيد الرقم",
                                "رقم الهاتف قد لا يكون بصيغة صحيحة. هل تريد المتابعة على أي حال؟")
            if not result:
                self.phone_entry.focus()
                return

        self.result = {
            "name": name,
            "phone": phone,
            "email": self.email_entry.get().strip() or None,
            "address": self.address_entry.get().strip() or None,
            "notes": self.notes_entry.get("1.0", "end-1c").strip() or None
        }
        self.dialog.destroy()

    def _cancel(self):
        self.result = None
        self.dialog.destroy()