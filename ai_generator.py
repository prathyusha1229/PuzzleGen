import json
import anthropic

client = anthropic.Anthropic()


def generate_themed_words(theme: str) -> dict:
    prompt = f"""You are an expert crossword puzzle creator. Generate a themed word list for a crossword puzzle on the topic: "{theme}"

Requirements:
- Generate exactly 18 words related to the theme
- Words must be 4-9 letters long, ALL UPPERCASE, no spaces, no hyphens, no apostrophes, no numbers
- Include varied lengths: at least 5 words of 4-5 letters, at least 7 words of 6-7 letters, at least 4 words of 8-9 letters
- Prefer words with common letters (E, A, R, I, O, N, S, T) so they can cross each other easily in the grid
- Avoid words with too many repeated letters (e.g. "MISSISSIPPI") or unusual letter combinations
- Each word needs a fascinating clue (1-2 sentences) that teaches an interesting fact — make it feel like fun trivia, not a dictionary definition
- Clues must NOT contain the answer word or obvious derivatives

Return ONLY valid JSON — no markdown, no explanation, just the raw JSON object:
{{
  "theme_name": "Creative, evocative title for this puzzle (max 40 chars)",
  "theme_tagline": "Compelling one-line description (max 60 chars)",
  "words": [
    {{"word": "EXAMPLE", "clue": "Fascinating fact related to {theme}"}},
    {{"word": "ANOTHER", "clue": "Another interesting fact"}}
  ]
}}"""

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the text block from the response
    text = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None,
    )

    if not text:
        raise ValueError("No text content in Claude response")

    # Strip accidental markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    data = json.loads(text)

    # Validate and clean words
    cleaned = []
    seen = set()
    for entry in data.get("words", []):
        word = str(entry.get("word", "")).upper().strip()
        clue = str(entry.get("clue", "")).strip()
        if (
            4 <= len(word) <= 9
            and word.isalpha()
            and word not in seen
            and clue
        ):
            cleaned.append({"word": word, "clue": clue})
            seen.add(word)

    if len(cleaned) < 8:
        raise ValueError(f"Claude only returned {len(cleaned)} valid words — too few to build a puzzle")

    data["words"] = cleaned
    return data
