# Suíte HVAC-R KAPTEK — especificação geral (arquitetura e contratos)

Data: 2026-11-08 · Status: **em revisão** · Arquitetura aprovada: monólito modular (opção 1)

Esta especificação fixa o que todas as trilhas compartilham. Cada trilha (T1–T7) terá a
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
| CAD/BIM | IFC no núcleo (IfcOpenShell) + plugin Bonsai; entrada DXF para os projetos atuais em AutoCAD | Usuário |

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
│   │       ├── cfd/         # T6: Clima2D como tarefa
│   │       └── bim/         # T7: leitura e verificação de IFC/DXF, lista de materiais
│   ├── migracoes/
│   └── testes/
├── frontend/
├── plugin-bonsai/           # T7: complemento do Blender/Bonsai (GPL), cliente fino da API
└── infra/                   # docker-compose e Dockerfiles (o CI fica em .github/workflows/suite.yml)
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
9. **Parâmetros de normas são dados privados, com edição.** Valores tirados de normas ABNT
   (tabelas de vazão, filtros, ruído, periodicidades) não entram no repositório público: ficam
   num catálogo de parâmetros carregado por empresa, e cada conjunto guarda norma, edição e
   seção/tabela de origem. O código cita só número de seção e tabela. Um cálculo feito com
   edição superada (ex.: NBR 16401-3:2008, NBR 13971:1997, NBR 10152:1987) traz esse aviso
   no resultado e no relatório. A RE ANVISA 09/2003 está revogada; a referência de qualidade
   do ar interior é a NBR 17037.

## 5. Modelo de dados canônico (dono → tabelas)

| Dono | Tabelas principais | Campos-chave |
|---|---|---|
| nucleo | `empresa`, `usuario`, `perfil_usuario`, `responsavel_tecnico`, `tarefa`, `arquivo`, `auditoria` | `empresa(razao_social, cnpj_cpf, endereco, contatos, comarca_foro, logomarca)`; `responsavel_tecnico(empresa, nome, registro CREA/CFT, assinatura, arquivado_em)`; `usuario.email` único no sistema |
| cadastro (T0) | `cliente`, `contato`, `obra`, `ambiente`, `ativo` | `cliente.cnpj_cpf` (dígito verificador validado), `cliente.representante_legal`, `obra.endereco`, `obra.uf`, `ambiente(obra, area_m2, uso, nivel_risco)`, `ativo(ambiente, fabricante/modelo/serie/fluido/carga_kg)`, `arquivado_em` em cliente e obra |
| comercial (T1) | `proposta`, `proposta_revisao`, `item_execucao`, `produtividade`, `funcao`, `contrato` | `produtividade(item, funcao, hh_por_unidade, fonte)` |
| campo (T2) | `ordem_servico`, `modelo_checklist`, `checklist_execucao`, `apontamento_hh`, `foto`, `assinatura`, `movimento_refrigerante` | `apontamento_hh(os, usuario, funcao, inicio, fim)`; `movimento_refrigerante(ativo, os, tipo: recarga/recolhimento/vazamento, fluido, kg, data)` |
| financeiro (T3) | `medicao`, `titulo_receber`, `exportacao` | `titulo_receber(contrato, vencimento, valor, situacao)` |
| energia (T4) | `estudo_energia`, `zona`, `resultado_energia`, `estudo_retrofit`, `calculo_leed` | resultados em JSONB com a rastreabilidade da regra 7 |
| selecao (T5) | `fabricante`, `familia`, `modelo_equipamento`, `ponto_desempenho`, `selecao` | esquema único que substitui `equipment_model`, `miraco_*` e `rooftop_*` |
| cfd (T6) | `estudo_cfd` | projeto Clima2D (JSON validado) + id da tarefa |
| bim (T7) | `modelo_bim`, `verificacao_bim`, `quantitativo_bim` | `modelo_bim(obra, formato: IFC/DXF, arquivo, versão)`; `verificacao_bim(modelo, regra, norma/edição, elemento, situação)`; `quantitativo_bim(modelo, item_execucao, quantidade, unidade)` |

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
- Cadastro: clientes, obras e ativos, com telas. Hierarquia cliente → obra (empreendimento) →
  ambiente climatizado → ativo; cliente PF ou PJ com representante legal; CPF/CNPJ com dígito
  verificador validado; arquivar sem apagar histórico; importação em lote de ambientes e ativos
  colando do Excel (tudo ou nada, com relatório de erros por linha).
- Configuração da empresa: dados cadastrais, comarca do foro, logomarca e vários responsáveis
  técnicos (nome, registro CREA/CFT, assinatura), usados em todo documento gerado.
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
- Segundo método de preço de projeto: honorário pelo método da área (ABRAVA/DNPC) — tipo de
  instalação (expansão direta, água gelada, VRF), área, custo básico unitário, fator do nível
  do RT e curva de percentual sobre a área; parâmetros privados por empresa (regra 9),
  comparável lado a lado com o preço por HH.
