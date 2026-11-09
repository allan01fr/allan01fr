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

### B3 — Preço por tabela e comparação com referências

**Forma de cobrança "valor"** (tarefa 5 do T1). A fase pode ter um valor definido:
`preço = valor definido + fornecimentos`. O custo por horas continua calculado e aparece ao lado,
com a margem que resulta.

**Tabela de referência.** `orcamento/tabela_referencia.py`, com dados em `dados/tabelas/*.json`.
Cada tabela declara fonte, órgão, data-base, e uma lista de itens:

```
{id, descricao, unidade ("m2" | "un"), faixas: [{ate, valor}], modo ("cheio" | "escalonado"),
 minimo, observacao}
```

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

Primeira tabela: `dados/tabelas/cehop_se_2023.json` (CEHOP-SE, referência jan/2023, valores
máximos): climatização simples e complexa, as built, compatibilização, orçamento e especificação,
laudo de vistoria, deslocamento e as regras gerais. Testes reproduzem os exemplos de cálculo do
próprio documento (laudo de 3.000 m²; prédio de 12 pavimentos de 500 m²).

**Comparação.** Na aba Preço, cada fase ganha um painel "Referências" com colunas lado a lado:

| Coluna | De onde vem |
|---|---|
| Preço por horas | `motor.precificar_fase` |
| Preço por tabela | `tabela_referencia.calcular`, atualizado por índice |
| Mediana de mercado | `referencias.cesta` sobre os itens ligados à fase |
| ABRAVA (bloco B4) | `honorario_abrava.calcular_abrava` |

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

## 4. Dados e arquivos

- Criar: `orcamento/{escopos,erros,execucao,tabela_referencia,honorario_abrava,ajustes_honorario,exportar_viabilidade_docx}.py`;
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
6. Qual índice usar para trazer as tabelas à data de hoje (INCC, IPCA ou outro).
