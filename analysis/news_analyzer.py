"""
News sentiment & market analysis pipeline using a local Ollama model.

Run:
    python -m analysis.news_analyzer
    python -m analysis.news_analyzer --batch-size 50
    python -m analysis.news_analyzer --all        # process every unanalyzed row
"""

import json
import re
import argparse
import requests
from database.db_utils import fetch_unanalyzed_news, update_news_analysis

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"  # ~4.7GB — fits in 6GB VRAM. Change if using a different model.

NEPSE_SECTORS = [
    "banking", "development bank", "finance", "microfinance", "insurance",
    "hydropower", "manufacturing", "trading", "hotels", "others",
    "investment", "life insurance", "non-life insurance",
]

PROMPT_TEMPLATE = """You are a financial news analyst specializing in Nepal's stock market (NEPSE).
Analyze the following news article and return ONLY a valid JSON object — no explanation, no markdown.

Article title: {title}
Article content: {content}

Return this exact JSON structure:
{{
  "sentiment": "<positive|negative|neutral>",
  "sentiment_score": <float between -1.0 and 1.0>,
  "relevance_score": <float between 0.0 and 1.0, how relevant this is to Nepal's stock market>,
  "impact_level": "<high|medium|low>",
  "market_signal": "<bullish|bearish|neutral>",
  "affected_sectors": <JSON array of NEPSE sectors from this list: {sectors}>,
  "entities": <JSON array of named companies, countries, or people mentioned>,
  "keywords": <JSON array of 5 key financial terms from the article>
}}

Rules:
- sentiment_score: positive = 0.0 to 1.0, negative = -1.0 to 0.0, neutral ≈ 0.0
- relevance_score: 1.0 = directly about Nepal/NEPSE, 0.0 = completely unrelated
- affected_sectors: only include sectors that are genuinely impacted, empty array if none
- Return ONLY the JSON object, nothing else."""


def _call_ollama(prompt: str) -> str | None:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",   # Ollama's JSON mode — forces valid JSON output
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Ollama. Is it running? (ollama serve)")
        return None
    except Exception as e:
        print(f"Ollama error: {e}")
        return None


def _parse_response(raw: str) -> dict | None:
    """Extract and validate JSON from the model response."""
    if not raw:
        return None
    # Strip any accidental markdown fences
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: grab the first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return None

    # Clamp numeric fields to expected ranges
    if "sentiment_score" in data:
        data["sentiment_score"] = max(-1.0, min(1.0, float(data["sentiment_score"])))
    if "relevance_score" in data:
        data["relevance_score"] = max(0.0, min(1.0, float(data["relevance_score"])))

    # Store list fields as JSON strings (they're Text columns in the DB)
    for field in ("affected_sectors", "entities", "keywords"):
        if field in data and isinstance(data[field], list):
            data[field] = json.dumps(data[field])

    return data


def analyze_batch(batch_size: int = 20):
    news_rows = fetch_unanalyzed_news(batch_size)
    if not news_rows:
        print("No unanalyzed news found.")
        return 0

    print(f"Analyzing {len(news_rows)} articles...")
    success = 0

    for row in news_rows:
        # Prefer full content, fall back to description
        content = (row.content or row.description or "").strip()
        if not content:
            print(f"  Skipping id={row.id} — no content (marking as skipped)")
            update_news_analysis(row.id, {"sentiment": "skipped", "sentiment_score": 0.0, "relevance_score": 0.0})
            continue

        prompt = PROMPT_TEMPLATE.format(
            title=row.title or "",
            content=content[:800],  # title + 800 chars is enough for sentiment; keeps VRAM usage low
            sectors=", ".join(NEPSE_SECTORS),
        )

        print(f"  Analyzing: [{row.source}] {row.title[:70] if row.title else '(no title)'}...")
        raw = _call_ollama(prompt)
        analysis = _parse_response(raw)

        if not analysis:
            print(f"    Failed to parse response for id={row.id}")
            continue

        update_news_analysis(row.id, analysis)
        print(f"    sentiment={analysis.get('sentiment')} ({analysis.get('sentiment_score')}) "
              f"impact={analysis.get('impact_level')} signal={analysis.get('market_signal')}")
        success += 1

    print(f"\nDone. {success}/{len(news_rows)} articles analyzed.")
    return success


def analyze_all(batch_size: int = 20):
    """Keep processing batches until no unanalyzed rows remain."""
    total = 0
    while True:
        count = analyze_batch(batch_size)
        total += count
        if count == 0:
            break
    print(f"Total analyzed: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze news sentiment with Ollama")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--all", action="store_true", help="Process all unanalyzed rows")
    args = parser.parse_args()

    if args.all:
        analyze_all(batch_size=args.batch_size)
    else:
        analyze_batch(batch_size=args.batch_size)
