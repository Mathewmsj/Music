#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
VENV_DIR="${BACKEND_DIR}/.venv"
REQ_FILE="${BACKEND_DIR}/requirements.txt"
REQ_STAMP="${VENV_DIR}/.requirements.sha256"

if [[ ! -d "${BACKEND_DIR}" || ! -d "${FRONTEND_DIR}" ]]; then
  echo "Error: script must run inside project root."
  exit 1
fi

ensure_backend() {
  if [[ ! -d "${VENV_DIR}" ]]; then
    echo "[backend] creating virtual env..."
    python3 -m venv "${VENV_DIR}"
  fi

  local current_hash=""
  current_hash="$(shasum -a 256 "${REQ_FILE}" | awk '{print $1}')"
  local previous_hash=""
  if [[ -f "${REQ_STAMP}" ]]; then
    previous_hash="$(cat "${REQ_STAMP}")"
  fi

  if [[ "${current_hash}" != "${previous_hash}" ]]; then
    echo "[backend] installing python deps..."
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    pip install -r "${REQ_FILE}"
    echo "${current_hash}" > "${REQ_STAMP}"
  fi

  if [[ ! -f "${BACKEND_DIR}/.env" && -f "${BACKEND_DIR}/.env.example" ]]; then
    cp "${BACKEND_DIR}/.env.example" "${BACKEND_DIR}/.env"
    echo "[backend] created backend/.env from .env.example"
  fi
}

ensure_frontend() {
  if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
    echo "[frontend] installing node deps..."
    (cd "${FRONTEND_DIR}" && npm install)
  fi
}

start_backend() {
  (
    cd "${BACKEND_DIR}"
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ) &
  BACKEND_PID=$!
  echo "[backend] started on http://127.0.0.1:8000 (pid ${BACKEND_PID})"
}

start_frontend() {
  (
    cd "${FRONTEND_DIR}"
    npm run dev
  ) &
  FRONTEND_PID=$!
  echo "[frontend] started on http://127.0.0.1:5173 (pid ${FRONTEND_PID})"
}

cleanup() {
  echo
  echo "Stopping services..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
}

trap cleanup INT TERM EXIT

ensure_backend
ensure_frontend
start_backend
start_frontend

echo
echo "Dev servers are running."
echo "Frontend: http://127.0.0.1:5173"
echo "Backend : http://127.0.0.1:8000"
echo "Press Ctrl+C to stop both."
echo

wait "${BACKEND_PID}" "${FRONTEND_PID}"
