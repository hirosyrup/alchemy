import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import re

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

def parse_odds(soup):
    """3連単オッズをパースする"""
    odds_list = []
    
    # div.contentsFrame1_inner -> div.table1 (2つ目)
    tables = soup.select("div.contentsFrame1_inner div.table1")
    if len(tables) < 2:
        return []
    
    tbody = tables[1].select_one("table tbody")
    if not tbody:
        return []

    rows = tbody.select("tr")
    
    # 1-2-3 ... 6-5-4 (全120通り)
    # テーブル構造が複雑なので注意深くパース
    # 20行 x 6列 (各セルに3つのオッズが入っている場合とそうでない場合がある)
    # createPredicts.ts のロジックを再現
    
    rows_with_second_boat = None
    
    for row_index, row in enumerate(rows):
        tds = row.select("td")
        
        for index in range(6): # 1号艇〜6号艇が頭
            first_boat = index + 1
            
            second_boat = 0
            third_boat = 0
            odds_val = 0.0
            
            if row_index % 4 == 0:
                rows_with_second_boat = tds
                target_index = index * 3
                try:
                    second_boat = int(rows_with_second_boat[target_index].text.strip())
                    third_boat = int(tds[target_index + 1].text.strip())
                    odds_val = float(tds[target_index + 2].text.strip())
                except: pass
            else:
                try:
                    second_boat = int(rows_with_second_boat[index * 3].text.strip())
                    target_index = index * 2
                    third_boat = int(tds[target_index].text.strip())
                    odds_val = float(tds[target_index + 1].text.strip())
                except: pass
            
            if second_boat != 0 and third_boat != 0:
                combination = f"{first_boat}-{second_boat}-{third_boat}"
                odds_list.append({
                    "combination": combination,
                    "odds": odds_val
                })

    return sorted(odds_list, key=lambda x: x['combination'])

def check_time(soup, deadline_time: datetime):
    """オッズ更新時間と締切までの時間を確認"""
    # 締切済みチェック
    if soup.select_one("p.tab4_time"):
        return None # 締切済み

    refresh_text_el = soup.select_one("p.tab4_refreshText")
    if not refresh_text_el:
        return None

    match = re.search(r'([01][0-9]|2[0-3]):[0-5][0-9]', refresh_text_el.text)
    if not match:
        return None
    
    refresh_time_str = match.group(0)
    # 今日の日付と結合
    refresh_time = datetime.strptime(f"{datetime.now().strftime('%Y/%m/%d')} {refresh_time_str}", "%Y/%m/%d %H:%M")
    
    minutes_ago = round((deadline_time - refresh_time).total_seconds() / 60.0)
    
    return {
        "minutes_ago": minutes_ago,
        "odds_refresh_time": refresh_time
    }

async def get_odds(date: datetime, place_id: int, race_number: int):
    """オッズを取得する"""
    str_date = date.strftime('%Y%m%d')
    str_place = str(place_id).zfill(2)
    
    url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race_number}&jcd={str_place}&hd={str_date}"
    
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        odds = parse_odds(soup)
        
        # 締切時間との差分などは呼び出し元で計算するためにここでは返さないか、
        # 必要なら引数でdeadlineを受け取る。
        # ここでは純粋にオッズデータを返す。
        
        return odds
