#!/usr/bin/env bash
# =============================================================================
# check_sakura_spec.sh
# Purpose : Inspect the server environment on Sakura.ne.jp shared hosting
#           to confirm available tools for the CAE list project.
# Usage   : bash check_sakura_spec.sh 2>&1 | tee sakura_spec_report.txt
# =============================================================================

DIVIDER="============================================================"
SECTION() { echo ""; echo "$DIVIDER"; echo "  $1"; echo "$DIVIDER"; }

# ─── 1. OS & Kernel ──────────────────────────────────────────────────────────
SECTION "1. OS & Kernel"
uname -a
if [ -f /etc/os-release ]; then
  cat /etc/os-release
elif [ -f /etc/redhat-release ]; then
  cat /etc/redhat-release
fi

# ─── 2. Disk Space ───────────────────────────────────────────────────────────
SECTION "2. Disk Space (ディスク使用量)"
df -h ~
echo ""
echo "--- Home directory usage ---"
du -sh ~/ 2>/dev/null
echo ""
echo "--- Top 10 largest directories under ~ ---"
du -sh ~/*/  2>/dev/null | sort -rh | head -10

# ─── 3. Shell & User ─────────────────────────────────────────────────────────
SECTION "3. Shell & User Info"
echo "Current user : $(whoami)"
echo "Home dir     : $HOME"
echo "Shell        : $SHELL"
echo "Bash version : $BASH_VERSION"

# ─── 4. PHP ──────────────────────────────────────────────────────────────────
SECTION "4. PHP"
if command -v php &>/dev/null; then
  php --version
  echo ""
  echo "--- php.ini location ---"
  php --ini 2>/dev/null | head -5
  echo ""
  echo "--- Key PHP settings ---"
  php -r "
    echo 'max_execution_time : ' . ini_get('max_execution_time') . PHP_EOL;
    echo 'memory_limit       : ' . ini_get('memory_limit')       . PHP_EOL;
    echo 'allow_url_fopen    : ' . ini_get('allow_url_fopen')    . PHP_EOL;
    echo 'curl extension     : ' . (extension_loaded('curl')    ? 'YES' : 'NO') . PHP_EOL;
    echo 'json extension     : ' . (extension_loaded('json')    ? 'YES' : 'NO') . PHP_EOL;
    echo 'mbstring extension : ' . (extension_loaded('mbstring')? 'YES' : 'NO') . PHP_EOL;
  "
else
  echo "PHP : NOT FOUND"
fi

# ─── 5. Node.js / npm ────────────────────────────────────────────────────────
SECTION "5. Node.js / npm / npx"
for cmd in node npm npx; do
  if command -v $cmd &>/dev/null; then
    echo "$cmd : $($cmd --version)"
  else
    echo "$cmd : NOT FOUND"
  fi
done

# ─── 6. Python ───────────────────────────────────────────────────────────────
SECTION "6. Python"
for cmd in python3 python; do
  if command -v $cmd &>/dev/null; then
    echo "$cmd : $($cmd --version 2>&1)"
  else
    echo "$cmd : NOT FOUND"
  fi
done
if command -v pip3 &>/dev/null; then
  echo "pip3 : $(pip3 --version 2>&1)"
fi

# ─── 7. Perl / Ruby ──────────────────────────────────────────────────────────
SECTION "7. Perl / Ruby"
for cmd in perl ruby; do
  if command -v $cmd &>/dev/null; then
    echo "$cmd : $($cmd --version 2>&1 | head -1)"
  else
    echo "$cmd : NOT FOUND"
  fi
done

# ─── 8. Crontab ──────────────────────────────────────────────────────────────
SECTION "8. Crontab"
if command -v crontab &>/dev/null; then
  echo "crontab binary : $(which crontab)"
  echo ""
  echo "--- Current crontab entries ---"
  crontab -l 2>/dev/null || echo "(no crontab for $(whoami))"
else
  echo "crontab : NOT FOUND"
fi

# ─── 9. Network Tools ────────────────────────────────────────────────────────
SECTION "9. Network Tools (for fetching CAE sites)"
for cmd in curl wget; do
  if command -v $cmd &>/dev/null; then
    echo "$cmd : $($cmd --version 2>&1 | head -1)"
  else
    echo "$cmd : NOT FOUND"
  fi
done

echo ""
echo "--- Outbound HTTP test (curl to example.com) ---"
if command -v curl &>/dev/null; then
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://example.com)
  echo "HTTP response code : $HTTP_CODE"
  if [ "$HTTP_CODE" = "200" ]; then
    echo "Outbound HTTPS : OK ✓"
  else
    echo "Outbound HTTPS : FAILED or BLOCKED"
  fi
fi

# ─── 10. Git ─────────────────────────────────────────────────────────────────
SECTION "10. Git"
if command -v git &>/dev/null; then
  git --version
else
  echo "git : NOT FOUND"
fi

# ─── 11. File Permissions & Web Root ─────────────────────────────────────────
SECTION "11. Directory Structure & Web Root"
echo "--- Listing home directory ---"
ls -la ~/

echo ""
echo "--- Likely web roots (さくら公開ディレクトリ) ---"
for dir in ~/www ~/public_html ~/html ~/web; do
  if [ -d "$dir" ]; then
    echo "FOUND : $dir"
    ls -la "$dir" | head -15
  else
    echo "NOT FOUND : $dir"
  fi
done

# ─── 12. GRAV CMS Detection ──────────────────────────────────────────────────
SECTION "12. GRAV CMS Detection"
GRAV_PATHS=(
  ~/www
  ~/public_html
  ~/html
)
GRAV_FOUND=false
for base in "${GRAV_PATHS[@]}"; do
  if [ -f "$base/system/src/Grav/Common/Grav.php" ]; then
    echo "GRAV found at : $base"
    echo "--- GRAV version ---"
    grep -r "VERSION" "$base/system/defines.php" 2>/dev/null | head -3
    GRAV_FOUND=true
    break
  fi
done
if [ "$GRAV_FOUND" = false ]; then
  echo "GRAV core file not found in expected paths."
  echo "Try: find ~/ -name 'Grav.php' 2>/dev/null"
fi

# ─── 13. Available Cron Script Locations ─────────────────────────────────────
SECTION "13. Recommended Cron Script Location"
echo "Suggested location for cron scripts:"
echo "  ~/cron/update_cae_data.sh"
echo ""
echo "--- Check if ~/cron exists ---"
if [ -d ~/cron ]; then
  echo "EXISTS : ~/cron"
  ls -la ~/cron/
else
  echo "NOT EXISTS : ~/cron  (will need to create: mkdir ~/cron)"
fi

# ─── 14. Memory & Process ────────────────────────────────────────────────────
SECTION "14. Memory & Process Info"
if command -v free &>/dev/null; then
  free -h
fi
echo ""
echo "--- Process count for current user ---"
ps aux 2>/dev/null | grep "^$(whoami)" | wc -l || echo "ps not available"

# ─── 15. Environment PATH ────────────────────────────────────────────────────
SECTION "15. PATH"
echo "$PATH" | tr ':' '\n'

# ─── Summary ─────────────────────────────────────────────────────────────────
SECTION "SUMMARY — Items Needed for CAE Project"
echo ""
printf "%-30s %s\n" "Item" "Required / Status"
printf "%-30s %s\n" "------------------------------" "-------------------"

check() {
  command -v "$1" &>/dev/null && echo "OK ✓" || echo "NOT FOUND ✗"
}

printf "%-30s %s\n" "curl (fetch CAE sites)"      "$(check curl)"
printf "%-30s %s\n" "crontab (scheduled fetch)"   "$(check crontab)"
printf "%-30s %s\n" "php (data processing)"       "$(check php)"
printf "%-30s %s\n" "node (TypeScript build)"     "$(check node)"
printf "%-30s %s\n" "git (deploy helper)"         "$(check git)"
printf "%-30s %s\n" "python3 (optional scraping)" "$(check python3)"

echo ""
echo "Report saved to: sakura_spec_report.txt  (if run with tee)"
echo "Run timestamp  : $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
echo "$DIVIDER"
echo "  Done. Review the report above and share with Claude."
echo "$DIVIDER"
