# -*- coding: utf-8 -*-
"""
ui/backup_ui.py
---------------
واجهة إدارة النسخ الاحتياطي لنظام إدارة الخدمات الذكي
.

توفر واجهة رسومية لإنشاء واستعادة وحذف النسخ الاحتياطية
مع عرض الحالة التلقائية ودعم اللغة العربية.

الإصدار: 2.2
تاريخ التحديث: أبريل 2026
"""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any
from datetime import datetime
import threading
import logging

from bidi.algorithm import get_display
import arabic_reshaper

from services.backup_service import BackupService
from repositories.database import DatabaseManager
from config import BACKUP_DIR, BACKUP_AUTO_ENABLED, BACKUP_AUTO_INTERVAL_HOURS
from utils.dialogs import show_info, show_success, show_warning, show_error, ask_yes_no

logger = logging.getLogger(__name__)


def reshape_text(text: str) -> str:
    """إعادة تشكيل النص العربي وعرضه بشكل صحيح من اليمين لليسار"""
    if not text:
        return ""
    try:
        reshaper = arabic_reshaper.reshape(
            account_for_ligatures=True,
            support_ligatures=True
        )
        reshaped = reshaper.reshape(text)
        return get_display(reshaped)
    except Exception as e:
        logger.error(f"خطأ في إعادة تشكيل النص: {e}")
        return text


