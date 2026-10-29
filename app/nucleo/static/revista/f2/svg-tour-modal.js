// Origem: svg-tour/common/svg-tour-modal.js (commit bcadc29), copiado sem alteração (S08, D-103).
/*!
 * SvgTourModal — abre um <dialog> nativo ao clicar/tocar/focar um nó
 * "[data-modal]" dentro de um SvgTour, em qualquer modo (tour ou
 * livre). Vanilla JS, sem dependências, arquivo separado de propósito:
 * svg-tour.js não sabe nada sobre "conteúdo" ou "modal".
 *
 * Premissas sobre svg-tour.js que este script assume (não mudar um sem
 * revisar o outro):
 *   1. Nenhum handler de pointer da lib chama stopPropagation.
 *   2. stage.setPointerCapture só é chamado dentro de startDrag(), nunca
 *      num pointerdown puro — por isso dá pra rastrear down/up aqui sem
 *      interferir no pan/zoom/inércia da lib.
 *
 * Uso:
 *   SvgTour.load("organograma.svg", "#organograma", options).then(function (tour) {
 *     SvgTourModal(tour);
 *   });
 */
(function (global) {
  "use strict";

  var TRIGGER_SELECTOR = "[data-modal]";
  var UI_SELECTOR = ".svg-tour__ui,.svg-tour__help,.svg-tour__toast";
  var MOVE_THRESHOLD = 8; // px
  var CSS =
    "[data-modal]{cursor:pointer}" +
    "[data-modal]:focus-visible{outline:3px solid #1a56db;outline-offset:2px}";

  function injectCss() {
    if (document.getElementById("svg-tour-modal-css")) return;
    var s = document.createElement("style");
    s.id = "svg-tour-modal-css";
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function onUi(e) {
    return e.target.closest && e.target.closest(UI_SELECTOR);
  }

  function triggerFor(e) {
    return e.target.closest && e.target.closest(TRIGGER_SELECTOR);
  }

  function attach(tour, opts) {
    opts = opts || {};
    var onOpen = opts.onOpen,
      onClose = opts.onClose;
    injectCss();
    var stage = tour.stage;
    var pts = new Map(); // pointerId -> { x, y, el, multi }
    var lastTrigger = null;

    function openFor(el) {
      var id = el.getAttribute("data-modal");
      var dlg = document.getElementById(id);
      if (!dlg || typeof dlg.showModal !== "function") {
        console.warn("SvgTourModal: dialog não encontrado:", id);
        return;
      }
      lastTrigger = el;
      dlg.showModal();
      if (typeof onOpen === "function") onOpen(dlg, el, tour);
    }

    function onDown(e) {
      if (onUi(e)) return;
      if (e.pointerType === "mouse" && e.button !== 0) return;
      var el = triggerFor(e);
      if (!el) return;
      if (pts.size > 0) {
        pts.forEach(function (p) {
          p.multi = true;
        });
      }
      pts.set(e.pointerId, {
        x: e.clientX,
        y: e.clientY,
        el: el,
        multi: pts.size > 0,
      });
    }

    function onUp(e) {
      var p = pts.get(e.pointerId);
      pts.delete(e.pointerId);
      if (!p || p.multi) return;
      var d = Math.hypot(e.clientX - p.x, e.clientY - p.y);
      if (d <= MOVE_THRESHOLD) openFor(p.el);
    }

    function onCancel(e) {
      pts.delete(e.pointerId);
    }

    function onKeyDown(e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var el = triggerFor(e);
      if (!el) return;
      e.preventDefault();
      openFor(el);
    }

    stage.addEventListener("pointerdown", onDown);
    stage.addEventListener("pointerup", onUp);
    stage.addEventListener("pointercancel", onCancel);
    stage.addEventListener("keydown", onKeyDown);

    var dialogs = Array.prototype.slice.call(
      document.querySelectorAll("dialog[id]"),
    );
    dialogs.forEach(function (dlg) {
      dlg.addEventListener("click", function (e) {
        if (e.target === dlg) dlg.close();
      });
      dlg.addEventListener("close", function () {
        if (lastTrigger && typeof lastTrigger.focus === "function")
          lastTrigger.focus();
        if (typeof onClose === "function") onClose(dlg, lastTrigger, tour);
      });
    });

    return {
      destroy: function () {
        stage.removeEventListener("pointerdown", onDown);
        stage.removeEventListener("pointerup", onUp);
        stage.removeEventListener("pointercancel", onCancel);
        stage.removeEventListener("keydown", onKeyDown);
        pts.clear();
      },
    };
  }

  global.SvgTourModal = attach;
})(typeof window !== "undefined" ? window : this);
