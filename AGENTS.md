# Project Layout Instructions

This repository contains a small FastAPI application for generating and animating SVG drawings with the help of AI models. Below is an overview of the main files and directories:

```
.
├── app.py            # FastAPI backend with WebSocket endpoints
├── svg_utils.py      # Utility for parsing streaming SVG paths
├── model_streamer.py # Class-based helpers for AI streaming
├── static/           # Frontend assets
│   └── index.html    # Client side HTML/JS/CSS
├── prompt.txt        # System prompt sent to the AI models
├── requirements.txt  # Python dependencies
├── test_claude.py    # Example script for interacting with Claude API
├── test_gemini.py    # Example script for interacting with Gemini API
├── README.md         # Project description and setup instructions
└── AGENTS.md         # (this file) repository layout instructions for future agents
```

Other assets like `animation.gif` and `screenshot.png` show the app in action. The `LICENSE` file contains the MIT license.

If adding new code or files, please keep this structure in mind and document any major additions in this file.
