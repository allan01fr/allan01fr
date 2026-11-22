# Tabelas de referência de preços além da CEHOP-SE (HVAC, RJ)

Data: 2026-11-12. Método: WebSearch apenas. WebFetch falhou (hosts fora da allowlist da sessão: rj.gov.br, carioca.rio, crea-sc.org.br, myside.com.br), então nada abaixo foi aberto na fonte. Itens marcados **[não confirmado]** precisam de checagem manual.

## 1. EMOP-RJ (Sistema de Custos de Obras)
- **Publica:** Empresa de Obras Públicas do Estado do RJ. Site: https://www.rj.gov.br/emop (a prefeitura do Rio tem o SCO-Rio, que é outro sistema).
- **Conteúdo:** Catálogo de Referência (códigos por família) e Boletim Mensal de Custos, com custos compostos (composições) e insumos. Códigos de ar-condicionado vistos em material do governo do RJ: `15.005.0220-0` (instalação de split 36.000 a 60.000 BTU/h) e `18.030.0002-0` (split 12.000 BTU/h, fornecimento). Esses códigos ficam nas famílias 15 (instalações) e 18 (aparelhos). A família 16 não foi verificada.
- **Unidade:** unidade/serviço, por código (un, m, m²). Não é R$/m² nem R$/TR.
- **Atualização:** boletim mensal. Um edital de Maricá cita a "13ª edição, nov/2023" **[não confirmado]**.
- **Acesso:** o edital cita arquivos `EMOP.dbf` e `Custos dos serviços.pdf`, o que indica base DBF e PDF. A página oficial de download não foi aberta, então **gratuidade, URL direta e licença não estão confirmadas**.
- **Fontes:** [edital Maricá](https://www.marica.rj.gov.br/wp-content/uploads/2024/03/QUESTIONAMENTO_III-CP_01-2024-SOMAR.pdf), [material de apoio orçamento AC (SEIOP)](https://www.rj.gov.br/seiop/sites/default/files/arquivos_pagina_basica/MATERIAL%20DE%20APOIO%20ORCAMENTO%20AR%20CONDICIONADO.pdf), [Carta de Serviços EMOP](https://www.rj.gov.br/emop/sites/default/files/arquivos_pagina_basica/Carta_de_Servicos_ao_Cidadao_EMOP_RJ.pdf).
- **Uso na ferramenta:** custo unitário e composição por código, com data-base. Os itens de split e de instalação servem como comparação com a CEHOP-SE. Para obra pública no RJ é a referência que o cliente e o TCE esperam.

## 2. ABRAVA / DNPC (honorários de projeto)
- **Publica:** ABRAVA, Departamento Nacional de Empresas Projetistas e Consultores (DNPC). Site: https://abrava.com.br
- **Conteúdo:** o CREA-SC noticiou que a ABRAVA disponibilizou uma **metodologia para cálculo de honorários**, não uma tabela de valores. Não foi encontrada nenhuma tabela pública de R$/m² ou R$/TR. Conteúdo, data e forma de acesso do documento **[não confirmados]**; pode ser restrito a associados.
- **Fontes:** [CREA-SC](https://portal.crea-sc.org.br/abrava-disponibiliza-metodologia-para-calculo-de-honorarios-em-servicos/).
- **Uso na ferramenta:** método de cálculo (percentual do custo da obra, ou horas × taxa × fatores), implementado como fórmula parametrizável. Não é tabela de preços.

## 3. SINDRATAR (grafia correta; "sindatar" está errado)
- **Entidade:** Sindicato da Indústria de Refrigeração, Aquecimento e Tratamento de Ar, com filiais estaduais: SINDRATAR-SP, **SINDRATAR-RJ** e SINDRATAR-RS. É sindicato patronal do setor, parceiro da ABRAVA. Para o Rio, o relevante é o SINDRATAR-RJ.
- **Tabela de preços/PMOC:** a busca não encontrou nenhuma tabela pública de preços referenciais de serviço, PMOC ou manutenção. Ele atua em eventos e na regulamentação (por exemplo, o evento da lei do PMOC/ar condicionado). Pode haver material só para associados, **[não confirmado]**.
- **Fontes:** [Webarcondicionado, entidades do setor](https://webarcondicionado.com.br/associacoes-conselhos-sindicatos-e-comites-de-ar-condicionado-no-brasil), [Sindratar-RJ, evento (Confea)](https://www.confea.org.br/node/122835).
- **Uso na ferramenta:** possivelmente nenhum. Só vale perguntar ao SINDRATAR-RJ se existe valor referencial de PMOC ou piso salarial para compor mão de obra.

## 4. SINDUSCON-Rio, CUB/m²
- **Publica:** Sinduscon-Rio, segundo a NBR 12721:2006 e a Lei 4.591/64. A CBIC reúne os CUBs estaduais em https://cub.org.br **[não confirmado]**.
- **Conteúdo:** R$/m² por projeto-padrão (R1-N, R8-N, PIS, CAL, CSL, GI e outros), em padrões baixo, normal e alto.
- **Atualização:** mensal, em torno do dia 5 do mês seguinte. A fonte é um guia de terceiros (myside), **[não confirmado]**.
- **Acesso:** a tabela é pública no site do Sinduscon-Rio. Os valores de SP vistos nos resultados (maio/2026) **não valem para o RJ**. Valores do RJ não foram obtidos.
- **Fontes:** [guia CUB RJ (terceiro)](https://myside.com.br/guia-imoveis/cub-rj), [CBIC, NBR 12721](https://cbic.org.br/industria-da-construcao-avalia-processo-para-atualizacao-da-nbr-127212006/).
- **Uso na ferramenta:** o CUB **não contém HVAC**. Serve como (a) estimativa grosseira do custo da obra para calcular honorários como percentual (conforme o método ABRAVA) e (b) **índice de correção** (variação % mensal entre data-base e data da proposta). Manter o rótulo "Referência pelo CUB" com aviso de baixa precisão.

## 5. SINAPI (Caixa), comparação
- **Publica:** Caixa/IBGE. Página: https://www.caixa.gov.br/sinapi
- **Conteúdo:** insumos e composições por UF, com e sem desoneração. O RJ tem preços próprios.
- **Formato e acesso:** ZIP por UF/mês, com XLSX e PDF (relatório de preços de insumos, custos de composições, analítico de composições). **Gratuito.** Licença: dado público, mas a Caixa pede citar a fonte **[não confirmado]**.
- **HVAC:** os itens de ar-condicionado (split, fan coil, dutos) são poucos e aparecem de forma irregular. Não foram verificados códigos específicos. Buscar "condicionador", "split" e "exaustor" no relatório do RJ.
- **Fontes:** [Caixa SINAPI](https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi), [explicação dos relatórios](https://sienge.com.br/blog/tabela-sinapi/).
- **Uso na ferramenta:** importação em lote (XLSX) de custo unitário por código, para comparar com a CEHOP-SE e a EMOP, e para mão de obra e encargos.

## Resumo

| Fonte | Tipo | Uso na ferramenta | Acesso | Prioridade |
|---|---|---|---|---|
| EMOP-RJ | Custo unitário e composição (por código, mensal) | Tabela de preços por código, comparada com a CEHOP-SE; referência RJ | DBF/PDF, provavelmente gratuito [a confirmar] | Alta |
| SINAPI RJ | Custo unitário e composição (mensal) | Importação XLSX, mão de obra e encargos, comparativo | Gratuito, ZIP/XLSX/PDF | Alta |
| CUB Sinduscon-Rio | Índice R$/m² (sem HVAC) | Índice de correção e custo de obra para honorários % | Público, mensal | Média |
| ABRAVA/DNPC | Método de honorários | Fórmula de honorários de projeto | Metodologia, acesso [a confirmar], talvez restrito | Média |
| SINDRATAR-RJ | Sindicato (nenhuma tabela achada) | Possível referência de PMOC ou mão de obra | Contato direto | Baixa |

## O que o Allan precisa fornecer
1. Arquivos da EMOP (boletim e catálogo atuais, DBF/PDF), ou liberar `rj.gov.br` na rede da sessão para baixar.
2. O documento de metodologia de honorários da ABRAVA/DNPC (pode exigir login de associado ou da empresa) e confirmar se a firma é associada.
3. Perguntar ao SINDRATAR-RJ se há valores referenciais de PMOC ou manutenção.
4. Tabela CUB do Sinduscon-Rio do mês corrente (ou liberar `sinduscon-rio.org.br` e `cub.org.br`).
5. ZIP SINAPI do RJ (data-base atual, desonerado e não desonerado), ou liberar `caixa.gov.br`.
6. Decidir a política de uso: tabelas de terceiros como referência interna ou no texto da proposta (licença **[não confirmada]** para EMOP e ABRAVA).
