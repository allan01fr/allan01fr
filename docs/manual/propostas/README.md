# Manual da ferramenta de propostas KAPTEK

Última atualização: 2026-11-22 (commit 50eb649)

## O que é

Ferramenta em tela (Streamlit) para montar propostas comerciais de engenharia com escopo e preço rastreáveis. A proposta tem **opções** (A, B...) e cada opção tem **fases** (por exemplo Projeto, Acompanhamento de obra, Execução). Cada fase tem a sua forma de cobrança: **Escopo fechado**, **Hora técnica**, **% da obra** ou **Pacote de horas**.

Você escolhe serviços do catálogo, preenche o formulário de cada um, e a ferramenta calcula horas, custos, preço, prazo e pagamento. No fim gera a planilha XLSX, as propostas DOCX, contrato, recibo e PDFs.

## Como abrir

**No computador (Linux/macOS):** na pasta `propostas`, rode `./iniciar.sh`. Na primeira vez ele instala as dependências (alguns minutos, precisa de Python 3.11 ou mais novo) e abre a tela no navegador (porta 8501). No Windows, use `iniciar.bat`. As propostas e os parâmetros ficam na sua máquina.

**Prévia online (Streamlit Community Cloud):** abre no navegador, inclusive no celular, sem instalar nada. O passo a passo para publicar está em `propostas/README.md`, seção "Prévia online". Cuidados:

- O que é salvo pela tela (parâmetros, catálogo, histórico, bases importadas) fica no servidor da prévia e pode sumir. Para guardar uma proposta, use **💾 Salvar proposta (.json)**.
- A prévia hiberna depois de 12 horas sem acesso. Ao abrir o link, clique em **Yes, get this app back up!**.
- No celular, feche a barra lateral («) depois de carregar um exemplo para ver a proposta.

## Fluxos típicos

**A. Só projeto**
1. Barra lateral, **Nova proposta**, tipo "Só projeto" ([00](00-barra-lateral-e-nova-proposta.md)).
2. Aba 1: cliente, objeto, UF, contexto ([01](01-dados-gerais.md)).
3. Aba 2: preencha o formulário dos serviços ([02](02-escopo.md)).
4. Aba 4: confira preço e margem ([04](04-preco.md)); aba 5: pagamento ([05](05-prazo-e-pagamento.md)).
5. Aba 6: **Gerar planilha e propostas** ([06](06-exportar.md)).

**B. Projeto + acompanhamento + execução**
1. **Nova proposta**, tipo "Projeto + acompanhamento + execução" ([00](00-barra-lateral-e-nova-proposta.md)).
2. Aba 1 e aba 2 como acima ([01](01-dados-gerais.md), [02](02-escopo.md)).
3. Aba 3b: aplique um kit ou lance os itens de execução, ajuste a configuração e clique **Levar execução para o preço** ([03b](03b-execucao.md)). Isso passa o acompanhamento para % sobre a execução.
4. Aba 4: confira a cobrança de cada fase, as ARTs e os avisos ([04](04-preco.md)).
5. Abas 5 e 6 como acima.

**C. Só execução (obra)**
1. **Nova proposta**, tipo "Só execução (obra)".
2. Lance materiais e mão de obra na aba 3 ([03](03-fornecimentos.md)) ou na aba 3b ([03b](03b-execucao.md)); preencha o prazo de execução.
3. Aba 4: o preço vem dos fornecimentos com BDI ([04](04-preco.md)).
4. Aba 6: exportar ([06](06-exportar.md)).

**D. Laudo**
1. **Nova proposta**, tipo "Inspeção com laudo de conformidade".
2. Abas 1 e 2: dados do cliente e formulário do serviço de inspeção.
3. Aba 4 e aba 6. As horas desse serviço são iniciais: calibre depois na aba 8 ([08](08-calibracao.md)).

**E. Estudo de viabilidade para o cliente:** ver [09](09-viabilidade.md).

## Índice das seções

| Arquivo | Tela |
|---|---|
| [00-barra-lateral-e-nova-proposta.md](00-barra-lateral-e-nova-proposta.md) | Barra lateral: número, opção, salvar/abrir, exemplos, Nova proposta |
| [01-dados-gerais.md](01-dados-gerais.md) | Aba 1 · Dados gerais |
| [02-escopo.md](02-escopo.md) | Aba 2 · Escopo |
| [03-fornecimentos.md](03-fornecimentos.md) | Aba 3 · Fornecimentos e subcontratações |
| [03b-execucao.md](03b-execucao.md) | Aba 3b · Execução |
| [04-preco.md](04-preco.md) | Aba 4 · Preço |
| [05-prazo-e-pagamento.md](05-prazo-e-pagamento.md) | Aba 5 · Prazo e pagamento |
| [06-exportar.md](06-exportar.md) | Aba 6 · Exportar |
| [07-catalogo-e-parametros.md](07-catalogo-e-parametros.md) | Aba 7 · Catálogo e parâmetros (com calculadora de BDI) |
| [08-calibracao.md](08-calibracao.md) | Aba 8 · Calibração |
| [09-viabilidade.md](09-viabilidade.md) | Aba 9 · Viabilidade |
| [10-bases-de-referencia.md](10-bases-de-referencia.md) | Aba 10 · Bases de referência |
| [99-previa-dos-proximos-blocos.md](99-previa-dos-proximos-blocos.md) | Página "Prévia dos próximos blocos" (maquete) |

## Regra de manutenção

Toda mudança visível ao usuário atualiza a seção correspondente (texto e linha nova no "Histórico") no mesmo commit.
