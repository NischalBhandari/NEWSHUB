"""
Master pipeline — scrape everything in parallel, then run analysis.

Usage:
    python run_pipeline.py                  # scrape + analyze
    python run_pipeline.py --scrape-only    # skip analysis
    python run_pipeline.py --analyze-only   # skip scraping
    python run_pipeline.py --no-kathmandu   # skip slow kathmandupost (fetches each article)
"""

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Scrapers ──────────────────────────────────────────────────────────────────
from scraper.bbc_com              import fetch_bbc_news
from scraper.merolagani_com       import fetch_merolagani_news
from scraper.kathmandupost_com    import fetch_news as fetch_kathmandupost
from scraper.nepsealpha_com       import fetch_share_prices, fetch_all_shares
from scraper.trading_economics_com import fetch_nepal_indicators

# ── Analyzers ─────────────────────────────────────────────────────────────────
from analysis.news_analyzer         import analyze_all as analyze_news
from analysis.social_media_analyzer import analyze_all as analyze_social


# ---------------------------------------------------------------------------
# Scraper registry
# Each entry: (label, callable)
# Fast RSS/API scrapers run in one thread pool; slow per-article scrapers
# (kathmandupost fetches every article individually) are optional.
# ---------------------------------------------------------------------------

FAST_SCRAPERS = [
    ("BBC News",              fetch_bbc_news),
    ("Merolagani",            fetch_merolagani_news),
    ("NEPSE Share Prices",    fetch_share_prices),
    ("NEPSE All Shares",      fetch_all_shares),
    ("Trading Economics",     fetch_nepal_indicators),
]

SLOW_SCRAPERS = [
    ("Kathmandu Post",        fetch_kathmandupost),
]


def run_scraper(label: str, fn) -> dict:
    """Run a single scraper and return a result summary."""
    print(f"  [START]  {label}")
    t0 = time.time()
    try:
        fn()
        elapsed = time.time() - t0
        print(f"  [DONE ]  {label} ({elapsed:.1f}s)")
        return {"label": label, "status": "ok", "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  [ERROR]  {label} ({elapsed:.1f}s): {e}")
        return {"label": label, "status": "error", "error": str(e), "elapsed": elapsed}


def run_scrapers(include_slow: bool = True):
    scrapers = FAST_SCRAPERS + (SLOW_SCRAPERS if include_slow else [])

    print(f"\n{'='*55}")
    print(f"  SCRAPING  ({len(scrapers)} scrapers, running in parallel)")
    print(f"{'='*55}")
    t0 = time.time()

    results = []
    # Use threads — all scrapers are I/O bound (HTTP requests + DB writes)
    with ThreadPoolExecutor(max_workers=len(scrapers)) as pool:
        futures = {pool.submit(run_scraper, label, fn): label for label, fn in scrapers}
        for future in as_completed(futures):
            results.append(future.result())

    elapsed = time.time() - t0
    ok    = [r for r in results if r["status"] == "ok"]
    errors = [r for r in results if r["status"] == "error"]

    print(f"\n  Scraping complete in {elapsed:.1f}s — "
          f"{len(ok)} succeeded, {len(errors)} failed")
    if errors:
        for r in errors:
            print(f"    ✗ {r['label']}: {r['error']}")

    return results


def run_analysis():
    print(f"\n{'='*55}")
    print(f"  ANALYSIS")
    print(f"{'='*55}")
    t0 = time.time()

    print("\n  [NEWS] Analyzing unanalyzed news articles…")
    analyze_news()

    print("\n  [SOCIAL] Analyzing unanalyzed social media posts/comments…")
    analyze_social()

    print(f"\n  Analysis complete in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIHub master pipeline")
    parser.add_argument("--scrape-only",   action="store_true", help="Skip analysis step")
    parser.add_argument("--analyze-only",  action="store_true", help="Skip scraping step")
    parser.add_argument("--no-kathmandu",  action="store_true",
                        help="Skip Kathmandu Post (slow — fetches each article individually)")
    args = parser.parse_args()

    total_start = time.time()

    if not args.analyze_only:
        run_scrapers(include_slow=not args.no_kathmandu)

    if not args.scrape_only:
        run_analysis()

    print(f"\n{'='*55}")
    print(f"  Pipeline finished in {time.time() - total_start:.1f}s")
    print(f"{'='*55}\n")
