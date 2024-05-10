#!/bin/bash
gcloud auth activate-service-account ${11} --key-file=${10} --project=$1
gcloud run deploy $2 --image $3 --platform managed --region $4 --no-allow-unauthenticated --memory $7 --port=${12} --update-env-vars gcs_bucket=$5,gcs_subdir=$6,MODEL_NAME=$8,MODEL_BASE_PATH=$9 
