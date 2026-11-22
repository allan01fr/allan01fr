# Suíte HVAC-R KAPTEK — leia antes de qualquer coisa

Dono: Allan (KAPTEK, engenharia HVAC-R, Rio de Janeiro). Fale em **português do Brasil**, curto e
direto. Ramo de trabalho: `ccr-1ff54909-xbul6a`.

## Ordem de leitura (5 minutos)

1. `docs/ESTADO.md` — onde paramos, próximo passo, bloqueios. **Comece por aqui.**
2. `docs/DECISOES.md` — o que o Allan já decidiu. Não pergunte de novo.
3. Planilha "Controle Suíte HVAC-R KAPTEK" (https://claude.ai/artifact/WLY5DvK7aQxS2P8uyLhb9K) —
   status e prazos de cada tarefa (IDs P-xx, T0-xx, T1-xx…). Roteiro em
   `docs/superpowers/plans/2026-11-22-roteiro.md`.
4. `docs/CONTEXTO_PARA_IA.md` — arquitetura, regras de código, limites. Leia a seção que a tarefa
   pede, não o arquivo todo.
5. O plano ou spec da tarefa (`docs/superpowers/plans/`, `docs/superpowers/specs/`).

## Como trabalhar

- **Uma tarefa da planilha por sessão.** Ao terminar: atualize `docs/ESTADO.md` (e
  `docs/DECISOES.md` se o Allan decidiu algo), marque o status na planilha, commit e push.
- Trabalho pesado (código, testes, pesquisa) vai para subagentes baratos com tarefa bem fechada
  (arquivos que podem mexer, testes a rodar, resposta em poucas linhas). A sessão principal só junta.
- Poucos testes novos por tarefa; bateria completa uma vez no fim. Não pule nem desligue testes.
- Mostre o resultado com print da tela quando a mudança for visual.
- **Manual do usuário:** toda mudança visível ao usuário atualiza, no mesmo commit, a seção
  correspondente em `docs/manual/` (texto e linha nova no "Histórico" do arquivo). Seção nova da
  tela ganha arquivo novo e entra no índice (`README.md` da pasta). Uma tarefa não está pronta sem
  isso.

## Limites que não se discutem

- Nunca commitar segredos (`suite/.env`) nem **dados financeiros da empresa** (custo/h, salários,
  faturamento): ficam fora do repositório. Este repositório pode ser público.
- Texto e valores de norma ABNT não entram no repositório (cite só o número).
- Não contornar proteção anti-robô de sites; não pedir de novo hosts que o Allan negou
  (usgbc.org, gbci.org, arcskoru.com).
- Não incluir identificador de modelo em commits ou PRs além dos trailers abaixo.
- Commits em português, terminando com:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01MBTaWF9DvZUC7F2rtrDAGV
  ```
  (outra IA ou sessão usa a própria atribuição).

## Como rodar a ferramenta de propostas

`cd propostas && python -m pytest -q testes` (bateria) · `./iniciar.sh` (tela Streamlit, porta 8501).
