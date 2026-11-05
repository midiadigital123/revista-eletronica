---
title: "O SVG enviado pelo design passa por lista branca de CSS, porque lista negra sempre deixa uma propriedade de layout escapar"
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 33, tokens: 177448 }
id: l-705761ad
scope: repo
status: active
src: agent
touches:
  - state.md
  - docs/design-revista-impressa.md
  - docs/modelo-er.md
  - plans/revista-express-django.md
  - app/nucleo/admin/bloqueio.py
  - app/nucleo/servicos/bloqueio.py
  - app/nucleo/static/nucleo/bloqueio.js
  - app/nucleo/templates/nucleo/bloqueio_change_form.html
  - app/nucleo/tests/test_bloqueio.py
  - app/nucleo/urls/__init__.py
---

## Decided
- O SVG do F2 vai inline no preview do admin e no zip, então o sanitizador aceita só o necessário: seletores feitos de .classe/#id, nenhuma at-rule, só url(#id) e uma lista branca de propriedades de pintura (fill, stroke, opacity, font, clip, mask e afins). Qualquer coisa fora disso recusa o arquivo inteiro.
- O <svg> raiz perde style, width, height, x, y, class, overflow e transform; só o viewBox fica.
- <style>, <title> e <desc> só aceitam texto: os filhos são descartados.

## Tried and ruled out
- Lista negra de propriedades (position, inset, z-index...): a segunda revisão cobriu a tela do admin com margin negativa, width em vw e transform pela class do raiz.
- Sanitizar só o .text do <style>: o tail de um filho (<style>.a{}<g/>CSS cru</style>) é CSS para o navegador e passava sem filtro, incluindo @import e url externa.
- Regex url\(.*?\) com re.S e busca de id em lista: quadráticas; 3 MB custavam horas de CPU.
- Trocar url externa por none em silêncio: dois caminhos (remover e recusar) aumentam a superfície de erro.

## Watch out
- O SVG real do Illustrator traz um PNG de ~500 KB em <image href="data:image/png;base64,...">; por isso data:image fica fora do limite de 4 KB por atributo, validado por regex linear.
- Atributo data-* com ":" (nome de camada) é só removido, não recusa.
- A capa só confere a assinatura mágica (sem Pillow): quem serve a capa precisa mandar nosniff e Content-Type fixo.

In the code: app/nucleo/servicos/arquivos.py (sanitizar_svg, receber_svg, receber_capa); limites 1 MB por <style>, 4 KB por atributo, 200 mil nós, profundidade 100, 1.000 <use>, 5.000 ids; decisões D-137 e D-145 no state.md.
