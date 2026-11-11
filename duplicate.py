import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from gemini_api import generate_content_with_retry

load_dotenv()

def deduplicate_issues(refined_issues_list):
    client = genai.Client()
    prompt = """
You are an expert Game Product Manager.
Review the professionally refined product issues, merge identical or very similar
issues, categorize each resulting issue, and translate its title and description
into clear, natural Hebrew.

CRITICAL RULES:
- Merge issues that describe the exact same bug, missing feature, or feedback point, even if phrased differently by players.
- For each merged issue, create a single clean title and description, and add a "count" field representing how many raw feedback items were merged into this single issue.
- Keep unique issues as they are with a count of 1.
- Assign exactly one category to each issue:
  - "הדרכה": Player onboarding, training on controls/keys, identifying items or mines, and first-time learning.
  - "מבוא לשלב": Pre-level briefing screen, level instructions, objective displays, or map preview before starting.
  - "משחקיות": In-game mechanics, controls, audio/sound, graphics, physics, and performance (lag, loading times, startup, game saves).
  - "מערכת סיכום": Post-game stats, score reviews, summary screens, or debriefing systems.
  - "שונות": General meta-feedback or administrative issues that do not fit the above.
- Write the title, description, and category in Hebrew.
- Titles must describe the reported problem, not give instructions or propose solutions.
- Do not invent technical causes or details not present in the input.
- Output MUST be a valid JSON object with the exact structure below.

Output Format:
{
  "issues": [
    {
      "title": "כותרת קצרה שמתארת את הבעיה",
      "description": "תיאור ברור ומקיף של הבעיה",
      "category": "משחקיות",
      "count": 3
    }
  ]
}

Input Professionally Refined Issues in English:
""" + json.dumps(
        refined_issues_list, ensure_ascii=False
    )

    response = generate_content_with_retry(
        client,
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    result_dict = json.loads(response.text)
    return result_dict.get("issues", [])


if __name__ == "__main__":
    result = deduplicate_issues(sample_categorized)
    print(json.dumps(result, indent=2, ensure_ascii=False))