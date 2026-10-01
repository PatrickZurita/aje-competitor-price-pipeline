#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
profile_name="${1:-aje-test}"
aws_region="${2:-sa-east-1}"

aws --version
aws sts get-caller-identity --profile "$profile_name" --region "$aws_region"
"$project_dir/scripts/build_lambda_package.sh"
PYTHONPATH="$project_dir/src:$project_dir/build" \
  python3 -m unittest discover -s "$project_dir/tests" -v
aws cloudformation validate-template \
  --template-body "file://$project_dir/infra/template.yaml" \
  --profile "$profile_name" --region "$aws_region"
printf '%s\n' 'Preflight completed successfully.'
