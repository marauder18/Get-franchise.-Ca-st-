import os


def main() -> None:
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is not set.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    response = client.chat.completions.create(
        model="openai/gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": "You are the Research Coordinator AI for GetFranchise. Analyze Subway as a franchise opportunity.",
            }
        ],
    )
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
