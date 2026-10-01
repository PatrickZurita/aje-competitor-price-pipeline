#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
build_dir="$project_dir/build"

rm -rf "$build_dir"
mkdir -p "$build_dir"

python3 -m pip install \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.13 \
  --only-binary=:all: \
  --target "$build_dir" \
  --requirement "$project_dir/requirements.txt"

cp -R "$project_dir/src/." "$build_dir/"
