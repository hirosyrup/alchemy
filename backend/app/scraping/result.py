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

async def get_race_result(date: datetime, place_id: int, race_number: int):
    """レース結果（3連単の払戻金）を取得する"""
    str_date = date.strftime('%Y%m%d')
    url = f"https://www.boatrace.jp/owpc/pc/race/pay?hd={str_date}"
    
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 該当する場のテーブルを探す
        # 画像alt属性で場名を判定するか、画像ファイル名で判定
        # checkHitPredict.tsでは画像ファイル名(src)で判定している
        
        target_table = None
        target_col_idx = -1
        
        tables = soup.select("table.is-strited1")
        
        for table in tables:
            thead = table.find("thead")
            if not thead: continue
            
            areas = thead.select("p.table1_areaName")
            for idx, area in enumerate(areas):
                img = area.select_one("p img")
                if img and img.get('src'):
                    match = re.search(r'(\d{1,2})\.png', img['src'])
                    if match and int(match.group(1)) == place_id:
                        target_table = table
                        target_col_idx = idx
                        break
            if target_table:
                break
        
        if not target_table or target_col_idx == -1:
            return None
            
        # 結果行を取得 (race_number - 1)
        tbody = target_table.select("tbody")[race_number - 1]
        tds = tbody.select("td")
        
        # 3連単は各場の列ごとに3つのセルを使う (組番, 払戻金, 人気)
        # target_col_idx * 3 が開始位置
        start_idx = target_col_idx * 3
        
        if len(tds) <= start_idx + 1:
            return None
            
        # 組番 (spanタグ内の数字を結合)
        combo_td = tds[start_idx]
        spans = combo_td.select("span")
        combination = "-".join([s.text.strip() for s in spans])
        
        # 払戻金
        price_td = tds[start_idx + 1]
        price_span = price_td.select_one("span")
        if not price_span:
            return None
            
        price_text = price_span.text.strip().replace('¥', '').replace(',', '')
        try:
            payout = int(price_text)
        except:
            payout = 0
            
        # 返還かどうか
        is_returned = False
        if len(tds) > start_idx + 2:
            return_span = tds[start_idx + 2].select_one("span")
            if return_span and return_span.text.strip() == "返":
                is_returned = True

        return {
            "combination": combination,
            "payout": payout,
            "is_returned": is_returned
        }
