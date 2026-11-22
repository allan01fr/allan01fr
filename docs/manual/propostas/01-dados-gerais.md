# 1 · Dados gerais

**Para que serve**
Registra o cliente, o objeto e a data da proposta, e define o contexto que multiplica as horas dos serviços (complexidade, documentação, acesso, urgência, risco).

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Razão social do contratante | Nome do cliente | Entra nos nomes dos arquivos |
| Contato (nome / cargo / e-mail / telefone) | Contato do cliente | |
| Endereço do objeto, Cidade, UF | Local do trabalho | UF fora de RJ e SP mostra aviso de visto no CREA (Lei 5.194/1966, art. 58) |
| Signatário do contratante (nome e cargo) | Quem assina pelo cliente | Usado nos documentos |
| Objeto da proposta (uma frase precisa) | Descrição do que será feito | |
| Data de emissão | Data da proposta | |
| Validade (dias corridos) | Prazo de validade | 1 a 180 |
| Vencimento das faturas (dias) | Prazo de pagamento das faturas | 0 a 120 |
| Complexidade, Documentação existente, Acesso, Urgência | Fatores que multiplicam as horas | Cada opção mostra o fator, por exemplo "(×1,00)"; valores vêm do catálogo |
| Risco do escopo (contingência) | Baixo, Médio ou Alto, com o percentual de contingência | Percentuais são os da proposta (aba 4, Parâmetros comerciais) |
| Distância da base até o local (km) | Calcula deslocamento | Acima do raio isento, entra como custo direto |
| Área de referência (m²) | Só para o indicador R$/m² | 0 = não calcular |
| Duplicar proposta | Cria uma cópia com ids novos | Zera número, revisão, data e nome do cliente |

**Passo a passo**
1. Preencha razão social, endereço, cidade e UF.
2. Escreva o objeto em uma frase.
3. Ajuste data, validade e vencimento.
4. Em "Contexto que ajusta as horas", escolha os fatores reais da obra.
5. Informe a distância e, se quiser R$/m², a área.

**Como o cálculo funciona**
Os fatores de complexidade, documentação, acesso e urgência multiplicam as horas das atividades que dependem deles. Cada serviço pode trocar a complexidade na aba 2 ("Ajustes deste serviço"). O risco escolhido soma uma contingência percentual ao custo da fase. O deslocamento só entra quando a distância passa do raio isento definido nos parâmetros comerciais.

**Cuidados e limitações**
- Os valores dos fatores e das contingências são do catálogo e dos parâmetros; confira se refletem a sua prática.
- Duplicar proposta troca a proposta aberta pela cópia; salve antes se quiser manter a original.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
