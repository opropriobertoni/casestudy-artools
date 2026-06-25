---
name: tier-classifier
description: >
  Use esta Skill sempre que precisar classificar um design-system.html (ou
  HTML de referência similar) na taxonomia Five-Tier — Foundations, Tokens,
  Atoms, Molecules, Organisms — gerando um tier-map.json estruturado. Ative
  para termos como "classificar design system", "mapear componentes em
  tiers", "Five-Tier audit", "que tier é esse elemento", "organizar atoms
  molecules organisms", ou quando for necessário decidir em qual pasta de
  app/design-system/ um componente HTML deve residir. Esta Skill é o ponto
  de entrada obrigatório (Fase 1) do Workflow design-system-pipeline —
  invoque-a antes de qualquer extração de tokens ou geração de Component
  Specs.
---

# Tier Classifier

## Quando usar esta Skill

- O usuário pede para classificar, mapear ou organizar um `design-system.html`
  na taxonomia Five-Tier.
- O Workflow `design-system-pipeline` chega à Fase 1.
- O usuário pergunta em qual tier (Foundations/Tokens/Atoms/Molecules/Organisms)
  um elemento específico deve residir.

## Quando NÃO usar esta Skill

- Não existe ainda `design-system.html` no diretório de referência (Fase 0
  manual via prompts Reference Cleaned HTML → Extract HTML Design System não
  foi executada). Direcione o usuário para rodar os prompts manuais primeiro.
- O pedido é extrair valores de cor/tipografia/spacing — isso é
  responsabilidade da Skill `token-pipeline-setup` (Fase 2).
- O pedido é gerar Component Specs individuais — isso é responsabilidade da
  Skill `component-spec-generator` (Fase 3).
- O pedido é auditar divergência (*drift*) entre um DS já estruturado e uma
  fonte de verdade externa (Figma/legado) — isso é responsabilidade da Skill
  `design-system-audit`, não desta.

## Regras de Arquitetura

| Tier | Critério de Classificação |
|---|---|
| `foundations` | Prosa de princípios globais — tom, acessibilidade, proibições estéticas. Não é elemento HTML, é regra textual. |
| `tokens` | Valor determinístico bruto (cor, espaçamento, tipografia) sem comportamento interativo próprio. |
| `atoms` | Elemento indivisível com comportamento próprio (botão, input, badge). Decompor destrói a função. |
| `molecules` | 2+ atoms combinados com responsabilidade única conjunta (campo de formulário: label + input + validação). |
| `organisms` | Zona funcional ampla compondo múltiplas molecules/atoms — geralmente uma seção inteira (header, footer, hero, tabela). |

- Cada elemento recebe **exatamente um** tier. Nunca atribuir dois tiers ao
  mesmo elemento — isso indica que o elemento precisa ser decomposto em
  partes menores antes de classificar.
- O script `parse_html.py` **nunca** decide tiers. Ele só extrai estrutura
  (tag, id, classes, comentário de seção, preview de texto). A decisão
  semântica é sempre do agente — preserva responsabilidade única entre
  script (determinístico) e Skill (interpretativa).
- Em caso de ambiguidade entre dois tiers, perguntar ao usuário. Nunca
  assumir — uma classificação errada na Fase 1 contamina as Fases 2 e 3
  inteiras do Workflow.

## Fluxo de Execução

1. Confirmar que `design-system.html` existe no diretório de referência.
   Se não existir, parar e informar o usuário.
2. Executar `scripts/parse_html.py --input design-system.html --output candidates.json`.
3. Ler `candidates.json`.
4. Para cada candidato, classificar em exatamente um tier usando a tabela de
   Regras de Arquitetura acima.
5. Descartar candidatos que sejam ruído estrutural puro (wrappers sem função
   visual ou interativa própria) — registrar a decisão na justificativa.
6. Escrever `tier-map.json`: lista de objetos `{elemento, tier, justificativa}`,
   com `justificativa` em uma linha.
7. Apresentar `tier-map.json` ao usuário e parar. Não prosseguir para a Fase
   2 do Workflow sem aprovação explícita.

## Referências Externas

- `scripts/parse_html.py` — script Python (stdlib puro, sem dependências
  externas). Execute primeiro com `--help` para confirmar a assinatura
  exata antes de invocar. Tratar como caixa-preta: não ler nem modificar o
  código interno do script.

## Exemplos

**Input** (entrada em `candidates.json`):
```json
{"tag": "button", "id": null, "classes": ["btn", "btn-primary"],
 "section_comment": "hero", "text_preview": "Começar agora"}
```

**Output** (entrada correspondente em `tier-map.json`):
```json
{"elemento": "button.btn-primary (CTA da seção hero)",
 "tier": "atoms",
 "justificativa": "Unidade interativa indivisível, sem composição de outros elementos."}
```

**Input:**
```json
{"tag": "header", "id": "main-nav", "classes": ["site-header"],
 "section_comment": "hero", "text_preview": ""}
```

**Output:**
```json
{"elemento": "header#main-nav",
 "tier": "organisms",
 "justificativa": "Zona funcional de navegação global, compõe múltiplos atoms (logo, links)."}
```

## Checklist de Validação

- [ ] Responsabilidade única confirmada? (classifica — não extrai tokens, não gera specs)
- [ ] Scripts externos referenciados com `--help`?
- [ ] Ausência de comportamentos ambíguos? (regra de perguntar em caso de dúvida está explícita)
- [ ] Principle of Lack of Surprise respeitado?
