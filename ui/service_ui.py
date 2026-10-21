# استيراد مكتبة واجهة المستخدم المحسنة
import customtkinter as ctk
# استيراد مربعات الرسائل والجداول من tkinter
from tkinter import messagebox, ttk
# استيراد الأنواع للـ type hints
from typing import Optional, Dict, Any
# استيراد وحدة datetime للتعامل مع التواريخ
from datetime import datetime
# استيراد وحدة التعبيرات النمطية (regular expressions)
import re
# استيراد وحدة الخيوط للتحميل غير المتزامن
import threading

# استيراد خوارزمية bidi للتعامل مع النصوص الثنائية
from bidi.algorithm import get_display
# استيراد مكتبة إعادة تشكيل النصوص العربية
import arabic_reshaper

# استيراد خدمة الخدمات
from services.service_service import ServiceService
# استيراد مدير قاعدة البيانات
from repositories.database import DatabaseManager
# استيراد نموذج الخدمة
from models.service import Service
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

class ServiceUI:
    """واجهة إدارة الخدمات مع دعم كامل للغة العربية وتحسينات RTL"""

    def __init__(self, parent: ctk.CTkFrame, service_service: ServiceService,
                 db_manager: DatabaseManager, current_user: Dict[str, Any]):
        self.parent = parent
        self.service_service = service_service
        self.db_manager = db_manager
        self.current_user = current_user
        self.categories = []  # سيتم ملؤها من قاعدة البيانات
        self._create_ui()
        self._load_services()

    def _create_ui(self):
        """إنشاء واجهة المستخدم مع ترتيب RTL"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # عنوان الصفحة (محاذاة لليمين)
        title_label = ctk.CTkLabel(
            main_frame,
            text="إدارة الخدمات",
            font=ctk.CTkFont(family="Cairo", size=24, weight="bold"),
            anchor="e"
        )
        title_label.pack(fill=ctk.X, pady=(0, 20))

        # شريط الأدوات
        toolbar_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        toolbar_frame.pack(fill=ctk.X, pady=(0, 15))

        # أزرار الإجراءات (على اليمين في RTL)
        actions_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        actions_frame.pack(side=ctk.RIGHT)

        # زر الإضافة
        add_btn = ctk.CTkButton(
            actions_frame,
            text="➕ إضافة خدمة",
            command=self._add_service,
            width=140,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#2ec4b6",
            hover_color="#25a89c"
        )
        add_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        # زر التعديل
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️ تعديل",
            command=self._edit_service,
            width=100,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#f77f00",
            hover_color="#e07000"
        )
        edit_btn.pack(side=ctk.RIGHT, padx=(5, 0))

        # زر الحذف
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️ حذف",
            command=self._delete_service,
            width=100,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#ef233c",
            hover_color="#d90429"
        )
        delete_btn.pack(side=ctk.RIGHT)

        # البحث والفلترة (على اليسار في RTL)
        search_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        search_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        # حقل البحث
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 البحث عن خدمة...",
            width=250,
            height=40,
            justify="right",
            font=ctk.CTkFont(family="Cairo", size=13)
        )
        self.search_entry.pack(side=ctk.LEFT, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._search_services())

        # فلتر الفئة
        category_label = ctk.CTkLabel(
            search_frame,
            text="الفئة:",
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        category_label.pack(side=ctk.LEFT, padx=(10, 5))

        self.category_var = ctk.StringVar(value="الكل")
        self.category_combo = ctk.CTkComboBox(
            search_frame,
            values=["الكل"],
            variable=self.category_var,
            width=150,
            height=40,
            command=self._filter_by_category,
            font=ctk.CTkFont(family="Cairo", size=13),
            dropdown_font=ctk.CTkFont(family="Cairo", size=13)
        )
        self.category_combo.pack(side=ctk.LEFT, padx=(0, 5))

        # زر إدارة الفئات
        manage_categories_btn = ctk.CTkButton(
            search_frame,
            text="⚙️ إدارة الفئات",
            command=self._manage_categories,
            width=120,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=13),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        manage_categories_btn.pack(side=ctk.LEFT, padx=(5, 5))

        # زر البحث
        search_btn = ctk.CTkButton(
            search_frame,
            text="بحث",
            width=80,
            height=40,
            command=self._search_services,
            font=ctk.CTkFont(family="Cairo", size=14),
            fg_color="#4361ee",
            hover_color="#3a56d4"
        )
        search_btn.pack(side=ctk.LEFT)

        # جدول الخدمات
        self._create_services_table(main_frame)

        # تحميل الفئات للفلتر
        self._load_categories()

    def _load_categories(self):
        """تحميل قائمة الفئات من قاعدة البيانات وتحديث القائمة المنسدلة"""
        try:
            self.categories = self.db_manager.get_service_categories()
            categories_list = ["الكل"] + [cat['name'] for cat in self.categories]
            self.category_combo.configure(values=categories_list)
        except Exception:
            pass

    def _manage_categories(self):
        """فتح نافذة إدارة الفئات"""
        dialog = ManageCategoriesDialog(self.parent, self.db_manager)
        # بعد إغلاق النافذة، أعد تحميل الفئات لتحديث القائمة المنسدلة
        self._load_categories()
        # وأعد تحميل الخدمات لتعكس أي تغييرات في أسماء الفئات
        self._load_services()

    def _create_services_table(self, parent):
        """إنشاء جدول عرض الخدمات مع تحسينات المظهر ودعم العربية"""
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill=ctk.BOTH, expand=True)

        # ترتيب الأعمدة من اليمين لليسار (أول عمود في القائمة يظهر في أقصى اليمين)
        # نريد الترتيب: المعرف - الاسم - الفئة - السعر - الوصف - تاريخ الإضافة
        # لتحقيق ذلك نضع الأعمدة في القائمة بالترتيب المعاكس
        columns = ("created_at", "description", "price", "category", "name", "id")
        headings = {
            "id": "المعرف",
            "name": "اسم الخدمة",
            "category": "الفئة",
            "price": "السعر",
            "description": "الوصف",
            "created_at": "تاريخ الإضافة"
        }
        widths = {
            "id": 50,
            "name": 200,
            "category": 150,
            "price": 100,
            "description": 300,
            "created_at": 120
        }

        # إعدادات نمط الجدول
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Custom.Treeview",
                        background="#f9f9f9",
                        foreground="black",
                        rowheight=40,  # ارتفاع صف أكبر
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

        # إنشاء Treeview
        self.services_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
            style="Custom.Treeview"
        )

        # تعيين العناوين والعرض (بنفس ترتيب الأعمدة)
        for col in columns:
            self.services_tree.heading(col, text=headings[col], anchor="center")
            self.services_tree.column(col, width=widths[col], minwidth=80, anchor="center")

        # شريط التمرير العمودي
        scrollbar = ttk.Scrollbar(table_frame, orient=ctk.VERTICAL, command=self.services_tree.yview)
        self.services_tree.configure(yscrollcommand=scrollbar.set)

        # ترتيب الجدول وشريط التمرير (الجدول على اليمين، والشريط على اليسار لـ RTL)
        self.services_tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y)

        self.services_tree.bind("<Double-1>", lambda e: self._edit_service())

    def _load_services(self, search_term: str = None, category_id: int = None):
        """تحميل وعرض الخدمات (باستخدام خيط منفصل)"""
        # إظهار مؤشر التحميل
        self._show_loading()
        
        # تشغيل التحميل في خيط منفصل
        thread = threading.Thread(target=self._load_services_thread, args=(search_term, category_id))
        thread.daemon = True
        thread.start()
    
    def _show_loading(self):
        """إظهار مؤشر التحميل"""
        self._hide_loading()
        
        self.loading_overlay = ctk.CTkFrame(self.services_tree.master, fg_color=("white", "#2d2d44"))
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
    
    def _load_services_thread(self, search_term: str, category_id: int):
        """الخيط الذي يقوم بتحميل البيانات"""
        try:
            services = self.service_service.get_services(search_term, category_id)
            self.parent.after(0, lambda: self._display_services(services))
        except Exception as e:
            self.parent.after(0, lambda: self._hide_loading())
    
    def _display_services(self, services):
        """عرض الخدمات في الجدول"""
        self._hide_loading()
        
        # مسح الجدول
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)

        # إدراج الصفوف مع ألوان متناوبة
        for i, service in enumerate(services):
            name_display = reshape_text(service.name)
            description_display = reshape_text(service.description) if service.description else "—"

            category_name = "—"
            if service.category_id:
                for cat in self.categories:
                    if cat['id'] == service.category_id:
                        category_name = reshape_text(cat['name'])
                        break

            price_display = f"{service.price:.2f} ر.س"
            created_at = service.created_at.strftime("%Y-%m-%d") if service.created_at else ""

            tag = "Even" if i % 2 == 0 else "Odd"

            self.services_tree.insert(
                "",
                ctk.END,
                values=(
                    created_at,
                    description_display,
                    price_display,
                    category_name,
                    name_display,
                    service.id
                ),
                tags=(tag,)
            )

        self.services_tree.tag_configure("Even", background="#f9f9f9")
        self.services_tree.tag_configure("Odd", background="#ffffff")

    def _search_services(self):
        """تنفيذ البحث حسب النص والفئة"""
        search_term = self.search_entry.get().strip() or None
        category_id = None

        selected_category = self.category_var.get()
        if selected_category != "الكل":
            for cat in self.categories:
                if cat['name'] == selected_category:
                    category_id = cat['id']
                    break

        self._load_services(search_term, category_id)

    def _filter_by_category(self, choice):
        """تصفية حسب الفئة (يتم استدعاؤها عند تغيير القائمة)"""
        self._search_services()

    def _add_service(self):
        """فتح نافذة إضافة خدمة جديدة"""
        dialog = ServiceDialog(self.parent, "إضافة خدمة جديدة", self.categories)
        if dialog.result:
            try:
                self.service_service.add_service(
                    name=dialog.result["name"],
                    description=dialog.result["description"],
                    price=dialog.result["price"],
                    category_id=dialog.result.get("category_id"),
                    created_by=self.current_user['id']
                )
                self._load_services()
                messagebox.showinfo("نجاح", "تم إضافة الخدمة بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء إضافة الخدمة: {str(e)}", parent=self.parent)

    def _edit_service(self):
        """فتح نافذة تعديل الخدمة المحددة"""
        selected = self.services_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار خدمة للتعديل", parent=self.parent)
            return

        # استخراج معرف الخدمة (آخر قيمة في القائمة)
        values = self.services_tree.item(selected[0])["values"]
        service_id = values[-1]  # id في نهاية القائمة

        service = self.service_service.get_service_by_id(service_id)
        if not service:
            messagebox.showerror("خطأ", "لم يتم العثور على الخدمة", parent=self.parent)
            return

        dialog = ServiceDialog(self.parent, "تعديل بيانات الخدمة", self.categories, service)
        if dialog.result:
            try:
                self.service_service.update_service(
                    service_id=service_id,
                    name=dialog.result["name"],
                    description=dialog.result["description"],
                    price=dialog.result["price"],
                    category_id=dialog.result.get("category_id"),
                    updated_by=self.current_user['id']
                )
                self._load_services()
                messagebox.showinfo("نجاح", "تم تحديث بيانات الخدمة بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تحديث البيانات: {str(e)}", parent=self.parent)

    def _delete_service(self):
        """حذف الخدمة المحددة بعد التأكيد"""
        selected = self.services_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار خدمة للحذف", parent=self.parent)
            return

        values = self.services_tree.item(selected[0])["values"]
        service_id = values[-1]
        service_name = values[-2]  # الاسم قبل الأخير

        confirm = messagebox.askyesno(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الخدمة: {service_name}؟\nلا يمكن التراجع عن هذا الإجراء.",
            parent=self.parent
        )
        if confirm:
            try:
                self.service_service.delete_service(service_id, self.current_user['id'])
                self._load_services()
                messagebox.showinfo("نجاح", "تم حذف الخدمة بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء الحذف: {str(e)}", parent=self.parent)


class ServiceDialog:
    """نافذة حوار محسنة لإضافة/تعديل الخدمات مع دعم العربية وعرض كامل للفئة"""

    def __init__(self, parent: ctk.CTkFrame, title: str,
                 categories: list, service: Optional[Service] = None):
        self.result = None
        self.categories = categories

        # نافذة بحجم أكبر لاستيعاب المحتوى بشكل مريح
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("550x480")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()

        self._create_ui(service)
        self._center_window()
        self.dialog.wait_window()

    def _create_ui(self, service: Optional[Service]):
        """إنشاء واجهة النافذة مع دعم RTL"""
        # حاوية رئيسية
        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=25)

        # عنوان النموذج
        form_title = ctk.CTkLabel(
            container,
            text="بيانات الخدمة",
            font=ctk.CTkFont(family="Cairo", size=18, weight="bold"),
            anchor="center"
        )
        form_title.pack(pady=(0, 20))

        # دالة مساعدة لإنشاء حقل إدخال مع تسمية
        def create_entry(parent, label_text, placeholder, initial_value="", required=False, height=40, is_textbox=False):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", pady=(5, 10))

            label = ctk.CTkLabel(
                frame,
                text=label_text,
                anchor="e",  # محاذاة لليمين
                font=ctk.CTkFont(family="Cairo", size=14, weight="bold" if required else "normal"),
                text_color=("#2b5b84" if required else "gray")
            )
            label.pack(fill="x", pady=(0, 3))

            if is_textbox:
                # حقل نص متعدد الأسطر (للوصف)
                textbox = ctk.CTkTextbox(
                    frame,
                    height=100,
                    font=ctk.CTkFont(family="Cairo", size=13)
                )
                if initial_value:
                    textbox.insert("1.0", initial_value)
                textbox.pack(fill="x")
                return textbox
            else:
                entry = ctk.CTkEntry(
                    frame,
                    height=height,
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

        # حقل اسم الخدمة
        self.name_entry = create_entry(
            container,
            "اسم الخدمة:*",
            "أدخل اسم الخدمة",
            service.name if service else "",
            required=True
        )

        # حقل الوصف (نص متعدد الأسطر)
        self.desc_textbox = create_entry(
            container,
            "الوصف:",
            "أدخل وصفاً تفصيلياً للخدمة (اختياري)",
            service.description if service else "",
            required=False,
            is_textbox=True
        )

        # حقل السعر
        self.price_entry = create_entry(
            container,
            "السعر (ر.س):*",
            "مثال: 150.00",
            str(service.price) if service else "",
            required=True
        )

        # اختيار الفئة
        category_frame = ctk.CTkFrame(container, fg_color="transparent")
        category_frame.pack(fill="x", pady=(5, 10))

        category_label = ctk.CTkLabel(
            category_frame,
            text="الفئة:",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14),
            text_color="gray"
        )
        category_label.pack(fill="x", pady=(0, 3))

        # قائمة الفئات (مع إضافة "بدون فئة" في البداية)
        categories_list = ["بدون فئة"] + [cat['name'] for cat in self.categories]
        self.category_var = ctk.StringVar(value="بدون فئة")

        # إذا كان لدينا خدمة موجودة، حدد الفئة المناسبة
        if service and service.category_id:
            for cat in self.categories:
                if cat['id'] == service.category_id:
                    self.category_var.set(cat['name'])
                    break

        self.category_combo = ctk.CTkComboBox(
            category_frame,
            values=categories_list,
            variable=self.category_var,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=13),
            dropdown_font=ctk.CTkFont(family="Cairo", size=13)
        )
        self.category_combo.pack(fill="x")

        # إطار الأزرار (باستخدام grid لتوزيع متساوٍ)
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(25, 0))

        # زر الحفظ (على اليمين في RTL)
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="حفظ",
            command=self._save,
            height=45,
            font=ctk.CTkFont(family="Cairo", size=15, weight="bold"),
            fg_color="#4361ee",
            hover_color="#3a56d4"
        )
        save_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # زر الإلغاء (على اليسار في RTL)
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

        # ربط المفاتيح
        self.dialog.bind("<Escape>", lambda e: self._cancel())
        self.dialog.bind("<Return>", lambda e: self._save())
        self.name_entry.focus()

    def _center_window(self):
        """توسيط النافذة على الشاشة"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _save(self):
        """التحقق من البيانات وحفظها"""
        name = self.name_entry.get().strip()
        description = self.desc_textbox.get("1.0", "end-1c").strip()
        price_str = self.price_entry.get().strip()

        # التحقق من الحقول المطلوبة
        if not name:
            messagebox.showwarning("تحذير", "اسم الخدمة مطلوب", parent=self.dialog)
            self.name_entry.focus()
            return
        if not price_str:
            messagebox.showwarning("تحذير", "السعر مطلوب", parent=self.dialog)
            self.price_entry.focus()
            return

        # التحقق من صحة السعر
        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("تحذير", "الرجاء إدخال سعر صحيح أكبر من صفر", parent=self.dialog)
            self.price_entry.focus()
            return

        # الحصول على معرف الفئة
        category_id = None
        if self.category_var.get() != "بدون فئة":
            for cat in self.categories:
                if cat['name'] == self.category_var.get():
                    category_id = cat['id']
                    break

        self.result = {
            "name": name,
            "description": description if description else None,
            "price": price,
            "category_id": category_id
        }
        self.dialog.destroy()

    def _cancel(self):
        """إلغاء العملية"""
        self.result = None
        self.dialog.destroy()


