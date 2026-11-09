# Suíte HVAC-R KAPTEK: contexto para uma IA colaboradora

Leia este arquivo inteiro antes de mexer em qualquer coisa. Ele resume as decisões, as regras e o
estado do trabalho em 2026-11-09. Os documentos citados aqui são a fonte de verdade; este arquivo é
o mapa.

## 1. Quem e o quê

- **Dono:** Allan (KAPTEK, consultoria de engenharia HVAC-R no Rio de Janeiro). Fale com ele em
  **português do Brasil**, de forma direta.
- **Produto:** a "Suíte HVAC-R KAPTEK", um conjunto de ferramentas de engenharia e gestão técnica
  para uso interno primeiro e venda como produto depois.
- **Usuários:** engenharia, comercial/financeiro e técnicos de campo (no celular).
- **Sem ERP externo:** a suíte tem seu próprio módulo mínimo de gestão técnica (propostas,
  contratos, OS, PMOC, financeiro básico). NFS-e apenas exportada para um provedor.
- **Implantação:** aplicação web na nuvem.
- **Prioridade dada pelo dono:** "todos e rápido".

### Módulos pedidos
1. Carga térmica e energia horária 8760 (algo como o HAP, **sem usar esse nome**).
2. Analisador de energia (linha de base, M&V/IPMVP, LEED O+M).
3. Retrofit/overhaul com CAPEX/OPEX.
4. CFD (conforto, distribuição de ar).
5. Estimativa de tempo de serviço: prazo de projeto, prazo de execução, HH por função,
   dimensionamento de equipe.
6. Precificação (inclui honorário de projeto pelo método ABRAVA/DNPC).
7. Seleção de equipamentos (DX dutado, difusores, ESP).
8. Campo/PMOC (Portaria 3.523, NBR 17037, medições de TAB pela NBR 17168).
9. BIM/CAD: **IFC + Bonsai** (a equipe usa AutoCAD; DXF por camadas na importação; plugin
   Bonsai/Blender GPL como cliente fino da API).

## 2. Repositórios (GitHub `allan01fr/*`)

| Repositório | Papel | Estado |
|---|---|---|
| `allan01fr` | Monorepo da suíte: `suite/` (back-end novo), `aerojax-hvac/` (CFD → pacote `clima2d`), `propostas/`, `docs/` (spec, planos, pesquisa) | ativo |
| `hvac-duct-dx` | Seleção DX, ESP e difusores (app PySide6 existente) → pacote `ductdx` | ativo |
| `python-hvac`, `mechpy`, `freecad-mcp`, `Aleph` | referência; não alterados | parado |

**Ramo de trabalho em todos:** `ccr-1ff54909-xbul6a`. O PR #3 (spec + planos) já foi mesclado no
`allan01fr`. O trabalho posterior ainda não tem PR aberto.

## 3. Documentos-fonte (leia nesta ordem)

1. `docs/superpowers/specs/2026-11-08-suite-hvacr-design.md`: **spec mestre**. Regras de contrato
   1–9, modelo de dados por módulo, trilhas T0–T7 e lista de decisões pendentes.
2. `docs/superpowers/plans/2026-11-08-t0-fundacao.md`: plano da fundação (21 tarefas).
3. `docs/superpowers/plans/2026-11-08-t1-comercial.md`: plano comercial (27 tarefas).
4. `docs/superpowers/plans/2026-11-08-t5-selecao.md`: plano da seleção (15 tarefas, executado no
   `hvac-duct-dx`).
5. `docs/superpowers/plans/2026-11-08-t6-cfd.md`: plano do CFD (7 tarefas).
6. `docs/pesquisa/leed/README.md` + relatórios 1–5: pesquisa de LEED v5, PBE Edifica/INI-C, software.

Cada tarefa dos planos traz arquivos, testes e passos. **Siga o plano; não invente escopo.**

## 4. Arquitetura

- **Monólito modular:** FastAPI + Pydantic v2 + SQLAlchemy 2 (síncrono, `postgresql+psycopg`) +
  Alembic + PostgreSQL 16.
- **Fila de tarefas** em tabela (`tarefa`) com `FOR UPDATE SKIP LOCKED`, sem broker externo.
- **Front-end:** React + TypeScript, PWA (técnico de campo no celular). Ainda não começou.
- **Contêineres:** Docker / docker-compose (tarefa 20 da T0).
- **Motores de cálculo** vivem em pacotes Python separados e instaláveis (`ductdx`, `clima2d`,
  `orcamento`); a suíte os chama por uma camada fina, **sem copiar código**.
