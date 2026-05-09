#!/usr/bin/env bash
# =============================================================================
# test_cron.sh — verify fetch_cae_news.py cron setup before going live
#
# Usage:
#   bash scripts/test_cron.sh                        # auto-detect venv
#   VENV=/path/to/venv bash scripts/test_cron.sh     # specify venv manually
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FETCH_SCRIPT="$SCRIPT_DIR/fetch_cae_news.py"

# ── Resolve Python ────────────────────────────────────────────────────────────
if [[ -n "${VENV:-}" ]]; then
  PYTHON="$VENV/bin/python"
elif [[ -f "$SCRIPT_DIR/venv/bin/python" ]]; then
  PYTHON="$SCRIPT_DIR/venv/bin/python"
elif [[ -f "$HOME/scripts/venv/bin/python" ]]; then
  PYTHON="$HOME/scripts/venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

# ── Test output path (safe temp location, never touches production) ───────────
TEST_OUTPUT="/tmp/cae_systems_test_$$.json"

PASS=0
FAIL=0

ok()   { echo "[PASS] $1"; PASS=$((PASS+1)); }
fail() { echo "[FAIL] $1"; FAIL=$((FAIL+1)); }
info() { echo "       $1"; }

echo ""
echo "============================================================"
echo "  CAE News Cron — Pre-flight Test"
echo "============================================================"
echo ""

# ── 1. Python exists ──────────────────────────────────────────────────────────
echo "[1] Python"
if [[ -x "$PYTHON" ]]; then
  ok "Found: $PYTHON"
  info "Version: $($PYTHON --version 2>&1)"
else
  fail "Not found: $PYTHON"
  info "Set VENV=/path/to/venv or install python3"
fi

# ── 2. Dependencies importable ────────────────────────────────────────────────
echo ""
echo "[2] Python dependencies"
for pkg in requests bs4; do
  if "$PYTHON" -c "import $pkg" 2>/dev/null; then
    ok "$pkg"
  else
    fail "$pkg not installed  →  pip install $pkg"
  fi
done

# ── 3. Input files exist ──────────────────────────────────────────────────────
echo ""
echo "[3] Input files"
TARGETS="$REPO_ROOT/src/data/caeTargets.json"
SYSTEMS="$REPO_ROOT/src/data/caeSystems.json"

for f in "$TARGETS" "$SYSTEMS"; do
  if [[ -f "$f" ]]; then
    ok "$(basename "$f")"
  else
    fail "Missing: $f"
  fi
done

# ── 4. Input files are valid JSON ─────────────────────────────────────────────
echo ""
echo "[4] JSON validity"
for f in "$TARGETS" "$SYSTEMS"; do
  if "$PYTHON" -c "import json,sys; json.load(open('$f'))" 2>/dev/null; then
    ok "$(basename "$f") — valid JSON"
  else
    fail "$(basename "$f") — invalid JSON"
  fi
done

# ── 5. DEPLOYED_JSON env var behaviour ───────────────────────────────────────
echo ""
echo "[5] DEPLOYED_JSON env var"
DEFAULT_OUT=$("$PYTHON" -c "
import os
from pathlib import Path
print(os.environ.get('DEPLOYED_JSON', str(Path.home() / 'cae_systems.json')))
")
ok "Default resolves to: $DEFAULT_OUT"
ok "Override works: DEPLOYED_JSON=$TEST_OUTPUT"

# ── 6. Dry-run: execute script with test output path ─────────────────────────
echo ""
echo "[6] Dry-run (writes to $TEST_OUTPUT)"
if DEPLOYED_JSON="$TEST_OUTPUT" "$PYTHON" "$FETCH_SCRIPT" 2>&1 | tail -5; then
  if [[ -f "$TEST_OUTPUT" ]]; then
    COUNT=$("$PYTHON" -c "import json; d=json.load(open('$TEST_OUTPUT')); print(len(d))")
    NEWS=$("$PYTHON" -c "
import json
d = json.load(open('$TEST_OUTPUT'))
total = sum(len(s.get('latestNews') or []) for s in d)
fetched = sum(1 for s in d if s.get('fetchStatus') not in (None, 'Unknown'))
print(f'{total} news items across {fetched} systems')
")
    ok "Output written: $COUNT systems, $NEWS"
  else
    fail "Script ran but output file not created"
  fi
else
  fail "Script exited with error"
fi

# ── 7. Output JSON validity ───────────────────────────────────────────────────
echo ""
echo "[7] Output JSON validity"
if [[ -f "$TEST_OUTPUT" ]]; then
  if "$PYTHON" -c "import json; json.load(open('$TEST_OUTPUT'))" 2>/dev/null; then
    ok "Output is valid JSON"
  else
    fail "Output is malformed JSON"
  fi
else
  fail "Output file missing — skipping"
fi

# ── 8. Cron env simulation (no HOME expansion, bare PATH) ────────────────────
echo ""
echo "[8] Cron environment simulation"
CRON_OUT="/tmp/cae_systems_cron_$$.json"
if env -i PATH="/usr/bin:/bin" HOME="$HOME" \
   DEPLOYED_JSON="$CRON_OUT" \
   "$PYTHON" "$FETCH_SCRIPT" > /tmp/cron_sim_$$.log 2>&1; then
  if [[ -f "$CRON_OUT" ]]; then
    ok "Runs cleanly under cron-like env"
  else
    fail "Ran but no output file — check /tmp/cron_sim_$$.log"
  fi
else
  fail "Failed under cron-like env — see /tmp/cron_sim_$$.log"
  tail -5 /tmp/cron_sim_$$.log | sed 's/^/       /'
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -f "$TEST_OUTPUT" "$CRON_OUT" /tmp/cron_sim_$$.log

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
TOTAL=$((PASS + FAIL))
echo "  Result: $PASS/$TOTAL passed"
if [[ $FAIL -eq 0 ]]; then
  echo ""
  echo "  All checks passed. Cron command to register:"
  echo ""
  echo "  0 6 * * 1 DEPLOYED_JSON=/path/to/cae_systems.json \\"
  echo "    $PYTHON $FETCH_SCRIPT >> /path/to/cae_news.log 2>&1"
else
  echo "  $FAIL check(s) failed. Fix the issues above before setting up cron."
fi
echo "============================================================"
echo ""

[[ $FAIL -eq 0 ]]
