import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from app.pubsub_client import publish_message

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

async def fetch_html(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            if response.status == 200:
                return await response.read()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

async def check_and_dispatch():
    """
    当日の全レースを確認し、タイミングに応じてイベントを発行する
    """
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, url)
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        
        # テーブルからレース情報を抽出
        # div.table1 -> table -> tbody -> tr (各場)
        
        table_div = soup.select_one("div.table1")
        if not table_div: return
        
        tbodies = table_div.select("table tbody")
        
        now = datetime.now()
        
        for tbody in tbodies:
            # 各場
            first_tr = tbody.select_one("tr")
            if not first_tr: continue
            
            # 場ID取得
            img = first_tr.select_one("td a img")
            if not img or not img.get('src'): continue
            
            match = re.search(r'(\d{1,2})\.png', img['src'])
            if not match: continue
            place_id = int(match.group(1))
            
            # レース一覧 (2行目以降のtd)
            # trs[1] にレース番号と時間が並んでいる
            trs = tbody.select("tr")
            if len(trs) < 2: continue
            
            race_tds = trs[1].select("td")
            
            for race_td in race_tds:
                # レース番号と時間を取得
                # 例: 1R 10:30
                text = race_td.text.strip()
                match = re.search(r'(\d{1,2})R\s*(\d{1,2}:\d{2})', text)
                if not match: continue
                
                race_number = int(match.group(1))
                time_str = match.group(2)
                
                # 締切時間
                deadline = datetime.strptime(f"{now.strftime('%Y/%m/%d')} {time_str}", "%Y/%m/%d %H:%M")
                
                diff_seconds = (deadline - now).total_seconds()
                
                event_type = None
                
                # 6分前 (360s ~ 420s) -> scrape_info
                if 360 <= diff_seconds < 420:
                    event_type = "scrape_info"
                
                # 5分前 (300s ~ 360s) -> predict_5min
                elif 300 <= diff_seconds < 360:
                    event_type = "predict_5min"
                
                # 1分前 (60s ~ 120s) -> predict_1min
                elif 60 <= diff_seconds < 120:
                    event_type = "predict_1min"
                
                # 結果確認 (レース後20分程度) (-1260s ~ -1200s)
                elif -1260 <= diff_seconds < -1200:
                    event_type = "check_result"
                
                if event_type:
                    message = {
                        "type": event_type,
                        "place_id": place_id,
                        "race_number": race_number,
                        "deadline": deadline.isoformat()
                    }
                    print(f"Dispatching: {message}")
                    publish_message(message)

