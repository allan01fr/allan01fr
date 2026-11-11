# Ferramenta de precificação KAPTEK: desenho

Data: 2026-11-09. Prioridade do Allan: esta ferramenta fica pronta antes de qualquer outra parte da
suíte. As trilhas T0, T5 e T6 ficam pausadas.

## 1. Objetivo

Completar a ferramenta que já existe em `propostas/` (pacote `orcamento`, tela Streamlit
`app/app.py`, CLI) até ela cobrir, sozinha, o ciclo de precificação da KAPTEK:

- montar a proposta com **escopos separados**: só o projeto, só o acompanhamento de obra, a
  execução, só uma inspeção com laudo de conformidade, ou a avaliação de desempenho;
- precificar a **execução de obra** (HH por função, equipe, prazo, cronograma, preço);
- precificar **por tabela de referência** (R$/m² por faixa) e **comparar** o preço com referências
  públicas;
- calcular o **honorário ABRAVA/DNPC**;
- entregar um **estudo de viabilidade** mais completo (projeção de custo, breakeven, payback);
- gerar **proposta, contrato e recibo**.

Pronto significa: o Allan abre a tela, monta uma proposta com qualquer combinação desses escopos,
vê o preço e as comparações, e exporta os documentos, sem editar JSON à mão.

## 2. O que já existe e não muda

- Motor de preço por fases (`orcamento/motor.py`): horas por perfil, custos diretos, overhead,
  contingência, impostos, margem; quatro formas de cobrança (`fechado`, `hora`, `percentual`,
  `pacote`); ART, deslocamento, cronograma e pagamento.
- Catálogo de 37 serviços (`dados/catalogo.json`) e parâmetros da empresa (`dados/parametros.json`).
- Bases de referência (`orcamento/referencias.py`): importação de tabelas, índices, cesta de preços
  pela mediana (`cesta`), atualização por índice (`atualizar`).
- Viabilidade (`orcamento/viabilidade.py`): CAPEX, OPEX, economia, breakeven, payback, VPL, TIR,
  LCC e sensibilidade; planilha em `exportar_viabilidade.py`.
- Exportação XLSX com fórmulas vivas e DOCX no modelo da KAPTEK.
- 177 testes passando (linha de base de 2026-11-09).

Regras que valem para tudo o que entrar:

1. **Os preços dos `exemplos/` não mudam.** Os testes que fixam esses preços continuam passando sem
   edição.
2. **O motor é puro.** Nada em `orcamento/` importa Streamlit. A tela só chama o motor.
3. **Arquivos antigos abrem.** `proposta.completar` migra propostas salvas antes desta entrega.
4. **A planilha repete o motor.** O que o motor calcula, a XLSX refaz em fórmula, e o teste de
   recálculo confere os dois.
5. **Toda referência tem fonte e data-base.** Valor sem fonte não entra em comparação.
6. **Normas ABNT ficam fora do repositório** (regra 9 da suíte). A tabela da ABRAVA também: os
   parâmetros ficam em arquivo local não versionado. Tabelas de órgãos públicos (CEHOP, licitações)
   são documentos públicos e podem ficar em `dados/`, com fonte e data.
7. **Nomes e mensagens em português.** Erros de entrada usam `ErroEntrada(codigo, mensagem,
   detalhes)`, o mesmo formato que a suíte vai usar depois.

## 3. Blocos

Cada bloco termina com a tela funcionando e capturas enviadas ao Allan. A ordem abaixo é sugestão
do autor; o Allan pode trocá-la.

### B1 — Escopos separados

**Problema.** Hoje a proposta tem fases, mas o usuário monta cada fase do zero, e não há como
desligar uma fase sem apagá-la.

