import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from gemini_api import generate_content_with_retry

load_dotenv()

def split_from_db(raw_feedback_list):
  client = genai.Client()
  prompt = f"""
You are Takt's feedback analyst.
For every raw feedback comment, identify each distinct issue, split multi-issue
comments into separate issues, and write each issue as a professional title
and clear description in English.

CRITICAL RULES:
- Process every input comment and do not omit any reported issue.
- Each output item must describe exactly one independent issue.
- Titles must briefly describe the reported problem, not give commands or solutions.
- Descriptions must be clear and professional without inventing technical causes.
- Do not categorize yet.
- If an input item is an object, its raw comment is in the "comment" field.
- Output MUST be a valid JSON object with objects under the key "issues".

EXAMPLES:

Input: ["Not all scenarios were saved at the end and were deleted, more clear instructions are needed."]
Output: {{
  "issues": [
    {{
      "title": "Game scenarios are not saved",
      "description": "Scenarios are missing after the session ends."
    }},
    {{
      "title": "Instructions are unclear",
      "description": "The instructions need to be clearer."
    }}
  ]
}}

Input: ["The game lagged during the tutorial and I couldn't skip the movie"]
Output: {{
  "issues": [
    {{
      "title": "Lag during the tutorial",
      "description": "The game lags while the tutorial is running."
    }},
    {{
      "title": "The cinematic cannot be skipped",
      "description": "The player cannot skip the cinematic."
    }}
  ]
}}

Output Format:
{{
  "issues": [
    {{
      "title": "Short title describing the problem",
      "description": "Clear, objective description of the problem"
    }}
  ]
}}

Raw Feedback:
{json.dumps(raw_feedback_list, ensure_ascii=False)}
"""
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