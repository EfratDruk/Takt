from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException


FEEDBACK_HEADER = "הערות"


def load_feedback_from_excel(source, source_name, header_name=FEEDBACK_HEADER):
    header_name = str(header_name).strip()
    if not header_name:
        raise ValueError("The Excel feedback column header cannot be empty.")

    try:
        workbook = load_workbook(source, read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, OSError, ValueError) as error:
        raise ValueError(f"Could not open Excel file {source_name}: {error}") from error

    feedback = []
    found_header = False
    try:
        for worksheet in workbook.worksheets:
            feedback_column = None
            header_row_index = None
            for row in worksheet.iter_rows():
                for column_index, cell in enumerate(row):
                    if str(cell.value or "").strip() == header_name:
                        feedback_column = column_index
                        header_row_index = row[0].row
                        found_header = True
                        break
                if feedback_column is not None:
                    break

            if feedback_column is None:
                continue

            for row in worksheet.iter_rows(min_row=header_row_index + 1):
                if feedback_column >= len(row):
                    continue
                value = row[feedback_column].value
                if value is not None and str(value).strip():
                    feedback.append({
                        "source_file": source_name,
                        "comment": str(value).strip(),
                    })
    finally:
        workbook.close()

    if not found_header:
        raise ValueError(
            f"Excel file {source_name} must contain a column headed "
            f"'{header_name}'."
        )
    return feedback
