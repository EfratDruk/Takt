import json
from database import load_feedback_from_folder

from split_feedback import split_from_db  
from professionality import refine_issues
from categorize import categorize_issues


if __name__ == "__main__":
    feedback = load_feedback_from_folder("Data/feedbacks")
    print(f"Total comments extracted: {len(feedback)}")

    print("\n--- Running Step 1: Splitting issues ---")
    atomized_issues = split_from_db(feedback)
    print(f"Total single issues created: {len(atomized_issues)}")

    # שלב 2: ניסוח מקצועי (כותרות ותיאורים נקיים)
    print("\n--- Running Step 2: Professional Refinement ---")
    refined_issues = refine_issues(atomized_issues)

    # שלב 3: שיוך לקטגוריות (Categorization)
    print("\n--- Running Step 3: Product Manager Categorization ---")
    categorized_issues = categorize_issues(refined_issues)

    # הצגת התוצאה הסופית של כל הצינור
    print("\n--- Final Categorized Takt Report ---")
    print(json.dumps(categorized_issues, indent=2, ensure_ascii=False))


