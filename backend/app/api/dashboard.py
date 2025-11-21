from fastapi import APIRouter
from app import firestore_client
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/balance")
async def get_balance_history():
    """
    収支推移を取得する
    """
    if not firestore_client.db:
        return {"history": []}
    
    # 過去30日分のベットを取得
    start_date = datetime.now() - timedelta(days=30)
    bets = firestore_client.db.collection('bets')\
        .where('created_at', '>=', start_date)\
        .order_by('created_at')\
        .stream()
        
    history = []
    current_balance = 0
    
    # 日付ごとに集計
    daily_balance = {}
    
    for bet in bets:
        data = bet.to_dict()
        date_str = data['date'].strftime('%Y-%m-%d')
        
        amount = data.get('amount', 0)
        return_amount = data.get('return_amount', 0)
        
        if date_str not in daily_balance:
            daily_balance[date_str] = 0
            
        daily_balance[date_str] += (return_amount - amount)
        
    # 累積和を計算
    sorted_dates = sorted(daily_balance.keys())
    cumulative = 0
    for date in sorted_dates:
        cumulative += daily_balance[date]
        history.append({
            "date": date,
            "balance": cumulative
        })
        
    return {"history": history}

@router.get("/bets")
async def get_recent_bets():
    """
    最近の投票履歴を取得する
    """
    if not firestore_client.db:
        return {"bets": []}
        
    bets = firestore_client.db.collection('bets')\
        .order_by('created_at', direction=firestore_client.firestore.Query.DESCENDING)\
        .limit(50)\
        .stream()
        
    result = []
    for bet in bets:
        data = bet.to_dict()
        # datetimeを文字列に変換
        data['date'] = data['date'].strftime('%Y-%m-%d')
        if 'created_at' in data:
            data['created_at'] = data['created_at'].isoformat()
        if 'result_checked_at' in data and data['result_checked_at']:
            data['result_checked_at'] = data['result_checked_at'].isoformat()
            
        result.append(data)
        
    return {"bets": result}
