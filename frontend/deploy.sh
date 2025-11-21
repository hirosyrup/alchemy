#!/bin/bash

# エラーが発生したら停止
set -e

echo "========================================"
echo "Deploying Frontend to Firebase Hosting..."
echo "========================================"

# 1. Build React App
echo "[1/2] Building React App..."
npm run build

# 2. Deploy to Firebase
echo "[2/2] Deploying to Firebase..."
# ユーザーがログイン済みで、プロジェクトが選択されていることを前提とする
# 初回は firebase init が必要かもしれないが、firebase.jsonがあれば deploy できる場合もある
# プロジェクト指定がない場合はエラーになるため、引数で受け取るか対話的にする

if [ -z "$PROJECT_ID" ]; then
    echo "Warning: PROJECT_ID is not set. Using default project or requiring manual selection."
    firebase deploy --only hosting
else
    firebase deploy --only hosting --project "$PROJECT_ID"
fi

echo "Deployment Complete!"
