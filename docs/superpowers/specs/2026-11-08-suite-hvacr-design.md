# Suíte HVAC-R KAPTEK — especificação geral (arquitetura e contratos)

Data: 2026-11-08 · Status: **em revisão** · Arquitetura aprovada: monólito modular (opção 1)

Esta especificação fixa o que todas as trilhas compartilham. Cada trilha (T1–T6) terá a
sua própria especificação curta e o seu plano, escritos a partir daqui.

## 1. Objetivo e premissas

Uma suíte web de engenharia e gestão técnica de HVAC-R: calcula (carga, energia, seleção,
CFD), orça (HH, equipe, prazo, preço), executa (OS, PMOC) e cobra (medições, contas a receber).

| Decisão | Valor | Origem |
|---|---|---|
| Para quem | Uso interno da KAPTEK primeiro; produto para outras empresas depois | Usuário: opção C |
| ERP | Nenhum. A suíte tem módulo próprio de gestão técnica, mínimo | Usuário: opção E |
| Onde roda | Aplicação web na nuvem; celular para o campo | Usuário: opção A |
| Usuários (6 meses) | Engenharia, comercial, financeiro e técnicos de campo | Usuário: opção C |
| Prioridade | Todos os módulos, em paralelo, depois da fundação | Usuário |
| Arquitetura | Monólito modular: um back-end, um banco, um front-end, módulos isolados | Usuário: aprovou opção 1 |

Consequências de "interno agora, produto depois":
- Dados separados por empresa (`empresa_id`) desde a primeira tabela.
- Cálculos usados em laudo ou certificação nascem com a norma citada e testes de referência.
- Cadastro self-service de clientes, cobrança e portal ficam para a fase de produto.

### Fora de escopo nesta fase

- Emissão de NFS-e (a suíte exporta para um provedor; a emissão fica com ele).
- Contabilidade, folha de pagamento, estoque completo e compras.
- CFD 3D (a primeira entrega usa o Clima2D 2D).
- Integração com ERPs de terceiros (o desenho por adaptadores permite fazer depois).

## 2. Arquitetura

```
navegador / celular (PWA)
        │ HTTPS, JSON
        ▼
FastAPI ──► módulos de domínio ──► PostgreSQL
   │              │
   │              └──► motores de cálculo (bibliotecas Python)
   ▼
worker de tarefas (mesmo código, outro processo) ──► armazenamento de arquivos (S3 compatível)
```

| Peça | Escolha | Motivo |
|---|---|---|
| Linguagem do back-end | Python 3.12 | Todos os motores existentes são Python; o python-hvac exige < 3.13 |
| API | FastAPI + Pydantic v2 | Validação na borda, OpenAPI gerado para o front-end |
| Banco | PostgreSQL 16, SQLAlchemy 2, migrações Alembic | Relacional, transações, JSONB para dados de cálculo |
| Fila de tarefas | Tabela `tarefa` no próprio PostgreSQL com `FOR UPDATE SKIP LOCKED` | Sem Redis nem broker extra; volume baixo |
| Front-end | React + TypeScript + Vite, instalável como PWA | Um front-end para escritório e campo; uso sem sinal via IndexedDB |
| Arquivos | Armazenamento S3 compatível (fotos, relatórios, DXF) | Fora do banco; URLs assinadas |
| Login | E-mail e senha (hash argon2), sessão em cookie httpOnly | Simples agora; SSO/OIDC na fase de produto |
| Entrega | Contêineres Docker (api, worker, web, banco) | Independente do provedor de nuvem |
| CI | GitHub Actions: lint, testes, build | Já usado no hvac-duct-dx |

## 3. Organização do código

Tudo em `allan01fr/allan01fr`, pasta `suite/` (o repositório já guarda `propostas` e
`aerojax-hvac`). Se for criado um repositório próprio, a pasta muda de lugar sem mudar o conteúdo.