**Desenho.**
- `orcamento/escopos.py` define os **módulos de escopo**. Cada módulo é um dado, não código:
  `{id, nome, descricao, cobranca, servicos: [ids do catálogo]}`. Módulos iniciais:

  | id | Nome | Serviços do catálogo | Cobrança padrão |
  |---|---|---|---|
  | `projeto` | Projeto | `hvac.carga_termica`, `hvac.projeto` | fechado |
  | `acompanhamento` | Acompanhamento de obra | `geral.acompanhamento_obra` | pacote |
  | `execucao` | Execução | (itens de execução, bloco B2) | fechado |
  | `inspecao_laudo` | Inspeção com laudo de conformidade | `hvac.inspecao_conformidade` (novo) | fechado |
  | `desempenho` | Avaliação de desempenho | `hvac.desempenho` | fechado |

- `escopos.incluir(opcao, modulo_id, cat, params)` cria uma fase nova com `proposta.nova_fase`,
  acrescenta os serviços com `proposta.novo_item` e grava `fase["modulo"] = modulo_id`. Incluir o
  mesmo módulo duas vezes cria duas fases (dois prédios, por exemplo).
- Cada fase ganha `ativa: bool` (padrão `True`). `motor.precificar_opcao` ignora fases inativas:
  elas não entram em preço, cronograma, pagamento nem documentos. `proposta.completar` põe
  `ativa=True` e `modulo=""` em propostas antigas.
- Novo serviço `hvac.inspecao_conformidade` no catálogo: vistoria em campo, verificação contra a
  lista de requisitos, registro fotográfico, laudo com não conformidades e recomendações, ART.
  Dados: área, número de sistemas, número de ambientes, normas verificadas (contagem). As horas
  iniciais são provisórias e ficam marcadas para calibração, como o resto do catálogo.
- Tela, aba **2 · Escopo**: barra "Incluir módulo" com os cinco botões; em cada fase, uma chave
  "incluir nesta proposta". Aba **4 · Preço**: tabela com o subtotal de cada fase ativa, o total da
  opção e, em cinza, as fases desligadas.
- XLSX e DOCX listam só as fases ativas.

### B2 — Execução de obra

Segue as tarefas 2, 3 e 4 do plano `docs/superpowers/plans/2026-11-08-t1-comercial.md`, que já
trazem assinaturas, fórmulas e um caso conferido à mão.

- `orcamento/erros.py`: `ErroEntrada`.
- `orcamento/execucao.py`:
  - `hh_execucao(itens, produtividade, fatores)`: `HH = quantidade × HH/unidade × fatores ×
    calibração`, por função e por frente. Fatores padrão: altura 1,00/1,15/1,30; acesso
    1,00/1,15/1,30; ambiente ocupado 1,20; noturno 1,25.
  - `dimensionar_equipe` e `cronograma_frentes`: pessoas por função = `ceil(HH ÷ (horas/dia × dias
    × eficiência))`; frentes em sequência; modos "prazo-alvo" e "equipe fixa"; dias corridos =
    `ceil(dias úteis × 7/5)`.
  - `fornecimentos_execucao` e `precificar_com_execucao`: a mão de obra vira fornecimento
    `mo_execucao` (HH × custo/h), o material vira `material`/`equipamento`, e o preço sai do mesmo
    `motor.precificar`, com o BDI por categoria que já existe.
- Dados: `dados/execucao.json` com funções (custo/h), produtividades (HH por unidade de cada item)
  e itens sugeridos. Valores iniciais provisórios, editáveis na tela.
- Tela: aba nova **Execução** (itens, fatores, equipe, prazo, cronograma por frentes). O módulo
  `execucao` do B1 aponta para essa aba.
- Caso de referência: HH 10,7 / 96,1 / 96,1; equipe 1/2/2; 9 dias úteis, 13 corridos; preço
  R$ 44.921,49.

**Calculadora de BDI.** Hoje o BDI de cada categoria de fornecimento é um número fixo em
`dados/parametros.json`. Novo `orcamento/bdi.py`:

- `bdi(ac, seguro_garantia, risco, despesas_financeiras, lucro, impostos)`, pela fórmula usada pelo
  TCU: `BDI = (1 + AC + S + R + G) × (1 + DF) × (1 + L) ÷ (1 − I) − 1`. Impostos que somam 100% ou
  mais levantam `ErroEntrada`.
