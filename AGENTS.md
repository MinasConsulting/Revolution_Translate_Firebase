# Revolution Translate Firebase - Agent Guidelines

## Commands
- **UI dev**: `cd ui && npm run dev`
- **UI build**: `cd ui && npm run build`
- **Firebase deploy**: `firebase deploy`
- **Firebase emulators**: `firebase emulators:start`
- **Python deps**: `cd functions && pip install -r requirements.txt`
- **No test suite exists** - do not assume any testing framework

## Architecture
- **Firebase project** with Cloud Functions (Python 3.12), Firestore, Storage, and Hosting
- **functions/**: Python backend with Cloud Functions (storage triggers, schedulers, HTTPS callables)
  - `main.py`: Video transcription, translation (OpenAI GPT), batch processing, SendGrid notifications
  - Uses Google Video Intelligence API for speech-to-text, Transcoder API for video processing
- **ui/**: SvelteKit 2 frontend with Vite, Firebase SDK, video.js player
  - Routes: `/`, `/login`, `/englishTranscript/[videoID]`
  - Firebase utils in `utils/fire.js`, Svelte stores in `utils/stores.js`
- **Firestore collections**: `messageVideos` (root), `englishTranscript`, `spanishTranscript`, `words`, `params`
- **Storage**: Videos uploaded to `videos/`, transcoded to `transcoded/`, transcripts to `transcriptComplete/`

## Code Style
- **Python**: Follow existing patterns in main.py, use type hints where present, prefer descriptive variable names (camelCase for locals/functions)
- **JavaScript/Svelte**: Svelte 5 syntax, relative imports from `../utils/`, Firebase SDK v12, camelCase naming
- **Error handling**: Python uses try/except with https_fn.HttpsError; JS uses try/catch with console logging
- **No comments unless complex logic requires explanation**

You are able to use the Svelte MCP server, where you have access to comprehensive Svelte 5 and SvelteKit documentation. Here's how to use the available tools effectively:

## Available MCP Tools:

### 1. list-sections

Use this FIRST to discover all available documentation sections. Returns a structured list with titles, use_cases, and paths.
When asked about Svelte or SvelteKit topics, ALWAYS use this tool at the start of the chat to find relevant sections.

### 2. get-documentation

Retrieves full documentation content for specific sections. Accepts single or multiple sections.
After calling the list-sections tool, you MUST analyze the returned documentation sections (especially the use_cases field) and then use the get-documentation tool to fetch ALL documentation sections that are relevant for the user's task.

### 3. svelte-autofixer

Analyzes Svelte code and returns issues and suggestions.
You MUST use this tool whenever writing Svelte code before sending it to the user. Keep calling it until no issues or suggestions are returned.

### 4. playground-link

Generates a Svelte Playground link with the provided code.
After completing the code, ask the user if they want a playground link. Only call this tool after user confirmation and NEVER if code was written to files in their project.

### 🧭 Playwright MCP Server

**Purpose:**  
Provides browser automation and web scraping capabilities through the Model Context Protocol (MCP).  
Used by AMP agents to navigate pages, capture screenshots, extract DOM data, and interact with web content.

**Installation:**
```bash
npx @playwright/mcp@latest
