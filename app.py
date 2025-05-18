from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging

from model_streamer import ModelStreamer
from svg_utils import parse_and_send
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

with open("prompt.txt", "r") as f:
    system_prompt = f.read().strip()

streamer = ModelStreamer(system_prompt)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("static/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)


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

            stream_fn = streamer.get_streamer(model)
            stream = stream_fn(user_input)
            path_count = await parse_and_send(websocket, stream)
                    
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