```
suite/
├── backend/
│   ├── app/
│   │   ├── nucleo/          # config, banco, login, perfis, empresa, erros, tarefas, arquivos
│   │   └── modulos/
│   │       ├── cadastro/    # T0: clientes, obras, ativos (equipamentos instalados)
│   │       ├── comercial/   # T1: propostas, HH de execução, equipe, preço, contratos
│   │       ├── campo/       # T2: OS, checklists, PMOC, apontamento de HH
│   │       ├── financeiro/  # T3: medições, contas a receber, exportações
│   │       ├── energia/     # T4: carga, energia anual, CAPEX/OPEX, LEED
│   │       ├── selecao/     # T5: seleção DX, difusores, catálogo
│   │       └── cfd/         # T6: Clima2D como tarefa
│   ├── migracoes/
│   └── testes/
├── frontend/
└── infra/                   # docker-compose, Dockerfiles, CI
```

Cada módulo tem sempre os mesmos arquivos, na mesma ordem de fluxo:

```
modulos/<nome>/
├── rotas.py         # HTTP: recebe, valida (esquemas), chama o serviço, devolve
├── esquemas.py      # Pydantic: entrada e saída da API
├── servico.py       # regras de negócio; ÚNICA porta de entrada para outros módulos
├── repositorio.py   # consultas ao banco, sempre filtradas por empresa_id
├── modelos.py       # tabelas SQLAlchemy do módulo
└── tarefas.py       # (opcional) tarefas longas executadas pelo worker
```

## 4. Contratos entre trilhas

Estas regras permitem que as trilhas avancem em paralelo sem conflito.

1. **Dono de cada tabela.** Só o módulo dono grava nas suas tabelas (seção 5). Outro módulo
   lê pelo `servico.py` do dono, nunca importando `modelos.py` ou `repositorio.py` alheio.
   Um teste de arquitetura falha se houver import cruzado.
2. **Empresa em tudo.** Toda tabela de dados tem `empresa_id` não nulo. O repositório base
   aplica o filtro; não existe consulta sem ele. Um teste cria duas empresas e prova o isolamento
   em cada endpoint.
3. **Perfis.** `admin`, `engenharia`, `comercial`, `financeiro`, `campo`. Cada rota declara
   os perfis permitidos; a matriz fica em `nucleo/perfis.py` e é testada.
4. **Formato de erro único.** `{"codigo": "...", "mensagem": "...", "detalhes": {...}}`,
   com status HTTP coerente. Mensagens em português, sem rastreamento interno.
5. **Unidades.** O banco e a API usam SI (W, m³/h, m, Pa, °C, kg). Conversões para unidades
   de catálogo (Btu/h, CFM, pol) acontecem só dentro dos motores e numa única tabela de
   constantes, `nucleo/unidades.py`.
6. **Tarefas longas** (simulação 8760, CFD, relatórios): `enfileirar(tipo, dados) -> id`,
   consulta de estado `pendente | executando | concluida | falhou`, resultado em arquivo.
   A rota nunca espera o cálculo terminar.
7. **Rastreabilidade de cálculo.** Todo resultado de motor grava: versão do motor, entradas,
   normas usadas e data. Proposta, laudo e relatório emitidos ficam imutáveis; uma alteração
   gera nova revisão.
8. **Motores ficam fora da suíte.** A suíte chama os motores por uma camada fina em cada
   módulo e não copia o código deles:
   - `propostas/orcamento` → instalado como pacote (receberá `pyproject.toml`);
   - `aerojax-hvac/hvac` → renomeado para `clima2d` (conflito com o pacote `hvac` do python-hvac);
   - `hvac-duct-dx` → motor de seleção extraído para pacote, sem PySide6 (itens 1–4 da auditoria);
   - `python-hvac` → dependência via git, com testes de caracterização do que a suíte usar.

## 5. Modelo de dados canônico (dono → tabelas)

