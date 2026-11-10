#!/usr/bin/env bash
set -euo pipefail

# Resolve paths relative to this script so it works from any current directory.
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mlflow_bin="$project_dir/.venv/bin/mlflow"
data_dir="$project_dir/mlflow-data"

if [[ ! -x "$mlflow_bin" ]]; then
  printf 'MLflow is missing from %s\n' "$mlflow_bin" >&2
  printf 'Create or activate the project .venv and install MLflow first.\n' >&2
  exit 1
fi

mkdir -p "$data_dir"
cd "$data_dir"

printf 'Starting MLflow at http://127.0.0.1:5000\n'
printf 'Database: %s/mlflow.db\n' "$data_dir"
printf 'Artifacts: %s/mlartifacts\n' "$data_dir"
printf 'Press Ctrl+C to stop the server.\n'

exec "$mlflow_bin" server \
  --host 127.0.0.1 \
  --port 5000 \
  --backend-store-uri sqlite:///mlflow.db \
  --artifacts-destination ./mlartifacts
