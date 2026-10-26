import json
import ollama


def categorize_issues(refined_issues_list):
    prompt = f"""
You are an expert Game Product Manager acting as the bridge between raw player feedback and the development team. 
Your task is to take a list of professionally refined issues and assign each one to STRICTLY ONE of the following defined categories:

Categories:
1. "Tutorial" - Introductory training, tutorial steps, onboarding, or first-time user experience.
2. "LevelIntro" - Pre-level briefing screen, level instructions, objective displays, or stage setup.
3. "Gameplay" - In-game mechanics, controls, audio/sound, graphics, physics, and performance (lag, loading times, startup).
4. "DebriefSystem" - Post-game stats, score reviews, summary screens, or debriefing systems.
5. "Misc" - General meta-feedback or administrative issues that strictly do not fit the above.

CRITICAL RULES:
- Write all outputs in English.
- Every issue MUST be assigned exactly one category from the list above.
- Output MUST be a valid JSON object with the exact structure below.

Output Format:
{{
  "categorized_issues": [
    {{
      "title": "Short Professional Title",
      "description": "Clean and objective description",
      "category": "Gameplay" // Must be one of: ["Tutorial", "LevelIntro", "Gameplay", "DebriefSystem", "Misc"]
    }}
  ]
}}

Input Refined Issues:
{json.dumps(refined_issues_list, ensure_ascii=False)}
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}],
        format="json",
        think=False,
        options={"temperature": 0},
    )

    result_dict = json.loads(response.message.content)
    return result_dict.get("categorized_issues", [])


if __name__ == "__main__":
    # סימולציה של מה שקיבלנו משלב 2 (לצורך בדיקה עצמאית)
    sample_refined = [
        {
            "title": "Slow Game Startup",
            "description": (
                "The game takes an excessively long time to boot up."
            ),
        },
        {
            "title": "Unclear Feedback Guidelines",
            "description": "The feedback instructions provided are confusing.",
        },
    ]

    result = categorize_issues(sample_refined)
    print(json.dumps(result, indent=2, ensure_ascii=False))