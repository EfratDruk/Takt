import json
import ollama


def split_from_db(raw_feedback_list):
prompt = f"""
You are Takt's Issue Atomizer. 
Your job is to take a dynamic list of raw feedback comments from a database and break down EVERY comment into individual, single-issue statements. 

Some comments might contain 1 issue, some might contain multiple issues. Break them all down so the output is a clean, expanded list where every item is strictly ONE independent issue.

CRITICAL RULES:
- Write all outputs in English.
- Do NOT categorize yet. Do NOT invent technical causes.
- If a single comment contains a bug AND a missing instruction (or any combination of distinct problems), you MUST split them into separate items in the list.
- Output MUST be a valid JSON object containing a flat list of strings under the key "issues".

EXAMPLE:
Input: ["Not all scenarios were saved and they got deleted, plus more clear instructions are needed."]
Output: {{
  "issues": [
    "Not all scenarios were saved at the end and they were deleted",
    "More clear instructions are needed"
  ]
}}

Raw Feedback from DB:
{json.dumps(raw_feedback_list, ensure_ascii=False)}
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}],
        format="json",
        think=False,
        options={"temperature": 0},
    )

   
    result_dict = json.loads(response.message.content)
    return result_dict.get("issues", [])


if __name__ == "__main__":
    db_feedback_sample = [
        "It takes too long for the game to start and the menu lags.",
        "The loading screen is very slow and the sound is too loud",
        "The feedback plan isn't very clear.",
        "Crashes when clicking settings.",
    ]


    flat_issues_list = split_from_db(db_feedback_sample)

    print("רשימת הבעיות הנקייה לשלב הבא:")
    print(json.dumps(flat_issues_list, indent=2, ensure_ascii=False))