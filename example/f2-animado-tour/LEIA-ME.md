# Demo: F2 com animação em cada passo do svg-tour

Abra `index.html` no navegador (duplo clique; funciona por `file://`, como o zip).

Fora do sistema: nada em `app/` foi alterado.

## Comportamento (decidido em 05/11; blocos escondidos desde a revisão do mesmo dia)

- **Visão geral:** o fundo e o título se montam; os blocos ainda não visitados ficam escondidos.
- **1ª visita a um passo:** enquanto a câmera do tour se move, o conector leva um ponto amarelo do
  descritor até o bloco, e o bloco se monta quando a câmera pousa.
- **Passo já visto:** o bloco aparece pronto, sem tocar a animação de novo.
- **Troca de passo no meio da animação:** a cena em andamento é concluída na hora.
- **Modo Explorar:** tudo o que falta aparece pronto.

Com `prefers-reduced-motion`, ou com um SVG fora da árvore esperada (aviso no console), nada anima
e o tour fica como hoje.

## Arquivos

- `index.html`: F2 da revista **SAEGO · LP** do banco de dev (05/11), com SVG, modais e `dados-tour`
  como o sistema gera.
- `f2/svg-tour.js`, `f2/svg-tour-modal.js`, `f2/revista.css`: cópias sem alteração de `app/nucleo/static/revista/f2/`.
- `f2/f2-init.js`: cópia com **2 linhas a mais**: `maxZoom: 2.6` (teto de zoom dos passos) e `window.f2Tour = t`.
- `animacao.js`: motor de efeitos de `example/infografico-animado/fonte/animacao.js`, com uma
  cena por passo. Usa só os eventos `svgtour:change` e `svgtour:mode` do tour.
- `animacao.css`: regra que vence o `opacity: 1 !important` do tour no passo ativo, base da página e escala do tour (`--u` de 13 a 15px no desktop, 16px no toque).

## Ponto frágil

As peças são achadas pela ordem dos filhos no SVG, e os conectores usam coordenadas fixas. Se o
design reexportar com outra ordem, a animação se desliga sozinha (checagem de contagens em `mapear()`).
