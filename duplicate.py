import json
import time
from google import genai
from google.genai.errors import ServerError
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def deduplicate_issues(refined_issues_list):
    client = genai.Client()
    prompt = """
You are an expert Game Product Manager. 
Your task is to review a list of professionally refined product issues, group identical or very similar issues, and merge them.

CRITICAL RULES:
- Merge issues that describe the exact same bug, missing feature, or feedback point, even if phrased differently by players.
- For each merged issue, create a single clean title and description, and add a "count" field representing how many raw feedback items were merged into this single issue.
- Keep unique issues as they are with a count of 1.
- Write all output text in English.
- Titles must describe the reported problem, not give instructions or propose solutions.
- Output MUST be a valid JSON object with the exact structure below.

Output Format:
{
  "deduplicated_issues": [
    {
      "title": "Short title describing the problem",
      "description": "Clear, comprehensive description combining the reports",
      "count": 3
    }
  ]
}

Input Professionally Refined Issues:
""" + json.dumps(
        refined_issues_list, ensure_ascii=False
    )

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
    return result_dict.get("deduplicated_issues", [])


if __name__ == "__main__":
    result = deduplicate_issues(sample_categorized)
    print(json.dumps(result, indent=2, ensure_ascii=False))