- **Energia anual (T4):** EnergyPlus/OpenStudio como motor (atende LEED e INI-C). O nome
  "EnergyPlus" e a marca LEED não podem aparecer no nome do produto. Honeybee (AGPL), BESOS (GPL)
  e Pollination ficam fora do núcleo.

### Trilhas
| Trilha | Conteúdo | Situação |
|---|---|---|
| T0 Fundação | núcleo, auth, permissões, arquivos, fila, cadastro, PWA, CI | tarefas 1–8 mescladas; 9 feita, sem revisão |
| T1 Comercial | orçamento, HH, ABRAVA, propostas, contratos, painel | planejada, não iniciada |
| T2 Campo/PMOC | OS, PMOC completo, NBR 17037, NBR 17168 (TAB) | sem plano ainda |
| T3 Financeiro | parcelas, painel financeiro | sem plano ainda |
| T4 Energia/LEED | 8760, EnergyPlus/OpenStudio, ventilação 62.1 + NBR 16401-3, PMV/PPD, refrigerantes | sem plano ainda |
| T5 Seleção | `ductdx` | tarefas 1–11 aprovadas; 12 feita, sem revisão; 13–15 pendentes |
| T6 CFD | `clima2d` | tarefas 1–6 aprovadas; 7 bloqueada até a T0 acabar |
| T7 BIM/CAD | IFC + Bonsai + DXF | sem plano ainda |

## 5. Regras de código (valem para tudo)

- **Nomes e mensagens em português.** Mensagens de erro ao usuário em português.
- **Formato único de erro da API:** `{"codigo", "mensagem", "detalhes"}`.
- **Multiempresa:** toda tabela tem `empresa_id` (exceto `empresa`); ids UUID v4.
  - Consultas de módulo partem **sempre** de `RepositorioBase.consulta()`. `listar()` recusa
    consultas que não vieram de lá (marca `suite_empresa_id` nas execution_options).
  - Página máxima: `LIMITE_MAXIMO_LISTA = 200` (`app/nucleo/esquemas.py`).
  - Id de outra empresa → **404**, nunca 403.
  - A empresa vem sempre do contexto autenticado, nunca do corpo da requisição.
- **Rotas:** sessão do banco via `SessaoDoBanco`; contexto via `ContextoAtual`; permissão via
  `exigir("<modulo>.<acao>")` de `app/nucleo/perfis.py`. Toda rota nova entra em
  `ROTAS_ESPERADAS` no teste de isolamento.
- **Perfis:** admin, engenharia, comercial, financeiro, campo.
- **Sessão:** cookie `suite_sessao` assinado (itsdangerous), httpOnly, SameSite=Lax, Secure
  configurável; senhas argon2.
- **Fluxo de arquivos de um módulo:** rotas → esquemas → serviço → repositório → modelos → tarefas.
  Um assunto por arquivo.
- **Unidades:** SI na suíte; constantes de conversão só em `app/nucleo/unidades.py` (suíte) ou
  `ductdx/unidades.py` (pacote). Dentro de motores legados, o nome leva o sufixo da unidade
  (`_btuh`, `_cfm`, `_inwg`, `_c`, `_mm`).
- **Rastreabilidade (regra 7):** resultado de cálculo leva versão do motor, entradas e versão do
  catálogo/dados.
- **Regra 9 — normas ABNT:** texto e valores de norma são dados privados com a edição registrada,
  **nunca** no repositório público. Código cita no máximo número de seção/tabela. Resultado feito
  com edição superada leva aviso.
- **TDD:** escreva o teste, veja falhar (RED), implemente, veja passar. Refatorações começam por
  testes de caracterização.
- **Referências congeladas nunca são regeneradas:**
  `hvac-duct-dx/tests/caracterizacao/referencia_selecao.json`,
  `tests/caracterizacao/dados/hvac_equipment_v1.sqlite`,
  `tests/difusores/referencia_difusores.json`, `tests/difusores/nomes_diffuser_calculator.txt`.