| Dono | Tabelas principais | Campos-chave |
|---|---|---|
| nucleo | `empresa`, `usuario`, `perfil_usuario`, `tarefa`, `arquivo`, `auditoria` | — |
| cadastro (T0) | `cliente`, `contato`, `obra`, `ativo` | `cliente.cnpj_cpf`, `obra.endereco`, `obra.uf`, `ativo.fabricante/modelo/serie/fluido/carga_kg` |
| comercial (T1) | `proposta`, `proposta_revisao`, `item_execucao`, `produtividade`, `funcao`, `contrato` | `produtividade(item, funcao, hh_por_unidade, fonte)` |
| campo (T2) | `ordem_servico`, `modelo_checklist`, `checklist_execucao`, `apontamento_hh`, `foto`, `assinatura` | `apontamento_hh(os, usuario, funcao, inicio, fim)` |
| financeiro (T3) | `medicao`, `titulo_receber`, `exportacao` | `titulo_receber(contrato, vencimento, valor, situacao)` |
| energia (T4) | `estudo_energia`, `zona`, `resultado_energia`, `estudo_retrofit`, `calculo_leed` | resultados em JSONB com a rastreabilidade da regra 7 |
| selecao (T5) | `fabricante`, `familia`, `modelo_equipamento`, `ponto_desempenho`, `selecao` | esquema único que substitui `equipment_model`, `miraco_*` e `rooftop_*` |
| cfd (T6) | `estudo_cfd` | projeto Clima2D (JSON validado) + id da tarefa |

Fluxo principal entre módulos:

```
cliente → obra → [selecao/energia/cfd] → comercial: proposta → contrato
   → campo: OS (obra ou PMOC) → apontamento HH ─┬─► financeiro: medição → título
                                                └─► comercial: calibração da produtividade
```

## 6. Trilhas: primeira entrega de cada uma

Cada trilha entrega uma fatia vertical utilizável (banco → API → tela), não camadas soltas.

**T0 Fundação** (sozinha, antes das outras)
- Núcleo da seção 3, login, perfis, empresa, fila de tarefas, arquivos, formato de erro.
- Cadastro: clientes, obras e ativos, com telas.
- Infraestrutura: docker-compose local, CI, imagem para deploy.
- Pronto quando: duas empresas isoladas provadas por teste; um usuário de cada perfil entra e
  vê só o que pode; uma tarefa de exemplo roda no worker; CI verde.

**T1 Comercial**
- Proposta pela web reaproveitando o motor `orcamento` (serviços de engenharia, fases, preço).
- Novo: **HH de execução**. Itens de obra (m² de duto, m de linha frigorífica, unidade
  evaporadora/condensadora, TR, ponto elétrico, difusor...) × tabela de produtividade por função
  (encarregado, mecânico de refrigeração, ajudante, soldador, eletricista, técnico de TAB),
  com fatores de altura, acesso, edifício ocupado e turno noturno.
- **Equipe e prazo**: para cada função, nº de pessoas = HH ÷ (horas por dia × dias úteis ×
  eficiência); prazo calculado ao contrário quando a equipe é fixa; cronograma por frentes.
- **Preço de obra**: HH × custo-hora com encargos + materiais + BDI, no mesmo motor de preço.
- Contrato gerado da proposta aceita.
- Pronto quando: os exemplos atuais de `propostas/exemplos` dão o mesmo preço pela API; uma
  obra de referência gera HH, equipe, prazo e preço conferidos à mão.

**T2 Campo / PMOC**
- OS dos tipos projeto, obra, PMOC e corretiva, ligadas a obra e ativos.
- Modelos de checklist de PMOC (Lei 13.589/2018, ABNT NBR 13971) com periodicidade por ativo.
- No celular: lista de OS do dia, checklist, fotos, assinatura do cliente, apontamento de HH.
- Uso sem sinal: grava no aparelho e sincroniza; o servidor decide o estado da OS, e os campos
  do checklist seguem "último que gravou vence" com registro do conflito.
- Pronto quando: um técnico fecha uma OS de PMOC em modo avião e ela chega completa ao
  sincronizar; o relatório de PMOC sai em PDF.

**T3 Financeiro básico**
- Medição a partir do contrato (por fase, por % executado ou por HH apontado).
- Contas a receber: títulos, vencimentos, baixa manual, situação.
- Exportação CSV para o provedor de NFS-e e para o contador.
- Pronto quando: contrato → medição → título → baixa funciona de ponta a ponta.

