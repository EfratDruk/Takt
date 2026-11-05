
import sqlite3
from contextlib import closing
from pathlib import Path

from excel_feedback import load_feedback_from_excel
from sqlite_feedback import read_feedback_column


def load_feedback_from_folder(
    folder_path,
    excel_header="הערות",
    sqlite_column="Comments",
):
    folder = Path(folder_path)

    if not folder.is_dir():
        raise NotADirectoryError(
            f"Folder does not exist: {folder}"
        )

    database_files = [
        path
        for path in folder.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".xlsx", ".xlsm"}
    ]

    all_feedback = []

    for database_file in sorted(database_files):
        if database_file.suffix.lower() in {".xlsx", ".xlsm"}:
            try:
                all_feedback.extend(
                    load_feedback_from_excel(
                        database_file,
                        database_file.name,
                        header_name=excel_header,
                    )
                )
            except ValueError as error:
                print(f"Could not process {database_file.name}: {error}")
            continue

        try:
            database_uri = (
                database_file.resolve().as_uri() + "?mode=ro"
            )

            with closing(sqlite3.connect(database_uri, uri=True)) as connection:
                rows = read_feedback_column(connection, sqlite_column)

                for row in rows:
                    all_feedback.append({
                        "source_file": database_file.name,
                        "comment": str(row[0]).strip(),
                    })

        except (sqlite3.Error, ValueError) as error:
            print(
                f"Could not process {database_file.name}: {error}"
            )

    return all_feedback
