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
