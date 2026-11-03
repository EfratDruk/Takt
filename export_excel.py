from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


HEADERS = ("כותרת", "תיאור הבעיה", "קטגוריה", "מספר דיווחים")
TEXT_FIELDS = ("title", "description", "category")


def _spreadsheet_text(value):
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def export_issues_to_excel(issues, output_path="דוח_בעיות_טקט.xlsx"):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "בעיות"
    worksheet.sheet_view.rightToLeft = True
    worksheet.append(HEADERS)

    for issue in issues:
        worksheet.append([
            _spreadsheet_text(issue.get(field, ""))
            for field in TEXT_FIELDS
        ] + [issue.get("count", 1)])

    header_fill = PatternFill(fill_type="solid", fgColor="1F4E78")
    for cell in worksheet[1]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="right", vertical="center")

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.sheet_view.showGridLines = False
    worksheet.row_dimensions[1].height = 24

    column_widths = (36, 90, 22, 18)
    for index, width in enumerate(column_widths, start=1):
        worksheet.column_dimensions[get_column_letter(index)].width = width

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(horizontal="right", vertical="top", wrap_text=True)
        row[3].alignment = Alignment(horizontal="center", vertical="top")

    worksheet.page_setup.orientation = "landscape"
    worksheet.page_setup.fitToWidth = 1
    worksheet.page_setup.fitToHeight = 0
    worksheet.sheet_properties.pageSetUpPr.fitToPage = True
    worksheet.print_title_rows = "1:1"

    if hasattr(output_path, "write"):
        workbook.save(output_path)
        return output_path

    output_path = Path(output_path)
    workbook.save(output_path)
    return output_path
