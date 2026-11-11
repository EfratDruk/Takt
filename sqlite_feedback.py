import sqlite3


TABLE_NAME = "TrainingFeedback"


def read_feedback_column(connection, column_name):
    column_name = str(column_name).strip()
    if not column_name:
        raise ValueError("The SQLite feedback column name cannot be empty.")

    available_columns = {
        row[1].casefold(): row[1]
        for row in connection.execute(
            f'PRAGMA table_info("{TABLE_NAME}")'
        ).fetchall()
    }
    actual_column = available_columns.get(column_name.casefold())
    if actual_column is None:
        raise ValueError(
            f"Table '{TABLE_NAME}' does not contain a column named "
            f"'{column_name}'."
        )

    quoted_column = '"' + actual_column.replace('"', '""') + '"'
    return connection.execute(
        f"""
        SELECT {quoted_column}
        FROM "{TABLE_NAME}"
        WHERE {quoted_column} IS NOT NULL
          AND TRIM({quoted_column}) != '';
        """
    ).fetchall()
