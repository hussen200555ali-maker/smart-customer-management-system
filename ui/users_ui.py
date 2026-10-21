import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import Dict, Any, List
from repositories.database import DatabaseManager
from models.user import User
import secrets
from bidi.algorithm import get_display
import arabic_reshaper
from utils.dialogs import show_info, show_success, show_warning, show_error, ask_yes_no


def reshape_text(text: str) -> str:
    """إعادة تشكيل النص العربي وعرضه بشكل صحيح من اليمين لليسار"""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

class UsersUI:
    """واجهة إدارة المستخدمين"""

    def __init__(self, parent: ctk.CTkFrame, db_manager: DatabaseManager, 
                 current_user: Dict[str, Any]):
        """تهيئة واجهة إدارة المستخدمين"""
        self.parent = parent
        self.db_manager = db_manager
        self.current_user = current_user
        self._create_ui()
        self._load_users()

    def _create_ui(self):
        """إنشاء واجهة المستخدم"""
        # عنوان الصفحة
        title_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        title_frame.pack(fill=ctk.X, pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=reshape_text("إدارة المستخدمين"),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1a1a2e"
        )
        title_label.pack(side=ctk.RIGHT)
        
        # إطار البحث والإضافة مع خلفية محسنة
        top_frame = ctk.CTkFrame(self.parent, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#dee2e6")
        top_frame.pack(fill=ctk.X, pady=(0, 15), padx=10)
        
        # محتوى الإطار العلوي مع padding
        inner_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        inner_frame.pack(fill=ctk.X, padx=20, pady=15)
        
        # معلومات المستخدم الحالي
        user_info = ctk.CTkLabel(
            inner_frame,
            text=reshape_text(f"مسجل ك: {self.current_user['full_name']} ({self._get_role_name(self.current_user['role'])})"),
            font=ctk.CTkFont(size=12),
            text_color="#6c757d",
            anchor="e"
        )
        user_info.pack(side=ctk.LEFT)
        
        # أزرار الإجراءات
        buttons_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        buttons_frame.pack(side=ctk.RIGHT)
        
        add_button = ctk.CTkButton(
            buttons_frame,
            text=reshape_text("➕ إضافة مستخدم"),
            command=self._add_user,
            width=140,
            height=40,
            fg_color="#2ec4b6",
            hover_color="#25a89c"
        )
        add_button.pack(side=ctk.RIGHT, padx=(0, 10))
        
        edit_button = ctk.CTkButton(
            buttons_frame,
            text=reshape_text("✏️ تعديل"),
            command=self._edit_user,
            width=100,
            height=40,
            fg_color="#f77f00",
            hover_color="#e07000"
        )
        edit_button.pack(side=ctk.RIGHT, padx=(0, 10))
        
        delete_button = ctk.CTkButton(
            buttons_frame,
            text=reshape_text("🗑️ حذف"),
            command=self._delete_user,
            width=100,
            height=40,
            fg_color="#ef233c",
            hover_color="#d90429"
        )
        delete_button.pack(side=ctk.RIGHT)
        
        # جدول المستخدمين مع إطار احترافي
        table_container = ctk.CTkFrame(self.parent, fg_color="#f8f9fa", corner_radius=10, border_width=2, border_color="#dee2e6")
        table_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(10, 0))
        
        # عنوان الجدول
        table_title = ctk.CTkLabel(
            table_container,
            text=reshape_text("قائمة المستخدمين"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2c3e50"
        )
        table_title.pack(pady=(15, 10))
        
        # إطار الجدول مع padding
        self.table_inner = ctk.CTkFrame(table_container, fg_color="transparent")
        self.table_inner.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self._create_users_table()

    def _create_users_table(self):
        """إنشاء جدول المستخدمين مع ترتيب RTL احترافي"""
        table_frame = ctk.CTkFrame(self.table_inner, fg_color="transparent")
        table_frame.pack(fill=ctk.BOTH, expand=True)
        
        # ترتيب الأعمدة من اليمين إلى اليسار: last_login, created_at, is_active, role, full_name, username, id
        columns = ("last_login", "created_at", "is_active", "role", "full_name", "username", "id")
        headings = {
            "id": reshape_text("الرقم"),
            "username": reshape_text("اسم المستخدم"),
            "full_name": reshape_text("الاسم الكامل"),
            "role": reshape_text("الدور"),
            "is_active": reshape_text("الحالة"),
            "created_at": reshape_text("تاريخ الإنشاء"),
            "last_login": reshape_text("آخر تسجيل")
        }
        
        # عرض الأعمدة مناسب للعرض من اليمين
        widths = {
            "id": 60, "username": 120, "full_name": 150, "role": 100, 
            "is_active": 80, "created_at": 120, "last_login": 120
        }
        
        # تنسيق الجدول مع مظهر احترافي
        style = ttk.Style()
        style.theme_use("default")
        style.configure("RTLUsers.Treeview",
                        background="#ffffff",
                        foreground="#2c3e50",
                        rowheight=35,
                        fieldbackground="#ffffff",
                        borderwidth=1,
                        relief="solid",
                        font=("Cairo", 10))
        style.map("RTLUsers.Treeview",
                  background=[("selected", "#3498db")],
                  foreground=[("selected", "white")])
        style.configure("RTLUsers.Treeview.Heading",
                        font=("Cairo", 11, "bold"),
                        background="#ecf0f1",
                        foreground="#2c3e50",
                        borderwidth=1,
                        relief="raised",
                        anchor="center")
        style.map("RTLUsers.Treeview.Heading",
                  background=[("active", "#bdc3c7")])
        
        self.users_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
            style="RTLUsers.Treeview"
        )
        
        # تعيين عناوين الأعمدة والعرض والمحاذاة (لليمين)
        for col in columns:
            self.users_tree.heading(col, text=headings[col], anchor="center")
            self.users_tree.column(col, width=widths[col], minwidth=50, anchor="center")  # كل البيانات تتوسط
        
        # شريط التمرير على اليسار (لأن الجدول على اليمين)
        scrollbar = ttk.Scrollbar(table_frame, orient=ctk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        # الجدول على اليمين، والشريط على اليسار
        self.users_tree.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        scrollbar.pack(side=ctk.LEFT, fill=ctk.Y)
        
        # ربط النقر المزدوج للتعديل
        self.users_tree.bind("<Double-1>", lambda e: self._edit_user())
        
        # تنسيق الصفوف حسب الحالة
        self.users_tree.tag_configure('active', background='#d4edda', foreground='#155724')
        self.users_tree.tag_configure('inactive', background='#f8d7da', foreground='#721c24')

    def _load_users(self):
        """تحميل بيانات المستخدمين"""
        # مسح الجدول
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # جلب البيانات
        users = self.db_manager.get_users()
        
        if not users:
            # إذا لم يكن هناك مستخدمون، عرض رسالة
            self.users_tree.insert("", ctk.END, values=("لا توجد مستخدمين", "", "", "", "", "", ""))
            return
        
        # تحويل الحالات للعربية
        role_map = {
            'admin': 'مدير',
            'employee': 'موظف',
            'viewer': 'مشاهد'
        }
        
        # عرض البيانات
        for user in users:
            created_at = ""
            if user.get('created_at'):
                # created_at من قاعدة البيانات هو string، لذا نستخدم str مباشرة
                created_at = str(user['created_at']).split(' ')[0] if user['created_at'] else ""
            
            last_login = "لم يسجل بعد"
            if user.get('last_login'):
                last_login = str(user['last_login']).split(' ')[0] + " " + str(user['last_login']).split(' ')[1][:5] if user['last_login'] and ' ' in str(user['last_login']) else str(user['last_login'])
            
            is_active = reshape_text("نشط") if user.get('is_active') == 1 else reshape_text("غير نشط")
            
            self.users_tree.insert(
                "",
                ctk.END,
                tags=['active' if user.get('is_active') == 1 else 'inactive'],
                values=(
                    last_login,
                    created_at,
                    is_active,
                    reshape_text(role_map.get(user['role'], user['role'])),
                    user['full_name'],
                    user['username'],
                    user['id']
                )
            )

    def _get_role_name(self, role: str) -> str:
        """الحصول على اسم الدور"""
        roles = {
            'admin': 'مدير',
            'employee': 'موظف',
            'viewer': 'مشاهد'
        }
        return reshape_text(roles.get(role, role))

    def _add_user(self):
        """إضافة مستخدم جديد"""
        dialog = UserDialog(self.parent, "إضافة مستخدم جديد")
        if dialog.result:
            # التحقق من صحة البيانات
            if not dialog.result.get("username") or not dialog.result.get("password"):
                messagebox.showerror("خطأ", "اسم المستخدم وكلمة المرور مطلوبان")
                return
            
            # التحقق من وجود المستخدم
            existing_users = self.db_manager.get_users()
            for user in existing_users:
                if user['username'] == dialog.result["username"]:
                    messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل")
                    return
            
            try:
                result = self.db_manager.add_user(
                    dialog.result["username"],
                    dialog.result["password"],
                    dialog.result["full_name"],
                    dialog.result["role"]
                )
                print(f"نتيجة إضافة المستخدم: {result}")
                self._load_users()
                messagebox.showinfo("نجاح", "تم إضافة المستخدم بنجاح")
            except Exception as e:
                print(f"خطأ في إضافة المستخدم: {e}")
                messagebox.showerror("خطأ", f"حدث خطأ أثناء إضافة المستخدم: {str(e)}")

    def _edit_user(self):
        """تعديل بيانات مستخدم"""
        selected_items = self.users_tree.selection()
        if not selected_items:
            messagebox.showwarning("تحذير", "الرجاء اختيار مستخدم للتعديل")
            return

        # نفترض أن عمود 'id' هو الأخير بعد ترتيب RTL
        values = self.users_tree.item(selected_items[0])["values"]
        user_id = values[-1]  # آخر قيمة هي المعرف
        
        # الحصول على بيانات المستخدم من قاعدة البيانات
        users = self.db_manager.get_users()
        user_data = None
        for u in users:
            if u['id'] == user_id:
                user_data = u
                break
        
        if not user_data:
            messagebox.showerror("خطأ", "لم يتم العثور على المستخدم")
            return

        dialog = UserDialog(
            self.parent,
            "تعديل بيانات المستخدم",
            user_data
        )

        if dialog.result:
            try:
                # تحديث بيانات المستخدم
                self.db_manager.execute_update("""
                    UPDATE users 
                    SET full_name = %s, role = %s, is_active = %s
                    WHERE id = %s
                """, (
                    dialog.result["full_name"],
                    dialog.result["role"],
                    dialog.result["is_active"],
                    user_id
                ))
                
                # تحديث كلمة المرور إذا تم إدخالها
                if dialog.result.get("password"):
                    password_hash = self._hash_password(dialog.result["password"])
                    self.db_manager.execute_update(
                        "UPDATE users SET password_hash = %s WHERE id = %s",
                        (password_hash, user_id)
                    )
                
                self._load_users()
                messagebox.showinfo("نجاح", "تم تحديث بيانات المستخدم بنجاح")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تحديث بيانات المستخدم: {str(e)}")

    def _hash_password(self, password: str) -> str:
        """تشفير كلمة المرور"""
        import hashlib
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"

    def _delete_user(self):
        """حذف مستخدم"""
        selected_items = self.users_tree.selection()
        if not selected_items:
            messagebox.showwarning("تحذير", "الرجاء اختيار مستخدم للحذف")
            return

        values = self.users_tree.item(selected_items[0])["values"]
        user_id = values[-1]  # المعرف آخر عمود بعد ترتيب RTL
        
        # منع حذف النفس
        if user_id == self.current_user['id']:
            messagebox.showwarning("تحذير", "لا يمكنك حذف حسابك الخاص")
            return

        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا المستخدم؟"):
            try:
                self.db_manager.execute_update("DELETE FROM users WHERE id = %s", (user_id,))
                self._load_users()
                messagebox.showinfo("نجاح", "تم حذف المستخدم بنجاح")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء حذف المستخدم: {str(e)}")

class UserDialog:
    """نافذة حوار لإضافة/تعديل مستخدم"""

    def __init__(self, parent: ctk.CTkFrame, title: str, user_data: Dict[str, Any] = None):
        """تهيئة النافذة الحوارية"""
        self.result = None
        self.user_data = user_data

        # إنشاء النافذة
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x480")
        self.dialog.resizable(False, False)
        
        # جعل النافذة مشروطة
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # إنشاء واجهة المستخدم
        self._create_ui()

        # توسيط النافذة
        self._center_window()

        # انتظار إغلاق النافذة
        self.dialog.wait_window()

    def _create_ui(self):
        """إنشاء واجهة المستخدم"""
        # إطار النموذج
        form_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=30, pady=20)
        
        # عنوان النموذج
        form_title = ctk.CTkLabel(
            form_frame,
            text=reshape_text("بيانات المستخدم"),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        form_title.pack(pady=(0, 20))
        
        # حقل اسم المستخدم
        username_label = ctk.CTkLabel(form_frame, text=reshape_text("اسم المستخدم:*"), anchor="e")
        username_label.pack(fill=ctk.X, pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=reshape_text("أدخل اسم المستخدم"),
            height=40,
            justify="right"
        )
        self.username_entry.pack(fill=ctk.X, pady=(0, 15))
        
        if self.user_data:
            self.username_entry.insert(0, self.user_data['username'])
            self.username_entry.configure(state="disabled")
        
        # حقل كلمة المرور
        password_label = ctk.CTkLabel(
            form_frame, 
            text=reshape_text("كلمة المرور:" + ("*" if not self.user_data else " (اتركها فارغة للاحتفاظ بالقديمة)")),
            anchor="e"
        )
        password_label.pack(fill=ctk.X, pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=reshape_text("أدخل كلمة المرور"),
            height=40,
            show="•",
            justify="right"
        )
        self.password_entry.pack(fill=ctk.X, pady=(0, 15))
        
        # حقل الاسم الكامل
        fullname_label = ctk.CTkLabel(form_frame, text=reshape_text("الاسم الكامل:*"), anchor="e")
        fullname_label.pack(fill=ctk.X, pady=(0, 5))
        
        self.fullname_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=reshape_text("أدخل الاسم الكامل"),
            height=40,
            justify="right"
        )
        self.fullname_entry.pack(fill=ctk.X, pady=(0, 15))
        
        if self.user_data:
            self.fullname_entry.insert(0, self.user_data.get('full_name', ''))
        
        # اختيار الدور
        role_label = ctk.CTkLabel(form_frame, text=reshape_text("الدور:*"), anchor="e")
        role_label.pack(fill=ctk.X, pady=(0, 5))
        
        role_values = [reshape_text("موظف"), reshape_text("مدير"), reshape_text("مشاهد")]
        self.role_var = ctk.StringVar(value=reshape_text("موظف"))
        self.role_combo = ctk.CTkComboBox(
            form_frame,
            values=role_values,
            variable=self.role_var,
            height=40
        )
        self.role_combo.pack(fill=ctk.X, pady=(0, 15))
        
        if self.user_data:
            role_map = {'admin': 'مدير', 'employee': 'موظف', 'viewer': 'مشاهد'}
            self.role_var.set(reshape_text(role_map.get(self.user_data.get('role', ''), 'موظف')))
        
        # تفعيل المستخدم
        if self.user_data:
            active_label = ctk.CTkLabel(form_frame, text=reshape_text("الحالة:"), anchor="e")
            active_label.pack(fill=ctk.X, pady=(0, 5))
            
            self.active_var = ctk.BooleanVar(value=(self.user_data.get('is_active', 1) == 1))
            active_checkbox = ctk.CTkCheckBox(
                form_frame,
                text=reshape_text("حساب نشط"),
                variable=self.active_var
            )
            active_checkbox.pack(fill=ctk.X, pady=(0, 20))

        # إطار الأزرار
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=10)
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text=reshape_text("إلغاء"),
            command=self._cancel,
            width=120,
            height=40,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_button.pack(side=ctk.LEFT, padx=(0, 10))
        
        save_button = ctk.CTkButton(
            buttons_frame,
            text=reshape_text("حفظ"),
            command=self._save,
            width=120,
            height=40,
            fg_color="#4361ee",
            hover_color="#3a56d4"
        )
        save_button.pack(side=ctk.RIGHT)

    def _center_window(self):
        """توسيط النافذة"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _save(self):
        """حفظ البيانات"""
        # التحقق من البيانات المطلوبة
        if not self.user_data:  # إضافة مستخدم جديد
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            
            if not username:
                messagebox.showwarning("تحذير", "اسم المستخدم مطلوب")
                return
            
            if not password:
                messagebox.showwarning("تحذير", "كلمة المرور مطلوبة")
                return
        else:  # تعديل مستخدم موجود
            username = self.user_data['username']
        
        full_name = self.fullname_entry.get().strip()
        
        if not full_name:
            messagebox.showwarning("تحذير", "الاسم الكامل مطلوب")
            return
        
        # تحويل الدور للإنجليزية
        role_map = {'مدير': 'admin', 'موظف': 'employee', 'مشاهد': 'viewer'}
        role = role_map.get(self.role_var.get(), 'employee')
        
        # التحقق من كلمة المرور
        password = None
        if self.password_entry.get().strip():
            password = self.password_entry.get().strip()
        
        self.result = {
            "username": username,
            "password": password,
            "full_name": full_name,
            "role": role,
            "is_active": 1 if hasattr(self, 'active_var') and self.active_var.get() else 0 if hasattr(self, 'active_var') else 1
        }

        self.dialog.destroy()

    def _cancel(self):
        """إلغاء العملية"""
        self.dialog.destroy()
