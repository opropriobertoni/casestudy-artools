---
name: {{name}}
tier: {{tier}}
status: proposed
---

# {{Component Display Name}}

## Origin
- Original selector: `{{seletor_original}}`
- Source file: `{{arquivo_fonte}}`
- Source naming convention: {{convencao_origem}} (e.g., BEM, utility, ad-hoc)

## Block (CUBE CSS)
Prescribed target class: `.{{classe_block_cube}}`

| Property | Value | Referenced Token |
|---|---|---|
{{tabela_propriedades_block}}

> `margin*` properties from the source CSS were excluded from this table — under CUBE CSS, external spacing is the responsibility of Composition, never of the Block (Rule 14).

## Native States

| State | Exists in reference? | Color Relation (Rule 35) |
|---|---|---|
| `:hover` | {{hover_existe}} | {{hover_relacao}} |
| `:focus` | {{focus_existe}} | {{focus_relacao}} |
| `:active` | {{active_existe}} | {{active_relacao}} |
| `:disabled` | {{disabled_existe}} | native (HTML attribute, not class) |

## Exceptions (variants and programmatic states — Rule 15)

| Source Class | Type | Target CUBE Exception |
|---|---|---|
{{tabela_exceptions}}

## Referenced Tokens
{{lista_tokens_referenciados}}

## Target Markup

```html
{{markup_alvo}}
<!-- {{comentario_agrupamento_bracket}} -->
```

## Violations Detected
{{lista_violacoes}}
