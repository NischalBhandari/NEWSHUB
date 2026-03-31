import cloudscraper
from bs4 import BeautifulSoup

def fetch_share_prices():
    # Using the AJAX URL you found
    url = "https://nepsealpha.com/trading-signals/funda?fsk=kvT7XzF1p7J77IJM&type=ajax"

    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all rows in the table body
    table_rows = soup.find_all('tr')
    
    for row in table_rows:
        cols = row.find_all('td')
        
        # Ensure the row actually has data columns
        if len(cols) > 0:
            # 1. Symbol (Inside the <a> tag in the first column)
            symbol = cols[0].find('a').text.strip() if cols[0].find('a') else cols[0].text.strip()
            
            # 2. Fundamental Quality (The text inside the button)
            quality = cols[1].text.strip()
            
            # 3. Valuation Score (Counting the checked stars)
            stars = len(cols[2].find_all('span', class_='checked'))
            
            # 4. Sector
            sector = cols[3].text.strip()
            
            # 5. Percentage Change
            change = cols[4].text.strip()
            
            # 6. LTP (Last Traded Price)
            ltp = cols[5].text.strip()
            
            # 11. Fundamental Score (The 47% in your example)
            f_score = cols[11].text.strip()
            
            # 12. Valuation Status (Overvalued/Undervalued)
            valuation = cols[12].text.strip()

            # For demonstration, printing the core values
            print(f"Symbol: {symbol} | Sector: {sector} | LTP: {ltp} | Score: {f_score} | Stars: {stars}/5")



def fetch_all_shares():
        # Using the AJAX URL you found
    url = "https://nepsealpha.com/trading-signals/funda?fsk=kvT7XzF1p7J77IJM"

    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    data = response.json()
    print(data)
if __name__ == "__main__":
    fetch_all_shares()