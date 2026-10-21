# -*- coding: utf-8 -*-
"""
وحدة المساعدة للتشغيل غير المتزامن (Async Helper)
--------------------------------------------------
تحل مشكلة تجمد الشاشة عند جلب البيانات من قاعدة البيانات

使用方法:
    from ui.async_helper import run_async
    
    # في أي مكان في الكود:
    run_async(lambda: db_manager.get_customers(), callback=update_ui)
"""

import threading
import queue
from typing import Callable, Any, Optional
import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)


class AsyncHelper:
    """مساعد التشغيل غير المتزامن"""
    
    def __init__(self, root: ctk.CTk = None):
        self.root = root
        self.task_queue = queue.Queue()
        self._process_queue()
    
    def _process_queue(self):
        """معالجة المهام في قائمة الانتظار"""
        try:
            while True:
                task = self.task_queue.get_nowait()
                func, callback, args, kwargs = task
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        if self.root:
                            self.root.after(0, lambda r=result: callback(r))
                        else:
                            callback(result)
                except Exception as e:
                    logger.error(f"خطأ في التنفيذ: {e}")
                    if callback:
                        if self.root:
                            self.root.after(0, lambda: callback(None))
                        else:
                            callback(None)
        except queue.Empty:
            pass
        
        # الاستمرار في المعالجة
        if self.root:
            self.root.after(100, self._process_queue)
    
    def run(self, func: Callable, callback: Optional[Callable] = None, *args, **kwargs):
        """تشغيل دالة في خيط منفصل"""
        thread = threading.Thread(target=self._run_task, args=(func, callback, args, kwargs))
        thread.daemon = True
        thread.start()
    
    def _run_task(self, func: Callable, callback: Optional[Callable], args: tuple, kwargs: dict):
        """تنفيذ المهمة في خيط منفصل"""
        try:
            result = func(*args, **kwargs)
            self.task_queue.put((func, callback, args, kwargs))
        except Exception as e:
            logger.error(f"خطأ في المهمة: {e}")
            self.task_queue.put((func, lambda r: callback and callback(None), args, kwargs))


# دالة مساعدة سريعة
_global_helper = None

def get_helper(root: ctk.CTk = None) -> AsyncHelper:
    """الحصول على مساعد التشغيل غير المتزامن"""
    global _global_helper
    if _global_helper is None:
        _global_helper = AsyncHelper(root)
    return _global_helper


def run_async(func: Callable, callback: Optional[Callable] = None, *args, **kwargs):
    """تشغيل دالة بشكل غير متزامن"""
    helper = get_helper()
    helper.run(func, callback, *args, **kwargs)


class LoadingOverlay:
    """طبقة التحميل التي تظهر فوق النافذة"""
    
    def __init__(self, parent: ctk.CTkFrame):
        self.parent = parent
        self.overlay = None
        self.label = None
        self.progress = None
    
    def show(self, message: str = "جاري التحميل..."):
        """إظهار طبقة التحميل"""
        if self.overlay:
            return
            
        # إنشاء الإطار الشامل
        self.overlay = ctk.CTkFrame(self.parent, fg_color="black")
        self.overlay.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        
        # شفافية
        self.overlay.winfo_children()
        
        # رسالة التحميل
        self.label = ctk.CTkLabel(
            self.overlay,
            text=message,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        self.label.pack(pady=20)
        
        # مؤشر التحميل
        self.progress = ctk.CTkProgressBar(
            self.overlay,
            mode="indeterminate",
            width=200
        )
        self.progress.pack(pady=10)
        self.progress.start()
    
    def hide(self):
        """إخفاء طبقة التحميل"""
        if self.progress:
            self.progress.stop()
            self.progress.destroy()
        if self.label:
            self.label.destroy()
        if self.overlay:
            self.overlay.destroy()
        
        self.overlay = None
        self.label = None
        self.progress = None


def add_loading_to_method(cls, method_name: str, loading_message: str = "جاري التحميل..."):
    """إضافة طبقة تحميل إلى دالة في كلاس"""
    original_method = getattr(cls, method_name)
    
    def new_method(self, *args, **kwargs):
        # إظهار التحميل
        loading = LoadingOverlay(self.parent if hasattr(self, 'parent') else None)
        loading.show(loading_message)
        
        try:
            return original_method(self, *args, **kwargs)
        finally:
            loading.hide()
    
    setattr(cls, method_name, new_method)


# Context Manager للاستخدام المؤقت
class AsyncContext:
    """سياق التشغيل غير المتزامن"""
    
    def __init__(self, frame: ctk.CTkFrame):
        self.frame = frame
        self.loading = None
    
    def __enter__(self):
        self.loading = LoadingOverlay(self.frame)
        self.loading.show()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.loading:
            self.loading.hide()
        return False