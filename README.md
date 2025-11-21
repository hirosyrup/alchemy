# Boat Race Trading Simulation System

## 概要
競艇の自動売買シミュレーションシステムです。

## 構成
- **Backend**: Python (FastAPI)
- **Frontend**: TypeScript (React)
- **Infrastructure**: GCP (Cloud Run, Firestore, Pub/Sub, Cloud Scheduler)

## セットアップ

### 前提条件
- Python 3.10+
- Node.js 16+
- Google Cloud SDK
- Terraform

### バックエンド
1. 依存関係のインストール
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. AutoGluonモデルの配置
   - `backend/AutogluonModels/` にモデルを配置するか、環境変数 `MODEL_PATH` で指定してください。
3. 実行
   ```bash
   uvicorn app.main:app --reload
   ```

### フロントエンド
1. 依存関係のインストール
   ```bash
   cd frontend
   npm install
   ```
2. 実行
   ```bash
   npm run dev
   ```

### インフラ
1. Terraformの適用
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

## 環境変数
- `PROJECT_ID`: GCPプロジェクトID
- `MODEL_PATH`: AutoGluonモデルのパス
