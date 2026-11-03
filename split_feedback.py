import json
import time
from google import genai
from google.genai.errors import ServerError
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def split_from_db(raw_feedback_list):
  client = genai.Client()
  prompt = f"""
You are Takt's Issue Atomizer. 
Your job is to take a dynamic list of raw feedback comments from a database and break down EVERY comment into individual, single-issue statements. 

Some comments might contain 1 issue, some might contain multiple issues. Break them all down so the output is a clean, expanded list where every item is strictly ONE independent issue.

CRITICAL RULES:
- Write all outputs in English.
- Do NOT categorize yet. Do NOT invent technical causes.
- IF A COMMENT CONTAINS MULTIPLE ISSUES (e.g., a bug/save issue AND missing instructions), YOU MUST SPLIT THEM INTO SEPARATE ITEMS.
- Output MUST be a valid JSON object containing a flat list of strings under the key "issues".

EXAMPLES:

Input: ["Not all scenarios were saved at the end and were deleted, more clear instructions are needed."]
Output: {{
  "issues": [
    "Not all scenarios were saved at the end and were deleted",
    "More clear instructions are needed"
  ]
}}

Input: ["The game lagged during the tutorial and I couldn't skip the movie"]
Output: {{
  "issues": [
    "The game lagged during the tutorial",
    "Unable to skip the cinematic movie"
  ]
}}

Raw Feedback from DB:
{json.dumps(raw_feedback_list, ensure_ascii=False)}
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
  return result_dict.get("issues", [])