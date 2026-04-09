"""
Social media sentiment & market analysis pipeline.

Analyzes both posts and comments from social_media_posts / social_media_comments
using the same local Ollama model as the news pipeline.

Run:
    python -m analysis.social_media_analyzer
    python -m analysis.social_media_analyzer --target comments
    python -m analysis.social_media_analyzer --all
"""

import json
import re
import argparse
import requests
from database.social_media_utils import (
    fetch_unanalyzed_posts,
    fetch_unanalyzed_comments,
    update_post_analysis,
    update_comment_analysis,
)

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"

NEPSE_SECTORS = [
    "banking", "development bank", "finance", "microfinance", "insurance",
    "hydropower", "manufacturing", "trading", "hotels", "others",
    "investment", "life insurance", "non-life insurance",
]

# Social media posts are often short and informal — the prompt reflects that
PROMPT_TEMPLATE = """You are a financial analyst specializing in Nepal's stock market (NEPSE).
The following is a social media post (or comment) from a Nepali stock market Facebook group.
Analyze it and return ONLY a valid JSON object — no explanation, no markdown.

Content: {text}

Return this exact JSON structure:
{{
  "sentiment": "<positive|negative|neutral>",
  "sentiment_score": <float -1.0 to 1.0>,
  "relevance_score": <float 0.0 to 1.0, how relevant to Nepal stock market>,
  "impact_level": "<high|medium|low>",
  "market_signal": "<bullish|bearish|neutral>",
  "affected_sectors": <JSON array from: {sectors}>,
  "entities": <JSON array of companies, stocks, or people mentioned>,
  "keywords": <JSON array of up to 5 key terms>
}}

Rules:
- sentiment_score: positive = 0.0→1.0, negative = -1.0→0.0
- relevance_score: 1.0 = directly about a NEPSE stock, 0.0 = unrelated
- For informal posts ("NMB ko share kinnu parcha!") still extract intent
- Return ONLY the JSON, nothing else."""


def _call_ollama(prompt: str) -> str | None:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
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
    if not raw:
        return None
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return None

    if "sentiment_score" in data:
        data["sentiment_score"] = max(-1.0, min(1.0, float(data["sentiment_score"])))
    if "relevance_score" in data:
        data["relevance_score"] = max(0.0, min(1.0, float(data["relevance_score"])))

    for field in ("affected_sectors", "entities", "keywords"):
        if field in data and isinstance(data[field], list):
            data[field] = json.dumps(data[field])

    return data


def _analyze_rows(rows, update_fn, label: str) -> int:
    """Generic loop: analyze a list of ORM rows and write results back."""
    success = 0
    for row in rows:
        text = (row.text or "").strip()
        if not text:
            print(f"  Skipping {label} id={row.id} — no text (marking skipped)")
            update_fn(row.id, {"sentiment": "skipped", "sentiment_score": 0.0, "relevance_score": 0.0})
            continue

        prompt = PROMPT_TEMPLATE.format(
            text=text[:600],   # social posts are short; 600 chars is plenty
            sectors=", ".join(NEPSE_SECTORS),
        )

        preview = text[:60].replace("\n", " ")
        print(f"  Analyzing {label} id={row.id}: {preview}…")
        raw = _call_ollama(prompt)
        analysis = _parse_response(raw)

        if not analysis:
            print(f"    Failed to parse response for id={row.id}")
            continue

        update_fn(row.id, analysis)
        print(f"    sentiment={analysis.get('sentiment')} ({analysis.get('sentiment_score')}) "
              f"signal={analysis.get('market_signal')} relevance={analysis.get('relevance_score')}")
        success += 1

    return success


def analyze_posts(batch_size: int = 20) -> int:
    rows = fetch_unanalyzed_posts(batch_size)
    if not rows:
        print("No unanalyzed posts.")
        return 0
    print(f"Analyzing {len(rows)} posts...")
    count = _analyze_rows(rows, update_post_analysis, "post")
    print(f"Done. {count}/{len(rows)} posts analyzed.")
    return count


def analyze_comments(batch_size: int = 50) -> int:
    rows = fetch_unanalyzed_comments(batch_size)
    if not rows:
        print("No unanalyzed comments.")
        return 0
    print(f"Analyzing {len(rows)} comments...")
    count = _analyze_rows(rows, update_comment_analysis, "comment")
    print(f"Done. {count}/{len(rows)} comments analyzed.")
    return count


def analyze_all(batch_size: int = 20):
    total_posts = total_comments = 0
    while True:
        n = analyze_posts(batch_size)
        total_posts += n
        if n == 0:
            break
    while True:
        n = analyze_comments(batch_size * 2)
        total_comments += n
        if n == 0:
            break
    print(f"\nTotal — posts: {total_posts}, comments: {total_comments}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze social media posts/comments with Ollama")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--target", choices=["posts", "comments", "both"], default="both")
    parser.add_argument("--all", action="store_true", help="Process all unanalyzed rows")
    args = parser.parse_args()

    if args.all:
        analyze_all(batch_size=args.batch_size)
    elif args.target == "posts":
        analyze_posts(args.batch_size)
    elif args.target == "comments":
        analyze_comments(args.batch_size * 2)
    else:
        analyze_posts(args.batch_size)
        analyze_comments(args.batch_size * 2)