class BackupUI:
    """
    واجهة إدارة النسخ الاحتياطي.

    توفر:
    - عرض قائمة النسخ الاحتياطية المتاحة مع التاريخ والحجم والنوع
    - إنشاء نسخة احتياطية يدوية
    - استعادة من نسخة احتياطية محددة
    - حذف نسخة احتياطية محددة
    - عرض حالة النسخ الاحتياطي التلقائي
    - تفعيل/إيقاف النسخ الاحتياطي التلقائي مع فترة قابلة للتكوين
    - مؤشر تقدم أثناء العمليات
    """

    def __init__(self, parent, db_manager: DatabaseManager,
                 current_user: Dict[str, Any]):
        """
        تهيئة واجهة النسخ الاحتياطي.

        Args:
            parent: عنصر الأب في واجهة المستخدم.
            db_manager: مدير قاعدة البيانات.
            current_user: بيانات المستخدم الحالي.
        """
        self.parent = parent
        self.db_manager = db_manager
        self.current_user = current_user
        self.backup_service = BackupService()

        # إعدادات الألوان
        self.colors = {
            'primary': '#4361ee',
            'secondary': '#3f37c9',
            'success': '#2ec4b6',
            'danger': '#ef233c',
            'warning': '#f77f00',
            'dark': '#1a1a2e',
            'light': '#f8f9fa',
            'gray': '#6c757d'
        }

        # إنشاء الواجهة
        self._create_ui()

        # تحميل قائمة النسخ الاحتياطية
        self._refresh_backup_list()

    # ═══════════════════════════════════════════
    # إنشاء الواجهة
    # ═══════════════════════════════════════════

    def _create_ui(self) -> None:
        """إنشاء جميع عناصر واجهة المستخدم."""
        # العنوان الرئيسي
        title_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        title_frame.pack(fill=ctk.X, pady=(0, 20))

        title_label = ctk.CTkLabel(
            title_frame,
            text=reshape_text("💾  النسخ الاحتياطي"),
            font=ctk.CTkFont(family="Cairo-Bold", size=24),
            text_color=self.colors['dark'],
            anchor="e"
        )
        title_label.pack(side=ctk.RIGHT)

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text=reshape_text("إدارة نسخ قاعدة البيانات الاحتياطية"),
            font=ctk.CTkFont(family="Cairo-Regular", size=13),
            text_color=self.colors['gray'],
            anchor="e"
        )
        subtitle_label.pack(side=ctk.RIGHT)

        # ── قسم حالة النسخ التلقائي ──
        self._create_auto_backup_section()

        # ── قسم الأزرار ──
        self._create_actions_section()

        # ── مؤشر التقدم ──
        self._create_progress_section()

        # ── قسم قائمة النسخ ──
        self._create_backup_list_section()

    def _create_auto_backup_section(self) -> None:
        """إنشاء قسم إعدادات النسخ التلقائي."""
        auto_frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors['light'],
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0"
        )
        auto_frame.pack(fill=ctk.X, pady=(0, 15))

        # عنوان القسم
        auto_title = ctk.CTkLabel(
            auto_frame,
            text=reshape_text("⚙️  إعدادات النسخ التلقائي"),
            font=ctk.CTkFont(family="Cairo-SemiBold", size=15),
            text_color=self.colors['dark'],
            anchor="e"
        )
        auto_title.pack(pady=(15, 10), padx=20, anchor="e")

        # إطار المحتوى
        auto_content = ctk.CTkFrame(auto_frame, fg_color="transparent")
        auto_content.pack(fill=ctk.X, padx=20, pady=(0, 15))

        # زر تفعيل/إيقاف النسخ التلقائي
        self.auto_backup_var = ctk.BooleanVar(
            value=self.backup_service.is_auto_backup_enabled()
        )

        self.btn_toggle_auto = ctk.CTkSwitch(
            auto_content,
            text=reshape_text("تفعيل النسخ التلقائي"),
            font=ctk.CTkFont(family="Cairo-Regular", size=13),
            command=self._toggle_auto_backup,
            variable=self.auto_backup_var,
            text_color=self.colors['dark'],
            fg_color="#d0d0d0",
            progress_color=self.colors['success']
        )
        self.btn_toggle_auto.pack(side=ctk.RIGHT, pady=5)

        # الفاصل بين العناصر
        separator = ctk.CTkLabel(auto_content, text="   ", font=("Arial", 5))
        separator.pack(side=ctk.RIGHT)

        # حقل فترة النسخ التلقائي
        interval_label = ctk.CTkLabel(
            auto_content,
            text=reshape_text("الفترة (ساعات):"),
            font=ctk.CTkFont(family="Cairo-Regular", size=13),
            text_color=self.colors['dark'],
            anchor="e"
        )
        interval_label.pack(side=ctk.RIGHT, pady=5)

        self.interval_entry = ctk.CTkEntry(
            auto_content,
            width=80,
            height=35,
            font=("Cairo", 13),
            justify="center"
        )
        self.interval_entry.insert(0, str(BACKUP_AUTO_INTERVAL_HOURS))
        self.interval_entry.pack(side=ctk.RIGHT, padx=(5, 5), pady=5)

        # زر تحديث الفترة
        self.btn_update_interval = ctk.CTkButton(
            auto_content,
            text=reshape_text("تحديث"),
            width=80,
            height=35,
            font=ctk.CTkFont(family="Cairo-Medium", size=12),
            fg_color=self.colors['primary'],
            hover_color=self.colors['secondary'],
            command=self._update_interval
        )
        self.btn_update_interval.pack(side=ctk.RIGHT, padx=(0, 10), pady=5)

        # عرض الحالة
        self.auto_status_label = ctk.CTkLabel(
            auto_content,
            text="",
            font=ctk.CTkFont(family="Cairo-Regular", size=11),
            text_color=self.colors['gray'],
            anchor="e"
        )
        self.auto_status_label.pack(side=ctk.LEFT, pady=5)
        self._update_auto_status_display()

    def _create_actions_section(self) -> None:
        """إنشاء قسم أزرار العمليات."""
        actions_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        actions_frame.pack(fill=ctk.X, pady=(0, 15))

        # زر إنشاء نسخة احتياطية
        self.btn_create = ctk.CTkButton(
            actions_frame,
            text=reshape_text("💾  إنشاء نسخة احتياطية"),
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            fg_color=self.colors['primary'],
            hover_color=self.colors['secondary'],
            command=self._create_backup
        )
        self.btn_create.pack(side=ctk.RIGHT, padx=(0, 10))

        # زر استعادة
        self.btn_restore = ctk.CTkButton(
            actions_frame,
            text=reshape_text("🔄  استعادة المحدد"),
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            fg_color=self.colors['success'],
            hover_color="#25a89b",
            command=self._restore_backup,
            state="disabled"
        )
        self.btn_restore.pack(side=ctk.RIGHT, padx=(0, 10))

        # زر حذف
        self.btn_delete = ctk.CTkButton(
            actions_frame,
            text=reshape_text("🗑️  حذف المحدد"),
            height=45,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            fg_color=self.colors['danger'],
            hover_color="#d90429",
            command=self._delete_backup,
            state="disabled"
        )
        self.btn_delete.pack(side=ctk.RIGHT, padx=(0, 10))

        # زر تحديث القائمة
        self.btn_refresh = ctk.CTkButton(
            actions_frame,
            text=reshape_text("🔄  تحديث"),
            height=45,
            width=80,
            font=ctk.CTkFont(family="Cairo-Medium", size=14),
            fg_color=self.colors['gray'],
            hover_color="#555555",
            command=self._refresh_backup_list
        )
        self.btn_refresh.pack(side=ctk.RIGHT)

    def _create_progress_section(self) -> None:
        """إنشاء قسم مؤشر التقدم."""
        self.progress_frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors['light'],
            corner_radius=10,
            border_width=1,
            border_color="#e0e0e0"
        )
        # لا يتم عرضه حتى تبدأ عملية
        # self.progress_frame.pack(fill=ctk.X, pady=(0, 15))

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text=reshape_text("جاري العملية..."),
            font=ctk.CTkFont(family="Cairo-Regular", size=13),
            text_color=self.colors['dark'],
            anchor="e"
        )
        self.progress_label.pack(pady=(10, 5), padx=20, anchor="e")

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=8,
            fg_color="#e0e0e0",
            progress_color=self.colors['primary']
        )
        self.progress_bar.pack(pady=(0, 10), padx=20, fill=ctk.X)
        self.progress_bar.set(0)

    def _create_backup_list_section(self) -> None:
        """إنشاء قسم قائمة النسخ الاحتياطية."""
        list_frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors['light'],
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0"
        )
        list_frame.pack(fill=ctk.BOTH, expand=True)

        # عنوان القائمة
        list_title = ctk.CTkLabel(
            list_frame,
            text=reshape_text("📋  النسخ الاحتياطية المتاحة"),
            font=ctk.CTkFont(family="Cairo-SemiBold", size=15),
            text_color=self.colors['dark'],
            anchor="e"
        )
        list_title.pack(pady=(15, 10), padx=20, anchor="e")

        # إطار التمرير
        self.scrollable_frame = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            height=350
        )
        self.scrollable_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 15))

        # متغير تتبع التحديد
        self.selected_backup_index = None
        self.backup_items = []

    # ═══════════════════════════════════════════
    # عمليات النسخ الاحتياطي
    # ═══════════════════════════════════════════

    def _create_backup(self) -> None:
        """إنشاء نسخة احتياطية جديدة (في خيط منفصل)."""
        self._show_progress(reshape_text("جاري إنشاء النسخة الاحتياطية..."))
        self._set_buttons_state(False)

        def worker():
            try:
                backup_path = self.backup_service.create_backup(backup_type="يدوي")
                self.parent.after(0, lambda: self._on_backup_success(backup_path))
            except Exception as e:
                self.parent.after(0, lambda: self._on_backup_error(str(e)))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _restore_backup(self) -> None:
        """استعادة النسخة الاحتياطية المحددة."""
        if self.selected_backup_index is None:
            messagebox.showwarning(
                "تحذير",
                "يرجى اختيار نسخة احتياطية للاستعادة"
            )
            return

        selected = self.backup_items[self.selected_backup_index]
        backup_path = selected['path']

        # تأكيد الاستعادة
        confirm = messagebox.askyesno(
            reshape_text("تأكيد الاستعادة"),
            reshape_text(
                f"هل تريد استعادة النسخة الاحتياطية:\n"
                f"{selected['filename']}\n"
                f"التاريخ: {selected['created_at']}\n\n"
                f"سيتم إنشاء نسخة احتياطية للحالة الحالية أولاً.\n"
                f"سيتم إعادة تشغيل قاعدة البيانات."
            ),
            icon='warning'
        )

        if not confirm:
            return

        self._show_progress(reshape_text("جاري استعادة قاعدة البيانات..."))
        self._set_buttons_state(False)

        def worker():
            try:
                self.backup_service.restore_backup(backup_path)
                self.parent.after(0, lambda: self._on_restore_success())
            except Exception as e:
                self.parent.after(0, lambda: self._on_backup_error(str(e)))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _delete_backup(self) -> None:
        """حذف النسخة الاحتياطية المحددة."""
        if self.selected_backup_index is None:
            messagebox.showwarning(
                "تحذير",
                "يرجى اختيار نسخة احتياطية للحذف"
            )
            return

        selected = self.backup_items[self.selected_backup_index]

        # تأكيد الحذف
        confirm = messagebox.askyesno(
            reshape_text("تأكيد الحذف"),
            reshape_text(
                f"هل تريد حذف النسخة الاحتياطية:\n"
                f"{selected['filename']}\n"
                f"التاريخ: {selected['created_at']}\n\n"
                f"لا يمكن التراجع عن هذا الإجراء!"
            ),
            icon='warning'
        )

        if not confirm:
            return

        try:
            self.backup_service.delete_backup(selected['path'])
            messagebox.showinfo(
                "نجاح",
                "تم حذف النسخة الاحتياطية بنجاح"
            )
            self._refresh_backup_list()
        except Exception as e:
            messagebox.showerror(
                "خطأ",
                f"فشل حذف النسخة الاحتياطية: {str(e)}"
            )

    # ═══════════════════════════════════════════
    # النسخ التلقائي
    # ═══════════════════════════════════════════

    def _toggle_auto_backup(self) -> None:
        """تفعيل أو إيقاف النسخ الاحتياطي التلقائي."""
        try:
            if self.auto_backup_var.get():
                interval = float(self.interval_entry.get())
                self.backup_service.schedule_auto_backup(interval_hours=interval)
                messagebox.showinfo(
                    "نجاح",
                    reshape_text("تم تفعيل النسخ الاحتياطي التلقائي")
                )
            else:
                self.backup_service.stop_auto_backup()
                messagebox.showinfo(
                    "معلومات",
                    reshape_text("تم إيقاف النسخ الاحتياطي التلقائي")
                )
            self._update_auto_status_display()
        except ValueError:
            messagebox.showerror(
                "خطأ",
                "يرجى إدخال رقم صحيح للفترة بالساعات"
            )
            self.auto_backup_var.set(False)
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ: {str(e)}")
            self.auto_backup_var.set(False)

    def _update_interval(self) -> None:
        """تحديث فترة النسخ الاحتياطي التلقائي."""
        try:
            interval = float(self.interval_entry.get())
            if interval < 1:
                messagebox.showerror(
                    "خطأ",
                    "يجب أن تكون الفترة ساعة واحدة على الأقل"
                )
                return

            if self.backup_service.is_auto_backup_enabled():
                self.backup_service.schedule_auto_backup(interval_hours=interval)
                self._update_auto_status_display()
                messagebox.showinfo(
                    "نجاح",
                    reshape_text(f"تم تحديث الفترة إلى {interval} ساعة")
                )
            else:
                messagebox.showinfo(
                    "معلومات",
                    "يرجى تفعيل النسخ التلقائي أولاً"
                )
        except ValueError:
            messagebox.showerror(
                "خطأ",
                "يرجى إدخال رقم صحيح للفترة بالساعات"
            )

    def _update_auto_status_display(self) -> None:
        """تحديث عرض حالة النسخ التلقائي."""
        try:
            if self.backup_service.is_auto_backup_enabled():
                next_time = self.backup_service.get_next_backup_time()
                status_text = f"✅ {reshape_text('مفعّل')}"
                if next_time:
                    status_text += f" - {reshape_text('النسخة التالية')}: {next_time}"
                self.auto_status_label.configure(
                    text=status_text,
                    text_color=self.colors['success']
                )
            else:
                self.auto_status_label.configure(
                    text=f"❌ {reshape_text('متوقف')}",
                    text_color=self.colors['danger']
                )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    # قائمة النسخ الاحتياطية
    # ═══════════════════════════════════════════

    def _refresh_backup_list(self) -> None:
        """تحديث قائمة النسخ الاحتياطية."""
        # مسح القائمة الحالية
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.backup_items = []
        self.selected_backup_index = None
        self.btn_restore.configure(state="disabled")
        self.btn_delete.configure(state="disabled")

        # الحصول على القائمة
        backups = self.backup_service.get_backup_list()

        if not backups:
            empty_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=reshape_text("📭  لا توجد نسخ احتياطية متاحة"),
                font=ctk.CTkFont(family="Cairo-Regular", size=14),
                text_color=self.colors['gray']
            )
            empty_label.pack(pady=30)
            return

        # إنشاء رأس الجدول
        self._create_table_header()

        # إنشاء صف لكل نسخة
        for index, backup in enumerate(backups):
            self._create_backup_row(index, backup)

        self.backup_items = backups

    def _create_table_header(self) -> None:
        """إنشاء رأس جدول النسخ الاحتياطية."""
        header_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=self.colors['dark'],
            corner_radius=8,
            height=40
        )
        header_frame.pack(fill=ctk.X, pady=(0, 5), padx=5)
        header_frame.pack_propagate(False)

        headers = [
            ("النوع", 100),
            ("الحجم", 100),
            ("التاريخ", 200),
            ("اسم الملف", 300),
        ]

        for text, width in reversed(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=reshape_text(text),
                font=ctk.CTkFont(family="Cairo-SemiBold", size=12),
                text_color="#ffffff",
                width=width,
                anchor="center"
            )
            label.pack(side=ctk.RIGHT, padx=5, pady=5)

    def _create_backup_row(self, index: int, backup: Dict[str, Any]) -> None:
        """إنشاء صف لنسخة احتياطية."""
        is_even = index % 2 == 0
        bg_color = "#f9f9f9" if is_even else "#ffffff"

        row_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=bg_color,
            corner_radius=8,
            height=45,
            cursor="hand2"
        )
        row_frame.pack(fill=ctk.X, pady=1, padx=5)
        row_frame.pack_propagate(False)

        # ربط الأحداث
        row_frame.bind("<Button-1>", lambda e, i=index: self._select_backup(i))
        for child in [row_frame]:
            child.bind("<Button-1>", lambda e, i=index: self._select_backup(i))

        # نوع النسخة
        type_text = backup.get('type', 'يدوي')
        type_color = self.colors['primary'] if type_text == 'تلقائي' else self.colors['warning']
        type_label = ctk.CTkLabel(
            row_frame,
            text=reshape_text(f"{'🤖 ' if type_text == 'تلقائي' else '👤 '}{type_text}"),
            font=ctk.CTkFont(family="Cairo-Regular", size=12),
            text_color=type_color,
            width=100,
            anchor="center"
        )
        type_label.pack(side=ctk.RIGHT, padx=5)
        type_label.bind("<Button-1>", lambda e, i=index: self._select_backup(i))

        # الحجم
        size_label = ctk.CTkLabel(
            row_frame,
            text=backup.get('size_formatted', ''),
            font=ctk.CTkFont(family="Cairo-Regular", size=12),
            text_color=self.colors['dark'],
            width=100,
            anchor="center"
        )
        size_label.pack(side=ctk.RIGHT, padx=5)
        size_label.bind("<Button-1>", lambda e, i=index: self._select_backup(i))

        # التاريخ
        date_label = ctk.CTkLabel(
            row_frame,
            text=backup.get('created_at', ''),
            font=ctk.CTkFont(family="Cairo-Regular", size=12),
            text_color=self.colors['dark'],
            width=200,
            anchor="center"
        )
        date_label.pack(side=ctk.RIGHT, padx=5)
        date_label.bind("<Button-1>", lambda e, i=index: self._select_backup(i))

        # اسم الملف
        name_label = ctk.CTkLabel(
            row_frame,
            text=backup.get('filename', ''),
            font=ctk.CTkFont(family="Cairo-Regular", size=12),
            text_color=self.colors['dark'],
            width=300,
            anchor="center"
        )
        name_label.pack(side=ctk.RIGHT, padx=5)
        name_label.bind("<Button-1>", lambda e, i=index: self._select_backup(i))

    def _select_backup(self, index: int) -> None:
        """تحديد نسخة احتياطية."""
        # إلغاء التحديد السابق
        if self.selected_backup_index is not None:
            self._highlight_row(self.selected_backup_index, False)

        self.selected_backup_index = index
        self._highlight_row(index, True)

        # تفعيل أزرار الاستعادة والحذف
        self.btn_restore.configure(state="normal")
        self.btn_delete.configure(state="normal")

    def _highlight_row(self, index: int, highlight: bool) -> None:
        """تمييز صف محدد."""
        children = self.scrollable_frame.winfo_children()
        # تخطي رأس الجدول (الفهرس 0)
        actual_index = index + 1
        if actual_index < len(children):
            if highlight:
                children[actual_index].configure(
                    fg_color=self.colors['primary']
                )
                # تغيير لون النص إلى أبيض
                for child in children[actual_index].winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        child.configure(text_color="#ffffff")
            else:
                bg_color = "#f9f9f9" if index % 2 == 0 else "#ffffff"
                children[actual_index].configure(fg_color=bg_color)
                for child in children[actual_index].winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        child.configure(text_color=self.colors['dark'])

    # ═══════════════════════════════════════════
    # مؤشر التقدم والنتائج
    # ═══════════════════════════════════════════

    def _show_progress(self, message: str) -> None:
        """عرض مؤشر التقدم."""
        self.progress_label.configure(text=message)
        self.progress_bar.set(0.3)
        self.progress_frame.pack(fill=ctk.X, pady=(0, 15))

    def _hide_progress(self) -> None:
        """إخفاء مؤشر التقدم."""
        self.progress_frame.pack_forget()

    def _set_buttons_state(self, enabled: bool) -> None:
        """تفعيل/تعطيل الأزرار أثناء العمليات."""
        state = "normal" if enabled else "disabled"
        self.btn_create.configure(state=state)
        self.btn_restore.configure(state=state if enabled else "disabled")
        self.btn_delete.configure(state=state if enabled else "disabled")
        self.btn_refresh.configure(state=state)

    def _on_backup_success(self, backup_path: str) -> None:
        """معالجة نجاح إنشاء النسخة الاحتياطية."""
        self.progress_bar.set(1.0)
        self._hide_progress()
        self._set_buttons_state(True)

        filename = os.path.basename(backup_path)
        messagebox.showinfo(
            "نجاح",
            reshape_text(f"تم إنشاء النسخة الاحتياطية بنجاح:\n{filename}")
        )
        self._refresh_backup_list()
        self._update_auto_status_display()

    def _on_restore_success(self) -> None:
        """معالجة نجاح استعادة النسخة الاحتياطية."""
        self.progress_bar.set(1.0)
        self._hide_progress()
        self._set_buttons_state(True)

        messagebox.showinfo(
            "نجاح",
            reshape_text(
                "تمت استعادة قاعدة البيانات بنجاح!\n"
                "يرجى إعادة تشغيل التطبيق لضمان التحميل الصحيح للبيانات."
            )
        )
        self._refresh_backup_list()

    def _on_backup_error(self, error_message: str) -> None:
        """معالجة خطأ في عملية النسخ الاحتياطية."""
        self._hide_progress()
        self._set_buttons_state(True)

        messagebox.showerror(
            "خطأ",
            reshape_text(f"فشلت العملية:\n{error_message}")
        )
