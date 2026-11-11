from categorize import categorize_issues
from categories import DEFAULT_CATEGORIES, validate_categories
from duplicate import deduplicate_issues
from split_feedback import split_from_db


BATCH_SIZE = 20


def process_feedback(feedback, progress_callback=None, categories=None):
    if not feedback:
        raise ValueError("No feedback comments were provided.")
    if categories is None:
        categories = DEFAULT_CATEGORIES
    categories = validate_categories(categories)

    resume_state = resume_state or {}

    def report_progress(message):
        if progress_callback is not None:
            progress_callback(message)

    def save_checkpoint(state):
        if checkpoint_callback is not None:
            checkpoint_callback(state)

    if resume_state.get("complete"):
        return resume_state["final_issues"]

    refined_issues = list(resume_state.get("refined_issues", []))
    batch_count = (len(feedback) + BATCH_SIZE - 1) // BATCH_SIZE
    completed_batches = resume_state.get("completed_batches", 0)

    if not resume_state.get("ready_for_final"):
        report_progress(
            f"שלב 1 מתוך 2: פיצול ועריכה מקצועית באנגלית "
            f"(אצווה {completed_batches + 1} מתוך {batch_count})"
        )
        for batch_index in range(completed_batches, batch_count):
            start = batch_index * BATCH_SIZE
            feedback_batch = feedback[start:start + BATCH_SIZE]
            refined_issues.extend(split_from_db(feedback_batch))
            save_checkpoint({
                "completed_batches": batch_index + 1,
                "refined_issues": refined_issues,
            })
            if batch_index + 1 < batch_count:
                report_progress(
                    f"שלב 1 מתוך 2: פיצול ועריכה מקצועית באנגלית "
                    f"(אצווה {batch_index + 2} מתוך {batch_count})"
                )

    if not refined_issues:
        raise ValueError("Feedback processing returned no issues.")

    report_progress("שלב 4 מתוך 4: תרגום לעברית וסיווג")
    final_issues = categorize_issues(deduplicated_issues, categories=categories)
    report_progress("העיבוד הסתיים בהצלחה")
    return final_issues