- `bdi_implicito(valor_bdi, custo)`: lê o BDI de um orçamento de terceiros.
- Tela, aba de parâmetros: uma composição por categoria (mão de obra de execução, material,
  equipamento, subcontrato). O resultado grava `parametros["bdi"][categoria]`, que
  `motor._fornecimentos` já usa. Quem preferir digita o percentual direto, como hoje.
- Faixa de referência: o usuário informa mínimo, mediana e máximo com a fonte e a data, por
  categoria, e a tela avisa quando o BDI calculado sai da faixa. Nenhuma faixa fica fixa no código.
- O que já está no custo direto (mão de obra da obra, encargos, administração local) não entra na
  composição; a tela diz isso ao lado dos campos.

### B3 — Preço por tabela e comparação com referências

**Forma de cobrança "valor"** (tarefa 5 do T1). A fase pode ter um valor definido:
`preço = valor definido + fornecimentos`. O custo por horas continua calculado e aparece ao lado,
com a margem que resulta.

**Tabela de referência.** `orcamento/tabela_referencia.py`, com dados em `dados/tabelas/*.json`.
Cada tabela declara fonte, órgão, data-base, e uma lista de itens:

```
{id, descricao, unidade ("m2" | "TR" | "kW" | "un"), faixas: [{ate, valor}],
 modo ("cheio" | "escalonado"), minimo, observacao}
```

**Área ou capacidade.** A grandeza de entrada segue a unidade do item: área (m²) ou capacidade
(TR ou kW). As conversões usam constantes nomeadas em `orcamento/unidades.py`
(1 TR = 12.000 BTU/h = 3,517 kW). O "HP" de VRF é rótulo comercial e não tem fator fixo: quem
informa HP informa também o kW nominal do fabricante. Quando a referência está numa grandeza e o
projeto só tem a outra, a tela pede a densidade (m²/TR) como dado do projeto e marca o resultado
como "estimado pela densidade".

- **Cheio:** a faixa em que a área cai dá o R$/m² de toda a área (projetos de engenharia da CEHOP:
  até 500 m² / acima de 500 m²).
- **Escalonado:** cada faixa remunera só a sua parte da área (laudo de vistoria, urbanização).
- Regras gerais da tabela, cada uma ligada ou desligada pelo usuário: valor mínimo; acréscimo por
  complexidade (hospital, até 25%); acréscimo por reforma com cadastro das instalações (até 20%);
  repetição de pavimentos (20% por repetição até a 10ª, 5% depois, teto de 5× a primeira);
  coordenação (5%); redutor para projetos grandes (até 40%); deslocamento (R$/km, ida e volta).
- `calcular(tabela, item_id, area, opcoes) -> {valor, memoria: [linhas], avisos}`. A memória de
  cálculo lista cada parcela, para a planilha e a proposta.
- `atualizar_para(valor, data_base, data_alvo, indice, con)` usa `referencias.atualizar`. Sem
  índice importado, o valor fica na data-base e a tela avisa.
- **Índice de correção à escolha:** INCC, IPCA ou IGP-M. Cada tabela e cada referência guarda o
  índice sugerido; o painel de comparação tem um seletor que vale para a proposta e pode mostrar o
  mesmo valor corrigido pelos três, lado a lado. As séries são importadas pela aba de bases com
  `referencias.importar_indices`, que já existe; a ferramenta não baixa índice sozinha. O índice
  usado e o fator aplicado aparecem na memória de cálculo.

Primeira tabela: `dados/tabelas/cehop_se_2023.json` (CEHOP-SE, referência jan/2023, valores
máximos): climatização simples e complexa, as built, compatibilização, orçamento e especificação,
laudo de vistoria, deslocamento e as regras gerais. Testes reproduzem os exemplos de cálculo do
próprio documento (laudo de 3.000 m²; prédio de 12 pavimentos de 500 m²).

**Comparação.** Na aba Preço, cada fase ganha um painel "Referências" com colunas lado a lado:

| Coluna | De onde vem |
|---|---|
| Preço por horas | `motor.precificar_fase` |
| Preço por tabela | `tabela_referencia.calcular`, atualizado por índice |
| Mercado: média, mediana e menor | `referencias.cesta` sobre os itens ligados à fase |
| ABRAVA (bloco B4) | `honorario_abrava.calcular_abrava` |

