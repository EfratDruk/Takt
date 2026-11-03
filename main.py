import json
from database import load_feedback_from_folder

from export_excel import export_issues_to_excel
from pipeline import process_feedback


if __name__ == "__main__":
    feedback = load_feedback_from_folder("Data/feedbacks")
    print(f"Total comments extracted: {len(feedback)}")

    final_issues = process_feedback(
        feedback,
        progress_callback=lambda message: print(f"\n{message}"),
    )

    print("\n--- Final Categorized Takt Report ---")
    print(json.dumps(final_issues, indent=2, ensure_ascii=False))

    report_path = export_issues_to_excel(final_issues)
    print(f"\nExcel report saved to: {report_path.resolve()}")
