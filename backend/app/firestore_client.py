import os
from google.cloud import firestore
from datetime import datetime

PROJECT_ID = os.getenv("PROJECT_ID", "dummy-project")

if PROJECT_ID == "dummy-project":
    db = None
    print("[Mock Firestore] Initialized")
else:
    db = firestore.Client(project=PROJECT_ID)

def get_race_id(date: datetime, place_id: int, race_number: int):
    return f"{date.strftime('%Y%m%d')}-{place_id}-{race_number}"

def save_race_info(date: datetime, place_id: int, race_number: int, data: dict):
    if not db: return
    race_id = get_race_id(date, place_id, race_number)
    doc_ref = db.collection('races').document(race_id)
    doc_ref.set({
        'info': data,
        'metadata': {
            'date': date,
            'place_id': place_id,
            'race_number': race_number,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
    }, merge=True)

def get_race_info_data(date: datetime, place_id: int, race_number: int):
    if not db: return {}
    race_id = get_race_id(date, place_id, race_number)
    doc = db.collection('races').document(race_id).get()
    if doc.exists:
        return doc.to_dict().get('info', {})
    return {}

def save_prediction(date: datetime, place_id: int, race_number: int, prediction_data: dict, type_key: str):
    """
    type_key: 'predict_5min' or 'predict_1min'
    """
    if not db: return
    race_id = get_race_id(date, place_id, race_number)
    doc_ref = db.collection('races').document(race_id)
    doc_ref.set({
        type_key: prediction_data,
        'metadata': {'updated_at': firestore.SERVER_TIMESTAMP}
    }, merge=True)

def save_bet(date: datetime, place_id: int, race_number: int, bet_data: dict):
    if not db: return
    race_id = get_race_id(date, place_id, race_number)
    # betsコレクションは独立させるか、racesのサブコレクションにするか
    # ここでは独立したコレクションにする
    bet_id = f"{race_id}-{bet_data['combination']}"
    db.collection('bets').document(bet_id).set({
        'race_id': race_id,
        'date': date,
        'place_id': place_id,
        'race_number': race_number,
        **bet_data,
        'created_at': firestore.SERVER_TIMESTAMP
    })

def save_result(date: datetime, place_id: int, race_number: int, result_data: dict):
    if not db: return
    race_id = get_race_id(date, place_id, race_number)
    
    # レース情報更新
    db.collection('races').document(race_id).set({
        'result': result_data
    }, merge=True)
    
    # ベットの判定
    bets = db.collection('bets').where('race_id', '==', race_id).stream()
    for bet in bets:
        bet_dict = bet.to_dict()
        if bet_dict['combination'] == result_data['combination']:
            status = 'won'
            return_amount = bet_dict['amount'] * (result_data['payout'] / 100.0) # 100円あたりの払戻金なので
        else:
            status = 'lost'
            return_amount = 0
            if result_data.get('is_returned'): # 返還の場合
                 # ここでは簡易的に全返還とするが、実際は艇番ごとの返還ロジックが必要
                 # 今回は要件にないのでスキップ、または全て返還扱いにするか
                 pass

        db.collection('bets').document(bet.id).update({
            'status': status,
            'return_amount': return_amount,
            'result_checked_at': firestore.SERVER_TIMESTAMP
        })
