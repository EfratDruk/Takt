import json
import time
from google import genai
from google.genai.errors import ServerError
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def refine_issues(single_issues_list):
    client = genai.Client()
    prompt = f"""
"You are an expert Game Product Manager acting as the bridge between raw player feedback and the development team. Your goal is to translate user complaints into precise, actionable technical issues."

Your task is to take a list of raw individual feedback issues and translate/reframe each one into a clean, professional issue format with a clear description.

CRITICAL RULES:
- Write all output text in English.
- Titles must be short, professional descriptions of the reported problem. Do not write titles as commands or solutions.
- Descriptions must clearly describe the issue without inventing technical causes or bugs.
- Output MUST be a valid JSON object with the exact structure below.

Output Format:
{{
  "refined_issues": [
    {{
      "title": "Short title describing the problem",
      "description": "Clear, objective description of the problem"
    }}
  ]
}}

Input Issues:
{json.dumps(single_issues_list, ensure_ascii=False)}
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
    return result_dict.get("refined_issues", [])


if __name__ == "__main__":
    refined_result = refine_issues(sample_atomized_issues)

    print("רשימת הבעיות המנוסחות מקצועית:")
    print(json.dumps(refined_result, indent=2, ensure_ascii=False))