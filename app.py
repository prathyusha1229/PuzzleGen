import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from ai_generator import generate_themed_words
from solver import CrosswordSolver

app = Flask(__name__)
CORS(app)


@app.route("/api/generate", methods=["POST"])
def generate_puzzle():
    body = request.get_json(silent=True) or {}
    theme = str(body.get("theme", "")).strip()

    if not theme:
        return jsonify({"error": "Theme is required"}), 400
    if len(theme) > 120:
        return jsonify({"error": "Theme must be under 120 characters"}), 400

    try:
        # Step 1 — Claude generates themed words + clues
        ai_data = generate_themed_words(theme)
        words = ai_data["words"]

        # Step 2 — CSP solver places words in a valid crossword grid
        solver = CrosswordSolver()
        puzzle = solver.generate(words, target=10)

        if puzzle is None or len(puzzle["placements"]) < 5:
            # Retry with a lower target
            solver2 = CrosswordSolver()
            puzzle = solver2.generate(words, target=6)

        if puzzle is None or len(puzzle["placements"]) < 4:
            return (
                jsonify(
                    {
                        "error": (
                            "Could not fit enough words into the grid. "
                            "Try a different theme or more specific topic."
                        )
                    }
                ),
                500,
            )

        return jsonify(
            {
                "theme_name": ai_data.get("theme_name", theme),
                "theme_tagline": ai_data.get("theme_tagline", ""),
                "puzzle": puzzle,
            }
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port, debug=True)
