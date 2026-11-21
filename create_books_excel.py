from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Book Inventory"

# --- Styles ---
header_font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
title_font = Font(name="Calibri", size=14, bold=True, color="2F5496")
normal_font = Font(name="Calibri", size=11)
bold_font = Font(name="Calibri", size=11, bold=True)
center = Alignment(horizontal="center", vertical="center")
left = Alignment(horizontal="left", vertical="center")
right = Alignment(horizontal="right", vertical="center")

thin = Side(border_style="thin", color="B0B0B0")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

# --- Title row ---
ws.merge_cells("A1:C1")
ws["A1"] = "Book Inventory & Pricing"
ws["A1"].font = title_font
ws["A1"].alignment = center
ws.row_dimensions[1].height = 24

# --- Header row ---
headers = ["Book Name", "Language", "Price (₹)"]
for col, h in enumerate(headers, start=1):
    c = ws.cell(row=2, column=col, value=h)
    c.font = header_font
    c.fill = header_fill
    c.alignment = center
    c.border = border
ws.row_dimensions[2].height = 20

# --- Data ---
# Srimad Bhagavatham (price varies by language)
data = [
    ("Srimad Bhagavatham", "Telugu", 7500),
    ("Srimad Bhagavatham", "English", 10000),
    ("Srimad Bhagavatham", "Hindi", 8000),
    ("Chaithanya Charithamrutham", "Telugu", None),
    ("Chaithanya Charithamrutham", "English", None),
    ("Chaithanya Charithamrutham", "Hindi", None),
    ("Bhagavadgita", "Any", 350),
    ("Ramayan", "Any", 300),
    ("Krishna", "Any", 350),
    ("Science of Self Realization", "Any", 200),
    ("Small Books (Any book)", "Any", 50),
]

start_row = 3
for i, (book, lang, price) in enumerate(data):
    r = start_row + i
    ws.cell(row=r, column=1, value=book).font = bold_font
    ws.cell(row=r, column=2, value=lang).font = normal_font
    price_cell = ws.cell(row=r, column=3, value=price)
    price_cell.font = normal_font
    if price is not None:
        price_cell.number_format = '#,##0" ₹"'
    else:
        price_cell.value = "—"
        price_cell.font = Font(name="Calibri", size=11, italic=True, color="808080")
        price_cell.alignment = center

    for col in range(1, 4):
        cell = ws.cell(row=r, column=col)
        cell.border = border
        if col == 1:
            cell.alignment = left
        else:
            cell.alignment = center if price is None else right
    ws.row_dimensions[r].height = 18

# --- Column widths ---
ws.column_dimensions["A"].width = 34
ws.column_dimensions["B"].width = 14
ws.column_dimensions["C"].width = 16

# Freeze header
ws.freeze_panes = "A3"

out_path = r"c:\Users\HP\Self Projects(Django)\Voice Auditor\Book_Inventory.xlsx"
wb.save(out_path)
print("Saved:", out_path)
