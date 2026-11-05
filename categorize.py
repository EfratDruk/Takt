import json
import time
from google import genai
from google.genai.errors import ServerError
from google.genai import types
from dotenv import load_dotenv

from categories import DEFAULT_CATEGORIES, validate_categories

load_dotenv()


def categorize_issues(refined_issues_list, categories=None):
    if categories is None:
        categories = DEFAULT_CATEGORIES
    categories = validate_categories(categories)
    client = genai.Client()
    prompt = f"""
You are an expert Game Product Manager acting as the bridge between raw player feedback and the development team. 
Your task is to assign each issue to exactly one category from the user-provided list below.

CRITICAL RULES:
- Treat the input as English source content. Translate every issue title and description into clear, natural Hebrew.
- Write the title, description, and category in Hebrew.
- Use exactly one category name from the provided list for each issue. Do not invent, rename, or translate category names.
- Use each category's Hebrew description to determine the best match.
- Preserve each issue's "count" value from the input without changing it.
- Titles must describe the reported problem, not give instructions or propose solutions.
- Output MUST be a valid JSON object with the exact structure below.

User-provided categories in Hebrew:
{json.dumps(categories, ensure_ascii=False)}

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