# Estado do projeto — onde paramos

Atualize este arquivo no fim de cada sessão: substitua "Última sessão" e "Próximo passo", mantenha
o resto curto. Histórico longo vai para o git, não para cá.

## Última sessão (22/11/2026)

- Revisão do motor de preço: 9 erros confirmados corrigidos (`5ac0a1f`), 391 testes passando.
  Relatório da revisão com mais 10 erros "possíveis" ainda não verificados (tarefa P-08).
- Planilha de controle criada e roteiro com metas M0–M8 gravado
  (`docs/superpowers/plans/2026-11-22-roteiro.md`).
- Cérebro externo criado: `CLAUDE.md`, este arquivo e `docs/DECISOES.md`.
- PR #4 (rascunho) atualizado: https://github.com/allan01fr/allan01fr/pull/4

## Meta atual

**M0 — Precificação v1 em uso real**, de 23/11 a 06/12/2026.

## Próximo passo

- Claude, sem depender do Allan: P-08 (verificar os 10 erros possíveis), P-09 (código da série
  INCC-M no Banco Central), P-10 (tabela da aba Preço corta a coluna de margem).
- Allan: P-01 custo/h, P-02 regime tributário com o contador, P-04 PDF da CEHOP e tabelas
  EMOP/SINAPI-RJ/CUB, P-06 regras de ART com o CREA-RJ.

## Bloqueios

- Valores da tabela CEHOP, dos kits e da ABRAVA são provisórios até P-01, P-02 e P-04.
- Regras do plano de ARTs são provisórias até P-06.
- O PDF da CEHOP-SE 2023 não está no Drive do Allan (busca em 13/11).

## Onde estão as coisas

| O quê | Onde |
|---|---|
| Ferramenta de propostas (Streamlit + pacote `orcamento`) | `propostas/` (ver `propostas/README.md`) |
| Back-end da suíte (T0) | `suite/backend` |
| CFD (`clima2d`) | `aerojax-hvac/` |
| Seleção (`ductdx`) | repositório `hvac-duct-dx` |
| Spec da precificação (blocos B1–B8) | `docs/superpowers/specs/2026-11-09-precificacao-design.md` |
| Spec mestre da suíte | `docs/superpowers/specs/2026-11-08-suite-hvacr-design.md` |
| Pesquisa de fontes de preço | `docs/pesquisa/tabelas_referencia_precos.md` |
| Dados da empresa achados no Drive | fora do repositório (privado); pedir ao Allan |
