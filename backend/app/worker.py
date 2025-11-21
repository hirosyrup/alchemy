import asyncio
from datetime import datetime
from app.scraping import race_info, odds, result
from app.processing import feature_engineering
from app.ml.predictor import get_predictor
from app import firestore_client

# 期待値の閾値 (設定ファイルや環境変数にするのが望ましい)
EV_THRESHOLD = 110.0 # 100円賭けて110円戻る期待値以上なら買う

async def handle_scrape_info(place_id: int, race_number: int, deadline: datetime):
    print(f"Handling scrape_info for {place_id}R{race_number}")
    # 1. スクレイピング
    data = await race_info.get_race_info(deadline, place_id, race_number)
    if not data:
        print("Failed to scrape race info")
        return

    # 2. 特徴量エンジニアリング
    processed_data = feature_engineering.engineer_boat_features(data)
    
    # 3. 保存
    firestore_client.save_race_info(deadline, place_id, race_number, processed_data)
    print("Race info saved")

async def handle_predict(place_id: int, race_number: int, deadline: datetime, type_key: str):
    print(f"Handling {type_key} for {place_id}R{race_number}")
    
    # 1. オッズ取得
    odds_data = await odds.get_odds(deadline, place_id, race_number)
    if not odds_data:
        print("Failed to scrape odds")
        return

    # 2. レース情報ロード
    race_info_data = firestore_client.get_race_info_data(deadline, place_id, race_number)
    if not race_info_data:
        print("Race info not found")
        # レース情報がないと予測できないので終了 (またはここでスクレイピングを試みる手もあるが)
        return

    # 3. 予測 (モデル入力作成 -> 推論)
    # モデル入力には race_info_data と オッズ情報の一部(人気順など)が必要かもしれない
    # ここでは簡易的に race_info_data をそのまま入力とする
    predictor = get_predictor()
    probabilities = predictor.predict_proba(race_info_data)
    
    # 4. 期待値計算 & 投票判断
    bets_to_place = []
    prediction_record = []
    
    for odd in odds_data:
        combo = odd['combination']
        val = odd['odds']
        prob = probabilities.get(combo, 0.0)
        
        expected_value = prob * val * 100 # 100円賭けた場合の期待払い戻し額 (または単に prob * val で回収率期待値)
        
        # 回収率期待値 (%)
        ev_percent = prob * val * 100
        
        prediction_record.append({
            'combination': combo,
            'probability': prob,
            'odds': val,
            'expected_value': ev_percent
        })
        
        if type_key == 'predict_1min' and ev_percent >= EV_THRESHOLD:
            bets_to_place.append({
                'combination': combo,
                'odds': val,
                'amount': 100, # 固定額
                'expected_value': ev_percent,
                'status': 'pending'
            })
            
    # 5. 保存
    firestore_client.save_prediction(deadline, place_id, race_number, prediction_record, type_key)
    
    if type_key == 'predict_1min':
        for bet in bets_to_place:
            firestore_client.save_bet(deadline, place_id, race_number, bet)
            print(f"Bet placed: {bet['combination']} (EV: {bet['expected_value']:.1f}%)")

async def handle_check_result(place_id: int, race_number: int, deadline: datetime):
    print(f"Handling check_result for {place_id}R{race_number}")
    result_data = await result.get_race_result(deadline, place_id, race_number)
    if not result_data:
        print("Failed to scrape result")
        return
        
    firestore_client.save_result(deadline, place_id, race_number, result_data)
    print(f"Result saved: {result_data['combination']}")

async def process_event(data: dict):
    """
    Pub/Subメッセージを処理する
    """
    event_type = data.get('type')
    place_id = data.get('place_id')
    race_number = data.get('race_number')
    deadline_str = data.get('deadline')
    
    if not (event_type and place_id and race_number and deadline_str):
        print("Invalid event data")
        return

    deadline = datetime.fromisoformat(deadline_str)
    
    if event_type == 'scrape_info':
        await handle_scrape_info(place_id, race_number, deadline)
    elif event_type == 'predict_5min':
        await handle_predict(place_id, race_number, deadline, 'predict_5min')
    elif event_type == 'predict_1min':
        await handle_predict(place_id, race_number, deadline, 'predict_1min')
    elif event_type == 'check_result':
        await handle_check_result(place_id, race_number, deadline)
    else:
        print(f"Unknown event type: {event_type}")
