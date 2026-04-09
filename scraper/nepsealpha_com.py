import cloudscraper
from bs4 import BeautifulSoup
from datetime import date
from database.stock import insert_stock
from database.share_price_utils import upsert_share_prices, mark_trading_day, mark_holiday, get_calendar_entry

# NEPSE is closed on Fridays and Saturdays (Nepal's non-trading days)
# Python weekday(): 0=Monday, 4=Friday, 5=Saturday
NEPSE_CLOSED_WEEKDAYS = {4: "Friday", 5: "Saturday"}


def _parse_number(text: str):
    """Strip % and commas, return float or None."""
    cleaned = text.strip().replace(",", "").replace("%", "").replace("+", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def fetch_share_prices(holiday_name: str | None = None):
    """Scrape today's NEPSE share prices and save to the database.

    Holiday handling:
    - Friday / Saturday: automatically logged as non-trading day, scrape skipped.
    - Any other day with no data returned: logged as a public holiday.
      Pass holiday_name="Dashain" etc. to record the name, otherwise saved as "Public Holiday".
    - Already processed today: skipped (safe to call multiple times).
    """
    today = date.today()

    # Skip if already processed today
    existing = get_calendar_entry(today)
    if existing:
        status = "trading day" if existing.is_trading_day else f"holiday ({existing.holiday_name})"
        print(f"{today} already recorded as {status}. Skipping.")
        return

    # Auto-detect fixed non-trading days
    weekday_name = NEPSE_CLOSED_WEEKDAYS.get(today.weekday())
    if weekday_name:
        mark_holiday(today, weekday_name)
        print(f"{today} is {weekday_name} — NEPSE closed. Logged as non-trading day.")
        return

    # Scrape
    # Column mapping (verified against live page, 22 columns total):
    # 0=Symbol, 1=Ratios Summary, 2=Financial Strength(stars), 3=Sector,
    # 4=Daily Gain, 5=LTP, 6=PE, 7=PB, 8=ROE, 9=ROA, 10=PEG,
    # 11=Discount From Graham Number, 12=PE vs Sector, 13=PB vs Sector,
    # 14=PEG vs Sector, 15=Dividend Yield vs Sector, 16=ROE vs Sector,
    # 17=YOY Growth vs Sector, 18=QOQ Growth vs Sector, 19=ROA vs Sector,
    # 20=Dividend Yield, 21=Payout Ratio
    url = "https://nepsealpha.com/trading-signals/funda?fsk=kvT7XzF1p7J77IJM&type=ajax"
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table_rows = soup.find_all('tr')

    def _vs_sector(text: str) -> str | None:
        """Normalise sector comparison text; return None for empty/dash values."""
        val = text.strip()
        return None if val in ("", "--", "-") else val

    rows = []
    for row in table_rows:
        cols = row.find_all('td')
        if len(cols) < 22:
            continue

        symbol = cols[0].find('a').text.strip() if cols[0].find('a') else cols[0].text.strip()
        if not symbol:
            continue

        rows.append({
            "symbol":                   symbol,
            "trade_date":               today,
            # Price
            "ltp":                      _parse_number(cols[5].text),
            "change_percent":           _parse_number(cols[4].text),
            # Fundamental quality
            "quality":                  cols[1].text.strip(),
            "stars":                    len(cols[2].find_all('span', class_='checked')),
            "sector":                   cols[3].text.strip(),
            # Valuation ratios
            "pe":                       _parse_number(cols[6].text),
            "pb":                       _parse_number(cols[7].text),
            "roe":                      _parse_number(cols[8].text),
            "roa":                      _parse_number(cols[9].text),
            "peg":                      _parse_number(cols[10].text),
            "graham_distance":          _parse_number(cols[11].text),
            "dividend_yield":           _parse_number(cols[20].text),
            "payout_ratio":             _parse_number(cols[21].text),
            # vs Sector comparisons
            "pe_vs_sector":             _vs_sector(cols[12].text),
            "pb_vs_sector":             _vs_sector(cols[13].text),
            "peg_vs_sector":            _vs_sector(cols[14].text),
            "dividend_yield_vs_sector": _vs_sector(cols[15].text),
            "roe_vs_sector":            _vs_sector(cols[16].text),
            "yoy_growth_vs_sector":     _vs_sector(cols[17].text),
            "qoq_growth_vs_sector":     _vs_sector(cols[18].text),
            "roa_vs_sector":            _vs_sector(cols[19].text),
        })

    if not rows:
        name = holiday_name or "Public Holiday"
        mark_holiday(today, name)
        print(f"{today}: No data returned from NEPSE — logged as '{name}'.")
        return

    upsert_share_prices(rows)
    mark_trading_day(today)
    print(f"{today}: Saved {len(rows)} share prices.")



def fetch_all_shares():
        # Using the AJAX URL you found
    url = "https://nepsealpha.com/trading/1/search?limit=500&query=&fsk=fs"
    seen = set()
    scraper = cloudscraper.create_scraper()
    shares = []
    all_shares = []
    response = scraper.get(url)
    datas = response.json()
    print(datas)
    for data in datas:
        print(data)
        shares.append({
            "symbol": data["symbol"],
            "description": data["description"],
            "full_name": data["full_name"],
            "sector": data["sector"],
            "type": data["type"],
            "logo_urls": data["logo_urls"],
            "exchange_logo": data["exchange_logo"],
            "is_master": data["is_master"],
        })
    for item in shares:
        if item["symbol"] not in seen:
            seen.add(item["symbol"])
            all_shares.append(item)

    for data in all_shares:
        insert_stock(data)
        #print(f"Symbol: {data['symbol']} | description: {data['description']} | type: {data['type']} | Exchange: {data['exchange']}")
if __name__ == "__main__":
   #fetch_all_shares()
   fetch_share_prices()