A coluna de mercado mostra as três medidas, o critério adotado, o número de cotações usadas e
quantas ficaram fora de ±25% da mediana.

**Cotações comparáveis.** Cada referência de uma cesta ganha `comparavel` (padrão `True`) e
`motivo` (modelo diferente, capacidade diferente, escopo diferente, outro). `cesta` deixa as não
comparáveis fora do cálculo, mas devolve todas, e a tela lista as excluídas com o motivo. Exemplo
que vira teste: no orçamento do TRE-DF, o derivador E-102SNB2 tem uma cotação do modelo certo
(R$ 353,98) e três de outras peças; com as três marcadas, o item fica com uma cotação só e a tela
avisa que faltam referências.

**Data-base presumida.** Uma referência pode ter `data_base_presumida: true` com a justificativa
(por exemplo, "relatório de 30/04/2026 com cotações de março; mês do SINAPI não informado"). A
tela mostra o aviso até alguém confirmar a data.

O painel mostra a diferença percentual de cada coluna para o preço adotado e avisa quando o preço
adotado fica mais de 25% fora da mediana (mesma faixa de alerta da `cesta`). O botão "Adotar este
valor" muda a fase para cobrança `valor` com o número escolhido e registra de onde ele veio.

**Referências de mercado.** As tabelas de formação de preço de licitações (mediana de cotações) e
os contratos públicos entram na base `referencias.sqlite` como itens com fonte, órgão, data-base e
unidade. Um preset novo em `referencias.PRESETS` lê tabelas no formato "item, especificação,
cotações…, média, mediana". Os dados extraídos dos documentos que o Allan enviou ficam em
`dados/referencias_publicas/` (CSV com fonte e data), para reimportar a qualquer momento.

### B4 — Honorário ABRAVA/DNPC

Segue as tarefas 6 e 7 do T1.

- `orcamento/honorario_abrava.py`: `area_corrigida`, `percentual_curva` (interpolação linear,
  travada nas pontas), `calcular_abrava`, `comparar_com_hh`, `aplicar_na_proposta`.
- `orcamento/ajustes_honorario.py`: cadeia de ajustes da empresa (nível do RT, planilha, adicional,
  desconto, custos extras, valor de licitação), sempre rotulados "Ajuste da empresa".
- Parâmetros (custo por TR, curva de percentual, pesos de ambiente, fatores) em
  `dados/local/abrava.json`, **fora do git**. A tela tem um formulário para preenchê-los. Enquanto
  o documento oficial não for conferido, a tela e os documentos mostram "parâmetros provisórios".
- Pendência do Allan: obter a tabela oficial (Rev. 01/2014) e confirmar a fórmula. A pesquisa
  achou `H = CB × P × FD`, com `CB = Ac × CBU`; o plano T1 usa TR × custo por TR. O módulo aceita
  as duas bases de custo e o parâmetro diz qual vale.

### B5 — Viabilidade mais completa

- Tela, aba **9 · Viabilidade**:
  - gráfico de **custo acumulado**: sistema atual e cada alternativa, ano a ano, com o ponto de
    breakeven (sem desconto) e o payback (descontado pela TMA) marcados;
  - gráfico de **fluxo de caixa acumulado** por alternativa;
  - gráfico de **sensibilidade** (economia, CAPEX, tarifa) a partir de `sensibilidade`, que
    `viabilidade.calcular` já devolve.
- `viabilidade.series(resultado)` devolve as séries dos gráficos (custo acumulado do sistema atual
  e de cada alternativa), para a tela e o relatório usarem os mesmos números.
- `orcamento/exportar_viabilidade_docx.py`: relatório para o cliente com premissas, tabela
  comparativa, os gráficos (imagens geradas com matplotlib), classificação de cada alternativa e
  conclusão. Usa o modelo e os estilos de `exportar_docx.py`.
- Fora desta entrega: financiamento com parcelas e cenários pessimista/base/otimista.

### B6 — Documentos

