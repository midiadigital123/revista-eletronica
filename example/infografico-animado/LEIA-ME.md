# Infográfico animado: Avaliação e currículo

## Arquivos

- `infografico-animado.html`: versão completa num arquivo só (SVG + CSS + JS). Abra no navegador para ver funcionando.
- `fonte/animacao.js`: motor de animação e roteiro. É o arquivo principal para estudar ou modificar.
- `fonte/estilo.css`: estilos da página e dos controles.
- `fonte/pagina.html`: estrutura da página, sem o SVG (há um comentário indicando onde colá-lo).
- `fonte/infografico.svg`: o infográfico original (~840 KB, texto convertido em curvas).

Para trabalhar no código, normalmente basta `fonte/animacao.js`. O SVG é grande e quase todo composto de paths de texto; só a estrutura de grupos importa (ids `f2-fundo`, `f2-titulo`, `f2-passo1` a `f2-passo4`, `f2-linhas`).

## Como o motor funciona (seções numeradas em animacao.js)

1. **Easing**: curvas `out`, `inOut`, `back` (passa do ponto e volta) e `lin`.
2. **Relógio próprio**: `tween(ms, tok, fn)` sobre `requestAnimationFrame`, com pausa, velocidade e modo instantâneo (`tok.instant`), usado para pular etapas. `tok.cancelled` interrompe tudo.
3. **Alvos**: `wrap()` envolve cada elemento num `<g data-wrap>` e anima só esse invólucro via CSS `transform` (com `transform-box: fill-box`), sem tocar no SVG original. `fx(el, estadoInicial, origem)` registra o elemento; `play()` leva do estado inicial ao final. `line()` + `draw()` desenham traços com `stroke-dasharray` / `stroke-dashoffset`.
4. **Efeitos**: `ring()` (anel de chegada) e `travel()` (linha se desenhando com um "pacote" e rastro na ponta, usando `getPointAtLength`).
5. **Câmera**: interpola o `viewBox` até o enquadramento de cada etapa (`fit()` ajusta à proporção do palco).
6. **Mapeamento**: seleciona os elementos do infográfico pelos ids e pela ordem dos filhos. Os conectores originais são ocultados e redesenhados como `<path>` com direção definida (do card para fora).
7. **Roteiro**: array `steps`, cada um com `name`, `frame` (área da câmera) e `run(tok)`.
8. **Player**: `runFrom(i)`, `jump(i)` (executa as etapas anteriores em modo instantâneo) e `reset()`.
9. **Controles**: play/pausa (Espaço), etapas (setas ou clique), velocidade e câmera.

## Para reaproveitar em outro SVG

Mantenha as seções 1 a 5, 8 e 9. Reescreva a 6 (seletores do novo SVG) e a 7 (ordem dos efeitos e enquadramentos). Respeita `prefers-reduced-motion`: nesse caso abre direto no estado final.
