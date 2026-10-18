# Propostas KAPTEK: escopo e preço por formulários

Ferramenta local para montar propostas comerciais de engenharia com escopo e preço
rastreáveis. Serve para um turnkey ou para a participação em etapas isoladas:
cálculos, projeto e desenhos (2D, 3D ou BIM), simulações, obra, comissionamento e
ensaios de certificação.

Você escolhe os serviços do catálogo e preenche o formulário de cada um (área, TR,
nº de difusores, vasos, máquinas, GHE...). A ferramenta calcula as horas por
perfil, os custos diretos, o preço nos três modelos e o prazo, e gera:

- uma **planilha XLSX** com fórmulas vivas: todas as opções lado a lado, editável;
- a **proposta DOCX** no template aprovado da KAPTEK, uma por opção.

## Como abrir

Windows: dê **dois cliques em `iniciar.bat`**. Na primeira vez ele cria o ambiente e
instala as dependências, o que leva alguns minutos. Depois a interface abre no navegador.

Linux/macOS: `./iniciar.sh`.

Sem interface, pela linha de comando:

```bash
python -m orcamento.cli exemplos/hvac_consultoria_2d_3d_bim.json --xlsx --docx --saida saida/
```

## Fluxo na interface

1. **Dados gerais**: cliente, objeto, UF (alerta de visto no CREA fora de RJ/SP), distância,
   área e o contexto que ajusta as horas: complexidade, documentação existente, acesso,
   urgência e risco.
2. **Escopo**: escolha a disciplina e o tipo, adicione o serviço e preencha o
   formulário dele. A prévia mostra as atividades e as horas por perfil. Para orçar em níveis
   diferentes (2D, 3D, BIM), use **Duplicar com nível**.
3. **Fornecimento e execução**: materiais, equipamentos, mão de obra e subcontratos do
   turnkey, cada categoria com seu BDI.
4. **Preço**: escopo fechado, hora técnica (estimado e teto) e % sobre a obra. Mostra também
   o preço mínimo (margem zero), a margem efetiva de cada modelo e o comparativo das opções.
   Os parâmetros comerciais desta proposta ficam no expansor.
5. **Prazo e pagamento**: Gantt por etapa e parcelas editáveis, que devem somar 100%.
6. **Exportar**: XLSX e DOCX. Antes de liberar, confere margens e logo do padrão KAPTEK
   e lista os campos que ainda faltam preencher.
7. **Catálogo e parâmetros**: edite a produtividade das atividades, os custos diretos, o
   formulário (JSON) e os parâmetros da empresa. Inclui uma calculadora de custo-hora.
8. **Calibração**: registre as horas realizadas de um projeto encerrado. O fator sugerido
   por atividade (mediana de realizado ÷ estimado) pode ser aplicado ao catálogo.

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
custo dos serviços = MO + overhead + diretos (instrumentos, terceiros, deslocamento, ART)
preço dos serviços = (custo + contingência) ÷ (1 − impostos − margem)
preço total        = preço dos serviços + Σ fornecimentos × (1 + BDI da categoria)
```

Hora técnica: horas × taxa de venda do perfil + reembolsáveis × (1 + administração) ÷ (1 − impostos).
O teto aplica a contingência às horas.

% sobre a obra: % × valor da obra informado (ou o custo dos fornecimentos).

O deslocamento é calculado pelos dias de campo, com três faixas de distância: isento, ida e
volta diária, viagem com diárias. O cronograma divide as horas de cada etapa pela equipe
(8 h/dia); as etapas seguem em sequência. As exclusões do serviço que outro item da mesma opção
anula não entram na proposta. Exemplo: "TAB, salvo se contratado" some quando o TAB está na
opção.

A planilha refaz todas essas contas em fórmulas, e os testes conferem que, depois de recalcular
no LibreOffice, ela dá o mesmo resultado do motor.

## Catálogo (v1)

| Disciplina | Serviços |
|---|---|
| HVAC-R | carga térmica, projeto 2D/3D/BIM, as-built 2D/3D/BIM, desempenho real × projeto, TAB, CFD, simulação energética, PMOC, qualidade do ar (RE 09), comissionamento, plano emergencial, viabilidade (CAPEX/OPEX/payback) |
| Mecânica e utilidades | ar comprimido, vapor e condensado, redes de gases, bombeamento, inspeção NR-13, prontuário NR-13, ensaios de pressão |
| Segurança do trabalho | NR-12, insalubridade (NR-15), periculosidade (NR-16), LTCAT, PGR, inspeção NR-10/33/35, perícia |
| Hidráulica e incêndio | hidrossanitário, SPCI, aprovação no CBMERJ, vistoria de incêndio, teste de hidrantes e bombas |
| Geral | acompanhamento de obra, gerenciamento de obra (turnkey), visita técnica, reuniões |

> **As produtividades são uma referência inicial (estimativa), não dados de mercado medidos.**
> Os custos/h, os BDIs e a taxa de ART também são valores iniciais. Ajuste-os aos seus custos
> reais na aba 7 e calibre com as horas realizadas na aba 8.

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
├── app/app.py              interface (Streamlit)
├── orcamento/              motor, catálogo, exportadores XLSX/DOCX, calibração, CLI
├── dados/catalogo.json     serviços, formulários e produtividades (editável pela aba 7)
├── dados/parametros.json   custos/h, impostos, margem, contingência, BDI, deslocamento
├── dados/historico.json    horas realizadas (aba 8)
├── dados/kaptek_org.json   dados institucionais, extraídos da biblioteca da marca
├── modelos/                template de proposta aprovado e logo
├── exemplos/               consultoria HVAC 2D/3D/BIM, NR-13, SPCI, turnkey VRF
└── testes/                 pytest: motor, catálogo, exportação (inclui recálculo no LibreOffice) e app
```

Testes: `python -m pytest testes -q`. O teste de recálculo é pulado quando o LibreOffice não
está instalado.

## Responsabilidade técnica

A proposta e os documentos técnicos que dela resultam só produzem efeito acompanhados da ART
registrada e quitada (Lei 6.496/1977). Para atuar fora de RJ e SP, é preciso visto no CREA do
estado (Lei 5.194/1966, art. 58); a ferramenta avisa quando a UF exige.
