#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  printf '%s\n' 'Usage: ./scripts/deploy.sh <artifact-bucket> <google-oauth-secret-arn> [profile] [region]'
  exit 2
fi

artifact_bucket="$1"
google_secret_arn="$2"
profile_name="${3:-aje-test}"
aws_region="${4:-sa-east-1}"
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
packaged_template="$project_dir/packaged.yaml"

"$project_dir/scripts/preflight.sh" "$profile_name" "$aws_region"
aws cloudformation package \
  --template-file "$project_dir/infra/template.yaml" \
  --s3-bucket "$artifact_bucket" \
  --output-template-file "$packaged_template" \
  --profile "$profile_name" --region "$aws_region"
aws cloudformation deploy \
  --template-file "$packaged_template" \
  --stack-name aje-competitor-prices \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides "GoogleOAuthSecretArn=$google_secret_arn" \
  --no-fail-on-empty-changeset \
  --profile "$profile_name" --region "$aws_region"
aws cloudformation describe-stacks \
  --stack-name aje-competitor-prices \
  --profile "$profile_name" --region "$aws_region" \
  --query 'Stacks[0].Outputs' --output table
