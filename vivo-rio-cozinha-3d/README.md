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
- `modelo.json` — fonte única de dados (o mesmo JSON embutido no HTML).

## Reconstruir
```
python3 build_data.py   # lê fonte/ (inclui fonte/dutos_subsolo.py via bloco_dutos.py) e gera saida/modelo.json
python3 build.py        # injeta o JSON no template.html e grava HTML + CSVs
```

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
| Navegador headless (claro, escuro, celular) | 22 de 22 testes OK, sem erro de console (`verificacao/teste_navegador.py`) |
| Escala | 1:96 medida (5 câmaras do memorial, desvio ≤ 0,3 %) — o carimbo diz 1:50 (DIV-002) |

Sobreposição do modelo sobre a prancha: `verificacao/sobreposicao/`. Screenshots: `verificacao/screenshots/`.
Os scripts de verificação recebem o caminho do PDF da prancha, que não está versionado aqui.
