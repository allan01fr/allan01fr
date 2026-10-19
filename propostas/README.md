# Propostas KAPTEK: escopo e preço por formulários

Ferramenta local para montar propostas comerciais de engenharia com escopo e preço
rastreáveis. A proposta é organizada em **fases** (por exemplo: laudo, estudo de viabilidade,
projeto e assessoria de obra), e cada fase tem a sua forma de cobrança: escopo fechado, hora
técnica, % da obra ou pacote de horas.

Você escolhe os serviços do catálogo e preenche o formulário de cada um (área, TR,
nº de difusores, vasos, máquinas, GHE...). A ferramenta calcula as horas por
perfil, os custos diretos, o preço de cada fase e o prazo, e gera:

- uma **planilha XLSX** com fórmulas vivas: todas as opções lado a lado, com o preço por fase;
- a **proposta DOCX** no template aprovado da KAPTEK, uma por opção;
- a **planilha do estudo de viabilidade** para o cliente (breakeven, payback, VPL, TIR, LCC).

## Como abrir

Windows: dê **dois cliques em `iniciar.bat`**. Na primeira vez ele cria o ambiente e
instala as dependências, o que leva alguns minutos. Depois a interface abre no navegador.

Linux/macOS: `./iniciar.sh`.

Sem interface, pela linha de comando:

```bash
python -m orcamento.cli exemplos/hvac_retrofit_fases.json --xlsx --docx --viabilidade --saida saida/
```

### Prévia online (Streamlit Community Cloud)

Para testar no navegador, inclusive no celular, sem instalar nada:

