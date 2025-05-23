import openai
import os

# You may want to set your OpenAI API key as an environment variable or load it securely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# This function will be updated with a custom prompt later
# For now, it just sends the contest detail to the OpenAI API and returns the response

def generate_marketing_content(contest_detail, model="gpt-4o"):
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")
    openai.api_key = OPENAI_API_KEY
    prompt = f"""
Given the following contest detail, generate:
- A catchy marketing title
- A short marketing text
- A creative image prompt for an AI image generator

Contest Detail:
{contest_detail}

---
Return the result as a JSON object with keys: title, text, image_prompt.
"""
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512,
    )
    return response.choices[0].message["content"] 