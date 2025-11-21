import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def parse_float(text, is_zero_to_none=False):
    """文字列をfloatに変換"""
    if not text: return None
    clean_text = text.replace('kg', '').replace('m', '').replace('cm', '').replace('℃', '').replace('%', '').strip()
    # 全角数字対策
    table = str.maketrans('０１２３４５６７８９．', '0123456789.')
    clean_text = clean_text.translate(table)
    try:
        result = float(clean_text)
        if result == 0.0 and is_zero_to_none:
          return None
        else:
          return result
    except ValueError:
        return None

async def fetch_html(session, url):
    """URLからHTMLを取得"""
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            if response.status == 200:
                html = await response.read()
                soup = BeautifulSoup(html, 'html.parser')
                if "データがありません" in soup.text or "指定されたページが見つかりません" in soup.text:
                    return None
                return soup
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def parse_racelist(soup, data, r_idx):
    """出走表の解析ロジック"""
    try:
        prefix = f'r{r_idx}_'
        table_div = soup.find('div', class_='table1 is-tableFixed__3rdadd')
        if not table_div: return

        # 該当艇のtbodyを探す
        tbodies = table_div.find('table').find_all('tbody')
        if len(tbodies) < r_idx: return
        tbody = tbodies[r_idx - 1]

        rows = tbody.find_all('tr')
        if not rows: return
        tds = rows[0].find_all('td', recursive=False)

        # 登録番号
        try:
            data[prefix + 'toban'] = rows[0].find('div', class_='is-fs11').text.strip().split('/')[0].strip()
        except: pass

        # 級別
        try:
            class_span = rows[0].find('span', class_='is-fColor1')
            if class_span:
                data[prefix + 'class'] = class_span.text.strip()
            else:
                match = re.search(r'(A1|A2|B1|B2)', rows[0].text)
                data[prefix + 'class'] = match.group(1) if match else None
        except: pass

        # 体重
        try:
            match = re.search(r'(\d{2}\.\d)kg', rows[0].text)
            data[prefix + 'weight'] = parse_float(match.group(1)) if match else None
        except: pass

        # F/L/ST
        try:
            fl_lines = [line.strip() for line in tds[3].stripped_strings]
            data[prefix + 'f_count'] = int(fl_lines[0].replace('F', ''))
            data[prefix + 'l_count'] = int(fl_lines[1].replace('L', ''))
            data[prefix + 'avg_st'] = parse_float(fl_lines[2])
        except: pass

        # 成績
        try:
            g_lines = [line.strip() for line in tds[4].stripped_strings] # 全国
            data[prefix + 'global_win_rate'] = parse_float(g_lines[0], is_zero_to_none=True) if g_lines[0] != '-' else None
            data[prefix + 'global_3ren_rate'] = parse_float(g_lines[2], is_zero_to_none=True) if g_lines[2] != '-' else None

            l_lines = [line.strip() for line in tds[5].stripped_strings] # 当地
            data[prefix + 'local_win_rate'] = parse_float(l_lines[0], is_zero_to_none=True) if l_lines[0] != '-' else None
            data[prefix + 'local_3ren_rate'] = parse_float(l_lines[2], is_zero_to_none=True) if l_lines[2] != '-' else None

            m_lines = [line.strip() for line in tds[6].stripped_strings] # モーター
            data[prefix + 'motor_3ren'] = parse_float(m_lines[2], is_zero_to_none=True) if m_lines[2] != '-' else None
        except: pass

    except Exception: pass

def parse_beforeinfo(soup, data, r_idx):
    """直前情報の解析ロジック"""
    try:
        prefix = f'r{r_idx}_'
        # 1. 各艇情報 (展示タイム、チルト)
        table_racer = soup.find('table', class_='is-w748')
        if table_racer:
            tbodies = table_racer.find_all('tbody')
            if len(tbodies) >= r_idx:
                row = tbodies[r_idx - 1].find('tr')
                tds = row.find_all('td', recursive=False)
                # インデックスは固定: 4=展示, 5=チルト
                try: data[prefix + 'exhibition_time'] = parse_float(tds[4].text)
                except: pass
                try: data[prefix + 'tilt'] = parse_float(tds[5].text)
                except: pass
    except: pass

def parse_start_exhibition(soup, data):
    """スタート展示の解析"""
    try:
        table_start = soup.find('table', class_='is-w238')
        if not table_start: return

        rows = table_start.find('tbody').find_all('tr')
        for course_idx, row in enumerate(rows):
            try:
                # 艇番
                boat_span = row.find('span', class_=re.compile(r'table1_boatImage1Number'))
                if not boat_span: continue
                boat_num = int(boat_span.text.strip())

                # ST
                st_span = row.find('span', class_=re.compile(r'table1_boatImage1Time'))
                st_text = st_span.text.strip()
                if 'F' in st_text: st_val = -parse_float(st_text.replace('F', ''))
                elif 'L' in st_text: st_val = 1.0
                else: st_val = parse_float(st_text)

                prefix = f'r{boat_num}_'
                data[prefix + 'exhibition_course'] = course_idx + 1
                data[prefix + 'exhibition_st'] = st_val
            except: pass
    except: pass

def parse_weather(soup, data):
    """気象情報の解析"""
    try:
        w_div = soup.find('div', class_='weather1_body')
        if not w_div: return

        try: data['weather_temperature'] = parse_float(w_div.find('div', class_='is-direction').find('span', class_='weather1_bodyUnitLabelData').text)
        except: pass

        try: data['weather_condition'] = w_div.find('div', class_='is-weather').find('span', class_='weather1_bodyUnitLabelTitle').text.strip()
        except: pass

        try: data['weather_wind_speed'] = parse_float(w_div.find('div', class_='is-wind').find('span', class_='weather1_bodyUnitLabelData').text)
        except: pass

        try:
            p_tag = w_div.find('div', class_='is-windDirection').find('p')
            cls = [c for c in p_tag.get('class') if 'is-wind' in c][0]
            data['weather_wind_direction'] = int(cls.replace('is-wind', ''))
        except: pass

        try: data['weather_water_temp'] = parse_float(w_div.find('div', class_='is-waterTemperature').find('span', class_='weather1_bodyUnitLabelData').text)
        except: pass

    except: pass

async def get_race_info(date: datetime, place_id: int, race_number: int):
    """
    指定されたレースの情報を取得する
    """
    str_date = date.strftime('%Y%m%d')
    str_place = str(place_id).zfill(2)
    str_rno = str(race_number)

    url_race = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={str_rno}&jcd={str_place}&hd={str_date}"
    url_info = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={str_rno}&jcd={str_place}&hd={str_date}"

    data = {
        'date': str_date,
        'place_id': place_id,
        'race_number': race_number
    }

    async with aiohttp.ClientSession() as session:
        task1 = fetch_html(session, url_race)
        task2 = fetch_html(session, url_info)
        soup_race, soup_info = await asyncio.gather(task1, task2)

        if soup_race:
            for i in range(1, 7):
                parse_racelist(soup_race, data, i)

        if soup_info:
            for i in range(1, 7):
                parse_beforeinfo(soup_info, data, i)
            parse_start_exhibition(soup_info, data)
            parse_weather(soup_info, data)

    return data