1. Entre em [share.streamlit.io](https://share.streamlit.io) com a conta do GitHub.
2. **Create app** → **Deploy a public app from GitHub**.
3. Repositório `allan01fr/allan01fr`, branch `claude/wonderful-wright-m65umc`, arquivo
   principal `propostas/app/app.py`.
4. Em **Advanced settings**, escolha Python 3.12 e clique em **Deploy**.

As dependências vêm de `app/requirements.txt`. O tema vem de `.streamlit/config.toml` na raiz
do repositório, cópia do `propostas/.streamlit/config.toml`. Um teste garante que os dois pares
de arquivos continuam iguais.

Para restringir o acesso: no app publicado, **Settings** → **Sharing** → **Only specific
people can view this app**, e inclua os e-mails convidados.

Limites da prévia:
- O que é salvo pela interface (parâmetros, catálogo, histórico e bases importadas na aba 10)
  fica no servidor da prévia. É compartilhado por quem usa o link e se perde quando o app
  reinicia ou é atualizado.
- Para guardar uma proposta, use **💾 Salvar proposta (.json)** na barra lateral e carregue o
  arquivo de novo em **📂 Abrir proposta (.json)**.
- A prévia hiberna depois de um tempo sem acesso. Ao abrir o link, clique no botão para
  acordá-la; leva cerca de um minuto.

## Fluxo na interface

1. **Dados gerais**: cliente, objeto, UF (alerta de visto no CREA fora de RJ/SP), distância,
   área e o contexto que ajusta as horas: complexidade, documentação existente, acesso,
   urgência e risco.
2. **Escopo e fases**:
   - a modalidade da opção: proposta em fases ou estimativa interna do valor global;
   - as fases, com nome, cobrança e ordem;
   - os serviços do catálogo, cada um na sua fase, com o formulário preenchido. A prévia mostra
     as atividades e as horas por perfil.

   Para orçar em níveis diferentes (2D, 3D, BIM), use **Duplicar com nível**.
3. **Fornecimentos e subcontratações**: equipamentos, materiais, mão de obra de execução e
   subcontratos, cada categoria com seu BDI. Cada item guarda fonte, código e data-base. A
   **cesta de preços** compara as referências do item (bases e cotações). Na estimativa, informe
   também o lead time dos equipamentos e o prazo de execução.
4. **Preço**:
   - preço total, com a parcela fixa e a estimada;
   - tabela por fase e detalhe de cada fase (cadeia de preço, horas, faturamento mensal do %,
     taxa de desempenho);
   - comparativo das opções;
   - entradas da cobrança de cada fase e parâmetros comerciais da proposta.
5. **Prazo e pagamento**: Gantt com as fases em sequência e o pagamento por fase. As parcelas
   do escopo fechado são editáveis.
6. **Exportar**: XLSX e DOCX. Antes de liberar, confere margens e logo do padrão KAPTEK
   e lista os campos que ainda faltam preencher.
7. **Catálogo e parâmetros**: edite a produtividade das atividades, os custos diretos, o
   formulário (JSON) e os parâmetros da empresa. Inclui uma calculadora de custo-hora.
8. **Calibração**: registre as horas realizadas de um projeto encerrado. O fator sugerido
   por atividade (mediana de realizado ÷ estimado) pode ser aplicado ao catálogo.
9. **Viabilidade**: estudo técnico-econômico para o cliente (seção própria abaixo).
10. **Bases de referência**: importação de tabelas de preço, convenções coletivas, CUB,
    encargos, índices e faixas de ART (seção própria abaixo).

## Proposta em fases e formas de cobrança

Cada fase é precificada sozinha, com a sua ART, porque pode ser contratada separadamente. As
fases correm em sequência no cronograma. Formas de cobrança:

| Cobrança | Como funciona |
|---|---|
| **Escopo fechado** | Preço pela cadeia de custos da fase (laudo, estudo de viabilidade, projeto). Pagamento em sinal + campo + entrega, editável. |
| **Hora técnica** | Horas × taxa de venda, faturadas pelo apontamento; estimado, com teto. |
| **% da obra** | Honorário sobre o valor global da obra, em três formas: **% sobre cada medição** (total estimado = % × valor global; o faturado acompanha as medições aprovadas); **fixo pelo valor global**, faturado na proporção das medições; **parcela fixa + % das medições**. As medições são projetadas mês a mês por curva S ou linear. |
| **Pacote de horas** | Fiscalização e planejamento. **Mensal** (h/mês × meses, saldo acumula ou não) ou **total** sob demanda (N horas, validade, parcelas). Taxa = média do mix de perfis × (1 − desconto); hora excedente com acréscimo opcional. Sem horas informadas, o pacote usa as horas dos serviços da fase. O custo usa as horas vendidas. |

**Taxa de desempenho** (opcional, nas fases de % e de pacote): variável, fora do preço. É a soma
de três critérios, limitada a um teto (% dos honorários da fase), e é paga no recebimento
definitivo da obra:
- participação na economia em relação ao valor global estimado;
- % dos honorários por semana de antecipação do prazo;
- bônus se o retrabalho (custo de retrabalho ÷ valor medido) ficar dentro da meta.

O app e a planilha simulam o potencial num cenário (economia, dias antecipados, meta de
retrabalho). O DOCX traz os critérios, a apuração e o teto.

**Estimativa interna do valor global da obra.** É uma opção à parte, com modalidade
"estimativa", que não gera proposta. Ela reúne:
- equipamentos, materiais e execução com BDI;
- provisão de garantia;
- etapa de suprimentos (lead time);
- checklist das etapas da obra, que podem ser incluídas ou ficar fora da estimativa (por
  exemplo, projeto e assessoria, que são fases da KAPTEK).

O valor dela serve de **base do %** da assessoria, por fornecimentos e execução ou pelo valor
global, e de **CAPEX** na viabilidade.

**Sistema ≠ modalidade.** O sistema é escolhido no formulário de cada serviço:
- climatização: split / multi-split, VRF, self-contained / rooftop ou água gelada;
- ventilação / distribuição de ar: renovação, DOAS, CAV ou VAV, com caixas VAV no projeto, no
  TAB e no comissionamento.

O exemplo `hvac_retrofit_fases.json` tem um retrofit VRF + DOAS em quatro fases (laudo,
viabilidade, projeto, assessoria de obra):
- **opção A**: assessoria por 4% sobre as medições, com taxa de desempenho;
- **opção B**: pacote de 40 h/mês × 4 meses;
- **estimativa interna**: a base de ambas.

Arquivos salvos antes das fases abrem como uma fase única com a cobrança antiga. Os antigos
"turnkey" viram estimativa interna.

## Como o preço é calculado

Horas de cada atividade, por perfil (RT, Eng. sênior, Eng. pleno, Projetista/BIM, Técnico, Estagiário):

```
h = (fixo + unid × q^b) × fatores × fator manual × calibração
```

- `q` é o **driver** da atividade, uma expressão sobre o formulário, por exemplo
  `terminais*amostragem`. Para um campo de opções existem também as variáveis `campo__valor`
  (1 ou 0), como em `area*(nivel__2d + 3.6*nivel__3d + 6.7*nivel__bim)`.
- `b < 1` representa a economia de escala.
- Os fatores vêm do contexto da proposta (complexidade, documentação, acesso, urgência) ou de
  campos de opções do serviço (nível 2D/3D/BIM, fase, tipo de sistema).

Escopo fechado:

```
custo dos serviços = MO + overhead + diretos (instrumentos, terceiros, deslocamento, ART; garantia na estimativa)
preço dos serviços = (custo + contingência) ÷ (1 − impostos − margem)
preço total        = preço dos serviços + Σ fornecimentos × (1 + BDI da categoria)
```

Hora técnica: horas × taxa de venda do perfil + reembolsáveis × (1 + administração) ÷ (1 − impostos).
O teto aplica a contingência às horas.

% da obra e pacote de horas: ver a seção acima. O preço da opção é a soma das fases: parcela fixa
(escopo fechado, pacote, % fixo e parcela fixa) + parcela estimada (hora técnica e % sobre as
medições).

Referência pelo CUB: % × CUB/m² × área (faixa usual de honorários: 2% a 11%).

A **ART** sai da faixa do valor do contrato (Tabela A do Confea). Como o valor depende da
ART, o motor itera até a faixa se estabilizar. O modo valor fixo continua disponível.

O deslocamento é calculado pelos dias de campo, com três faixas de distância: isento, ida e
volta diária, viagem com diárias. O cronograma divide as horas de cada etapa pela equipe
(8 h/dia); as etapas seguem em sequência, fase após fase, e as fases de obra duram os meses da
obra. As exclusões do serviço que outro item da mesma opção
anula não entram na proposta. Exemplo: "TAB, salvo se contratado" some quando o TAB está na
opção.

A planilha refaz todas essas contas em fórmulas: cada opção tem uma matriz de preço com uma
coluna por fase (com `SUMIFS` pela coluna Fase das atividades, dos diretos e dos fornecimentos)
e a coluna Total. A base do % aponta para a célula da estimativa interna. Os testes conferem
que, depois de recalcular no LibreOffice, a planilha dá o mesmo resultado do motor, em todas as
formas de cobrança. A aba **Pesquisa de preços** repete a cesta
de cada item em fórmulas:
- valor, fator de atualização e desvio da mediana;
- referências fora da faixa;
- valor adotado, conferido com o custo unitário usado.

## Estudo de viabilidade (aba 9)

**Linha de base, o sistema atual.** Pode ser descrita de dois modos:
- pela capacidade: TR × kW/TR medido × horas/ano × fator de carga;
- pelo consumo anual medido.

Com o kW/TR de projeto, o estudo mostra quanto o sistema consome acima do previsto no projeto
original e o custo anual dessa perda de desempenho. Também entram:
- tarifa e manutenção anual;
- paliativos (manutenção de emergência), comuns a todas as alternativas: entram no LCC, não
  no fluxo incremental;
- TMA, horizonte (até 30 anos) e reajustes anuais de energia e manutenção.

**Alternativas.** Cada uma tem CAPEX, redução de consumo (%), geração FV (kWh/ano) e
manutenção anual. O CAPEX pode ser **vinculado ao preço de uma opção da proposta** (por
exemplo, a estimativa interna do valor global da obra), mais um extra.

```
economia no ano t = economia de energia × (1 + reajuste da energia)^(t−1)
                  + economia de manutenção × (1 + reajuste da manutenção)^(t−1)
fluxo             = −CAPEX no ano 0, depois a economia de cada ano
```

Indicadores:
- **breakeven**: quando as contas empatam, ou seja, a economia acumulada iguala o CAPEX (o custo
  acumulado do sistema atual cruza o da alternativa), em anos e meses;
- **payback**: quando o projeto se paga, ou seja, a economia acumulada descontada pela TMA devolve
  o investimento com o custo do capital (VPL acumulado = 0), em anos e meses;
- VPL e TIR;
- LCC no horizonte;
- economia mínima no ano 1 para VPL = 0 e margem de segurança;
- consumo comparado ao projeto original;
- classificação: quick win (breakeven ≤ 2 anos), viável, inviável financeiramente ou sem
  economia.

A sensibilidade do VPL é exata: economia ±30%, CAPEX ±20% e tarifa ±20%.

A planilha exportada tem as abas Resumo, Premissas, Alternativas, FluxoCaixa (com gráfico) e
Sensibilidade. É toda em fórmulas: mudar tarifa, TMA, horizonte ou CAPEX recalcula tudo.

## Bases de referência (aba 10)

Nenhuma tabela vem embutida. Baixe o arquivo oficial da entidade e importe. Cada valor fica
gravado com fonte, código, data-base e UF. O banco é local, em `dados/referencias.sqlite`;
a variável `KAPTEK_REFERENCIAS` aponta para outro arquivo.

| Grupo | Entidades no registro (`dados/fontes.json`) |
|---|---|
| Preços | EMOP-RJ, SCO-Rio, SINAPI, SICRO, ORSE, SEINFRA-CE, CPOS/CDHU, SIURB, SUDECAP, Painel de Preços, cotações de fornecedores |
| Convenções coletivas e pisos | SENGE-RJ (engenheiros), SINDRATAR-RJ (refrigeração), SINDISTAL × SINTRAINDISTAL-RJ (instaladores), SINDUSCON-Rio × SINTRACONST-Rio (construção), Mediador/MTE |
| CUB | SINDUSCON-Rio, CBIC |
| ART | Confea (Tabela A) / CREA-RJ |
| Honorários | ABRAVA, IBAPE, Instituto de Engenharia |
| Encargos sociais | SINAPI, por UF |
| Índices | FGV (INCC-M, IGP-M), IBGE (IPCA) |
| Tarifas e BDI | ANEEL; TCU, Acórdão 2.622/2013 |

**O que baixar.** Em ordem de prioridade para propostas de HVAC no RJ:

| O quê | Onde | Frequência | Como entra |
|---|---|---|---|
| SINAPI RJ (insumos e composições) | caixa.gov.br/sinapi → Relatórios Mensais | Mensal | Importar → Preços, preset SINAPI |
| Encargos sociais SINAPI RJ | mesmo pacote do SINAPI | Quando mudar | Quatro percentuais em "Encargos sociais por UF" |
| Catálogo EMOP-RJ | rj.gov.br/emop | Periódica | Importar → Preços, preset EMOP-RJ |
| Convenção SINDRATAR-RJ | Mediador/MTE ou o sindicato | Anual | Importar → Pisos (PDF) |
| CUB/m² RJ | Sinduscon-Rio, até o dia 5 do mês seguinte | Mensal | Digitado na aba Preço |
| Tabela de ART | CREA-RJ | Anual | Conferir as faixas em aba 10 → ART |
| Cotações | fornecedores | Por proposta | Cesta de preços do item |

Conforme o caso:
- SCO-Rio, para obra no município do Rio;
- convenções de instaladores (SINDISTAL) e da construção (SINDUSCON/SINTRACONST), com equipe
  própria de execução;
- SENGE-RJ, se preferir o piso da convenção ao cálculo da Lei 4.950-A;
- IPCA (IBGE, tabela SIDRA 1737) e INCC-M (FGV), para atualizar preços de data-base antiga;
- tarifa de energia (faturas do cliente ou ANEEL), para a viabilidade.

**Importação.**
- XLSX e CSV: o cabeçalho é detectado mesmo com títulos acima dele, e as colunas podem ser
  remapeadas à mão. Há presets para EMOP-RJ, SCO-Rio, SINAPI, SICRO, ABRAVA e um genérico. UF,
  data-base e desoneração são lidos do nome do arquivo, quando existem.
- SINAPI a partir de 2025, com todas as UFs no mesmo arquivo: a coluna cujo cabeçalho é a UF
  informada vira o preço.
- PDF (`pdfplumber`): as tabelas vão para uma grade de revisão obrigatória antes de gravar.
- Índices: número-índice ou variação mensal (%). As variações, como o Banco Central e a FGV
  publicam, são encadeadas num número-índice com base 100; meses faltando ou repetidos são
  recusados.

**Hierarquia de fontes.** No RJ vale o Decreto Estadual 48.929/2024: EMOP, depois SCO-Rio,
SINAPI e SICRO. A busca ordena os resultados por essa prioridade, editável por UF nos
parâmetros desta proposta (aba 10 → Buscar itens), com opção de salvar como padrão da empresa. Em obra do
município do Rio, ponha o SCO-Rio primeiro.

**Cesta de preços.**
- Junta várias referências e cotações do mesmo item.
- Atualiza a data-base pelo índice importado.
- Marca os valores fora de ±25% da mediana e adota a mediana, a média ou o menor valor dos
  que restam.
- Recomenda no mínimo 3 referências.

**Convenções → custo/h.**

```
custo/h = (piso × (1 + adicionais) × (1 + encargos sociais) + benefícios) ÷ horas produtivas
```

O resultado vai para um perfil (na proposta ou na empresa) ou para um item de mão de obra de
execução. Para engenheiros, a Lei 4.950-A/1966 dá 6 salários mínimos para 6 h/dia, mais 25%
por hora excedente. A base pode ser:
- o salário mínimo vigente (R$ 1.621 em 2026);
- a base fixada pelo STF (R$ 1.212, ADPF 53/149/171) mais o reajuste negociado na convenção
  do SENGE.

## Catálogo

| Disciplina | Serviços |
|---|---|
| HVAC-R | carga térmica, projeto 2D/3D/BIM (sistema de climatização + ventilação: VRF, água gelada, DOAS, VAV...), as-built 2D/3D/BIM, desempenho real × projeto, TAB, CFD, simulação energética, PMOC, qualidade do ar (RE 09), comissionamento, plano emergencial, viabilidade (CAPEX/OPEX/breakeven/payback) |
| Mecânica e utilidades | ar comprimido, vapor e condensado, redes de gases, bombeamento, inspeção NR-13, prontuário NR-13, ensaios de pressão |
| Segurança do trabalho | NR-12, insalubridade (NR-15), periculosidade (NR-16), LTCAT, PGR, inspeção NR-10/33/35, perícia |
| Hidráulica e incêndio | hidrossanitário, SPCI, aprovação no CBMERJ, vistoria de incêndio, teste de hidrantes e bombas |
| Geral | acompanhamento técnico / fiscalização de obra, planejamento e controle da obra (assessoria ao contratante), gerenciamento e administração da execução, entrega técnica (start-up, treinamento, manuais, data book), visita técnica, reuniões |

> **As produtividades são uma referência inicial (estimativa), não dados de mercado medidos.**
> Os custos/h, os BDIs e as faixas de ART também são valores iniciais. Ajuste-os aos seus
> custos reais na aba 7, calibre com as horas realizadas na aba 8 e use as convenções da aba
> 10 para o custo/h.

Para criar um serviço, duplique um parecido na aba 7 e ajuste o JSON. Estrutura mínima:

```json
{
  "id": "hvac.novo", "disciplina": "HVAC-R", "tipo": "ensaio", "nome": "...", "descricao": "...",
  "dados": [{"id": "pontos", "rotulo": "Pontos", "tipo": "int", "padrao": 10}],
  "atividades": [{"id": "medir", "nome": "Medições", "entregavel": "Planilha", "etapa": "ensaio",
                  "driver": "pontos", "b": 1.0, "fixo": {"TC": 2}, "unid": {"TC": 0.5},
                  "fatores": ["acesso", "urgencia"], "calibracao": 1.0}],
  "diretos": [{"id": "lab", "nome": "Laboratório", "qtd": "pontos", "valor_unit": 200, "unid": "amostra"}],
  "exclusoes": ["...", {"texto": "...", "exceto_se": ["hvac.tab"], "exceto_fornecimento": true}],
  "premissas": ["..."], "normas": ["..."]
}
```

## Arquivos

```
propostas/
├── app/app.py                interface (Streamlit)
├── orcamento/                motor, cobranças (%, pacote, desempenho), catálogo, viabilidade, referências,
│                             exportadores XLSX/DOCX, calibração, CLI
├── dados/catalogo.json       serviços, formulários, produtividades e etapas da obra completa (aba 7)
├── dados/parametros.json     custos/h, impostos, margem, contingência, BDI, garantia, ART, CUB, hierarquia de fontes
├── dados/fontes.json         registro das entidades de referência (aba 10)
├── dados/referencias.sqlite  bases importadas (local, fora do git)
├── dados/historico.json      horas realizadas (aba 8)
├── dados/kaptek_org.json     dados institucionais, extraídos da biblioteca da marca
├── modelos/                  template de proposta aprovado e logo
├── exemplos/                 consultoria HVAC em fases (2D/3D/BIM), NR-13, SPCI, retrofit VRF + DOAS em fases
└── testes/                   pytest: motor, fases e cobranças, estimativa, catálogo, viabilidade, referências, exportação e app
```

Testes: `python -m pytest testes -q`. Os testes de recálculo no LibreOffice e de extração de
PDF são pulados quando o LibreOffice não está instalado.

## Limites

- As tabelas oficiais (SINAPI, EMOP, SCO-Rio, convenções, CUB, índices) não vêm com a
  ferramenta: são baixadas pelo usuário e importadas.
- As faixas de ART vêm semeadas com a Tabela A do Confea 2026 publicada pelo CREA-MT: até
  R$ 15.000 = R$ 108,39; acima = R$ 285,59. Confira no CREA-RJ e edite na aba 10.
- Não encontrei publicadas na web a convenção do SINDRATAR-RJ nem uma tabela de preços da
  ABRAVA. Entram pela importação genérica ou de PDF quando você tiver os arquivos.
- Os valores dos fornecimentos nos exemplos são ilustrativos.

## Responsabilidade técnica

A proposta e os documentos técnicos que dela resultam só produzem efeito acompanhados da ART
registrada e quitada (Lei 6.496/1977). Para atuar fora de RJ e SP, é preciso visto no CREA do
estado (Lei 5.194/1966, art. 58); a ferramenta avisa quando a UF exige.
