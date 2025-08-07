
import requests
from bs4 import BeautifulSoup

def get_sector_performance():
    url = "https://finance.yahoo.com/sectors"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    data = []
    table = soup.find("table")
    if table:
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                data.append({
                    "sector": cols[0].text.strip(),
                    "1D Change": cols[1].text.strip(),
                    "5D Change": cols[2].text.strip()
                })
    return {"sectors": data}
