import pandas as pd
import numpy as np

def engineer_boat_features(data_dict: dict) -> dict:
    """
    辞書形式のレースデータに特徴量を追加して返す
    """
    # DataFrameに変換して処理（pandasの便利な機能を使うため）
    df = pd.DataFrame([data_dict])
    
    boats = range(1, 7)

    # 各データのカラム名パターン定義
    col_win_rate = [f'r{b}_global_win_rate' for b in boats]   # 勝率
    col_motor    = [f'r{b}_motor_3ren' for b in boats] # モーター3連対率
    col_tenji    = [f'r{b}_exhibition_time' for b in boats]      # 展示タイム
    col_st       = [f'r{b}_exhibition_st' for b in boats]         # スタート展示

    # -------------------------------------------------
    # 2. 偏差値・相対評価 (Z-Score & Relative)
    # -------------------------------------------------
    target_groups = {
        'win_rate': col_win_rate,
        'motor': col_motor
    }

    for name, cols in target_groups.items():
        # 存在チェック (DataFrameなのでカラムがあるか)
        if not all(c in df.columns for c in cols):
            continue

        # 行ごとの平均と標準偏差を計算
        row_mean = df[cols].mean(axis=1)
        row_std = df[cols].std(axis=1).replace(0, 1)

        for col in cols:
            df[f'{col}_z'] = (df[col] - row_mean) / row_std
            if col != cols[0]: # 1号艇以外の場合
                df[f'{col}_diff_1'] = df[col] - df[cols[0]]

    # -------------------------------------------------
    # 3. ランク付け (Ranking)
    # -------------------------------------------------
    # 勝率・モーター（数値が大きい方が偉い -> ascending=False）
    for name, cols in target_groups.items():
        if not all(c in df.columns for c in cols): continue
        ranks = df[cols].rank(axis=1, ascending=False, method='min')
        for i, col in enumerate(cols):
            df[f'{col}_rank'] = ranks[cols[i]]

    # 展示タイム・ST（数値が小さい方が偉い -> ascending=True）
    time_groups = {
        'tenji': col_tenji,
        'st': col_st
    }

    for name, cols in time_groups.items():
        if not all(c in df.columns for c in cols): continue
        ranks = df[cols].rank(axis=1, ascending=True, method='min')
        for i, col in enumerate(cols):
            df[f'{col}_rank'] = ranks[cols[i]]
            df[f'{col}_is_top'] = (ranks[cols[i]] == 1).astype(int)

    # -------------------------------------------------
    # 4. スタート展示の深掘り (ST Gap)
    # -------------------------------------------------
    if all(c in df.columns for c in col_st):
        row_st_mean = df[col_st].mean(axis=1)
        for col in col_st:
            df[f'{col}_gap_avg'] = df[col] - row_st_mean

    # 辞書に戻して返す (NaNはNoneに変換)
    result = df.iloc[0].replace({np.nan: None}).to_dict()
    return result
