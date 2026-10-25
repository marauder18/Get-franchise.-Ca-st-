import os


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        print("API key loaded successfully!")
    else:
        print("API key not found")


if __name__ == "__main__":
    main()
