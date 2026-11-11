from categorize import categorize_issues
from categories import DEFAULT_CATEGORIES, validate_categories
from duplicate import deduplicate_issues
from professionality import refine_issues
from split_feedback import split_from_db


BATCH_SIZE = 20


def process_feedback(
    feedback,
    progress_callback=None,
    categories=None,
    checkpoint_callback=None,
    resume_state=None,
):
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

    phase = resume_state.get("phase", "split")
    atomized_issues = list(resume_state.get("atomized_issues", []))
    refined_issues = list(resume_state.get("refined_issues", []))

    if phase == "split":
        batch_count = (len(feedback) + BATCH_SIZE - 1) // BATCH_SIZE
        completed_batches = resume_state.get("completed_batches", 0)
        report_progress(
            f"שלב 1 מתוך 4: פיצול המשובים לנושאים "
            f"(אצווה {completed_batches + 1} מתוך {batch_count})"
        )
        for batch_index in range(completed_batches, batch_count):
            start = batch_index * BATCH_SIZE
            feedback_batch = feedback[start:start + BATCH_SIZE]
            atomized_issues.extend(split_from_db(feedback_batch))
            save_checkpoint({
                "phase": "split",
                "completed_batches": batch_index + 1,
                "atomized_issues": atomized_issues,
            })
            if batch_index + 1 < batch_count:
                report_progress(
                    f"שלב 1 מתוך 4: פיצול המשובים לנושאים "
                    f"(אצווה {batch_index + 2} מתוך {batch_count})"
                )

        if not atomized_issues:
            raise ValueError("The splitting stage returned no issues to process.")

        phase = "refine"
        refined_issues = []
        save_checkpoint({
            "phase": phase,
            "completed_batches": 0,
            "atomized_issues": atomized_issues,
            "refined_issues": refined_issues,
        })

    if phase == "refine":
        batch_count = (len(atomized_issues) + BATCH_SIZE - 1) // BATCH_SIZE
        completed_batches = resume_state.get("completed_batches", 0)
        report_progress(
            f"שלב 2 מתוך 4: ניסוח מקצועי באנגלית "
            f"(אצווה {completed_batches + 1} מתוך {batch_count})"
        )
        for batch_index in range(completed_batches, batch_count):
            start = batch_index * BATCH_SIZE
            issue_batch = atomized_issues[start:start + BATCH_SIZE]
            refined_issues.extend(refine_issues(issue_batch))
            save_checkpoint({
                "phase": phase,
                "completed_batches": batch_index + 1,
                "atomized_issues": atomized_issues,
                "refined_issues": refined_issues,
            })
            if batch_index + 1 < batch_count:
                report_progress(
                    f"שלב 2 מתוך 4: ניסוח מקצועי באנגלית "
                    f"(אצווה {batch_index + 2} מתוך {batch_count})"
                )

        if not refined_issues:
            raise ValueError("The refinement stage returned no issues to process.")

        phase = "deduplicate"
        save_checkpoint({
            "phase": phase,
            "atomized_issues": atomized_issues,
            "refined_issues": refined_issues,
        })

    if phase == "deduplicate":
        report_progress("שלב 3 מתוך 4: איחוד נושאים כפולים")
        deduplicated_issues = deduplicate_issues(refined_issues)
        phase = "categorize"
        save_checkpoint({
            "phase": phase,
            "atomized_issues": atomized_issues,
            "refined_issues": refined_issues,
            "deduplicated_issues": deduplicated_issues,
        })
    else:
        deduplicated_issues = resume_state.get("deduplicated_issues", [])

    report_progress("שלב 4 מתוך 4: תרגום לעברית וסיווג")
    final_issues = categorize_issues(deduplicated_issues, categories=categories)
    save_checkpoint({
        "phase": "complete",
        "refined_issues": refined_issues,
        "atomized_issues": atomized_issues,
        "deduplicated_issues": deduplicated_issues,
        "complete": True,
        "final_issues": final_issues,
    })
    report_progress("העיבוד הסתיים בהצלחה")
    return final_issues
