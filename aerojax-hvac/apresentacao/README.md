# Apresentação: as ferramentas por trás do Clima2D

16 slides que explicam, camada por camada, as bibliotecas e ferramentas usadas:
Python, NumPy, JAX, AeroJAX, a física (psicrometria, conforto, CFD), Streamlit,
ezdxf, Matplotlib, pandas, pytest, Git/GitHub e as ferramentas de bastidor.

| Arquivo | Para quê |
|---|---|
| `ferramentas_clima2d.excalidraw` | **apresentação editável** no Excalidraw |
| `ferramentas_clima2d.pdf` | versão para ver ou imprimir sem o Excalidraw |
| `slides/01.png` … `16.png` | cada slide como imagem |
| `gerar_apresentacao.py` | script que descreve o conteúdo dos slides |

## Como abrir no Excalidraw

1. Acesse **https://excalidraw.com** (gratuito, sem cadastro).
2. Menu ☰ (canto superior esquerdo) → **Abrir** → escolha `ferramentas_clima2d.excalidraw`.
   Também funciona arrastar o arquivo para dentro da página.
3. Cada slide é um **quadro** (frame) de 1600 × 900, lado a lado. Use a rolagem ou o
   zoom (Shift+1 mostra tudo).
4. **Para apresentar:** selecione um quadro e use *Ampliar para a seleção* (Shift+2), ou
   exporte um quadro como imagem (menu ☰ → Exportar imagem, com o quadro selecionado).

O arquivo fica no seu computador. O Excalidraw só envia algo para a internet se você
usar o botão de compartilhar ou de colaboração ao vivo.

## Cores

Cada cor representa uma camada da arquitetura, igual em todos os slides:

- vermelho: interface
- amarelo: projeto e arquivos
- verde: física (módulos do Clima2D)
- azul: motor numérico
- roxo: gráficos e tabelas
- cinza: qualidade e bastidores
