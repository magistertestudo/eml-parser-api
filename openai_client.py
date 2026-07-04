from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)


def ask_gpt(system_prompt: str, user_prompt: str):

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

    return response.output_text
