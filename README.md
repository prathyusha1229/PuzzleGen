# PuzzleGen Backend

A Flask backend for generating themed crossword puzzles. It uses Anthropic Claude to create puzzle words and clues, then solves crossword placement using a CSP-style solver.

## Features

- `POST /api/generate` to generate a crossword puzzle from a theme
- `GET /api/health` to verify the service is running
- Uses `.env` for secret configuration
- Ignores virtualenv files, Python bytecode, and local environment files

## Requirements

- Python 3.12
- pip
- An Anthropic API key

## Setup

1. Create a Python virtual environment:

```powershell
python -m venv venv
```

2. Activate it:

```powershell
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file from the example:

```powershell
copy .env.example .env
```

5. Add your Anthropic API key to `.env`:

```text
ANTHROPIC_API_KEY=sk-your-key-here
```

## Run

```powershell
python app.py
```

The backend starts on port `5001` by default.

## API

### Generate Puzzle

- Endpoint: `POST /api/generate`
- Payload:

```json
{
  "theme": "ocean life"
}
```

- Response:

```json
{
  "theme_name": "...",
  "theme_tagline": "...",
  "puzzle": {
    "placements": [...],
    "grid": [...]
  }
}
```

### Health

- Endpoint: `GET /api/health`
- Response:

```json
{
  "status": "ok"
}
```

## Notes

- Keep `.env` secret and never commit it to GitHub.
- Local files such as `venv/`, `__pycache__/`, and `.env` are already ignored by `.gitignore`.
