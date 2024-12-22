import sys
from dotenv import load_dotenv
import argparse
import asyncio
import os
from google import genai
from google.genai import types
load_dotenv()

async def main() -> None:
    with open("prompt.txt", "r") as f:
        system_prompt = f.read().strip()

    parser = argparse.ArgumentParser(description='Chat with Claude using a system prompt')
    parser.add_argument('message', help='The message to send to Claude')
    args = parser.parse_args()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    try:
        async for chunk in client.aio.models.generate_content_stream(
            model="gemini-2.0-flash-exp",
            contents=[types.Part.from_text(args.message)],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024
            )
        ):
            print(chunk.text, end="", flush=True)
        print()

    except Exception as e:
        print(f"\nError occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
