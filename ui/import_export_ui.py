import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Dict, Any
from services.import_export_service import DataImporter, DataExporter, create_template_files
from repositories.database import DatabaseManager
from bidi.algorithm import get_display
import arabic_reshaper
from utils.dialogs import show_info, show_success, show_warning, show_error, ask_yes_no


def reshape_text(text: str) -> str:
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

class ImportExportUI:
    """واجهة استيراد وتصدير البيانات"""

    def __init__(self, parent: ctk.CTkFrame, db_manager: DatabaseManager, 
                 current_user: Dict[str, Any]):
        """تهيئة واجهة الاستيراد والتصدير"""
        self.parent = parent
        self.db_manager = db_manager
        self.current_user = current_user
        self.importer = DataImporter(db_manager)
        self.exporter = DataExporter(db_manager)
        self._create_ui()

    def _create_ui(self):
        """إنشاء واجهة المستخدم"""
        # عنوان الصفحة
        title_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        title_frame.pack(fill=ctk.X, pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=reshape_text("استيراد وتصدير البيانات"),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1a1a2e",
            anchor="e"
        )
        title_label.pack(side=ctk.RIGHT)

        
        # إطار الاستيراد
        import_frame = ctk.CTkFrame(self.parent, fg_color="white", corner_radius=15,
                                    border_width=1, border_color="#e0e0e0")
        import_frame.pack(fill=ctk.BOTH, expand=True, pady=(0, 20))
        
        import_title = ctk.CTkLabel(
            import_frame,
            text=reshape_text("📥 استيراد البيانات"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1a1a2e",
            anchor="e"
        )
        import_title.pack(pady=15)

        
        # محتوى الاستيراد
        import_content = ctk.CTkFrame(import_frame, fg_color="transparent")
        import_content.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # زر تحميل القوالب
        templates_button = ctk.CTkButton(
            import_content,
            text=reshape_text("📋 تنزيل ملفات القوالب"),
            command=self._download_templates,
            width=250,
            height=45,
            fg_color="#6c757d",
            hover_color="#5a6268",
            font=ctk.CTkFont(size=14)
        )
        templates_button.pack(pady=(0, 20))
        
        # أزرار الاستيراد
        buttons_grid = ctk.CTkFrame(import_content, fg_color="transparent")
        buttons_grid.pack(fill=ctk.X)
        
        # استيراد العملاء
        import_customers_btn = ctk.CTkButton(
            buttons_grid,
            text=reshape_text("👥 استيراد العملاء"),
            command=lambda: self._import_data('customers'),
            width=200,
            height=50,
            fg_color="#2ec4b6",
            hover_color="#25a89c",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        import_customers_btn.pack(side=ctk.LEFT, padx=(0, 15), pady=10)
        
        # استيراد الخدمات
        import_services_btn = ctk.CTkButton(
            buttons_grid,
            text=reshape_text("🛠️ استيراد الخدمات"),
            command=lambda: self._import_data('services'),
            width=200,
            height=50,
            fg_color="#4361ee",
            hover_color="#3a56d4",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        import_services_btn.pack(side=ctk.LEFT, padx=(0, 15), pady=10)
        
        # استيراد الطلبات
        import_orders_btn = ctk.CTkButton(
            buttons_grid,
            text=reshape_text("📋 استيراد الطلبات"),
            command=lambda: self._import_data('orders'),
            width=200,
            height=50,
            fg_color="#f77f00",
            hover_color="#e07000",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        import_orders_btn.pack(side=ctk.LEFT, pady=10)
        
        # معلومات الاستيراد
        info_frame = ctk.CTkFrame(import_content, fg_color="#f8f9fa", corner_radius=10)
        info_frame.pack(fill=ctk.X, pady=(20, 0))
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="""ملاحظات مهمة للاستيراد:
• الملفات المدعومة: Excel (.xlsx, .xls) و CSV
• يجب أن تحتوي الملفات على الأعمدة المطلوبة المحددة في القوالب
• للاستيراد، يجب أن تكون البيانات موجودة مسبقاً (مثل: اسم العميل للطلبات)
• سيتم تجاهل الصفوف التي تحتوي على بيانات ناقصة""",
            font=ctk.CTkFont(size=11),
            text_color="#6c757d",
            justify="right"
        )
        info_label.pack(pady=15)
        
        # إطار التصدير
        export_frame = ctk.CTkFrame(self.parent, fg_color="white", corner_radius=15,
                                     border_width=1, border_color="#e0e0e0")
        export_frame.pack(fill=ctk.BOTH, expand=True)
        
        export_title = ctk.CTkLabel(
            export_frame,
            text="📤 تصدير البيانات",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1a1a2e"
        )
        export_title.pack(pady=15)
        
        # محتوى التصدير
        export_content = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_content.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # أزرار التصدير
        export_buttons_grid = ctk.CTkFrame(export_content, fg_color="transparent")
        export_buttons_grid.pack(fill=ctk.X)
        
        # تصدير العملاء
        export_customers_btn = ctk.CTkButton(
            export_buttons_grid,
            text="👥 تصدير العملاء",
            command=lambda: self._export_data('customers'),
            width=200,
            height=50,
            fg_color="#2ec4b6",
            hover_color="#25a89c",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        export_customers_btn.pack(side=ctk.LEFT, padx=(0, 15), pady=10)
        
        # تصدير الخدمات
        export_services_btn = ctk.CTkButton(
            export_buttons_grid,
            text="🛠️ تصدير الخدمات",
            command=lambda: self._export_data('services'),
            width=200,
            height=50,
            fg_color="#4361ee",
            hover_color="#3a56d4",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        export_services_btn.pack(side=ctk.LEFT, padx=(0, 15), pady=10)
        
        # تصدير الطلبات
        export_orders_btn = ctk.CTkButton(
            export_buttons_grid,
            text="📋 تصدير الطلبات",
            command=lambda: self._export_data('orders'),
            width=200,
            height=50,
            fg_color="#f77f00",
            hover_color="#e07000",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        export_orders_btn.pack(side=ctk.LEFT, pady=10)

    def _download_templates(self):
        """تحميل ملفات القوالب"""
        try:
            # اختيار مجلد الحفظ
            folder_selected = filedialog.askdirectory(title="اختر مجلد حفظ القوالب")
            
            if not folder_selected:
                return
            
            # إنشاء القوالب
            create_template_files(folder_selected)
            
            messagebox.showinfo(
                "نجاح",
                f"تم إنشاء ملفات القوالب في المجلد:\n{folder_selected}\n\nالملفات:\n- قالب_العملاء.xlsx\n- قالب_الخدمات.xlsx\n- قالب_الطلبات.xlsx"
            )
            
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إنشاء القوالب: {str(e)}")

    def _import_data(self, data_type: str):
        """استيراد البيانات من ملف"""
        try:
            # فتح نافذة اختيار الملف
            file_path = filedialog.askopenfilename(
                title=f"اختر ملف استيراد {data_type}",
                filetypes=[
                    ("Excel files", "*.xlsx *.xls"),
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # استيراد البيانات
            if data_type == 'customers':
                result = self.importer.import_customers_from_file(
                    file_path, 
                    self.current_user['id']
                )
            elif data_type == 'services':
                result = self.importer.import_services_from_file(
                    file_path,
                    self.current_user['id']
                )
            elif data_type == 'orders':
                result = self.importer.import_orders_from_file(
                    file_path,
                    self.current_user['id']
                )
            else:
                messagebox.showerror("خطأ", "نوع بيانات غير معروف")
                return
            
            # عرض النتيجة
            if result.get('success'):
                message_text = f"✅ تم الاستيراد بنجاح!\n\n"
                message_text += f"العدد المستورد: {result.get('imported', 0)}\n"
                message_text += f"الأخطاء: {result.get('errors', 0)}"
                
                if result.get('error_details'):
                    message_text += "\n\nأول 10 أخطاء:"
                    for error in result['error_details']:
                        message_text += f"\n- {error}"
                
                messagebox.showinfo("نجاح", message_text)
            else:
                messagebox.showerror("خطأ", result.get('message', 'حدث خطأ غير معروف'))
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الاستيراد: {str(e)}")

    def _export_data(self, data_type: str):
        """تصدير البيانات إلى ملف"""
        try:
            # فتح نافذة حفظ الملف
            file_path = filedialog.asksaveasfilename(
                title=f"حفظ {data_type}",
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("CSV files", "*.csv")
                ]
            )
            
            if not file_path:
                return
            
            # تحديد التنسيق
            format_type = 'csv' if file_path.endswith('.csv') else 'xlsx'
            
            # تصدير البيانات
            success = False
            
            if data_type == 'customers':
                success = self.exporter.export_customers(file_path, format_type)
            elif data_type == 'services':
                success = self.exporter.export_services(file_path, format_type)
            elif data_type == 'orders':
                success = self.exporter.export_orders(file_path, format_type)
            
            if success:
                # تسجيل النشاط
                self.db_manager.log_activity(
                    self.current_user['id'],
                    f"تصدير {data_type}",
                    data_type,
                    None,
                    f"تصدير البيانات إلى الملف: {file_path}"
                )
                
                messagebox.showinfo(
                    "نجاح",
                    f"✅ تم تصدير البيانات بنجاح!\n\nمسار الملف:\n{file_path}"
                )
            else:
                messagebox.showwarning("تحذير", "لا توجد بيانات للتصدير")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التصدير: {str(e)}")
