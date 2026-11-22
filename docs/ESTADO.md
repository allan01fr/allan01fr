# Estado do projeto — onde paramos

Atualize este arquivo no fim de cada sessão: substitua "Última sessão" e "Próximo passo", mantenha
o resto curto. Histórico longo vai para o git, não para cá.

## Última sessão (22/11/2026)

- P-08 feita: dos 10 erros possíveis da revisão, 3 corrigidos e 7 descartados (`fca598c`);
  bateria com 394 testes.
- P-09 feita: INCC-M é a série 7456 do Banco Central; INCC-DI (192) incluído (`dd11427`).
  Confirmação veio de fonte secundária; conferir no catálogo oficial do SGS quando possível.
- P-10 feita: tabela por fase da aba Preço cabe na tela, com a Margem visível (`761dc63`).
- Manual do usuário criado em `docs/manual/propostas/` (uma página por aba).
- Agenda: 18 eventos no Google Agenda (contato@kaptek.com.br): prazos M0–M8 (lembrete 3 dias antes),
  8 tarefas do Allan da M0 (lembrete na véspera) e revisão semanal às sextas 17h.

## Meta atual

**M0 — Precificação v1 em uso real**, de 23/11 a 06/12/2026.

## Próximo passo

- Claude: nada pendente sem dados do Allan na M0. Próximas tarefas dependem de P-01, P-02, P-04 e P-06.
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
| Manual do usuário, uma página por aba | `docs/manual/propostas/` |
| Pesquisa de fontes de preço | `docs/pesquisa/tabelas_referencia_precos.md` |
| Dados da empresa achados no Drive | fora do repositório (privado); pedir ao Allan |
