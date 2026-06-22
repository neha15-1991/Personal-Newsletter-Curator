import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ---------------------------------------------------------
# LOAD .env FILE
# ---------------------------------------------------------
# summariser.py is inside Backend folder.
# .env is inside the main capstone-project folder.
#
# Path(__file__).resolve().parent        -> Backend folder
# Path(__file__).resolve().parent.parent -> capstone-project folder

ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(ENV_FILE_PATH)


# ---------------------------------------------------------
# GEMINI CLIENT
# ---------------------------------------------------------
def get_gemini_client():
    """
    Creates and returns the Gemini client.

    The API key is loaded from the root .env file.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from the .env file"
        )

    client = genai.Client(api_key=api_key)

    return client


# ---------------------------------------------------------
# STORY SUMMARISER
# ---------------------------------------------------------
def summarise_story(
    title: str,
    content: str | None,
    user_interest_text: str | None,
    topics: list[str]
) -> dict:
    """
    Summarises one story using Gemini.

    This function is called from digest_builder.py.

    It returns:
    1. summary -> exactly two sentences
    2. why_it_matters -> exactly one personalised sentence
    """

    safe_content = content or title
    limited_content = safe_content[:4000]
    topic_text = ", ".join(topics) if topics else "No specific topic tags"
    safe_interest_text = user_interest_text or ""

    prompt = f"""
You are building a personalised newsletter digest.

Story title:
{title}

Story content:
{limited_content}

User's interest description:
{safe_interest_text}

User's topic tags:
{topic_text}

Your task:
1. Write a clear summary in exactly two sentences.
2. Write exactly one sentence explaining why this story matters to this user.

Return only a valid JSON object in this exact format:

{{
    "summary": "Two sentence summary here.",
    "why_it_matters": "One personalised sentence here."
}}
"""

    client = get_gemini_client()

    model_name = os.getenv(
        "GEMINI_MODEL_NAME",
        "gemini-2.5-flash"
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a personal newsletter curator. "
                "Summarise stories accurately and explain why each story "
                "matters to the user. Return only valid JSON."
            ),
            response_mime_type="application/json",
            temperature=0.2
        )
    )

    response_text = response.text

    if not response_text:
        raise ValueError(
            "Gemini returned an empty response"
        )

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError:
        raise ValueError(f"Gemini returned invalid JSON: {response_text}")

    summary = result.get("summary", "").strip()

    why_it_matters = result.get("why_it_matters","").strip()

    if not summary or not why_it_matters:
        raise ValueError("Gemini response is missing summary or why_it_matters")

    return {
        "summary": summary,
        "why_it_matters": why_it_matters
    }


# ---------------------------------------------------------
# QUICK TEST
# ---------------------------------------------------------
# This runs only when we execute python summariser.py
# It will NOT run when FastAPI imports this file.

if __name__ == "__main__":
    test_result = summarise_story(
        title="Python 3.13 improves performance",
        content=(
            "Python 3.13 introduces performance improvements, "
            "developer tools, and updates to the standard library."
        ),
        user_interest_text="I am interested in Python and AI projects.",
        topics=["Python", "AI", "Software Development"]
    )

    print(test_result)