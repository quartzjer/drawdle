from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# Mount the static directory to serve static files like index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the index.html on the root path
@app.get("/", response_class=HTMLResponse)
async def get():
    with open("static/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

# Example WebSocket endpoint (placeholder for future use)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo the received message (for demonstration)
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8086, reload=True)
