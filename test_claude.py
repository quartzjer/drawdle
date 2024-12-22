import sys
from dotenv import load_dotenv
import argparse
import asyncio
from anthropic import AsyncAnthropic
load_dotenv()

async def main() -> None:
    with open("prompt.txt", "r") as f:
        system_prompt = f.read().strip()

    parser = argparse.ArgumentParser(description='Chat with Claude using a system prompt')
    parser.add_argument('message', help='The message to send to Claude')
    args = parser.parse_args()

    client = AsyncAnthropic()

    try:
        async with client.messages.stream(
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": args.message}
            ],
            model="claude-3-5-sonnet-20241022",
        ) as stream:
            async for text in stream.text_stream:
                print(text, end="", flush=True)
            print()

    except Exception as e:
        print(f"\nError occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
