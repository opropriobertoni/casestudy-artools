#!/bin/bash
# ============================================================
# Workflow Global Antigravity — Setup de Otimização de Tokens
# Ferramentas: rtk (nativo) · caveman (Rule always-on, não-oficial)
# headroom: DEFERIDO — sem integração nativa Antigravity confirmada;
#           o ganho principal (compressão de output de shell) já
#           está coberto pelo rtk, que usa esse binário internamente.
#
# Execução determinística: para no primeiro erro (set -e), não
# pergunta nada, não tenta "adivinhar" — se algo falhar, falha alto
# e visível.
# ============================================================
set -euo pipefail

PROJECT_ROOT="$(pwd)"
RULES_DIR="$PROJECT_ROOT/.agents/rules"
mkdir -p "$RULES_DIR"

echo "==> Workflow de otimização de tokens — projeto: $PROJECT_ROOT"
echo ""

# ------------------------------------------------------------
# FASE 1 + 3 — rtk: detectar e instalar se ausente
# ------------------------------------------------------------
if ! command -v rtk &> /dev/null; then
    echo "[rtk] não encontrado. Instalando..."
    curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"

    # Garante PATH persistente em novos terminais (idempotente).
    # NOTA: isto só afeta terminais abertos DEPOIS deste ponto — não
    # existe forma confiável de propagar PATH/alias pro shell que
    # chamou este script (limitação de processo filho vs. pai).
    if ! grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo "[PATH] ~/.local/bin adicionado ao .bashrc (efetivo em novos terminais)"
    fi
else
    echo "[rtk] já instalado: $(rtk --version)"
fi

if ! command -v rtk &> /dev/null; then
    echo "[ERRO] rtk não ficou disponível no PATH após instalação. Abortando." >&2
    exit 1
fi

# ------------------------------------------------------------
# FASE 2 — rtk: configurar ESTE projeto para Antigravity
# Gera .agents/rules/antigravity-rtk-rules.md (escopo: projeto)
# ------------------------------------------------------------
echo ""
echo "[rtk] configurando integração com Antigravity neste projeto..."
rtk init --agent antigravity
rtk init --show

# ------------------------------------------------------------
# FASE 2 — caveman: Rule always-on (engenharia não-oficial)
# Fonte única do repositório: src/rules/caveman-activate.md
# Sempre busca a versão mais recente e sobrescreve — mantém a
# regra sincronizada com upstream (idempotente: mesmo resultado
# a cada execução, sem duplicar nada).
# ------------------------------------------------------------
echo ""
echo "[caveman] sincronizando Rule always-on..."
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/src/rules/caveman-activate.md \
    -o "$RULES_DIR/caveman-rules.md"

if [ ! -s "$RULES_DIR/caveman-rules.md" ]; then
    echo "[ERRO] falha ao baixar a regra do caveman. Abortando." >&2
    exit 1
fi
echo "[caveman] regra gravada em: $RULES_DIR/caveman-rules.md"

# ------------------------------------------------------------
# headroom — deferido (ver cabeçalho do script)
# ------------------------------------------------------------
echo ""
echo "[headroom] DEFERIDO neste Workflow — ver nota no topo do arquivo."

# ------------------------------------------------------------
# FASE 4 — verificação final
# ------------------------------------------------------------
echo ""
echo "==> Status final"
echo "rtk:      $(rtk --version)"
if [ -f "$RULES_DIR/antigravity-rtk-rules.md" ]; then
    echo "          rule .................. OK"
else
    echo "          rule .................. AUSENTE (verifique 'rtk init --agent antigravity')"
fi
if [ -f "$RULES_DIR/caveman-rules.md" ]; then
    echo "caveman:  rule .................. OK"
else
    echo "caveman:  rule .................. AUSENTE"
fi
echo "headroom: deferido (não configurado neste projeto)"
echo ""
echo "Workflow concluído."
