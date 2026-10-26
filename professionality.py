import json
import ollama


def refine_issues(single_issues_list):
    prompt = f"""
"You are an expert Game Product Manager acting as the bridge between raw player feedback and the development team. Your goal is to translate user complaints into precise, actionable technical issues."

Your task is to take a list of raw individual feedback issues and translate/reframe each one into a clean, professional issue format with a clear Description.

CRITICAL RULES:
- Write all outputs in English.
- Titles must be short, action-oriented, and professional.
- Descriptions must clearly describe the issue without inventing technical causes or bugs.
- Output MUST be a valid JSON object with the exact structure below.

Output Format:
{{
  "refined_issues": [
    {{
      "title": "Short Professional Title",
      "description": "Clean and objective description of the issue"
    }}
  ]
}}

Input Issues:
{json.dumps(single_issues_list, ensure_ascii=False)}
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}],
        format="json",
        think=False,
        options={"temperature": 0},
    )

    result_dict = json.loads(response.message.content)
    return result_dict.get("refined_issues", [])


if __name__ == "__main__":
    sample_atomized_issues = [
        "It takes too long for the game to start",
        "The menu lags",
        "The loading screen is very slow",
        "The sound is too loud",
        "The feedback plan isn't very clear.",
    ]

    refined_result = refine_issues(sample_atomized_issues)

    print("רשימת הבעיות המנוסחות מקצועית:")
    print(json.dumps(refined_result, indent=2, ensure_ascii=False))