- Status: rascunho → enviada → aprovada | recusada; aprovada → entregue (com desfazer);
  revisões guardadas; validade com alerta de proposta vencendo ou vencida.
- Documentos PDF com a identidade da empresa e do RT: proposta, contrato e recibo (do projeto
  ou por parcela paga), com texto de cada seção editável e "restaurar padrão".
- Painel comercial: projetos por estágio, conversão geral e por faixa de valor, valor aguardando
  resposta, total aprovado, ticket médio, propostas vencendo, entregas atrasadas.
- Pronto quando: os exemplos atuais de `propostas/exemplos` dão o mesmo preço pela API; uma
  obra de referência gera HH, equipe, prazo e preço conferidos à mão.

**T2 Campo / PMOC**
- OS dos tipos projeto, obra, PMOC e corretiva, ligadas a obra e ativos.
- Modelos de checklist de PMOC (Lei 13.589/2018, ABNT NBR 13971) com periodicidade por ativo.
- No celular: lista de OS do dia, checklist, fotos, assinatura do cliente, apontamento de HH.
- Registro de recarga, recolhimento e vazamento de refrigerante por ativo (kg e fluido): é o
  dado que o LEED v5 exige no inventário de refrigerantes e na recertificação O+M.
- Uso sem sinal: grava no aparelho e sincroniza; o servidor decide o estado da OS, e os campos
  do checklist seguem "último que gravou vence" com registro do conflito.
- Ciclo do PMOC completo, na ordem: PMOC em PDF no modelo do Anexo I da Portaria MS 3.523/1998
  → cronograma de 12 meses → OS do mês abertas automaticamente → execução com checklist por
  equipamento, medidas conferidas, fotos com legenda e histórico por equipamento → revisão e
  conclusão pelo RT → não conformidade (RNC) com acompanhamento e verificação de eficácia →
  laudo de qualidade do ar e plano de amostragem pela NBR 17037 → controle de torre de
  resfriamento → relatório circunstanciado do período.
- Painel do que vence e do que está atrasado; áreas críticas (saúde) com nível de risco e
  pressão por ambiente; emissão para vários RTs da mesma empresa.
- Pronto quando: um técnico fecha uma OS de PMOC em modo avião e ela chega completa ao
  sincronizar; o relatório de PMOC sai em PDF.

**T3 Financeiro básico**
- Medição a partir do contrato (por fase, por % executado ou por HH apontado).
- Contas a receber: títulos, vencimentos, baixa manual, situação.
- Exportação CSV para o provedor de NFS-e e para o contador.
- Parcelas geradas automaticamente ou uma a uma, com recibo por parcela paga (documento da T1).
- Painel financeiro: a receber, recebido no mês e no ano, atrasado, próximos vencimentos,
  clientes com maior faturamento, faturamento mensal; exportação CSV/Excel para o contador.
- Pronto quando: contrato → medição → título → baixa funciona de ponta a ponta.

**T4 Energia / LEED** (base: pesquisa em `docs/pesquisa/leed/`)
- Primeira entrega, em ordem, os cálculos que não dependem da simulação anual:
  1. Inventário de refrigerantes: carga, GWP e tCO2e por ativo; alternativas para GWP > 700;
     GWP médio ponderado (LEED v5 EAp5 e EAc7), a partir dos ativos (T0) e movimentos (T2).
  2. Ventilação pela ASHRAE 62.1-2022 (VRP) e pela NBR 16401-3, lado a lado (EQp e EQc1).
  3. Carga de pico de resfriamento e aquecimento com ventilação, por zona (EAc2).
  4. CAPEX/OPEX de retrofit e overhaul, reaproveitando `orcamento/viabilidade` (VPL, TIR, payback),
     com consumo antes/depois pelo método de faixas de temperatura do python-hvac.
- Segunda entrega: simulação anual 8760 com EnergyPlus/OpenStudio (seção 9) como tarefa
  assíncrona, modelo de referência do Apêndice G via openstudio-standards, consumo por uso final.
- Terceira entrega: analisador de energia (linha de base com contas e medições, M&V pelo IPMVP)
  para LEED O+M e retrofit; exportação para o Arc.
- Pronto (primeira entrega) quando: um caso de referência produz inventário de refrigerantes,
  ventilação pelas duas normas, carga de pico e estudo de retrofit com VPL, TIR e payback,
  todos rastreáveis à norma (regra 7) e conferidos à mão.
- Todo número de LEED usado em cálculo é conferido no documento oficial antes da entrega: a
  pesquisa não teve acesso direto aos PDFs do USGBC.

**T5 Seleção**
- Extrair o motor de seleção do `main.py` do hvac-duct-dx, com testes que fixam o resultado atual.
- Catálogo único (fabricante, família, modelo, pontos de desempenho) substituindo as três famílias.
- Difusores e seleção DX pela API, gravando em `selecao`.
- Pronto quando: a seleção pela API dá os mesmos modelos que a interface atual para os casos de teste.

