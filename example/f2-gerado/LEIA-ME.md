# F2 gerado a partir de dados (protótipo da fase 0)

Prova que o fascículo F2 pode ser um **SVG gerado de dados** (texto real, `foreignObject` para
texto longo, posições calculadas) carregado no `svg-tour.js` atual **sem alterar o svg-tour**,
aberto por `file://`. Usa os arquivos da demo irmã por caminho relativo (`../f2-animado-tour/f2/`).

`desenho-original.svg` é o desenho original do Illustrator (antes em `app/nucleo/tests/fixtures/f2-lp.svg`):
referência das medidas de `app/nucleo/servicos/f2.py` e `app/nucleo/templates/revista/f2.svg`.

## Gerar e verificar

```bash
python3 gerar.py --check                                        # único teste do gerador; imprime OK
python3 gerar.py                                                # index.html (4 passos)
python3 gerar.py -o index-sem-habilidades.html --desligar habilidades   # 3 passos, layout refluído
NODE_PATH=/home/otavio.peres/dev/revista-express/app/e2e/node_modules node verificar.cjs   # Playwright; PNGs no scratchpad
```

Abrir no navegador: `xdg-open index.html` (ou arraste o arquivo para o Chrome). Não precisa de servidor.

## Dados sintéticos (`dados.json`)

- `descritor.descricao`: D05 de LP, texto plausível.
- `habilidades`: códigos e marcas (I/A/C/R) vêm do seed `app/templates_seed/2026/f2-lp.hbs` (`dlg-p3`);
  os textos de 1EF, 2EF, 4EF, 9EF, 2EM e 3EM foram **alongados ou inventados** (300 a 400 caracteres) para
  testar texto longo; 5EF (C) é síntese do seed; 3EM com marca **R** é invenção (o seed dá A para o EM).
- `tarefas`: etapas e descritores do SVG real; os modais dos itens são placeholder.
- `passos`: adaptados do seed com os nomes certos (no seed, passo2 e passo3 estão trocados).
- `modais`: `habilidades` ← `dlg-p3`, `progressao` ← `dlg-p2` (título corrigido), com cortes de tamanho.

## Critérios

| Critério | O que `verificar.cjs` provou | Precisa de olho humano |
| --- | --- | --- |
| Zoom/pan com `foreignObject` | Tour com 4 e 3 passos, cada passo enquadra o bloco (`*-passo-N.png`); modo explorar a 1200% com texto nítido (`*-zoom-livre.png`); arrasto move a vista sem selecionar texto | Suavidade da animação; comportamento no celular (pinça) |
| Minimapa | `<img>` do minimapa renderizado (`naturalWidth > 0`) e com estilo e texto dos `foreignObject` (`*-minimapa.png`). Exigiu `<style>` dentro do SVG **sem seletor pela classe do `<svg>` raiz** (o minimapa remove `class` do clone, `svg-tour.js:559`) | Legibilidade a 137×91 px |
| Texto longo em caixa fixa | 12 linhas de 32 px com `-webkit-line-clamp: 3` e reticências; nada transborda; texto é DOM real e selecionável (`user-select: text` dentro do SVG) | Se 3 linhas a 8,5 px bastam no passo 2 (`index-passo-2.png`): o bloco é mais alto que o stage em `minScale` 1,6, então o tour ancora e pede arrasto; a legenda fica abaixo da dobra |
| Passo desligado | Sem `f2-habilidades`, sem `dlg-habilidades`, 3 steps, `progressao` sobe para `y = 69`, linha some (`index-sem-habilidades-*.png`) | Se o reflow por coluna fica bom em outras combinações (só `habilidades` foi testado) |
| Acessibilidade mínima | Clique, Enter no botão `+` focado abre o `<dialog>` certo; Escape fecha e devolve o foco ao botão; sem erro de console | Leitor de tela sobre `<text>` + `foreignObject`; `role="button"` vem do `f2-init.js` |

Veredito proposto (06/11, após as capturas): **SVG gerado serve**; os 5 critérios passaram no Chromium. Pendentes de olho humano: altura do bloco de habilidades no passo 2 (ancora e pede arrasto), minimapa a 137×91 px, Safari/Firefox (não há WebKit no Playwright local). Decisão final é do usuário (vira D-228 no `state.md`).
