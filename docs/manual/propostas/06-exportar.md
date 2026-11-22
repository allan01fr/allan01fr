# 6 · Exportar

**Para que serve**
Gera os arquivos que saem para o cliente: a planilha de cálculo (XLSX), a proposta (DOCX), o contrato e o recibo, além de PDFs e um pacote .zip com tudo.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Aviso amarelo (topo da aba) | Alerta sobre a proposta, por exemplo fator fora do normal | Resolva antes de enviar |
| Gerar planilha e propostas | Cria o XLSX e um DOCX por opção | Aparece só com serviços ou preço de execução |
| 📊 (nome do XLSX) | Baixa a planilha | Fórmulas vivas; inclui a estimativa interna |
| 📄 (nome do DOCX) | Baixa a proposta de uma opção | Não há DOCX para a estimativa interna |
| PDF (ao lado de cada DOCX) | Baixa o PDF daquele documento | Só aparece se houver conversor de PDF |
| Gerar contrato (DOCX) | Baixa o contrato preenchido | Indisponível para estimativa interna |
| Valor do recibo (R$) | Valor que vai no recibo | Vem do preço da opção; pode ser ajustado |
| Referente a | Texto do recibo | Vem do objeto da proposta |
| Gerar recibo (DOCX) | Baixa o recibo | |
| Gerar PDFs | Converte contrato, recibo e demais DOCX em PDF | Mostra "Convertendo para PDF..." |
| Baixar todos os documentos (.zip) | Pacote com XLSX, DOCX, contrato, recibo, PDFs gerados e o relatório de viabilidade (se houver) | |

**Passo a passo**
1. Confira os avisos no topo da aba e corrija o que for necessário nas abas anteriores.
2. Clique em "Gerar planilha e propostas".
3. Baixe a planilha e confira os totais por fase.
4. Baixe cada proposta (DOCX). Se for enviar em PDF, clique em "PDF" ao lado do documento.
5. Em "Contrato e recibo", confira o valor do recibo e o texto "Referente a"; baixe o contrato e o recibo.
6. Clique em "Gerar PDFs" se quiser PDFs de contrato e recibo no pacote.
7. Clique em "Baixar todos os documentos (.zip)" para guardar a versão final.

**Como o cálculo funciona**
A planilha recalcula as fórmulas quando você abre no Excel ou LibreOffice. O contrato e a proposta são preenchidos com os valores que estão na tela no momento da geração.

Se você mudar a proposta depois de gerar os arquivos, aparece a mensagem "A proposta mudou desde a última geração — gere de novo". Os arquivos antigos deixam de ser oferecidos para download até você gerar de novo.

O PDF é gerado pelo LibreOffice. No Windows com Microsoft Word, o PDF também pode ser gerado pelo Word (pacote docx2pdf). Se nenhum dos dois estiver instalado, a tela mostra "PDF indisponível aqui"; nesse caso, salve o DOCX como PDF no Word ou no leitor de PDF.

**Editar o modelo do contrato**
O contrato é preenchido a partir do arquivo `modelos/contrato_padrao.docx`. Os textos entre chaves duplas são substituídos pelos dados da proposta. Campos disponíveis:

| Campo | Conteúdo |
|---|---|
| `{{cliente_nome}}`, `{{cliente_cnpj}}`, `{{cliente_endereco}}`, `{{cliente_signatario}}` | Dados do contratante |
| `{{empresa_nome}}`, `{{empresa_cnpj}}`, `{{empresa_endereco}}`, `{{empresa_resp}}` | Dados da KAPTEK (vêm da configuração da empresa) |
| `{{objeto}}` | Objeto da proposta |
| `{{escopo}}` | Lista do escopo, com entregáveis |
| `{{fases}}` | Fases de execução |
| `{{valor_total}}`, `{{valor_extenso}}` | Preço em reais e por extenso |
| `{{pagamento}}`, `{{prazo_pagamento_dias}}` | Forma de cobrança e prazo de pagamento |
| `{{prazo}}` | Prazos por fase e prazo de execução |
| `{{arts}}` | ARTs previstas |
| `{{foro}}`, `{{data}}`, `{{numero}}`, `{{revisao}}` | Foro, data, número e revisão |

Para editar, abra o arquivo no Word, mantenha os nomes exatamente como estão (com as chaves duplas juntas, sem espaço extra) e salve. Não apague uma chave sem substituí-la por texto fixo, senão o campo deixa de ser preenchido. Ao abrir o contrato no Word, aceite a atualização de campos.

O recibo usa `modelos/recibo_padrao.docx` com os campos `{{cliente_nome}}`, `{{cliente_cnpj}}`, `{{empresa_nome}}`, `{{empresa_cnpj}}`, `{{valor_total}}`, `{{valor_extenso}}`, `{{referente}}`, `{{proposta_numero}}`, `{{numero}}` e `{{data}}`.

**Cuidados e limitações**
- Confira a planilha e a proposta antes de enviar; o sistema confere só o padrão do documento (logo e margens), não o conteúdo técnico.
- A estimativa interna gera apenas a planilha. Não envie a estimativa interna ao cliente.
- A proposta só produz efeito acompanhada da ART registrada e quitada (Lei 6.496/1977). Confirme isso no texto antes do envio.
- Se você alterar o modelo do contrato, peça revisão antes de usar em uma proposta real.
- Os arquivos gerados ficam disponíveis só enquanto a tela está aberta e a proposta não muda: baixe e guarde você mesmo.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
