import json
import re
import anthropic

client = anthropic.Anthropic()


def _extract_json(text: str) -> str:
    """Pull the first complete {...} block out of Claude's response."""
    text = text.strip()

    # Strip markdown fences
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:]
            if part.strip().startswith("{"):
                text = part.strip()
                break

    # Find outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def generate_themed_words(theme: str) -> dict:
    prompt = f"""You are an expert crossword puzzle creator. Generate a themed word list for a crossword puzzle on the topic: "{theme}"

Requirements:
- Generate exactly 15 words related to the theme
- Words must be 4-9 letters long, ALL UPPERCASE, no spaces, no hyphens, no apostrophes, no numbers
- Include varied lengths: at least 4 short words (4-5 letters) and at least 4 long words (7-9 letters)
- Prefer words with common letters (E, A, R, I, O, N, S, T) so words can intersect in the grid
- Each word gets a short, engaging trivia clue (one sentence max)
- Clues must NOT contain the answer word

Return ONLY a raw JSON object — no markdown fences, no explanation:
{{
  "theme_name": "Title for this puzzle (max 40 chars)",
  "theme_tagline": "One-line description (max 60 chars)",
  "words": [
    {{"word": "EXAMPLE", "clue": "One sentence of trivia."}},
    {{"word": "ANOTHER", "clue": "Another fact."}}
  ]
}}"""

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None,
    )

    if not text:
        raise ValueError("No text content in Claude response")

    raw = _extract_json(text)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\n\nRaw text (first 400 chars):\n{text[:400]}")

    # Validate and clean words
    cleaned = []
    seen: set[str] = set()
    for entry in data.get("words", []):
        word = str(entry.get("word", "")).upper().strip()
        clue = str(entry.get("clue", "")).strip()
        if 4 <= len(word) <= 9 and word.isalpha() and word not in seen and clue:
            cleaned.append({"word": word, "clue": clue})
            seen.add(word)

    if len(cleaned) < 6:
        raise ValueError(
            f"Only {len(cleaned)} valid words extracted — try a more specific theme."
        )

    data["words"] = cleaned
    return data
