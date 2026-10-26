
import ollama


def analyze_feedback(feedback):
    prompt = f"""
You are a QA feedback analyst.
Analyze the provided list of raw feedback comments and transform them into a refined list of unique issues. YOU MUST PROCESS EVERY SINGLE COMMENT PROVIDED. DO NOT SKIP ANY.

Categorization Rules (Choose the best fit):
1. "Tutorial": Introductory training, tutorial steps, or onboarding.
2. "LevelIntro": Pre-level briefing screen, level instructions, or stage setup.
3. "Gameplay": In-game mechanics, controls, audio/sound, graphics, and performance (e.g., lag, long loading times, start delays).
4. "DebriefSystem": Post-game stats, score reviews, or debriefing screen.
5. "Misc": Only for general meta-feedback or items that strictly do not belong to the game experience above.

CRITICAL INSTRUCTIONS:
- Write all outputs in English.
- PROCESS ALL COMMENTS: Ensure every single line in the input feedback is addressed and converted into an issue.
- MERGE DUPLICATES: Group together comments that describe the SAME root issue (e.g., slow start and slow loading).
- SPLIT MULTI-TOPIC: If a comment has two distinct issues, split them.
- NO INVENTED CAUSES: Describe only what was reported.

Output Format:
Return ONLY a valid JSON object with this structure:
{{
  "issues": [
    {{
      "title": "string",
      "description": "string",
      "category": "string"
    }}
  ]
}}

Feedback comments:
{feedback}
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format="json",
        think=False,
        options={"temperature": 0}
    )

    return response.message.content


if __name__ == "__main__":
    sample_feedback = [
        "It takes too long for the game to start.",
        "The loading screen is very slow and the sound is too loud",
        "The feedback plan isn't very clear."
    ]

    result = analyze_feedback(sample_feedback)
    print(result)
