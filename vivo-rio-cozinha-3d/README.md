# Vivo Rio — Cozinha de banquetes (subsolo) · modelo 3D de tubulações

Fonte: prancha **TOM001-COZ-PJ-E-R-006-R001** ("Cozinha – pontos elet. e hidr.", R001, 09/01/2006),
memorial de equipamentos COZINHA-SUBSOLO. O projeto hidrossanitário predial (`hidráulica.zip`) não
estava acessível; ver DIV-001.

## Entregáveis (`saida/`)
- `modelo_3d_tubulacoes.html` — visualizador autocontido (Three.js r128 via CDN), abre direto no navegador.
- `pontos.csv`, `trechos.csv`, `divergencias.csv`, `niveis.csv` — separador `;`, decimal `,`.
- `modelo.json` — fonte única de dados (o mesmo JSON embutido no HTML).

## Reconstruir
```
python3 build_data.py   # lê fonte/ e gera saida/modelo.json (IDs estáveis em fonte/registro_ids.json)
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
| Navegador headless (claro, escuro, celular) | 18 de 18 testes OK, sem erro de console (`verificacao/teste_navegador.py`) |
| Escala | 1:96 medida (5 câmaras do memorial, desvio ≤ 0,3 %) — o carimbo diz 1:50 (DIV-002) |

Sobreposição do modelo sobre a prancha: `verificacao/sobreposicao/`. Screenshots: `verificacao/screenshots/`.
Os scripts de verificação recebem o caminho do PDF da prancha, que não está versionado aqui.
