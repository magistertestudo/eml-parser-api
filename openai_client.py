import json
import os

from openai import OpenAI


def get_client():

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("Variabile OPENAI_API_KEY non configurata.")

    return OpenAI(api_key=api_key)


def ask_gpt(system_prompt: str, user_prompt: str) -> dict:

    client = get_client()

    response = client.responses.create(
        model="gpt-5.5",
        input=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    text = response.output_text.strip()

    return json.loads(text)