
import sqlite3
from pathlib import Path


def load_feedback_from_folder(folder_path):
    folder = Path(folder_path)

    if not folder.is_dir():
        raise NotADirectoryError(
            f"Folder does not exist: {folder}"
        )

    database_files = [
        path
        for path in folder.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}
    ]

    all_feedback = []

    for database_file in sorted(database_files):
        try:
            database_uri = (
                database_file.resolve().as_uri() + "?mode=ro"
            )

            with sqlite3.connect(database_uri, uri=True) as connection:
                cursor = connection.cursor()

                cursor.execute("""
                    SELECT Comments
                    FROM TrainingFeedback
                    WHERE Comments IS NOT NULL
                      AND TRIM(Comments) != '';
                """)

                rows = cursor.fetchall()

                for row in rows:
                    all_feedback.append({
                        "source_file": database_file.name,
                        "comment": row[0]
                    })

        except sqlite3.Error as error:
            print(
                f"Could not process {database_file.name}: {error}"
            )

    return all_feedback
