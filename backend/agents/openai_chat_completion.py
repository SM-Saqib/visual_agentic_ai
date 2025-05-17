from openai import OpenAI

import os

from dotenv import load_dotenv

load_dotenv()


def deephermes_free(role: str, content: str) -> str:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    site_url = os.getenv("SITE_URL")
    site_name = os.getenv("SITE_NAME")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
    )

    completion = client.chat.completions.create(
        # extra_headers={
        #     "HTTP-Referer": site_url,  # Optional. Site URL for rankings on openrouter.ai.
        #     "X-Title": site_name,  # Optional. Site title for rankings on openrouter.ai.
        # },
        extra_body={},
        model="nousresearch/deephermes-3-mistral-24b-preview:free",
        messages=[
            {
                "role": role,
                "content": content,
            }
        ],
    )
    return completion.choices[0].message.content


def main():
    print("Welcome to DeepHermes chatbot!")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() == "quit":
                break
            response = deephermes_free("user", user_input)
            print(f"DeepHermes: {response}")
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