**T4 Energia / LEED**
- Carga térmica por zona e consumo anual de energia como tarefa assíncrona.
- CAPEX/OPEX de retrofit e overhaul, reaproveitando `orcamento/viabilidade` (VPL, TIR, payback).
- Cálculos LEED ligados a HVAC-R, começando pelos que não dependem de simulação completa:
  impacto de refrigerante e vazão de ar externo (ASHRAE 62.1).
- O motor de energia anual será escolhido com base nas pesquisas sobre LEED (seção 9).
- Pronto quando: um estudo de retrofit de referência produz consumo antes/depois, OPEX,
  CAPEX, VPL, TIR e payback rastreáveis.

**T5 Seleção**
- Extrair o motor de seleção do `main.py` do hvac-duct-dx, com testes que fixam o resultado atual.
- Catálogo único (fabricante, família, modelo, pontos de desempenho) substituindo as três famílias.
- Difusores e seleção DX pela API, gravando em `selecao`.
- Pronto quando: a seleção pela API dá os mesmos modelos que a interface atual para os casos de teste.

**T6 CFD**
- Renomear `hvac` → `clima2d`; validar o JSON do projeto na entrada (formato e versão).
- Simulação como tarefa; relatório de conforto (ISO 7730 / NBR 16401-2) como arquivo.
- Pronto quando: um projeto de exemplo roda pelo worker e o relatório sai igual ao do app atual.

## 7. Ordem e paralelismo

```
T0 Fundação ──► T1 Comercial ──► T3 Financeiro
           ├──► T2 Campo/PMOC
           ├──► T5 Seleção
           ├──► T6 CFD
           └──► T4 Energia/LEED (começa ao fechar a escolha do motor, seção 9)
```

- T5 e T6 podem começar já, durante a T0, porque mexem nos motores (pacotes fora de `suite/`).
- Cada trilha: especificação curta → plano → implementação por um subagente em branch de
  trabalho isolado → revisão → integração no branch da sessão.
- Uma trilha não altera contratos da seção 4; mudança de contrato volta para esta especificação.

## 8. Testes e qualidade

- pytest por módulo; testes de isolamento entre empresas e de perfis em todas as rotas.
- Teste de arquitetura: nenhum módulo importa `modelos`/`repositorio` de outro.
- Motores: testes de caracterização antes de qualquer extração ou renome.
- Front-end: testes de componente e um teste ponta a ponta com Playwright por trilha.
- CI no GitHub Actions; ruff no back-end e lint no front-end.
- Os três itens obrigatórios da auditoria de qualidade valem para todo código novo:
  um assunto por arquivo, legível por um júnior, o mesmo fluxo para o mesmo tipo de trabalho.

## 9. Decisões em aberto

| Decisão | Quando se decide | Quem |
|---|---|---|
| Motor de energia anual: python-hvac (RTS) ou EnergyPlus/OpenStudio | Ao concluir as pesquisas de LEED, antes da especificação da T4 | Engenharia, com recomendação da pesquisa |
| Quais créditos LEED entram na T4 e em que ordem | Mesma ocasião | Engenharia |
| Provedor de nuvem e domínio | No fim da T0, antes do primeiro deploy | KAPTEK |
| Provedor de NFS-e | Na especificação da T3 | KAPTEK / contador |
| Nome do produto | Antes da fase de produto | KAPTEK |

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Trilhas paralelas divergem no modelo de dados | Contratos da seção 4 e teste de arquitetura |
| Extração do hvac-duct-dx muda resultados de seleção | Testes de caracterização antes de mover código |
| Constantes de unidade unificadas mudam valores nas últimas casas | Commit separado e anunciado |
| Uso sem sinal gera conflitos de dados no campo | Servidor decide o estado da OS; conflitos registrados e visíveis |
| Cálculos para LEED/laudo sem validação suficiente | Norma citada, casos de referência e revisão por engenheiro responsável |
| Escopo de "módulo próprio de gestão" crescer até virar ERP | Fora de escopo explícito (seção 1); integrar em vez de construir |