- A proposta ganha **número de revisão** e **validade** (padrão 15 dias); "Gerar proposta" cria
  uma revisão nova com data, e o histórico de revisões fica no arquivo da proposta.
- `exportar_docx.py` passa a gerar também **contrato** e **recibo**, a partir de modelos em
  `modelos/contrato.docx` e `modelos/recibo.docx`, com os dados da empresa e do responsável
  técnico de `dados/kaptek_org.json`.
- PDF: fora desta entrega. O Allan revisa o DOCX no Word e exporta.

### B7 — Plano de ARTs (pedido em 2026-11-11)

Decisão do Allan: a ART **entra no preço**, inclusive na execução. Um orçamento pode exigir mais
de uma ART, então a ferramenta precisa dizer **quantas e quais** e somar a taxa de cada uma pela
faixa do valor do contrato.

- Catálogo: cada serviço ganha `art: {atividade, modalidade}`. A atividade pode ser projeto,
  execução, fiscalização/acompanhamento, laudo/vistoria, manutenção/PMOC ou consultoria. A
  modalidade pode ser mecânica, elétrica ou civil. A mão de obra de execução da aba Execução ganha
  a mesma marca, por função (eletricista conta como modalidade elétrica).
- Novo `orcamento/arts.py`: `planejar_arts(opcao, cat, params) -> [ART]`. Cada ART tem:
  - tipo: obra/serviço, múltipla mensal, complementar (aditivo), corresponsabilidade ou do
    subcontratado;
  - profissional/modalidade, atividades, fases vinculadas e valor base (soma do preço das fases
    ou itens vinculados);
  - taxa, calculada por `motor.valor_art`;
  - `no_preco: bool`.
- Regras de sugestão, todas editáveis, ficam em `parametros["art"]["regras"]` e não fixas no
  código. São **provisórias** e precisam ser confirmadas com o CREA-RJ:
  1. Atividades de natureza diferente (projeto, execução, fiscalização, laudo) ficam em ARTs
     separadas. Existe uma chave "agrupar por profissional" que junta as do mesmo profissional.
  2. Modalidade diferente (elétrica) exige ART do profissional dessa modalidade.
  3. Manutenção recorrente usa ART de obra/serviço pela vigência do contrato, ou múltipla mensal.
  4. Subcontratado com ART própria fica listado e fora do preço, ou como repasse, se marcado.
  5. Aditivo gera ART complementar.
- Motor: a soma das ARTs com `no_preco` substitui a ART por fase de hoje. Cada taxa é rateada na
  fase de origem. Propostas antigas sem plano de ARTs continuam com a regra atual (uma por fase
  com serviço), e os preços dos `exemplos/` não mudam.
- Tela: caixa "ARTs previstas" na aba Preço (sem aba própria), com tabela simples (no preço,
  profissional, atividade, valor base, taxa) e o total que vai para o preço. Prévia visual em
  `app/pages/2_Prévia_dos_próximos_blocos.py`.
- Proposta (DOCX): lista as ARTs previstas e diz quais estão inclusas e quais são do
  subcontratado.

### Ajustes de 2026-11-11 (aprovados pelo Allan)

A comparação com o OrçaFascio (orçamento de obra civil sobre a SINAPI e outras bases oficiais)
e com os softwares de PMOC mostrou que nenhum junta projeto, execução, ART, ABRAVA e
viabilidade. O plano fica mais enxuto:

1. **Nova ordem de entrega:**
   1. B2 (execução + BDI) e B7 (ARTs), que mudam o preço direto;
   2. B6 (documentos);
   3. painel de comparação (B3 + B4);
   4. relatório de viabilidade (B5).
2. **B3 e B4 viram um painel só.** A ABRAVA é uma coluna da comparação, com o detalhe numa caixa
   recolhível na aba de preço, sem aba própria.
3. **Execução sobre composições SINAPI** (B2): cada item aponta para uma base (`sinapi` ou
   `propria`). A SINAPI dá o HH e o material de referência; os fatores de produtividade valem por
   cima. A tela escolhe encargos sociais com ou sem desoneração. A base própria continua para os
   itens que a SINAPI não cobre, como VRF e comissionamento.