- **Segredos:** nunca commitar `suite/.env`. `.env.example` só com valores de desenvolvimento.
- **Commits:** mensagem em português, com estes trailers:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01MBTaWF9DvZUC7F2rtrDAGV
  ```
  (uma IA diferente deve usar a própria atribuição).

## 6. Como rodar

### Back-end da suíte (`allan01fr/suite/backend`)
```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # ver pyproject.toml
# PostgreSQL 16 local: papel `suite`, bancos `suite` e `suite_teste`; copiar .env.example → .env
.venv/bin/alembic upgrade head
.venv/bin/python -m pytest -q
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/alembic check
```
Docs da API (`/docs`) só aparecem com `SUITE_AMBIENTE=dev`.

### Seleção (`hvac-duct-dx`)
```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest -q --ignore=tests/test_app_smoke.py
python build_db.py            # regenera hvac_equipment.sqlite a partir de data/
python main.py                # app de desktop PySide6
```
Ruff: só nos arquivos que você tocar. Há erros antigos em `main.py` e em 3 testes, que são tolerados.

### CFD (`allan01fr/aerojax-hvac`)
```bash
python -m pytest -q
python -m clima2d exemplos/projetos/escritorio_rapido.json relatorio.html
```

## 7. Estado em 2026-11-09 (trabalho pausado pelo dono até o fim da semana)

- **T0:** as tarefas 1–8 foram revisadas e mescladas no ramo da sessão. Dois commits existem só no
  worktree local `t0-fundacao` (`d9ba6be` reforços pedidos na revisão da tarefa 8; `7b3a29d` tarefa
  9, armazenamento S3). **Não foram revisados nem enviados.** Se não estiverem no GitHub, refaça a
  tarefa 9 a partir do plano.
- **T5:** as tarefas 1–11 estão aprovadas. A tarefa 12 (`ee856b1`, divisão da base comum dos
  difusores) está no GitHub, mas a revisão foi interrompida. Ela criou 7 módulos; confira se o plano
  pedia os 7.
- **T6:** as tarefas 1–6 estão aprovadas. A tarefa 7 espera a T0.
- **Ainda não há interface nova da suíte.** O que dá para usar: o app desktop do `hvac-duct-dx`,
  o app e a CLI do `clima2d` e a API da suíte pelo `/docs`.

### Pendências anotadas para a revisão final / endurecimento
- Limite de tentativas de login; auditoria de tentativas falhas; revogar sessões ao trocar a senha.
- Recusar o segredo de exemplo do `.env.example` em produção.
- Redefinição de senha (CLI ou admin).
- O e-mail é único no sistema todo (o login é global), o que revela a um admin que um e-mail existe
  em outra empresa. Aceito e documentado.
- Arquivos: `client_max_body_size` no proxy; lista de tipos permitidos; objeto órfão no S3 se o
  commit falhar.
- `clima2d`: o teto `MAX_PASSOS` (1e8) tem só 1,15× de folga sobre o caso mais extremo da UI.
- `ductdx`: fechar conexões no `closeEvent`.

## 8. Perguntas de engenharia em aberto (respostas do Allan)

1. Dados do 53QDMT30-708: hoje herdados do 718 (`inherited_fields`), aguardando confirmação.
2. O filtro trifásico exclui rooftops ("400-3-50")?
3. Desempate de aquecimento do QDMT escolhe 15 °C. Está certo?
4. Fator de licitação 0,85 no ABRAVA é um palpite; confirmar.
5. PDF oficial do método ABRAVA (2014) não pôde ser baixado (o CREA-SP bloqueia).
6. A planilha "Exaustão NBR 14158.xlsx" pode superestimar coifas de parede em cerca de 48% (não
   verificado).
7. Edições de norma a comprar: NBR 17037, 17168:2024, 16401:2024, 13971:2014, 14679:2012,
   10152:2017, 10151:2019.
8. Difusores: RVCD não aceita classe "MP"; VCD 1250×610 sai como medida especial; os layouts
   retangular e em L saem sem opção conforme; em L, 2 de 4 difusores posicionados.

## 9. Limites que não se discutem

- Não contornar proteção anti-robô de sites; não pedir de novo hosts que o dono negou
  (usgbc.org, gbci.org, arcskoru.com).
- Não colocar texto ou valores de norma ABNT no repositório.
- Não reescrever histórico de ramos alheios; não pular nem desligar testes para ficar verde.
- RE ANVISA 09/2003 está **revogada**; o lugar dela é da NBR 17037.

## 10. Como contribuir sem quebrar nada

1. Escolha uma tarefa pendente de um plano (ou peça ao Allan).
2. Leia a tarefa inteira e a seção do spec da trilha.
3. TDD: primeiro o teste que falha.
4. Rode a bateria completa e o lint do projeto.
5. Commit pequeno, mensagem em português.
6. Relate: o que mudou, a contagem de testes, as dúvidas. Não marque como pronto sem revisão.
