from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from anthropic import AsyncAnthropic
import os
from google import genai
from google.genai import types
from openai import AsyncOpenAI
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

client_anthropic = AsyncAnthropic()
client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
client_openai = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  # added OpenAI client initialization

app = FastAPI()

with open("prompt.txt", "r") as f:
    system_prompt = f.read().strip()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("static/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

async def parse_and_send(websocket, text_stream):
    accumulated_text = ""
    path_count = 0
    async for chunk in text_stream:
        # Extract text from different model response formats
        chunk_text = (chunk.choices[0].delta.content if hasattr(chunk, 'choices')
                 else chunk.text if hasattr(chunk, 'text') 
                 else chunk)
        accumulated_text += chunk_text or ""
        while "<path" in accumulated_text and "/>" in accumulated_text:
            start_idx = accumulated_text.find("<path")
            end_idx = accumulated_text.find("/>", start_idx) + 2
            path_element = accumulated_text[start_idx:end_idx]
            accumulated_text = accumulated_text[end_idx:]
            await websocket.send_text(path_element)
            logger.info(f"Sent path: {path_element}")
            path_count += 1
    return path_count


async def send_error(websocket: WebSocket, message: str) -> None:
    """Send a JSON formatted error message to the WebSocket client."""
    await websocket.send_json({"error": message})

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    model: str = Query(default="claude")
):
    logger.info("New WebSocket connection request received")
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    try:
        while True:
            user_input = await websocket.receive_text()
            logger.info(f"Received user input: {user_input}")
            
            if model.lower() == "gemini":
                stream = await client_gemini.aio.models.generate_content_stream(
                    model="gemini-2.0-pro-exp-02-05",
                    contents=[user_input],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=1024
                    )
                )
                path_count = await parse_and_send(websocket, stream)
            elif model.lower() == "openai":
                response = await client_openai.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": [
                                {
                                    "type": "text",
                                    "text": system_prompt
                                }
                            ]
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_input
                                }
                            ]
                        }
                    ],
                    model="o3-mini",
                    reasoning_effort="low",
                    stream=True
                )
                path_count = await parse_and_send(websocket, response)
            else:
                async with client_anthropic.messages.stream(
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_input}],
                    model="claude-3-7-sonnet-20250219",
                ) as stream:
                    path_count = await parse_and_send(websocket, stream.text_stream)
                    
            logger.info(f"Stream completed. Total paths sent: {path_count}")
            await websocket.close()
            break
                
    except WebSocketDisconnect:
        logger.info("Client disconnected unexpectedly")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        await send_error(websocket, str(e))
        await websocket.close()
    finally:
        logger.info("WebSocket connection closed")

@app.get('/favicon.ico')
def serve_favicon():
    return '', 204

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8086, reload=True)
