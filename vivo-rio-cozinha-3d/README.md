# Vivo Rio — Cozinha de banquetes (subsolo) · modelo 3D de tubulações

Fontes:
- **TOM001-COZ-PJ-E-R-006-R001** ("Cozinha – pontos elet. e hidr.", R001, 09/01/2006) — pontos hidráulicos, níveis, paredes.
- **As-built de exaustão do subsolo, Fase 2** (Anexo D do PA-COZINHA-003, 1:35, 27/08/2026) — dutos de exaustão, insuflamento e ar exterior.
- **Fluxogramas TDM001-ARC-PJ-E-R-012** e relatório **PA-COZINHA-003/2026 rev. 02** — prumadas, ventiladores e níveis (+1,50 / +8,36 / +20,93).
- Memorial de equipamentos COZINHA-SUBSOLO.

O projeto hidrossanitário predial (`hidráulica.zip`) não estava acessível; ver DIV-001.

## Entregáveis (`saida/`)
- `modelo_3d_tubulacoes.html` — visualizador 100 % autocontido (Three.js r128, OrbitControls e fontes embutidos; funciona offline). É o arquivo para enviar.
- `artifact_modelo_3d.html` — mesma página com Three.js via CDN (versão leve para publicação).
- `pontos.csv`, `trechos.csv`, `dutos.csv`, `divergencias.csv`, `niveis.csv` — separador `;`, decimal `,`.
- `modelo.ifc` — modelo BIM IFC4 (Design Transfer View) com o mesmo conteúdo: pavimentos (subsolo −2,87, térreo +1,50, laje técnica +8,36, cobertura +20,93), paredes, vãos, ambientes (`IfcSpace`), tubos (`IfcPipeSegment`), pontos (`IfcPipeFitting` / `IfcWasteTerminal`), louças (`IfcSanitaryTerminal`), dutos (`IfcDuctSegment`), coifas, captores e difusores (`IfcAirTerminal`), ventiladores (`IfcFan`) e 9 sistemas (`IfcDistributionSystem`). Cada elemento leva o conjunto de propriedades `Pset_KaptekOrigem` (situação EXTRAÍDO/INFERIDO/PENDENTE, memória de cálculo, motivo, prancha, DIVs). GlobalIds estáveis entre builds (derivados do ID).
- `divergencias.bcf` — BCF 2.1 com um tópico por divergência (DIV-001 a DIV-025): prioridade = gravidade, rótulos = disciplinas, câmera, elementos destacados no IFC e imagem.
- `ifc_guids.json` — ID do modelo → GlobalId do IFC.
- `modelo.json` — fonte única de dados (o mesmo JSON embutido no HTML e convertido para o IFC).

## Reconstruir
```
python3 build_data.py   # lê fonte/ (inclui fonte/dutos_subsolo.py via bloco_dutos.py) e gera saida/modelo.json
python3 build.py        # injeta o JSON no template.html e grava HTML + CSVs
python3 build_ifc.py    # grava modelo.ifc e divergencias.bcf (pip install ifcopenshell)
python3 verificacao/bcf_snapshots.py && python3 build_ifc.py   # imagens dos tópicos do BCF (Playwright) e reempacota
```
Geometria do IFC: tubos com seção circular no DN nominal, dutos com a seção do rótulo, louças/equipamentos como caixas, paredes sem camadas nem material; pontos de espera como cilindros curtos simbólicos. Serve para coordenação e verificação de interferências, não para quantitativo de conexões.

## Verificações (última execução)
| Verificação | Resultado |
|---|---|
| Pontas soltas fora dos limites declarados | 0 (122 pontas em limite: rede IHSD ausente) |
| Pontos sem trecho | 4 (2 esgotos indiretos com descarga livre, 2 canaletas pendentes) |
| Declividades fora de 2–5 % | 0 de 10 |
| Louças invadindo parede | 0 de 12 |
| Louças com folga > 3 cm | 7 (registradas como DIV-012 a DIV-018; 2 bancadas em ilha) |
| Pontos sem parede de referência | 0 |
| Locação × medida independente no vetor | 117 de 129 pontos com diferença ≤ 1 cm (`verificacao/locacao_independente.py`) |
| Dutos: pontas ligadas a outro duto, prumada, captor ou terminal declarado | 54 de 54 |
| Dutos do modelo × as-built (sobreposição pela transformação inversa) | `verificacao/sobreposicao/sobreposicao_dutos_anexoD.png` |
| Navegador headless (claro, escuro, celular, sem rede) | 23 de 23 testes OK, sem erro de console (`verificacao/teste_navegador.py`) |
| IFC: esquema IFC4 + regras WHERE (`ifcopenshell.validate --rules`) | 0 erros |
| IFC × JSON (contagens, posição de pontos/paredes, extremidades de tubos e dutos, seção dos dutos, Pset em todo elemento, sistemas) | 22 de 22 testes OK (`verificacao/teste_ifc.py`) |
| BCF: XML contra os XSD oficiais 2.1, componentes existentes no IFC | OK (`verificacao/teste_ifc.py <pasta_xsd>`) |
| Escala | 1:96 medida (5 câmaras do memorial, desvio ≤ 0,3 %) — o carimbo diz 1:50 (DIV-002) |

Sobreposição do modelo sobre a prancha: `verificacao/sobreposicao/`. Screenshots: `verificacao/screenshots/`.
Os scripts de verificação recebem o caminho do PDF da prancha, que não está versionado aqui.