**T6 CFD**
- Renomear `hvac` → `clima2d`; validar o JSON do projeto na entrada (formato e versão).
- Simulação como tarefa; relatório de conforto (ISO 7730 / NBR 16401-2) como arquivo.
- Pronto quando: um projeto de exemplo roda pelo worker e o relatório sai igual ao do app atual.

**T7 BIM/CAD** (decisão: IFC no núcleo + plugin Bonsai; a equipe desenha hoje em AutoCAD)
- Back-end com IfcOpenShell (LGPL): importa um modelo IFC de qualquer origem (Revit, ArchiCAD,
  Bonsai) e extrai ambientes (`IfcSpace`), dutos, difusores, tubulações e equipamentos.
- Importação de DXF por layers (reaproveita o `importar_dxf` do Clima2D) para os projetos
  atuais feitos em AutoCAD, com uma convenção de layers da KAPTEK documentada.
- Verificação pelas regras das trilhas T4/T5 (vazão de ar exterior, velocidade em duto,
  coifas pela NBR 14518, pressões e trocas de ar pela NBR 7256, ruído), com a edição da norma
  em cada resultado (regra 9).
- Lista de materiais (m² de duto, m de linha frigorífica, difusores, equipamentos) que vira
  `item_execucao` na T1 (HH, equipe, prazo e preço).
- Plugin Bonsai: complemento do Blender em Python, GPL, só cliente da API (login, envio do
  IFC, painel com as não conformidades marcadas nos elementos, lançamento de difusores e
  dutos com os parâmetros da suíte). Nenhum valor de norma fica no plugin.
- Pronto quando: um IFC de referência e um DXF de referência geram a mesma lista de
  ambientes e materiais, com as não conformidades esperadas; o plugin mostra essas não
  conformidades no Bonsai.

## 7. Ordem e paralelismo

```
T0 Fundação ──► T1 Comercial ──► T3 Financeiro
           ├──► T2 Campo/PMOC
           ├──► T5 Seleção
           ├──► T6 CFD
           ├──► T4 Energia/LEED (1ª entrega já; simulação 8760 ao fechar o motor, seção 9)
           └──► T7 BIM/CAD (leitura IFC/DXF já; verificação ao ficarem prontas as regras de T4/T5)
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
| Motor de energia anual. **Recomendação da pesquisa: integrar EnergyPlus/OpenStudio** (testado pela ASHRAE 140, aceito no Apêndice G e na prática do INI-C, API Python, modelo de referência pronto). O python-hvac fica para carga de pico e estimativas rápidas. O nome EnergyPlus e a marca LEED não entram no nome do produto | Na revisão desta especificação | Engenharia |
| Liberar usgbc.org e ashrae.org na rede, ou conferir os números de LEED manualmente nos PDFs oficiais | Antes da especificação da T4 | KAPTEK |
| Provedor de nuvem e domínio | No fim da T0, antes do primeiro deploy | KAPTEK |
| Provedor de NFS-e | Na especificação da T3 | KAPTEK / contador |
| Nome do produto | Antes da fase de produto | KAPTEK |
| Adquirir as edições vigentes: NBR 17037, NBR 16401-1/2/3:2024, NBR 13971:2014, NBR 14679:2012, NBR 10152:2017, NBR 10151:2019 (verificar antes os arquivos `Normas.rar` e `envio ao sindratar.rar` do Drive) | Antes das especificações de T2, T4 e T7 | KAPTEK |
| Convenção de layers DXF da KAPTEK para ambientes, dutos, difusores e equipamentos | Na especificação da T7 | Engenharia |
| Obter a tabela do método da área (ABRAVA/DNPC): custo básico por tipo de instalação, fator por nível do RT e curva de percentual | Antes da implementação do método da área na T1 | KAPTEK |

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Trilhas paralelas divergem no modelo de dados | Contratos da seção 4 e teste de arquitetura |
| Extração do hvac-duct-dx muda resultados de seleção | Testes de caracterização antes de mover código |
| Constantes de unidade unificadas mudam valores nas últimas casas | Commit separado e anunciado |
| Uso sem sinal gera conflitos de dados no campo | Servidor decide o estado da OS; conflitos registrados e visíveis |
| Cálculos para LEED/laudo sem validação suficiente | Norma citada, casos de referência e revisão por engenheiro responsável |
| Escopo de "módulo próprio de gestão" crescer até virar ERP | Fora de escopo explícito (seção 1); integrar em vez de construir |
| Normas no Drive estão em edições superadas (16401-3:2008, 13971:1997, 10152:1987...) e a NBR 17037 não está disponível | Aviso de edição em cada resultado (regra 9); adquirir as edições vigentes; casos de teste refeitos ao trocar a edição |
| Equipe desenha em AutoCAD, sem experiência em Blender/Bonsai; ferramentas MEP do Bonsai menos maduras que as do Revit | Entrada por DXF com layers para o fluxo atual; Bonsai adotado aos poucos, começando pela verificação |
| Plugin do Blender precisa ser GPL | Plugin só como cliente da API; regras, parâmetros e servidor seguem fechados |
