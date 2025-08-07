
import requests
from bs4 import BeautifulSoup

def get_macro_indicators():
    url = "https://tradingeconomics.com/united-states/indicators"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    indicators = []
    rows = soup.select("table.table-hover tbody tr")
    for row in rows[:10]:
        cols = row.find_all("td")
        if len(cols) >= 4:
            indicators.append({
                "name": cols[0].text.strip(),
                "latest": cols[1].text.strip(),
                "previous": cols[2].text.strip(),
                "unit": cols[3].text.strip()
            })
    return {"macro_indicators": indicators}
