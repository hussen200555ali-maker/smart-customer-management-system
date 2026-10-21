import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import Optional, Dict, Any
from repositories.database import DatabaseManager
from bidi.algorithm import get_display
import arabic_reshaper
from utils.dialogs import show_info, show_success, show_warning, show_error, ask_yes_no

def reshape_text(text: str) -> str:
    """إعادة تشكيل النص العربي"""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

class CategoriesUI:
    """واجهة إدارة فئات الخدمات"""

    def __init__(self, parent: ctk.CTkFrame, db_manager: DatabaseManager):
        self.parent = parent
        self.db = db_manager
        self._create_ui()
        self._load_categories()

    def _create_ui(self):
        # عنوان الصفحة
        title_label = ctk.CTkLabel(
            self.parent,
            text="إدارة فئات الخدمات",
            font=ctk.CTkFont(family="Cairo", size=24, weight="bold"),
            anchor="e"
        )
        title_label.pack(fill=ctk.X, pady=(0, 20))

        # شريط الأدوات (زر الإضافة)
        toolbar = ctk.CTkFrame(self.parent, fg_color="transparent")
        toolbar.pack(fill=ctk.X, pady=(0, 15))

        add_btn = ctk.CTkButton(
            toolbar,
            text="➕ إضافة فئة جديدة",
            command=self._add_category,
            width=150,
            height=40,
            font=ctk.CTkFont(family="Cairo", size=14)
        )
        add_btn.pack(side=ctk.RIGHT)

        # جدول عرض الفئات
        self._create_categories_table()

    def _create_categories_table(self):
        table_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        table_frame.pack(fill=ctk.BOTH, expand=True)

        # ترتيب الأعمدة من اليمين: المعرف - الاسم - الوصف - تاريخ الإضافة
        columns = ("created_at", "description", "name", "id")
        headings = {
            "id": "المعرف",
            "name": "اسم الفئة",
            "description": "الوصف",
            "created_at": "تاريخ الإضافة"
        }
        widths = {"id": 50, "name": 200, "description": 300, "created_at": 120}

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview", font=("Cairo", 12), rowheight=40)
        style.configure("Custom.Treeview.Heading", font=("Cairo", 13, "bold"))

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
            style="Custom.Treeview"
        )

        for col in columns:
            self.tree.heading(col, text=headings[col], anchor="center")
            self.tree.column(col, width=widths[col], anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y)

        self.tree.bind("<Double-1>", lambda e: self._edit_category())
        self.tree.bind("<Delete>", lambda e: self._delete_category())

    def _load_categories(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        categories = self.db.get_service_categories()
        for i, cat in enumerate(categories):
            name_display = reshape_text(cat['name'])
            desc_display = reshape_text(cat['description']) if cat['description'] else "—"
            created_at = str(cat['created_at'])[:10] if cat.get('created_at') else ""
            tag = "Even" if i % 2 == 0 else "Odd"
            self.tree.insert("", ctk.END, values=(
                created_at,
                desc_display,
                name_display,
                cat['id']
            ), tags=(tag,))

        self.tree.tag_configure("Even", background="#f9f9f9")
        self.tree.tag_configure("Odd", background="#ffffff")

    def _add_category(self):
        dialog = CategoryDialog(self.parent, "إضافة فئة جديدة")
        if dialog.result:
            try:
                self.db.insert_service_category(
                    name=dialog.result['name'],
                    description=dialog.result.get('description')
                )
                self._load_categories()
                messagebox.showinfo("نجاح", "تم إضافة الفئة بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {str(e)}", parent=self.parent)

    def _edit_category(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار فئة للتعديل", parent=self.parent)
            return
        cat_id = self.tree.item(selected[0])['values'][-1]  # آخر قيمة هي id
        cat = self.db.get_service_category_by_id(cat_id)
        if not cat:
            messagebox.showerror("خطأ", "لم يتم العثور على الفئة", parent=self.parent)
            return
        dialog = CategoryDialog(self.parent, "تعديل الفئة", cat)
        if dialog.result:
            try:
                self.db.update_service_category(
                    category_id=cat_id,
                    name=dialog.result['name'],
                    description=dialog.result.get('description')
                )
                self._load_categories()
                messagebox.showinfo("نجاح", "تم تحديث الفئة بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {str(e)}", parent=self.parent)

    def _delete_category(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار فئة للحذف", parent=self.parent)
            return
        cat_id = self.tree.item(selected[0])['values'][-1]
        cat_name = self.tree.item(selected[0])['values'][-2]  # الاسم قبل الأخير
        confirm = messagebox.askyesno(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الفئة: {cat_name}؟\nقد تؤثر هذه العملية على الخدمات المرتبطة.",
            parent=self.parent
        )
        if confirm:
            try:
                self.db.delete_service_category(cat_id)
                self._load_categories()
                messagebox.showinfo("نجاح", "تم حذف الفئة بنجاح", parent=self.parent)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء الحذف: {str(e)}", parent=self.parent)


class CategoryDialog:
    """نافذة حوار لإضافة/تعديل فئة"""

    def __init__(self, parent, title, category: Optional[Dict] = None):
        self.result = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self._create_ui(category)
        self.dialog.wait_window()

    def _create_ui(self, category):
        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # اسم الفئة
        ctk.CTkLabel(container, text="اسم الفئة:*", anchor="e", font=ctk.CTkFont(family="Cairo", size=14)).pack(fill="x", pady=(0,5))
        self.name_entry = ctk.CTkEntry(container, height=40, justify="right", font=ctk.CTkFont(family="Cairo", size=13))
        if category:
            self.name_entry.insert(0, category['name'])
        self.name_entry.pack(fill="x", pady=(0,15))

        # الوصف
        ctk.CTkLabel(container, text="الوصف:", anchor="e", font=ctk.CTkFont(family="Cairo", size=14)).pack(fill="x", pady=(0,5))
        self.desc_text = ctk.CTkTextbox(container, height=80, font=ctk.CTkFont(family="Cairo", size=13))
        if category and category['description']:
            self.desc_text.insert("1.0", category['description'])
        self.desc_text.pack(fill="x", pady=(0,20))

        # الأزرار
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        save_btn = ctk.CTkButton(btn_frame, text="حفظ", command=self._save, height=40, fg_color="#28a745")
        save_btn.pack(side=ctk.RIGHT, padx=(5,0), expand=True, fill="x")

        cancel_btn = ctk.CTkButton(btn_frame, text="إلغاء", command=self._cancel, height=40, fg_color="#6c757d")
        cancel_btn.pack(side=ctk.LEFT, padx=(0,5), expand=True, fill="x")

        self.dialog.bind("<Return>", lambda e: self._save())
        self.dialog.bind("<Escape>", lambda e: self._cancel())
        self.name_entry.focus()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("تحذير", "اسم الفئة مطلوب", parent=self.dialog)
            return
        desc = self.desc_text.get("1.0", "end-1c").strip() or None
        self.result = {"name": name, "description": desc}
        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()