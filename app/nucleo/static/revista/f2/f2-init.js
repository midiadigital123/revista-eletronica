/**
 * F2 (infográfico svg-tour) na página única da revista (S08; substitui svg-tour/avaliacao-e-curriculo/revista.js).
 *
 * Sem fetch (a página do zip abre por file://, S15): o SVG já está inline em #revista e os
 * textos do tour vêm de <script type="application/json" id="dados-tour">, gerado das seções
 * `abertura`, `passoN` e `dlg-*` do template F2. Ids do SVG têm o prefixo f2- (D-145):
 * seção dlg-xx → botão #f2-btn-action-xx → <dialog id="dlg-xx">.
 */
(function () {
  "use strict";

  // Config do tour (era revista.json); os textos vêm do template.
  var CONFIG = {
    padding: 80,
    minScale: 1.6,
    minimapAuto: true,
    fitButton: false,
    helpOnStart: false, // na página única a ajuda não abre sozinha: roubaria o foco do F1
    helpGeneral: false,
    helpNote: "Toque nos botões amarelos (+) do desenho para abrir o detalhe de cada item.",
    dimOthers: true,
  };

  var raiz = document.getElementById("revista");
  var dados = document.getElementById("dados-tour");
  if (!raiz || !dados || !raiz.querySelector("svg")) return; // sem SVG: a faixa do preview avisa

  var tour = JSON.parse(dados.textContent);

  // Botão do SVG → <dialog> (era BOTOES_MODAL fixo em revista.js).
  var BOTOES_MODAL = {};
  tour.modais.forEach(function (dlg) {
    BOTOES_MODAL["f2-btn-action-" + dlg.slice(4)] = dlg;
  });

  var t = new SvgTour(raiz, Object.assign({}, CONFIG, tour));

  Object.keys(BOTOES_MODAL).forEach(function (id) {
    var el = t.stage.querySelector("#" + CSS.escape(id));
    if (!el) {
      console.warn("revista: botão não encontrado no SVG:", id);
      return;
    }
    var dlg = BOTOES_MODAL[id];
    el.setAttribute("data-modal", dlg);
    el.setAttribute("tabindex", "0");
    el.setAttribute("role", "button");
    el.setAttribute("aria-haspopup", "dialog");
    el.setAttribute("aria-labelledby", "dlgTitle-" + dlg.slice(4));
  });

  SvgTourModal(t);
})();
