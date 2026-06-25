---
title: Design System Pipeline
description: Orquestra classificação Five-Tier, extração de Design Tokens e geração de Component Specs a partir de um design-system.html já extraído (Fase 0 manual).
---

# Design System Pipeline

## Pré-condição (Fase 0 — manual, fora do Antigravity)
Antes de invocar este Workflow, confirme que já existem no diretório de referência:
- `design-system.html` (output do prompt Extract HTML Design System)
- `STACK.md` (output do prompt Reference Cleaned HTML)
- `assets/css/`, `assets/js/`, `assets/images/svg/` já extraídos

Se algum destes não existir: PARAR e instruir o usuário a rodar os prompts Reference Cleaned HTML → Extract HTML Design System manualmente primeiro. Não tentar substituir essa etapa.

---

## Fase 1 — Classificação Five-Tier
1. Carregar a Skill `tier-classifier`.
2. Ler `design-system.html` seção por seção.
3. Classificar cada elemento em exatamente um tier: `foundations`, `tokens`, `atoms`, `molecules`, `organisms`.
4. Escrever `tier-map.json`: lista de `{elemento, tier, justificativa}` (justificativa em uma linha, sem prosa adicional).
5. PARAR. Apresentar `tier-map.json` ao usuário.
6. NÃO prosseguir para a Fase 2 sem aprovação explícita.
7. Em caso de ambiguidade entre dois tiers: perguntar ao usuário. NUNCA assumir.

---

## Fase 2 — Extração de Design Tokens
1. Carregar a Skill `token-pipeline-setup`.
2. Usar apenas os elementos aprovados como `tokens` no `tier-map.json`.
3. Extrair cor, tipografia e spacing do CSS original (`assets/css/`).
4. Escrever `app/design-system/tokens.json` em conformidade DTCG (`$value`, `$type`, `$description`, aliasing onde aplicável).
5. Rodar Style Dictionary v4 (`convertToDTCG` se houver tokens legados misturados) para gerar `app/design-system/tokens.css`.
6. PARAR. Apresentar diff de `tokens.json` e `tokens.css`.
7. NÃO prosseguir para a Fase 3 sem aprovação explícita.

---

## Fase 3 — Geração de Component Specs
1. Carregar a Skill `component-spec-generator`.
2. Para cada elemento classificado como `atoms`, `molecules` ou `organisms`:
   - Gerar spec em `app/design-system/specs/<tier>/<nome>.md`.
   - Incluir estados: `default`, `hover`, `active`, `focus`, `disabled` — apenas os que existem na referência original.
   - Limitar cada spec a 2–5KB.
   - YAML Frontmatter: `name`, `tier`, `status: proposed`.
3. PROIBIDO incluir código `<template>` completo ou tokens transcritos dentro do spec — usar apenas referência (`$ref`) ao `tokens.json`.
4. PARAR. Apresentar lista de specs gerados.

---

## Fase 4 — Consolidação do DESIGN.md
1. Sem Skill dedicada. Executar seguindo a Rule `design-system-architecture.md`.
2. Compilar YAML Frontmatter (propriedades semânticas + hexadecimais brutos) seguido de prosa de Foundations (Voice & Tone, acessibilidade, proibições estéticas).
3. Escrever `app/design-system/DESIGN.md`.
4. Apresentar resumo final: contagem de tokens, atoms, molecules, organisms gerados.

---

## Regras Transversais
- Toda PARADA exige aprovação explícita do usuário antes de prosseguir para a fase seguinte.
- Nomenclatura de classes, atributos e valores DEVE ser extraída literalmente do `design-system.html`. NUNCA inventar ou aproximar.
- Se o usuário rejeitar uma classificação na Fase 1, corrigir `tier-map.json` e repetir a aprovação antes de continuar.
