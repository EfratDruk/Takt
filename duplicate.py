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
issues, and write each resulting issue in clear, objective English.

CRITICAL RULES:
- Merge issues that describe the exact same bug, missing feature, or feedback point, even if phrased differently by players.
- For each merged issue, create a single clean title and description, and add a "count" field representing how many raw feedback items were merged into this single issue.
- Keep unique issues as they are with a count of 1.
- Do not categorize or translate issues; categorization and translation happen in a later step.
- Preserve the meaning and details of the input without inventing technical causes.
- Titles must describe the reported problem, not give instructions or propose solutions.
- Do not invent technical causes or details not present in the input.
- Output MUST be a valid JSON object with the exact structure below.

Output Format:
{
  "issues": [
    {
      "title": "Short title describing the problem",
      "description": "Clear, objective description of the issue",
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