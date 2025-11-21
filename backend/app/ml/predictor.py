import os
import pandas as pd
try:
    from autogluon.tabular import TabularPredictor
except ImportError:
    print("AutoGluon not installed or failed to import.")
    TabularPredictor = None

MODEL_PATH = os.getenv("MODEL_PATH", "AutogluonModels/ag-20220904_034430") # Default path or env var

class Predictor:
    def __init__(self):
        self.predictor = None
        if TabularPredictor and os.path.exists(MODEL_PATH):
            try:
                self.predictor = TabularPredictor.load(MODEL_PATH)
                print(f"Model loaded from {MODEL_PATH}")
            except Exception as e:
                print(f"Failed to load model: {e}")
        else:
            print(f"Model not found at {MODEL_PATH}")

    def predict_proba(self, input_data: dict):
        """
        入力データを受け取り、各クラス（組み合わせ）の確率を返す
        """
        if not self.predictor:
            # モック: ランダムな確率を返す
            print("Using mock prediction")
            combinations = [f"{i}-{j}-{k}" for i in range(1,7) for j in range(1,7) for k in range(1,7) if i!=j and i!=k and j!=k]
            return {c: 1.0/len(combinations) for c in combinations}

        df = pd.DataFrame([input_data])
        # AutoGluonのpredict_probaはDataFrameを返す
        pred_proba = self.predictor.predict_proba(df)
        
        # 1行目の結果を辞書で返す {class_label: prob, ...}
        return pred_proba.iloc[0].to_dict()

predictor_instance = Predictor()

def get_predictor():
    return predictor_instance
