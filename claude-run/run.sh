#!/usr/bin/env bash
# One logged, headless Claude Code run against SolidCraft 0.22.0 (tipping lab, SolidCraft for Beginners #7).
#   bash claude-run/run.sh viewer|outcome RUN_ID
# The run gets a fresh copy of part 1's stand design in its own folder (/lab/work in the container) and a prompt:
#   viewer : the viewer's own words, made into a request (phone's centre of mass over the middle of the base);
#   outcome: "make sure it doesn't tip when printed with the 0.20mm SPEED preset", no method given.
# The phone is given in both (150 x 72 x 9 mm, 210 g). The trap (the print is about a quarter of the solid weight)
# is not named. Claude Code --stdio--> docker run -i ... [mcp_log_proxy.py --watchdog 180 --stdio--> solidcraft-cli mcp];
# only the solidcraft tools. From solidcraft-flatiron-lab/claude-run, plus:
#   1. the SHARED ledger of the AI-CAD set labs ($20 total; claude-run/budget.py), checked before the run;
#   2. cost survives a kill: an empty claude-output.json is logged at the run's full cap ("killed-floor");
#   3. sealed memory: no user/ancestor CLAUDE.md (claudeMdExcludes), auto memory off (setting + env), only project/local
#      settings, no session persistence; the proxy's watchdog writes HANG after 180 s without a reply.
set -euo pipefail
ARM=$1; RUN=$2
cd "$(dirname "$0")/.."
LAB="$(pwd -W 2>/dev/null || pwd)"
OUT=out/runs/$ARM-$RUN
LEDGER="${LEDGER:-$LAB/../ai-cad-set-BUDGET.tsv}"
MODEL="${MODEL:-claude-sonnet-5-5}"
BUDGET="${BUDGET:-1.50}"
python claude-run/budget.py check "$LEDGER" "$BUDGET" || { echo "BUDGET STOP"; exit 2; }
[ -e "$OUT/run-meta.json" ] && { echo "refusing to overwrite $OUT"; exit 3; }
mkdir -p "$OUT/work"
cp data/part1-stand.solidcraft "$OUT/work/stand.solidcraft"
NAME="tipping-$ARM-$RUN-$$"

cat > "$OUT/mcp-config.json" <<JSON
{"mcpServers": {"solidcraft": {"command": "docker", "args": ["run", "-i", "--rm", "--name", "$NAME", "-v", "$LAB/proxy:/proxy:ro", "-v", "$LAB/$OUT/work:/lab/work", "-v", "$LAB/$OUT:/lab/log", "solidcraft-tipping-lab:0.22.0", "python3", "/proxy/mcp_log_proxy.py", "--log", "/lab/log/transcript.jsonl", "--png-dir", "/lab/log", "--watchdog", "180", "--", "solidcraft-cli", "mcp", "--allow-path", "/lab/work"]}}}
JSON

PHONE="The phone is 150 x 72 x 9 mm and weighs 210 g; it stands in the slot on its long edge (portrait)."
DONE="Keep it a phone stand that holds this phone. When you are done, save the design to /lab/work/stand.solidcraft and export only the stand (not any phone body you may add to check it) as STL to /lab/work/stand.stl. Then report what you changed and the numbers you relied on."
case "$ARM" in
  viewer)
    PROMPT="Use the solidcraft MCP tools. /lab/work/stand.solidcraft is a 3D-printable phone stand: a phone stands in its slot, leaning back. A viewer wrote: \"It looks like if you put a phone in that slot it's likely to tip over. If the prompt stated that the holder had to center the center of mass of a phone over the middle of the base when angled back could claude figure that out?\" So: change the design so that the center of mass of a phone in the slot sits over the middle of the base. $PHONE $DONE" ;;
  outcome)
    PROMPT="Use the solidcraft MCP tools. /lab/work/stand.solidcraft is a 3D-printable phone stand: a phone stands in its slot, leaning back. A viewer thinks it will tip over with a phone in it. Make sure it does not tip over with this phone when the stand is 3D printed with PrusaSlicer's 0.20mm SPEED preset (2 walls, 15% infill, PLA). $PHONE $DONE" ;;
  *) echo "arm: viewer|outcome"; exit 4 ;;
esac
printf '%s\n' "$PROMPT" > "$OUT/prompt.txt"

T0=$(date +%s)
set +e
MSYS_NO_PATHCONV=1 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 timeout 900 "${CLAUDE:-claude}" -p "$PROMPT" --model "$MODEL" \
  --mcp-config "$OUT/mcp-config.json" --strict-mcp-config \
  --tools "" --allowedTools "mcp__solidcraft__*" --permission-mode dontAsk \
  --max-budget-usd "$BUDGET" --no-session-persistence \
  --setting-sources project,local --settings '{"claudeMdExcludes":["**/CLAUDE.md","**/CLAUDE.local.md"],"autoMemoryEnabled":false}' \
  --output-format json < /dev/null > "$OUT/claude-output.json" &
PID=$!
HUNG=0
while kill -0 "$PID" 2>/dev/null; do
  if grep -q '"HANG"' "$OUT/transcript.jsonl" 2>/dev/null; then
    HUNG=1
    WP=$(cat /proc/$PID/winpid 2>/dev/null || true)
    kill "$PID" 2>/dev/null; [ -n "$WP" ] && taskkill //F //T //PID "$WP" >/dev/null 2>&1
    docker kill "$NAME" >/dev/null 2>&1
    break
  fi
  sleep 3
done
wait "$PID"; RC=$?
set -e
docker kill "$NAME" >/dev/null 2>&1 || true
# no host path in the saved config (the lab may be published)
sed -i "s#$LAB#\$LAB#g" "$OUT/mcp-config.json"
COST=$(python -c "import json,sys
try: print(json.load(open(sys.argv[1]))['total_cost_usd'])
except Exception: print('')" "$OUT/claude-output.json")
python claude-run/budget.py record "$LEDGER" "tipping-$ARM-$RUN" "$COST" "$BUDGET" tipping
echo "{\"arm\": \"$ARM\", \"run\": \"$RUN\", \"model\": \"$MODEL\", \"budget_usd\": $BUDGET, \"exit\": $RC, \"hang_killed\": $HUNG, \"wall_s\": $(( $(date +%s) - T0 )), \"claude_version\": \"$(${CLAUDE:-claude} --version | head -1)\", \"solidcraft\": \"0.22.0\"}" > "$OUT/run-meta.json"
cat "$OUT/run-meta.json"; echo "cost ${COST:-killed (counted at cap)}"
