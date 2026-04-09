import cloudscraper
from bs4 import BeautifulSoup
from database.economic_indicator_utils import upsert_indicators

URL = "https://tradingeconomics.com/nepal/indicators"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://tradingeconomics.com/",
}

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_reference(ref: str) -> tuple[int | None, int | None]:
    """Parse a reference string like 'Dec/24' or 'Q3/24' or '2024'.

    Returns (year, month) where month is None for quarterly/annual data.
    """
    ref = ref.strip()
    if not ref or ref == "-":
        return None, None

    if "/" in ref:
        parts = ref.split("/")
        raw_period = parts[0].strip().lower()
        raw_year   = parts[1].strip()

        # Convert two-digit year: "24" → 2024
        try:
            year = int(raw_year)
            if year < 100:
                year += 2000
        except ValueError:
            year = None

        # Monthly reference: "dec", "jan", etc.
        if raw_period in MONTH_MAP:
            return year, MONTH_MAP[raw_period]

        # Quarterly reference: "q1", "q2", etc. — store month as None
        return year, None

    # Plain year: "2024"
    try:
        return int(ref), None
    except ValueError:
        return None, None


def _parse_number(text: str) -> float | None:
    """Strip commas/spaces and convert to float. Returns None on failure."""
    cleaned = text.strip().replace(",", "").replace(" ", "")
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_table(table, category: str) -> list[dict]:
    rows = table.find_all("tr")
    indicators = []

    for row in rows:
        cols = row.find_all("td")
        # Expect at least 7 columns: name, last, previous, highest, lowest, unit, date
        if len(cols) < 7:
            continue

        name = cols[0].get_text(strip=True)
        if not name:
            continue

        value    = _parse_number(cols[1].get_text(strip=True))
        previous = _parse_number(cols[2].get_text(strip=True))
        highest  = _parse_number(cols[3].get_text(strip=True))
        lowest   = _parse_number(cols[4].get_text(strip=True))
        unit     = cols[5].get_text(strip=True)
        reference = cols[6].get_text(strip=True)

        year, month = _parse_reference(reference)

        indicators.append({
            "indicator": name,
            "category":  category,
            "value":     value,
            "previous":  previous,
            "highest":   highest,
            "lowest":    lowest,
            "unit":      unit,
            "reference": reference,
            "year":      year,
            "month":     month,
            "country":   "Nepal",
            "source":    "Trading Economics",
        })

    return indicators


def fetch_nepal_indicators():
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Each category section has an <h2> or <h3> heading followed by a <table>
    # Trading Economics wraps each category in a div; we walk headings + tables together
    all_indicators = []

    # Strategy: find all tables; use the nearest preceding heading as the category
    tables = soup.find_all("table")
    for table in tables:
        # Walk backwards through siblings to find the closest heading
        category = "Overview"
        for sibling in table.find_all_previous(["h2", "h3", "h4"]):
            category = sibling.get_text(strip=True)
            break

        rows = _parse_table(table, category)
        if rows:
            print(f"  [{category}] found {len(rows)} indicators")
            all_indicators.extend(rows)

    if all_indicators:
        upsert_indicators(all_indicators)
        print(f"Done. Upserted {len(all_indicators)} indicators.")
    else:
        print("No indicators found — page structure may have changed.")


if __name__ == "__main__":
    fetch_nepal_indicators()
