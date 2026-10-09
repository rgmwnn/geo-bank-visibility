"""Builds tests/fixtures/report.pdf: two pages of invented text. Run once: python tests/fixtures/make_pdf.py"""
from pathlib import Path

from fpdf import FPDF

pdf = FPDF()
pdf.set_font("Helvetica", size=12)
for text in ["Laporan tahunan contoh halaman pertama. Bank Contoh mencatat laba bersih yang tumbuh.",
             "Halaman kedua laporan contoh. Rasio kecukupan modal tetap kuat sepanjang tahun."]:
    pdf.add_page()
    pdf.multi_cell(0, 8, text)
pdf.output(str(Path(__file__).with_name("report.pdf")))
