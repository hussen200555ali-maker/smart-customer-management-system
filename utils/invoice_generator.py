# -*- coding: utf-8 -*-
"""
utils/invoice_generator.py
--------------------------
أدوات توليد الفواتير PDF والطباعة.

الإصدار: 2.1
تاريخ التحديث: أبريل 2026
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont
import arabic_reshaper
from bidi.algorithm import get_display
import os

from config import FONTS_DIR


class InvoiceGenerator:
    """فئة لتوليد فواتير PDF"""

    def __init__(self):
        """تهيئة مولد الفواتير"""
        self._register_arabic_fonts()

    def _register_arabic_fonts(self):
        """تسجيل الخطوط العربية"""
        try:
            # مسار الخطوط من config
            fonts_dir = FONTS_DIR

            # تسجيل خطوط Cairo المختلفة
            cairo_fonts = {
                'Cairo-Regular': 'Cairo-Regular.ttf',
                'Cairo-Bold': 'Cairo-Bold.ttf'
            }

            for font_name, font_file in cairo_fonts.items():
                font_path = os.path.join(fonts_dir, font_file)
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        registerFont(TTFont(font_name, font_path))
                    except Exception:
                        pass
        except Exception:
            pass

    def _reshape_arabic(self, text):
        """إعادة تشكيل النص العربي"""
        if not text:
            return ""
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text

    def generate_invoice(self, order, output_path):
        """توليد فاتورة PDF للطلب المحدد"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        elements = []
        styles = getSampleStyleSheet()

        # إنشاء أنماط مخصصة للعربية
        arabic_title = ParagraphStyle(
            'ArabicTitle',
            parent=styles['Heading1'],
            fontName='Cairo-Bold',
            fontSize=24,
            alignment=1,  # 1 = center
            spaceAfter=0.5*cm
        )

        arabic_normal = ParagraphStyle(
            'ArabicNormal',
            parent=styles['Normal'],
            fontName='Cairo-Regular',
            fontSize=11,
            alignment=1,  # 1 = center
            spaceAfter=0.3*cm
        )

        arabic_bold = ParagraphStyle(
            'ArabicBold',
            parent=styles['Normal'],
            fontName='Cairo-Bold',
            fontSize=12,
            alignment=1,  # 1 = center
            spaceAfter=0.3*cm
        )

        # عنوان الفاتورة
        title = self._reshape_arabic("فاتورة رسمية")
        elements.append(Paragraph(title, arabic_title))

        # معلومات الطلب
        order_info = [
            [self._reshape_arabic(f"رقم الطلب: #{order.id}"),
             self._reshape_arabic(f"التاريخ: {order.created_at.strftime('%Y-%m-%d') if order.created_at else '—'}")],
            [self._reshape_arabic(f"العميل: {order.customer_name}"),
             self._reshape_arabic(f"الهاتف: {order.customer_phone or '—'}")]
        ]

        order_table = Table(order_info, colWidths=[8*cm, 8*cm])
        order_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Cairo-Regular'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.3*cm),
        ]))
        elements.append(order_table)
        elements.append(Spacer(1, 0.5*cm))

        # جدول الخدمات
        if hasattr(order, 'details') and order.details:
            # رأس الجدول
            headers = [
                self._reshape_arabic('الخدمة'),
                self._reshape_arabic('الكمية'),
                self._reshape_arabic('السعر'),
                self._reshape_arabic('المجموع')
            ]

            # بيانات الخدمات
            data = [headers]
            for detail in order.details:
                service_name = detail.get('service_name', '')
                qty = detail.get('quantity', 1)
                price = detail.get('unit_price', 0)
                total = detail.get('total_price', qty * price)

                row = [
                    self._reshape_arabic(service_name),
                    str(qty),
                    f"{price:.2f}",
                    f"{total:.2f}"
                ]
                data.append(row)

            # إنشاء الجدول
            services_table = Table(data, colWidths=[6*cm, 3*cm, 4*cm, 4*cm])
            services_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f7a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Cairo-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, -1), 'Cairo-Regular'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.3*cm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.3*cm),
            ]))
            elements.append(services_table)
            elements.append(Spacer(1, 0.5*cm))

        # المجموع الكلي
        total_text = self._reshape_arabic(f"المجموع الكلي: {order.total_amount:.2f} ر.س")
        total_paragraph = Paragraph(total_text, arabic_bold)
        elements.append(total_paragraph)

        # الملاحظات
        if order.notes:
            elements.append(Spacer(1, 0.5*cm))
            notes_title = self._reshape_arabic("ملاحظات:")
            elements.append(Paragraph(notes_title, arabic_bold))
            notes_text = self._reshape_arabic(order.notes)
            elements.append(Paragraph(notes_text, arabic_normal))

        # توليد الملف
        doc.build(elements)
        return output_path
