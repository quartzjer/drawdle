import logging
import re

logger = logging.getLogger(__name__)

# Regex to match self-closing SVG path elements
_PATH_RE = re.compile(r"<path[^>]*/>")

async def parse_and_send(websocket, text_stream):
    """Extract <path ... /> elements from a streaming response and send them.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection to send SVG path elements over.
    text_stream : AsyncIterator
        Streaming response from the AI model yielding text chunks.

    Returns
    -------
    int
        Total number of path elements sent.
    """
    accumulated_text = ""
    path_count = 0
    async for chunk in text_stream:
        chunk_text = (
            chunk.choices[0].delta.content if hasattr(chunk, "choices") else
            chunk.text if hasattr(chunk, "text") else
            chunk
        )
        accumulated_text += chunk_text or ""
        while True:
            match = _PATH_RE.search(accumulated_text)
            if not match:
                break
            path_element = match.group(0)
            accumulated_text = accumulated_text[match.end():]
            await websocket.send_text(path_element)
            logger.info(f"Sent path: {path_element}")
            path_count += 1
    return path_count
