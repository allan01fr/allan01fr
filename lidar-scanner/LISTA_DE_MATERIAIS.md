# Lista de materiais (BOM)

A lista parte do [BOM do mandeye_controller](referencias/mandeye_controller/doc/BIM.md).
Ela foi adaptada para Raspberry Pi 5, SSD NVMe e câmeras, chegando perto do Peppe's Ghost.

> Os preços são estimativas em R$ (out/2026) para compra no Brasil.
> Itens importados (Mid-360, cabo M12) incluem imposto de importação.
> Confira os preços antes de comprar. O Mid-360 sozinho é cerca de 60–70% do custo.

## 1. Núcleo (obrigatório na fase 1)

| # | Item | Qtd | Especificação / modelo | Preço est. (R$) | Observação |
|---|---|---|---|---|---|
| 1 | LiDAR **Livox Mid-360** | 1 | 360°×59°, 0,1–40 m, IMU ICM40609 interna, 9–27 V | 6.000–8.000 | Comprar na loja Livox/DJI. Esgota com frequência |
| 2 | Cabo do Mid-360 | 1 | Amphenol M12A12FL12AFLSD001 (M12 12 pinos) **ou** cabo "three-wire aviation connector" da Livox | 150–400 | O cabo Livox já vem separado em RJ45 e alimentação, o que dispensa crimpar |
| 3 | Conector RJ45 + capa | 2 | Cat5e/Cat6 | 10 | Só se usar o cabo M12 cru (ver fiação) |
| 4 | **Raspberry Pi 5** | 1 | 8 GB RAM (o FAST-LIO no aparelho precisa de RAM) | 800–1.100 | O Pi 4 8 GB também funciona |
| 5 | Cooler ativo oficial Pi 5 | 1 | Active Cooler | 50–80 | Obrigatório: o SLAM ocupa a CPU em 100% |
| 6 | cartão microSD | 1 | 32 GB A2 | 50 | Só para o sistema operacional |
| 7 | Armazenamento dos scans | 1 | HAT M.2 NVMe para Pi 5 + SSD 256–512 GB **ou** pendrive USB 3 de 128 GB (padrão Mandeye) | 300–600 | O SSD é o que o Peppe's Ghost usa |
| 8 | Bateria | 1 | Li-ion 4S (14,4–16,8 V), ≥ 2.500 mAh, com BMS **ou** bateria de ferramenta 12–18 V + adaptador impresso | 200–500 | O Mandeye usa a DJI RB1/BG37 (cara). A comunidade usa bateria Parkside 12 V |
| 9 | Conversor DC-DC step-down | 1 | entrada 9–24 V → **5,1 V / 5 A** (USB-C ou bornes) | 50–120 | O Pi 5 precisa de 5 A. Conversores de 3 A causam *undervoltage* |
| 10 | Chave liga/desliga | 1 | gangorra ou alavanca, 10 A | 10 | No positivo da bateria |
| 11 | Fusível + porta-fusível | 1 | lâmina 5 A | 15 | Proteção da bateria |
| 12 | Conectores de força | 2 pares | XT30 ou XT60 | 20 | |

## 2. Interface (botões, LEDs, buzzer), igual ao Mandeye

| # | Item | Qtd | Especificação | Preço est. (R$) |
|---|---|---|---|---|
| 13 | Botão pulsador 12 mm | 2 | Onpow GQ12B (V12B-12W-A) ou equivalente NA | 30–60 |
| 14 | LED 5 mm | 3 | vermelho, verde, amarelo | 3 |
| 15 | Resistor 220 Ω 1/4 W | 3 | um por LED | 1 |
| 16 | Buzzer ativo 5 V | 1 | | 5 |
| 17 | Jumpers fêmea-fêmea | ~10 | 20 cm | 10 |
| 18 | Pogo pins 2 mm × 11,3 mm | 4 | contato com a bateria (opcional, depende do suporte) | 20 |

## 3. Cor / câmeras (fase 4, opcional)

| # | Item | Qtd | Especificação | Preço est. (R$) | Observação |
|---|---|---|---|---|---|
| 19 | Câmera Pi | 2 | Camera Module 3 Wide (simples) **ou** Global Shutter Camera + lente M12/CS (melhor contra borrão de movimento) | 250–600 cada | O Pi 5 tem 2 portas CSI, como no Peppe's Ghost |
| 20 | Cabo flat Pi 5 (22→15 pinos) | 2 | 200–300 mm | 20 cada | O Pi 5 usa o conector mini |

## 4. Mecânica

| # | Item | Qtd | Preço est. (R$) |
|---|---|---|---|
| 21 | Filamento PLA ou **PETG** (PETG aguenta mais calor no carro/sol) | 1 kg | 100–150 |
| 22 | Parafuso M3×8 (fixação do Mid-360; normalmente vem com ele) | 4 | — |
| 23 | Parafuso Allen DIN 912 M3×45 + porca DIN 934 M3 | 4 + 4 | 10 |
| 24 | Parafuso M2,5×6 + espaçador M2,5×10 (Pi) | 4 + 4 | 10 |
| 25 | Parafuso Philips M3×8 | 4 | 5 |
| 26 | Porca/insert 1/4"-20 (para tripé/bastão) | 1 | 10 |
| 27 | Insertos roscados M3 a quente (opcional) | 10 | 15 |

## 5. Ferramentas e equipamento

- Ferro de solda, estanho e termorretrátil.
- Alicate de crimpar RJ45 (se usar o cabo M12 cru).
- Multímetro.
- Impressora 3D FDM (mesa de ~220 × 220 mm).
- PC para processamento: Linux ou Windows, 16 GB+ RAM. O HDMapping não usa GPU.

## Custo total estimado

| Configuração | R$ |
|---|---|
| Fase 1–3 (Mid-360 + Pi 5 + SSD + bateria, sem câmera) | **8.000 – 11.000** |
| + Câmeras (fase 4) | + 600 – 1.300 |

Para comparar: o Peppe's Ghost custa cerca de £1.000 para montar (já incluindo o plano de £128)
e £2.950 pronto.

## Fiação (resumo, detalhes em `referencias/mandeye_controller/doc/wiring/wiring.md`)

**Mid-360 (cabo M12, 12 pinos):** pinos 1 e 9 = V+ (9–27 V), pinos 2 e 3 = GND.
Ethernet: 4 (TX+) → RJ45-1, 5 (TX−) → RJ45-2, 6 (RX+) → RJ45-3, 7 (RX−) → RJ45-6.
Pino 8 = PPS e pino 10 = NMEA, usados só com GNSS.

**Raspberry Pi (GPIO, padrão Mandeye):**

| Função | GPIO (pino físico) |
|---|---|
| Botão 1 | GPIO5 (29) → GND |
| Botão 2 | GPIO6 (31) → GND |
| LED verde | GPIO13 (33) |
| LED vermelho | GPIO19 (35) |
| LED amarelo | GPIO26 (37) |
| Buzzer + | GPIO12 (32) |

**Energia:** Bateria → fusível → chave → (a) Mid-360 direto, (b) step-down 5,1 V/5 A → Pi 5.
