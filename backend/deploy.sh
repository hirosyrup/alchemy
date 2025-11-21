#!/bin/bash

# エラーが発生したら停止
set -e

# 環境変数のチェック
if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID environment variable is not set."
    echo "Usage: export PROJECT_ID=your-project-id"
    exit 1
fi

REGION="asia-northeast1"
REPO_NAME="alchemy-repo"
IMAGE_NAME="backend"
SERVICE_NAME="alchemy-worker"

echo "========================================"
echo "Deploying Backend to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "========================================"

# 1. Build and Push Image to Artifact Registry
echo "[1/3] Building and Pushing Docker Image..."
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:latest" .

# 2. Deploy to Cloud Run
echo "[2/3] Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:latest" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars PROJECT_ID="$PROJECT_ID"

echo "[3/3] Deployment Complete!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')"
