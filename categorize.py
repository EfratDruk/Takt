import json
import time
from google import genai
from google.genai.errors import ServerError
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def categorize_issues(refined_issues_list):
    client = genai.Client()
    prompt = f"""
You are an expert Game Product Manager acting as the bridge between raw player feedback and the development team. 
Your task is to take a list of professionally refined issues and assign each one to STRICTLY ONE of the following defined categories:

Categories:
1. "הדרכה" - Player onboarding, training on controls/keys, identifying items or mines, and first-time learning.
2. "מבוא לשלב" - Pre-level briefing screen, level instructions, objective displays, or map preview before starting.
3. "משחקיות" - In-game mechanics, controls, audio/sound, graphics, physics, and performance (lag, loading times, startup, game saves).
4. "מערכת סיכום" - Post-game stats, score reviews, summary screens, or debriefing systems.
5. "שונות" - General meta-feedback or administrative issues that strictly do not fit the above.

CRITICAL RULES:
- Treat the input as English source content. Translate every issue title and description into clear, natural Hebrew.
- Write the title, description, and category in Hebrew.
- Every issue MUST be assigned exactly one category from the list above.
- Preserve each issue's "count" value from the input without changing it.
- Titles must describe the reported problem, not give instructions or propose solutions.
- Output MUST be a valid JSON object with the exact structure below.

Output Format:
{{
  "categorized_issues": [
    {{
      "title": "כותרת קצרה שמתארת את הבעיה",
      "description": "תיאור ברור וענייני של הבעיה",
      "category": "משחקיות",
      "count": 3
    }}
  ]
}}

Input Deduplicated Issues:
{json.dumps(refined_issues_list, ensure_ascii=False)}
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            break
        except ServerError as error:
            if error.code != 503 or attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))

    result_dict = json.loads(response.text)
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