class ManageCategoriesDialog:
    """نافذة حوار لإدارة فئات الخدمات (إضافة، تعديل، حذف)"""

    def __init__(self, parent: ctk.CTkFrame, db_manager: DatabaseManager):
        self.db = db_manager
        self.result = None  # يمكن استخدامها إذا أردنا إرجاع شيء

        # إنشاء نافذة الحوار
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("إدارة فئات الخدمات")
        self.dialog.geometry("700x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()

        self._create_ui()
        self._load_categories()
        self.dialog.wait_window()

    def _create_ui(self):
        # إطار رئيسي
        main = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # عنوان
        title = ctk.CTkLabel(
            main,
            text="إدارة فئات الخدمات",
            font=ctk.CTkFont(family="Cairo", size=20, weight="bold"),
            anchor="center"
        )
        title.pack(pady=(0, 15))

        # إطار لأزرار الإجراءات (إضافة، تعديل، حذف)
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 10))

        # زر إضافة فئة
        add_btn = ctk.CTkButton(
            btn_frame,
            text="➕ إضافة فئة",
            command=self._add_category,
            width=120,
            height=35,
            font=ctk.CTkFont(family="Cairo", size=13),
            fg_color="#28a745",
            hover_color="#218838"
        )
        add_btn.pack(side=ctk.RIGHT, padx=5)

        # زر تعديل فئة
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️ تعديل",
            command=self._edit_category,
            width=100,
            height=35,
            font=ctk.CTkFont(family="Cairo", size=13),
            fg_color="#f77f00",
            hover_color="#e07000"
        )
        edit_btn.pack(side=ctk.RIGHT, padx=5)

        # زر حذف فئة
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ حذف",
            command=self._delete_category,
            width=100,
            height=35,
            font=ctk.CTkFont(family="Cairo", size=13),
            fg_color="#ef233c",
            hover_color="#d90429"
        )
        delete_btn.pack(side=ctk.RIGHT, padx=5)

        # إطار الجدول
        table_frame = ctk.CTkFrame(main, fg_color="transparent")
        table_frame.pack(fill="both", expand=True)

        # إعدادات نمط الجدول
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Categories.Treeview",
                        font=("Cairo", 12),
                        rowheight=40,
                        background="#f9f9f9",
                        fieldbackground="#f9f9f9")
        style.map("Categories.Treeview",
                  background=[("selected", "#2b5b84")],
                  foreground=[("selected", "white")])
        style.configure("Categories.Treeview.Heading",
                        font=("Cairo", 13, "bold"),
                        background="#e9ecef",
                        foreground="black")

        # الأعمدة (من اليمين: المعرف - الاسم - الوصف - تاريخ الإضافة)
        columns = ("created_at", "description", "name", "id")
        headings = {
            "id": "المعرف",
            "name": "اسم الفئة",
            "description": "الوصف",
            "created_at": "تاريخ الإضافة"
        }
        widths = {"id": 50, "name": 200, "description": 300, "created_at": 120}

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
            style="Categories.Treeview"
        )

        for col in columns:
            self.tree.heading(col, text=headings[col], anchor="center")
            self.tree.column(col, width=widths[col], anchor="center")

        # شريط التمرير
        scrollbar = ttk.Scrollbar(table_frame, orient=ctk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ترتيب RTL: الجدول على اليمين، الشريط على اليسار
        self.tree.pack(side=ctk.RIGHT, fill="both", expand=True)
        scrollbar.pack(side=ctk.LEFT, fill="y")

        # ربط النقر المزدوج للتعديل
        self.tree.bind("<Double-1>", lambda e: self._edit_category())

        # زر إغلاق
        close_btn = ctk.CTkButton(
            main,
            text="إغلاق",
            command=self.dialog.destroy,
            width=100,
            height=35,
            font=ctk.CTkFont(family="Cairo", size=13),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        close_btn.pack(pady=(15, 0))

    def _load_categories(self):
        """تحميل وعرض الفئات في الجدول"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        categories = self.db.get_service_categories()
        for i, cat in enumerate(categories):
            name_display = reshape_text(cat['name'])
            desc_display = reshape_text(cat['description']) if cat['description'] else "—"
            
            # معالجة تاريخ الإضافة بشكل آمن
            created_at_val = cat.get('created_at')
            if created_at_val:
                if isinstance(created_at_val, datetime):
                    created_at = created_at_val.strftime("%Y-%m-%d")
                else:
                    created_at = str(created_at_val)[:10]
            else:
                created_at = ""
                
            tag = "Even" if i % 2 == 0 else "Odd"
            self.tree.insert(
                "",
                ctk.END,
                values=(created_at, desc_display, name_display, cat['id']),
                tags=(tag,)
            )

        self.tree.tag_configure("Even", background="#f9f9f9")
        self.tree.tag_configure("Odd", background="#ffffff")

    def _add_category(self):
        """فتح نافذة إضافة فئة جديدة"""
        dialog = CategoryEntryDialog(self.dialog, "إضافة فئة جديدة")
        if dialog.result:
            try:
                self.db.insert_service_category(
                    name=dialog.result['name'],
                    description=dialog.result.get('description')
                )
                self._load_categories()
                messagebox.showinfo("نجاح", "تم إضافة الفئة بنجاح", parent=self.dialog)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {str(e)}", parent=self.dialog)

    def _edit_category(self):
        """فتح نافذة تعديل الفئة المحددة"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار فئة للتعديل", parent=self.dialog)
            return

        values = self.tree.item(selected[0])['values']
        cat_id = values[-1]  # آخر قيمة هي id
        cat = self.db.get_service_category_by_id(cat_id)
        if not cat:
            messagebox.showerror("خطأ", "لم يتم العثور على الفئة", parent=self.dialog)
            return

        dialog = CategoryEntryDialog(self.dialog, "تعديل الفئة", cat)
        if dialog.result:
            try:
                self.db.update_service_category(
                    category_id=cat_id,
                    name=dialog.result['name'],
                    description=dialog.result.get('description')
                )
                self._load_categories()
                messagebox.showinfo("نجاح", "تم تحديث الفئة بنجاح", parent=self.dialog)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {str(e)}", parent=self.dialog)

    def _delete_category(self):
        """حذف الفئة المحددة بعد التأكيد"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار فئة للحذف", parent=self.dialog)
            return

        values = self.tree.item(selected[0])['values']
        cat_id = values[-1]
        cat_name = values[-2]  # الاسم قبل الأخير

        confirm = messagebox.askyesno(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الفئة: {cat_name}؟\nقد تؤثر هذه العملية على الخدمات المرتبطة.",
            parent=self.dialog
        )
        if confirm:
            try:
                self.db.delete_service_category(cat_id)
                self._load_categories()
                messagebox.showinfo("نجاح", "تم حذف الفئة بنجاح", parent=self.dialog)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء الحذف: {str(e)}", parent=self.dialog)


class CategoryEntryDialog:
    """نافذة حوار بسيطة لإدخال بيانات الفئة (اسم، وصف)"""

    def __init__(self, parent, title, category: Optional[Dict] = None):
        self.result = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()

        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # اسم الفئة
        ctk.CTkLabel(
            container,
            text="اسم الفئة:*",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            text_color="#2b5b84"
        ).pack(fill="x", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(
            container,
            height=40,
            justify="right",
            font=ctk.CTkFont(family="Cairo", size=13),
            placeholder_text="أدخل اسم الفئة"
        )
        if category:
            self.name_entry.insert(0, category['name'])
        self.name_entry.pack(fill="x", pady=(0, 15))

        # الوصف
        ctk.CTkLabel(
            container,
            text="الوصف:",
            anchor="e",
            font=ctk.CTkFont(family="Cairo", size=14),
            text_color="gray"
        ).pack(fill="x", pady=(0, 5))
        self.desc_text = ctk.CTkTextbox(
            container,
            height=80,
            font=ctk.CTkFont(family="Cairo", size=13)
        )
        if category and category['description']:
            self.desc_text.insert("1.0", category['description'])
        self.desc_text.pack(fill="x", pady=(0, 20))

        # الأزرار
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="حفظ",
            command=self._save,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838"
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
        self.name_entry.focus()

        self.dialog.wait_window()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("تحذير", "اسم الفئة مطلوب", parent=self.dialog)
            self.name_entry.focus()
            return
        desc = self.desc_text.get("1.0", "end-1c").strip() or None
        self.result = {"name": name, "description": desc}
        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()