from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from anthropic import AsyncAnthropic

from dotenv import load_dotenv
load_dotenv()

client = AsyncAnthropic()

app = FastAPI()

with open("prompt.txt", "r") as f:
    system_prompt = f.read().strip()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("static/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("New WebSocket connection request received")
    await websocket.accept()
    print("WebSocket connection accepted")
    try:
        while True:
            user_input = await websocket.receive_text()
            print(f"Received user input: {user_input}")
            
            async with client.messages.stream(
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}],
                model="claude-3-5-sonnet-20241022",
            ) as stream:
                accumulated_text = ""
                path_count = 0
                async for chunk in stream.text_stream:
                    accumulated_text += chunk
                    # Extract <path /> elements
                    while "<path" in accumulated_text and "/>" in accumulated_text:
                        start_idx = accumulated_text.find("<path")
                        end_idx = accumulated_text.find("/>", start_idx) + 2
                        path_element = accumulated_text[start_idx:end_idx]
                        accumulated_text = accumulated_text[end_idx:]
                        # Send each <path /> element back to the client
                        await websocket.send_text(path_element)
                        path_count += 1
                        print(f"Sent path element {path_count} to client: {path_element}")
                
                print(f"Stream completed. Total paths sent: {path_count}")
                await websocket.close()
                break
                
    except WebSocketDisconnect:
        print("Client disconnected unexpectedly")
    except Exception as e:
        print(f"Error occurred: {e}")
        try:
            await websocket.close()
        except:
            pass
    finally:
        print("WebSocket connection closed")

@app.get('/favicon.ico')
def serve_favicon():
    return '', 204

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8086, reload=True)
