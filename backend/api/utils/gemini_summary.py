from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_summary(landmark, facts):
    prompt = f"""
    Summarize in 3-4 sentences why {landmark} is famous.
    Use the facts below. Be factual and concise.

    Facts:
    {facts}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",  # or another supported model name
        contents=prompt
    )
    return response.text.strip()
