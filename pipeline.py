from categorize import categorize_issues
from categories import DEFAULT_CATEGORIES, validate_categories
from duplicate import deduplicate_issues
from professionality import refine_issues
from split_feedback import split_from_db


BATCH_SIZE = 20


def process_feedback(feedback, progress_callback=None, categories=None):
    if not feedback:
        raise ValueError("No feedback comments were provided.")
    if categories is None:
        categories = DEFAULT_CATEGORIES
    categories = validate_categories(categories)

    def report_progress(message):
        if progress_callback is not None:
            progress_callback(message)

    report_progress("שלב 1 מתוך 4: פיצול המשובים לנושאים")
    atomized_issues = []
    for start in range(0, len(feedback), BATCH_SIZE):
        feedback_batch = feedback[start:start + BATCH_SIZE]
        atomized_issues.extend(split_from_db(feedback_batch))

    report_progress("שלב 2 מתוך 4: ניסוח מקצועי באנגלית")
    refined_issues = []
    for start in range(0, len(atomized_issues), BATCH_SIZE):
        issues_batch = atomized_issues[start:start + BATCH_SIZE]
        refined_issues.extend(refine_issues(issues_batch))

    if not refined_issues:
        raise ValueError("The splitting stage returned no issues to process.")

    report_progress("שלב 3 מתוך 4: איחוד נושאים כפולים")
    deduplicated_issues = deduplicate_issues(refined_issues)

    report_progress("שלב 4 מתוך 4: תרגום לעברית וסיווג")
    final_issues = categorize_issues(deduplicated_issues, categories=categories)
    report_progress("העיבוד הסתיים בהצלחה")
    return final_issues