4. **Curva ABC** dos itens e insumos da execução (classes A ≤ 80%, B ≤ 95%, C resto), na aba
   Execução e na XLSX.
5. **Reaproveitamento:** duplicar proposta, modelos (kits como "split 12k padrão") e importação
   de lista de equipamentos pelo Excel.
6. **Correção por índice** começa com o fator digitado à mão e a fonte anotada. A importação das
   séries de INCC, IPCA e IGP-M fica para depois.
7. **Verificação:** revisão completa só no motor de preço. Na tela, só uma checagem rápida de que
   abre sem erro.

Prévia visual atualizada em `app/pages/2_Prévia_dos_próximos_blocos.py`.

## 4. Dados e arquivos

- Criar: `orcamento/{escopos,erros,execucao,bdi,unidades,tabela_referencia,honorario_abrava,ajustes_honorario,exportar_viabilidade_docx}.py`;
  `dados/execucao.json`; `dados/tabelas/cehop_se_2023.json`; `dados/referencias_publicas/*.csv`;
  `modelos/{contrato,recibo}.docx`; testes em `testes/`.
- Modificar: `orcamento/{proposta,motor,referencias,viabilidade,exportar_xlsx,exportar_docx,cli}.py`;
  `app/app.py`; `dados/{catalogo,fontes}.json`; `README.md`; `.gitignore` (`dados/local/`).
- `app/app.py` já tem 1.495 linhas. Cada aba nova entra em arquivo próprio em `app/abas/`
  (`execucao.py`, `referencias_preco.py`, `abrava.py`), e `app.py` só as chama. As abas antigas
  não são movidas nesta entrega.

## 5. Erros

- Entrada inválida no motor levanta `ErroEntrada`; a tela mostra a mensagem em português ao lado
  do campo e não derruba a sessão.
- Tabela sem a faixa pedida, índice ausente, referência sem data: a conta segue com aviso na
  memória de cálculo, nunca com valor inventado.
- Parâmetros ABRAVA ausentes: a coluna ABRAVA aparece como "não configurado".

## 6. Testes e verificação

- TDD em cada tarefa. Bateria: `cd propostas && python -m pytest -q`.
- Casos fixos: preços dos `exemplos/` inalterados; obra de referência (R$ 44.921,49); exemplos de
  cálculo da tabela CEHOP; caso fictício do ABRAVA do plano T1.
- BDI: o exemplo do spec (AC 4%, seguro e garantia 0,8%, risco 1,27%, despesas financeiras 1,23%,
  lucro 7,4%, impostos 6,15%) dá 22,88%; BDI implícito de 484,88 sobre 2.181,22 dá 22,23%.
- XLSX: o teste de recálculo com LibreOffice confere planilha × motor nos blocos B1, B2 e B3.
- Tela: `testes/test_app.py` (AppTest do Streamlit) cobre as abas novas; ao fim de cada bloco,
  capturas de tela feitas com Playwright vão para o Allan.
- CLI: `python -m orcamento.cli exemplos/hvac_retrofit_fases.json --xlsx --docx --viabilidade
  --saida saida/` continua funcionando; ganha `--relatorio-viabilidade`.

## 7. Pendências do Allan

1. Ordem dos blocos, conteúdo da viabilidade e formato dos documentos: as escolhas acima são
   sugestão do autor.
2. Valores reais da empresa: custo/h e taxa por perfil, overhead, margem, BDI, produtividades de
   execução e custo/h por função. Hoje são provisórios.
3. Regime tributário (Simples ou Lucro Presumido) e, no Simples, anexo e faixa.
4. Tabela oficial da ABRAVA e confirmação da fórmula.
5. Dois links não abriram: o da SES-SP recusa a conexão e o da SEIOP-RJ bloqueia o acesso
   automático. Se forem importantes, enviar os PDFs.
6. Índice de correção: decidido em 2026-11-09 — INCC, IPCA e IGP-M, à escolha na tela. Falta o
   Allan importar as séries (ou dizer de onde tirá-las) e dizer qual é o padrão.
