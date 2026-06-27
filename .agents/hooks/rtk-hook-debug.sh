#!/bin/bash
# ============================================================
# Hook de DIAGNÓSTICO — não reescreve nada, só captura o payload
# real do PreToolUse pra confirmarmos o formato exato antes de
# construir o hook de reescrita do rtk.
#
# Sempre permite o comando original passar (fail-open), nunca
# bloqueia nada — é só um espião temporário.
# ============================================================

INPUT="$(cat)"

{
    echo "---- $(date '+%Y-%m-%d %H:%M:%S') ----"
    echo "$INPUT"
    echo ""
} >> /tmp/antigravity-hook-debug.log

echo '{"permissionDecision": "allow"}'
exit 0
