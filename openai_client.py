import json
import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)


def ask_gpt(system_prompt: str, user_prompt: str) -> dict:

    response = client.responses.create(
        model="gpt-5.5",
        temperature=0,
        text={
            "format": {
                "type": "json_object"
            }
        },
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_prompt
                    }
                ]
            }
        ]
    )

    text = response.output_text.strip()

    try:
        return json.loads(text)

    except Exception as e:

        raise RuntimeError(
            f"GPT non ha restituito un JSON valido.\n\n{text}"
        ) from e
