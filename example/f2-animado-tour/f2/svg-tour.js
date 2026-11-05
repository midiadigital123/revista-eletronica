// Origem: svg-tour/common/svg-tour.js (commit bcadc29), copiado sem alteração (S08, D-103).
/*!
 * SvgTour 3 — tour guiado + exploração livre em SVGs grandes.
 * Vanilla JS, sem dependências. Interface revisada com as 10 heurísticas de Nielsen.
 *
 * Uso:
 *   const tour = new SvgTour('#organograma', {
 *     label: 'Organograma da Secretaria',
 *     intro: { title: 'Organograma', text: 'Conheça a estrutura em 5 etapas.' },
 *     steps: [
 *       { target: 'secao1', title: 'Presidência', text: '...' },
 *       { target: '.coordenacao', title: 'Coordenações' },   // classe: une vários elementos
 *       'secao3'                                            // só o ID
 *     ]
 *   });
 *
 * Personalização visual por variáveis CSS no container:
 *   --svg-tour-accent, --svg-tour-bg, --svg-tour-surface, --svg-tour-text,
 *   --svg-tour-muted, --svg-tour-border, --svg-tour-radius
 */
(function (global) {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* Estilos                                                             */
  /* ------------------------------------------------------------------ */
  var CSS = [
    ".svg-tour{--st-accent:var(--svg-tour-accent,#1a56db);--st-accent-fg:var(--svg-tour-accent-fg,#fff);--st-bg:var(--svg-tour-bg,#f3f5f8);--st-surface:var(--svg-tour-surface,#fff);--st-text:var(--svg-tour-text,#1f2937);--st-muted:var(--svg-tour-muted,#5b6472);--st-border:var(--svg-tour-border,#dfe3ea);--st-radius:var(--svg-tour-radius,12px);--st-shadow:0 1px 2px rgba(15,23,42,.08),0 4px 12px rgba(15,23,42,.08);",
    "position:relative;display:flex;flex-direction:column;gap:10px;color:var(--st-text);font-family:inherit;outline:none}",
    ".svg-tour *{box-sizing:border-box}",
    ".svg-tour:focus-visible .svg-tour__stage{outline:3px solid var(--st-accent);outline-offset:2px}",
    /* palco */
    ".svg-tour__stage{position:relative;width:100%;min-height:300px;max-height:75vh;overflow:hidden;border-radius:var(--st-radius);background:var(--st-bg);border:1px solid var(--st-border);user-select:none;-webkit-user-select:none}",
    ".svg-tour__stage>svg{position:absolute;inset:0;display:block;width:100%;height:100%}",
    ".svg-tour--free .svg-tour__stage{cursor:grab;touch-action:none}",
    ".svg-tour--anchored .svg-tour__stage{cursor:grab;touch-action:none}",
    ".svg-tour--dragging .svg-tour__stage{cursor:grabbing}",
    ".svg-tour--free .svg-tour__stage{box-shadow:inset 0 0 0 2px var(--st-accent)}",
    /* camadas de UI sobre o palco */
    ".svg-tour__ui{position:absolute;z-index:2;display:flex;gap:6px}",
    ".svg-tour__tl{top:10px;left:10px}.svg-tour__tr{top:10px;right:10px}",
    ".svg-tour__br{bottom:10px;right:10px;flex-direction:column;align-items:center}",
    ".svg-tour__bl{bottom:10px;left:10px}",
    ".svg-tour__bl--auto{opacity:0;pointer-events:none;transition:opacity .2s ease-in .1s}",
    ".svg-tour__bl--auto.svg-tour__bl--on{opacity:1;pointer-events:auto;transition:opacity .15s ease-out}",
    /* botões */
    ".svg-tour__icon{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;padding:0;border:1px solid var(--st-border);border-radius:10px;background:var(--st-surface);color:var(--st-text);cursor:pointer;box-shadow:var(--st-shadow);transition:background .15s,transform .1s}",
    ".svg-tour__icon:hover{background:#eef2f7}.svg-tour__icon:active{transform:scale(.96)}",
    ".svg-tour__icon:disabled{opacity:.4;cursor:default}",
    ".svg-tour button:focus-visible{outline:3px solid var(--st-accent);outline-offset:2px}",
    ".svg-tour svg.st-i{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}",
    ".svg-tour__zoomgroup{display:flex;flex-direction:column;border-radius:10px;box-shadow:var(--st-shadow);background:var(--st-surface);border:1px solid var(--st-border);overflow:hidden}",
    ".svg-tour__zoomgroup .svg-tour__icon{box-shadow:none;border:0;border-radius:0}",
    ".svg-tour__zoomgroup .svg-tour__icon+.svg-tour__icon{border-top:1px solid var(--st-border)}",
    ".svg-tour__zoomlabel{font:600 11px/1 system-ui,sans-serif;color:var(--st-muted);background:var(--st-surface);border:1px solid var(--st-border);border-radius:6px;padding:4px 6px;min-width:44px;text-align:center;font-variant-numeric:tabular-nums}",
    /* seletor de modo (segmented control) */
    ".svg-tour__modes{display:flex;padding:3px;gap:2px;background:var(--st-surface);border:1px solid var(--st-border);border-radius:10px;box-shadow:var(--st-shadow)}",
    ".svg-tour__mode{display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 12px;border:0;border-radius:7px;background:transparent;color:var(--st-muted);font-size:14px;font-weight:500;line-height:1;font-family:inherit;cursor:pointer;transition:background .2s,color .2s}",
    ".svg-tour__mode:hover{color:var(--st-text)}",
    ".svg-tour__mode[aria-pressed=true]{background:var(--st-accent);color:var(--st-accent-fg)}",
    /* minimapa */
    ".svg-tour__minimap{position:relative;border:1px solid var(--st-border);border-radius:8px;background:var(--st-surface);box-shadow:var(--st-shadow);overflow:hidden;cursor:pointer;touch-action:none}",
    ".svg-tour__minimap img{display:block;width:100%;height:100%;object-fit:fill;opacity:.85;pointer-events:none}",
    ".svg-tour__viewport{position:absolute;border:2px solid var(--st-accent);background:color-mix(in srgb,var(--st-accent) 15%,transparent);border-radius:2px;pointer-events:none}",
    /* aviso temporário */
    ".svg-tour__toast{position:absolute;z-index:3;left:50%;bottom:16px;transform:translate(-50%,4px);max-width:calc(100% - 32px);padding:12px 18px;border-radius:10px;border:1px solid var(--st-accent);background:rgba(17,24,39,.94);color:#fff;font-size:16px;font-weight:600;line-height:1.35;text-align:center;box-shadow:0 8px 24px rgba(0,0,0,.35);opacity:0;pointer-events:none;transition:opacity .12s ease-in,transform .12s ease-in}",
    ".svg-tour__toast.is-on{opacity:1;transform:translate(-50%,0);pointer-events:auto;transition:opacity .22s ease-out,transform .22s ease-out}",
    /* ajuda */
    ".svg-tour__help{position:absolute;z-index:4;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(15,23,42,.35);padding:16px;visibility:hidden;opacity:0;transition:opacity .12s ease-in,visibility 0s .12s}",
    ".svg-tour__help.is-on{visibility:visible;opacity:1;transition:opacity .2s ease-out,visibility 0s}",
    ".svg-tour__helpcard:focus{outline:none}",
    ".svg-tour--help-start .svg-tour__actions .svg-tour__btn--primary{visibility:hidden}", // o botão da ajuda já inicia o tour

    ".svg-tour__helpnote{margin:0 0 4px;font-size:15px;font-weight:600;line-height:1.4}",
    ".svg-tour__helpfoot{display:flex;justify-content:flex-end;margin-top:16px}",
    "@media (pointer:coarse){.svg-tour__helpcard .st-kb{display:none}}",
    ".svg-tour__helpcard{position:relative;max-width:420px;width:100%;max-height:100%;overflow:auto;background:var(--st-surface);border-radius:var(--st-radius);box-shadow:0 10px 30px rgba(0,0,0,.25);padding:20px 22px}",
    ".svg-tour__helpcard h3{margin:0 0 12px;font-size:17px}",
    ".svg-tour__helpcard h4{margin:14px 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--st-muted)}",
    ".svg-tour__helpcard dl{display:grid;grid-template-columns:auto 1fr;gap:6px 12px;margin:0;font-size:14px}",
    ".svg-tour__helpcard dt{white-space:nowrap}.svg-tour__helpcard dd{margin:0;color:var(--st-muted)}",
    ".svg-tour kbd{display:inline-block;min-width:22px;padding:2px 6px;border:1px solid var(--st-border);border-bottom-width:2px;border-radius:5px;background:var(--st-bg);font:600 12px/1.3 system-ui,sans-serif;text-align:center}",
    ".svg-tour__helpclose{position:absolute;top:10px;right:10px;width:34px;height:34px;box-shadow:none}",
    /* painel de legenda */
    ".svg-tour__panel{background:var(--st-surface);border:1px solid var(--st-border);border-radius:var(--st-radius);padding:14px 16px;display:flex;flex-direction:column;gap:10px}",
    ".svg-tour__progress{display:flex;gap:4px}",
    ".svg-tour__seg{flex:1;height:8px;padding:0;border:0;border-radius:4px;background:var(--st-border);cursor:pointer;position:relative;transition:background .25s}",
    ".svg-tour__seg::before{content:'';position:absolute;inset:-8px 0}",
    ".svg-tour__seg.is-done{background:color-mix(in srgb,var(--st-accent) 45%,var(--st-border))}",
    ".svg-tour__seg[aria-current=step]{background:var(--st-accent)}",
    ".svg-tour__seg:hover{filter:brightness(.9)}",
    ".svg-tour__meta{font-size:13px;color:var(--st-muted);font-weight:500}",
    ".svg-tour__title{margin:0;font-size:18px;font-weight:700;line-height:1.25}",
    ".svg-tour__text{margin:0;font-size:15px;line-height:1.5}",
    ".svg-tour__text:empty,.svg-tour__title:empty{display:none}",
    ".svg-tour__note{display:none;margin:0;padding:8px 10px;border-radius:8px;background:#fff7e6;color:#8a5300;font-size:13px}",
    ".svg-tour__note.is-on{display:block}",
    ".svg-tour__actions{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:2px}",
    ".svg-tour__btn{display:inline-flex;align-items:center;gap:6px;min-height:42px;padding:0 16px;border-radius:10px;border:1px solid var(--st-border);background:var(--st-surface);color:var(--st-text);font-size:15px;font-weight:600;line-height:1;font-family:inherit;cursor:pointer;transition:background .15s,filter .15s}",
    ".svg-tour__btn:hover{background:#eef2f7}",
    ".svg-tour__btn--primary{background:var(--st-accent);border-color:var(--st-accent);color:var(--st-accent-fg);margin-left:auto}",
    ".svg-tour__btn--primary:hover{background:var(--st-accent);filter:brightness(1.1)}",
    ".svg-tour__btn[hidden]{display:none}",
    /* esmaecimento */
    ".svg-tour--dim .svg-tour__dimmable{opacity:.22;transition:opacity .4s}",
    ".svg-tour--dim .svg-tour-active,.svg-tour--dim .svg-tour-active *{opacity:1!important}",
    /* tela cheia */
    ".svg-tour:fullscreen{background:var(--st-bg);padding:16px}",
    ".svg-tour:fullscreen .svg-tour__stage{flex:1;max-height:none;aspect-ratio:auto!important}",
    /* compacto (palco estreito) */
    ".svg-tour--compact .svg-tour__minimap,.svg-tour--compact .svg-tour__zoomlabel{display:none}",
    ".svg-tour--compact .svg-tour__mode span{display:none}",
    ".svg-tour--compact .svg-tour__mode{padding:0 10px}",
    ".svg-tour--compact .svg-tour__btn span.st-lbl{display:none}",
    "@media (prefers-reduced-motion:reduce){.svg-tour *{transition:none!important}}",
  ].join("");

  var ICONS = {
    route:
      '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h8.5a3.5 3.5 0 0 0 0-7h-9a3.5 3.5 0 0 1 0-7H16"/>',
    hand: '<path d="M18 11V6a2 2 0 0 0-4 0v5"/><path d="M14 10V4a2 2 0 0 0-4 0v6"/><path d="M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    fit: '<path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/>',
    full: '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>',
    exitfull: '<path d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7"/>',
    help: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>',
    close: '<path d="M18 6 6 18M6 6l12 12"/>',
    left: '<path d="m15 18-6-6 6-6"/>',
    right: '<path d="m9 18 6-6-6-6"/>',
    restart: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    back: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
  };
  function icon(name) {
    return (
      '<svg class="st-i" viewBox="0 0 24 24" aria-hidden="true">' +
      ICONS[name] +
      "</svg>"
    );
  }

  function injectCss() {
    if (document.getElementById("svg-tour-css")) return;
    var s = document.createElement("style");
    s.id = "svg-tour-css";
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function el(tag, cls, parent, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  }

  function iconBtn(parent, name, label, onClick) {
    var b = el("button", "svg-tour__icon", parent, icon(name));
    b.type = "button";
    b.title = label;
    b.setAttribute("aria-label", label);
    b.addEventListener("click", onClick);
    return b;
  }

  var ease = function (t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  };

  var DEFAULT_LABELS = {
    region: "Imagem interativa",
    tour: "Tour guiado",
    free: "Explorar",
    step: "Etapa",
    of: "de",
    prev: "Anterior",
    next: "Próximo",
    start: "Iniciar tour",
    finish: "Concluir",
    restart: "Recomeçar tour",
    backToStep: "Voltar à etapa",
    backToTour: "Voltar ao tour",
    overview: "Visão geral",
    introTitle: "Visão geral",
    introText:
      "Siga o tour guiado para conhecer cada parte ou use Explorar para navegar livremente.",
    doneTitle: "Tour concluído",
    doneText:
      "Você passou por todas as etapas. Explore livremente ou recomece o tour.",
    freeMeta: "Modo exploração",
    freeText:
      "Arraste para mover e use a roda do mouse, a pinça ou os botões + e − para o zoom.",
    freeHintMouse: "Arraste para mover · Role para dar zoom",
    freeHintTouch: "Arraste para mover · Use a pinça para dar zoom",
    dragHint: "Arraste para ver o restante deste bloco.",
    wheelHint: "Para dar zoom, use Ctrl + roda do mouse ou clique em Explorar",
    notFound:
      "Não foi possível localizar esta parte no desenho. Mostrando a visão geral.",
    zoomIn: "Aproximar (+)",
    zoomOut: "Afastar (−)",
    fit: "Ver desenho inteiro (0)",
    fullscreen: "Tela cheia (F)",
    exitFullscreen: "Sair da tela cheia (F)",
    help: "Ajuda e atalhos (?)",
    close: "Fechar",
    helpTitle: "Como navegar",
    helpGotIt: "Entendi",
    helpGotItStart: "Entendi, iniciar tour",
    minimap: "Minimapa: clique para ir a um ponto",
  };

  /* ------------------------------------------------------------------ */
  /* Construtor                                                          */
  /* ------------------------------------------------------------------ */
  function SvgTour(container, options) {
    this.root =
      typeof container === "string"
        ? document.querySelector(container)
        : container;
    if (!this.root) throw new Error("SvgTour: container não encontrado");

    this.opts = Object.assign(
      {
        steps: [],
        svg: null, // markup do SVG (string), opcional
        label: null, // nome acessível da região (ex.: "Organograma")
        intro: null, // { title, text } exibidos na visão geral
        padding: 24, // margem em px de tela ao redor da parte focada
        duration: 700, // ms da animação
        maxZoom: null, // limite de zoom do tour, relativo à visão geral
        minScale: null, // piso de leitura: px de tela por unidade do SVG; se o bloco não cabe, ancora no canto e permite arrastar (também por passo)
        dimOthers: true, // esmaece o que não está em foco
        activeClass: "svg-tour-active",
        startAt: -1, // -1 = visão geral
        loop: false,
        keyboard: true,
        // exploração
        freeMode: true,
        startMode: "tour", // "tour" | "free"
        freeMinZoom: 1,
        freeMaxZoom: 12,
        dragToFree: true, // arrastar com mouse no tour entra em Explorar
        inertia: true,
        minimap: true,
        minimapAuto: false, // true: minimapa só aparece enquanto a vista se move (e 1,5s depois; 3s em Explorar)
        fullscreen: true,
        fitButton: true, // botão "ver desenho inteiro" no grupo de zoom
        help: true,
        helpOnStart: false, // abre "Como navegar" ao carregar
        helpGeneral: true, // seção "Geral" (E, F, ?) na ajuda
        helpNote: "", // frase de destaque no topo da ajuda (texto puro)
        onChange: null, // function(index, step, tour)
        onModeChange: null, // function(mode, tour)
      },
      options || {},
    );
    this.opts.labels = Object.assign(
      {},
      DEFAULT_LABELS,
      (options || {}).labels,
    );

    injectCss();
    this.steps = this.opts.steps.map(function (s) {
      return typeof s === "string" ? { target: s } : s;
    });
    this.index = null;
    this.current = null;
    this.mode = "tour";
    this._done = false;
    this._build();
    this._bindPointer();

    var self = this;
    if (global.ResizeObserver) {
      this._ro = new ResizeObserver(function () {
        self.root.classList.toggle(
          "svg-tour--compact",
          self.stage.clientWidth < 560,
        );
        self._quiet = true; // redimensionar não mostra o minimapa
        self._refit();
        self._quiet = false;
      });
      this._ro.observe(this.stage);
    }
    this.go(this.opts.startAt, true);
    if (this.opts.startMode === "free") this.setMode("free");
    if (this.opts.helpOnStart) this.toggleHelp(true);
  }

  /* ------------------------------------------------------------------ */
  /* Montagem da interface                                              */
  /* ------------------------------------------------------------------ */
  SvgTour.prototype._build = function () {
    var root = this.root,
      o = this.opts,
      L = o.labels,
      self = this;
    if (typeof o.svg === "string") root.innerHTML = o.svg;
    var svg = root.querySelector("svg");
    if (!svg) throw new Error("SvgTour: nenhum <svg> encontrado");
    this.svg = svg;

    var vb = svg.viewBox && svg.viewBox.baseVal;
    if (vb && vb.width && vb.height) {
      this.home = { x: vb.x, y: vb.y, width: vb.width, height: vb.height };
    } else {
      var b = svg.getBBox();
      this.home = { x: b.x, y: b.y, width: b.width, height: b.height };
    }
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.setAttribute("focusable", "false");

    root.classList.add("svg-tour");
    if (o.dimOthers) root.classList.add("svg-tour--dim");
    root.setAttribute("role", "region");
    root.setAttribute("aria-label", o.label || L.region);
    if (!root.hasAttribute("tabindex")) root.setAttribute("tabindex", "0");

    /* palco */
    this.stage = el("div", "svg-tour__stage");
    this.stage.style.aspectRatio = this.home.width + " / " + this.home.height;
    root.insertBefore(this.stage, svg);
    this.stage.appendChild(svg);

    /* topo esquerdo: seletor de modo */
    if (o.freeMode) {
      var tl = el("div", "svg-tour__ui svg-tour__tl", this.stage);
      var modes = el("div", "svg-tour__modes", tl);
      modes.setAttribute("role", "group");
      modes.setAttribute("aria-label", "Modo de navegação");
      this.btnModeTour = el(
        "button",
        "svg-tour__mode",
        modes,
        icon("route") + "<span>" + L.tour + "</span>",
      );
      this.btnModeFree = el(
        "button",
        "svg-tour__mode",
        modes,
        icon("hand") + "<span>" + L.free + "</span>",
      );
      this.btnModeTour.type = this.btnModeFree.type = "button";
      this.btnModeTour.title = L.tour + " (E)";
      this.btnModeFree.title = L.free + " (E)";
      this.btnModeTour.onclick = function () {
        self.setMode("tour");
      };
      this.btnModeFree.onclick = function () {
        self.setMode("free");
      };
    }

    /* topo direito: tela cheia + ajuda */
    var tr = el("div", "svg-tour__ui svg-tour__tr", this.stage);
    if (o.fullscreen && root.requestFullscreen) {
      this.btnFull = iconBtn(tr, "full", L.fullscreen, function () {
        self.toggleFullscreen();
      });
      this._onFs = function () {
        var on = document.fullscreenElement === root;
        self.btnFull.innerHTML = icon(on ? "exitfull" : "full");
        self.btnFull.title = on ? L.exitFullscreen : L.fullscreen;
        self.btnFull.setAttribute("aria-label", self.btnFull.title);
      };
      document.addEventListener("fullscreenchange", this._onFs);
    }
    if (o.help)
      this.btnHelp = iconBtn(tr, "help", L.help, function () {
        self.toggleHelp(true);
      });

    /* baixo direito: zoom */
    var br = el("div", "svg-tour__ui svg-tour__br", this.stage);
    var zg = el("div", "svg-tour__zoomgroup", br);
    iconBtn(zg, "plus", L.zoomIn, function () {
      self.zoomBy(1.15);
    });
    iconBtn(zg, "minus", L.zoomOut, function () {
      self.zoomBy(1 / 1.15);
    });
    if (o.fitButton)
      iconBtn(zg, "fit", L.fit, function () {
        self.fitAll();
      });
    this.elZoom = el("div", "svg-tour__zoomlabel", br);
    this.elZoom.setAttribute("aria-hidden", "true");

    /* baixo esquerdo: minimapa */
    if (o.minimap) this._buildMinimap();

    /* aviso temporário */
    this.elToast = el("div", "svg-tour__toast", this.stage);
    this.elToast.setAttribute("role", "status");
    // mouse em cima pausa o aviso; clique dispensa (Esc também, em _key)
    this.elToast.addEventListener("pointerenter", function () {
      self._toastPause(true);
    });
    this.elToast.addEventListener("pointerleave", function () {
      self._toastPause(false);
    });
    this.elToast.addEventListener("click", function () {
      self._toastHide();
    });

    /* ajuda */
    if (o.help) {
      this.elHelp = el("div", "svg-tour__help", this.stage);
      var card = el("div", "svg-tour__helpcard", this.elHelp);
      var hid = "svg-tour-help-" + (SvgTour._n = (SvgTour._n || 0) + 1);
      card.setAttribute("role", "dialog");
      card.setAttribute("aria-modal", "true");
      card.setAttribute("aria-labelledby", hid);
      card.tabIndex = -1; // recebe o foco ao abrir (sem anel: o leitor lê o título)
      this.elHelpCard = card;
      // kb = linha só de teclado: some em telas de toque
      var row = function (dt, dd, kb) {
        var c = kb ? ' class="st-kb"' : "";
        return "<dt" + c + ">" + dt + "</dt><dd" + c + ">" + dd + "</dd>";
      };
      card.innerHTML =
        '<h3 id="' +
        hid +
        '">' +
        L.helpTitle +
        "</h3>" +
        "<h4>" +
        L.tour +
        "</h4><dl>" +
        row("<kbd>→</kbd> <kbd>←</kbd>", "Próxima / etapa anterior", true) +
        row("<kbd>Home</kbd>", "Visão geral", true) +
        row("Barra de progresso", "Clique para ir direto a uma etapa") +
        "</dl><h4>" +
        L.free +
        "</h4><dl>" +
        row("Arrastar", "Mover o desenho") +
        row("Roda · pinça", "Zoom no ponto indicado") +
        row("Duplo clique", "Aproximar (Shift afasta)") +
        row("<kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd>", "Mover", true) +
        row("<kbd>+</kbd> <kbd>−</kbd> <kbd>0</kbd>", "Aproximar, afastar, ver tudo", true) +
        row("<kbd>Esc</kbd>", "Voltar ao tour", true) +
        "</dl>" +
        (o.helpGeneral
          ? '<h4 class="st-kb">Geral</h4><dl>' +
            row("<kbd>E</kbd>", "Alternar Tour / Explorar", true) +
            (o.fullscreen ? row("<kbd>F</kbd>", "Tela cheia", true) : "") +
            row("<kbd>?</kbd>", "Esta ajuda", true) +
            "</dl>"
          : "");
      if (o.helpNote) {
        var note = el("p", "svg-tour__helpnote");
        note.textContent = o.helpNote;
        card.insertBefore(note, card.children[1]);
      }
      this.btnHelpClose = iconBtn(card, "close", L.close, function () {
        self.toggleHelp(false);
      });
      this.btnHelpClose.classList.add("svg-tour__helpclose");
      var foot = el("div", "svg-tour__helpfoot", card);
      this.btnHelpGo = el(
        "button",
        "svg-tour__btn svg-tour__btn--primary",
        foot,
      );
      this.btnHelpGo.type = "button";
      this.btnHelpGo.onclick = function () {
        var start = self._helpStart;
        self.toggleHelp(false);
        if (start) {
          self.go(0);
          self.btnMain.focus();
        }
      };
      this.elHelp.addEventListener("click", function (e) {
        if (e.target === self.elHelp) self.toggleHelp(false);
      });
    }

    /* painel */
    var panel = el("div", "svg-tour__panel", root);
    this.elProgress = el("div", "svg-tour__progress", panel);
    this.elProgress.setAttribute("role", "group");
    this.elProgress.setAttribute("aria-label", "Etapas");
    this.segs = this.steps.map(function (s, i) {
      var b = el("button", "svg-tour__seg", self.elProgress);
      b.type = "button";
      var name = L.step + " " + (i + 1) + (s.title ? ": " + s.title : "");
      b.title = name;
      b.setAttribute("aria-label", name);
      b.onclick = function () {
        self.go(i);
      };
      return b;
    });
    if (!this.steps.length) this.elProgress.style.display = "none";
    var live = el("div", "", panel);
    live.setAttribute("aria-live", "polite");
    live.style.display = "contents";
    this.elMeta = el("div", "svg-tour__meta", live);
    this.elTitle = el("h3", "svg-tour__title", live);
    this.elText = el("p", "svg-tour__text", live);
    this.elNote = el("p", "svg-tour__note", live);
    var actions = el("div", "svg-tour__actions", panel);
    this.btnPrev = el(
      "button",
      "svg-tour__btn",
      actions,
      icon("left") + '<span class="st-lbl">' + L.prev + "</span>",
    );
    this.btnPrev.type = "button";
    this.btnPrev.setAttribute("aria-label", L.prev);
    this.btnPrev.onclick = function () {
      self.prev();
    };
    this.btnMain = el(
      "button",
      "svg-tour__btn svg-tour__btn--primary",
      actions,
    );
    this.btnMain.type = "button";
    this.btnMain.onclick = function () {
      self._mainAction();
    };

    /* teclado */
    if (o.keyboard) {
      this._onKey = function (e) {
        self._key(e);
      };
      root.addEventListener("keydown", this._onKey);
    }
  };

  SvgTour.prototype._buildMinimap = function () {
    var self = this,
      h = this.home,
      maxW = 170,
      maxH = 110,
      r = Math.min(maxW / h.width, maxH / h.height);
    var wrap = el("div", "svg-tour__ui svg-tour__bl", this.stage);
    if (this.opts.minimapAuto) wrap.classList.add("svg-tour__bl--auto");
    var mm = el("div", "svg-tour__minimap", wrap);
    mm.style.width = Math.round(h.width * r) + "px";
    mm.style.height = Math.round(h.height * r) + "px";
    mm.style.aspectRatio = h.width + " / " + h.height; // permite ao CSS redimensionar só pela largura
    mm.title = this.opts.labels.minimap;
    mm.setAttribute("aria-hidden", "true");
    try {
      var clone = this.svg.cloneNode(true);
      clone.setAttribute(
        "viewBox",
        h.x + " " + h.y + " " + h.width + " " + h.height,
      );
      clone.setAttribute("width", h.width);
      clone.setAttribute("height", h.height);
      clone.removeAttribute("class");
      clone.removeAttribute("style");
      // remove atributos com nome inválido em XML (ex.: ;="" vindo de style="...";)
      var validName = /^[A-Za-z_][\w.:-]*$/;
      [clone]
        .concat(Array.prototype.slice.call(clone.querySelectorAll("*")))
        .forEach(function (n) {
          Array.prototype.slice.call(n.attributes).forEach(function (a) {
            if (!validName.test(a.name)) n.removeAttribute(a.name);
          });
        });
      Array.prototype.forEach.call(
        clone.querySelectorAll(".svg-tour__dimmable"),
        function (n) {
          n.classList.remove("svg-tour__dimmable");
        },
      );
      var src = new XMLSerializer().serializeToString(clone);
      this._mmUrl = URL.createObjectURL(
        new Blob([src], { type: "image/svg+xml" }),
      );
      var img = el("img", "", mm);
      img.alt = "";
      img.src = this._mmUrl;
    } catch (err) {
      /* minimapa sem miniatura */
    }
    this.elViewport = el("div", "svg-tour__viewport", mm);
    this.elMinimap = mm;

    var dragging = false;
    function goTo(e) {
      var b = mm.getBoundingClientRect(),
        sx = h.x + ((e.clientX - b.left) / b.width) * h.width,
        sy = h.y + ((e.clientY - b.top) / b.height) * h.height,
        c = self.current;
      self._set(
        self._clamp({
          x: sx - c.width / 2,
          y: sy - c.height / 2,
          width: c.width,
          height: c.height,
        }),
      );
    }
    mm.addEventListener("pointerdown", function (e) {
      e.stopPropagation();
      if (self.mode !== "free") self.setMode("free");
      cancelAnimationFrame(self._raf);
      dragging = true;
      try {
        mm.setPointerCapture(e.pointerId);
      } catch (err) {}
      goTo(e);
    });
    mm.addEventListener("pointermove", function (e) {
      if (dragging) goTo(e);
    });
    mm.addEventListener("pointerup", function () {
      dragging = false;
    });
    mm.addEventListener("pointercancel", function () {
      dragging = false;
    });
  };

  /* ------------------------------------------------------------------ */
  /* Teclado, ajuda, tela cheia, avisos                                 */
  /* ------------------------------------------------------------------ */
  SvgTour.prototype._key = function (e) {
    if (e.altKey || e.metaKey || (e.ctrlKey && e.key !== "0")) return;
    var k = e.key,
      free = this.mode === "free",
      handled = true,
      step = 80;
    var onButton = e.target !== this.root && e.target.tagName === "BUTTON";

    if (this._helpOpen) {
      if (k === "Escape" || k === "?") this.toggleHelp(false);
      else handled = false;
    } else if (k === "Escape" && this.elToast.classList.contains("is-on"))
      this._toastHide(); // Esc fecha primeiro o aviso; o segundo Esc segue o fluxo normal
    else if (k === "?") this.toggleHelp(true);
    else if ((k === "e" || k === "E") && this.opts.freeMode)
      this.setMode(free ? "tour" : "free");
    else if ((k === "f" || k === "F") && this.btnFull) this.toggleFullscreen();
    else if (onButton && (k === "Enter" || k === " ")) handled = false;
    else if (free) {
      if (k === "ArrowRight") this.panBy(-step, 0);
      else if (k === "ArrowLeft") this.panBy(step, 0);
      else if (k === "ArrowUp") this.panBy(0, step);
      else if (k === "ArrowDown") this.panBy(0, -step);
      else if (k === "+" || k === "=") this.zoomBy(1.25);
      else if (k === "-" || k === "_") this.zoomBy(0.8);
      else if (k === "0") this.fitAll();
      else if (k === "Escape") this.setMode("tour");
      else handled = false;
    } else {
      if (k === "ArrowRight") this.next();
      else if (k === "ArrowLeft") this.prev();
      else if (k === "Home") this.overview();
      else if (k === "+" || k === "=") this.zoomBy(1.25);
      else if (k === "-" || k === "_") this.zoomBy(0.8);
      else handled = false;
    }
    if (handled) e.preventDefault();
  };

  SvgTour.prototype.toggleHelp = function (open) {
    if (!this.elHelp) return this;
    open = open == null ? !this._helpOpen : !!open;
    if (open === !!this._helpOpen) return this;
    this._helpOpen = open;
    this.elHelp.classList.toggle("is-on", open);
    if (open) {
      this._helpPrev = document.activeElement;
      // com o tour ainda na visão geral, o botão da ajuda já inicia o tour
      this._helpStart =
        this.mode === "tour" &&
        this.index === -1 &&
        !this._done &&
        this.steps.length > 0;
      var L = this.opts.labels;
      this.btnHelpGo.textContent = this._helpStart ? L.helpGotItStart : L.helpGotIt;
      this.root.classList.toggle("svg-tour--help-start", this._helpStart);
      this._inert(true);
      this.elHelpCard.focus();
    } else {
      this.root.classList.remove("svg-tour--help-start");
      this._inert(false);
      var p = this._helpPrev;
      var back =
        p && p.isConnected && p !== document.body ? p : this.btnHelp;
      if (back) back.focus();
    }
    return this;
  };

  // diálogo modal: o resto da interface fica inerte (sem foco, clique nem leitura)
  SvgTour.prototype._inert = function (on) {
    var self = this;
    (this._inerted || []).forEach(function (n) {
      n.inert = false;
    });
    this._inerted = [];
    if (this._onFocusIn) document.removeEventListener("focusin", this._onFocusIn);
    this._onFocusIn = null;
    if (!on) return;
    // `inert` só existe em elementos HTML: o foco que escapar para o <svg> volta ao diálogo
    this._onFocusIn = function (e) {
      if (!self.elHelp.contains(e.target)) self.elHelpCard.focus();
    };
    document.addEventListener("focusin", this._onFocusIn);
    [this.stage, this.root].forEach(function (parent) {
      Array.prototype.forEach.call(parent.children, function (n) {
        if (n === self.elHelp || n === self.stage) return;
        n.inert = true;
        self._inerted.push(n);
      });
    });
  };

  SvgTour.prototype.toggleFullscreen = function () {
    if (document.fullscreenElement === this.root) document.exitFullscreen();
    else if (this.root.requestFullscreen)
      this.root.requestFullscreen().catch(function () {});
    return this;
  };

  SvgTour.prototype.toast = function (msg, ms) {
    var self = this,
      t = this.elToast;
    clearTimeout(this._toastT);
    clearTimeout(this._toastSwap);
    clearTimeout(this._toastClr);
    // tempo mínimo para ler a frase inteira; a mesma dica repetida dura 60% (redução progressiva)
    var seen = this._toastSeen || (this._toastSeen = {}),
      dur = Math.max(ms || 2200, 1800 + msg.length * 55);
    seen[msg] = (seen[msg] || 0) + 1;
    if (seen[msg] > 2) dur = Math.round(dur * 0.6);
    function show() {
      t.textContent = msg;
      t.style.setProperty("--st-toast-ms", dur + "ms"); // o CSS desenha o fio de tempo com isto
      t.classList.remove("is-run", "is-paused");
      void t.offsetWidth; // reinicia o fio
      t.classList.add("is-on", "is-run");
      self._toastLeft = dur;
      self._toastRun();
    }
    if (!t.classList.contains("is-on") || t.textContent === msg) show();
    else {
      // aviso diferente com outro na tela: o antigo sai, o novo entra (o texto nunca troca "no ar")
      this._toastHide(true);
      this._toastSwap = setTimeout(show, 160);
    }
  };

  // conta o tempo restante do aviso (pausado com mouse em cima)
  SvgTour.prototype._toastRun = function () {
    var self = this;
    this._toastAt = Date.now();
    this._toastT = setTimeout(function () {
      self._toastHide();
    }, this._toastLeft);
  };

  SvgTour.prototype._toastPause = function (on) {
    var t = this.elToast;
    if (!t.classList.contains("is-on")) return;
    if (on) {
      clearTimeout(this._toastT);
      this._toastLeft -= Date.now() - this._toastAt;
      t.classList.add("is-paused");
    } else if (t.classList.contains("is-paused")) {
      t.classList.remove("is-paused");
      this._toastLeft = Math.max(this._toastLeft, 800);
      this._toastRun();
    }
  };

  SvgTour.prototype._toastHide = function (keepText) {
    var t = this.elToast;
    clearTimeout(this._toastT);
    clearTimeout(this._toastClr);
    t.classList.remove("is-on", "is-run", "is-paused");
    // esvazia depois do fade: a live region não guarda o último aviso
    if (!keepText)
      this._toastClr = setTimeout(function () {
        t.textContent = "";
      }, 400);
  };

  /* ------------------------------------------------------------------ */
  /* Ponteiro: arrastar, pinça, roda                                    */
  /* ------------------------------------------------------------------ */
  SvgTour.prototype._bindPointer = function () {
    var self = this,
      stage = this.stage,
      pts = new Map(),
      last = null,
      pending = null, // arrasto de mouse no tour, antes de passar do limiar
      vel = { x: 0, y: 0, t: 0 },
      inertiaRaf = null;

    function local(e) {
      var r = stage.getBoundingClientRect();
      return { x: e.clientX - r.left, y: e.clientY - r.top };
    }
    function gesture() {
      var a = Array.from(pts.values());
      if (a.length === 1) return { x: a[0].x, y: a[0].y, d: 0 };
      return {
        x: (a[0].x + a[1].x) / 2,
        y: (a[0].y + a[1].y) / 2,
        d: Math.hypot(a[1].x - a[0].x, a[1].y - a[0].y),
      };
    }
    function startDrag(e, p) {
      cancelAnimationFrame(self._raf);
      cancelAnimationFrame(inertiaRaf);
      try {
        stage.setPointerCapture(e.pointerId);
      } catch (err) {}
      pts.set(e.pointerId, p);
      last = gesture();
      vel = { x: 0, y: 0, t: performance.now() };
      self.root.classList.add("svg-tour--dragging");
    }
    function onUi(e) {
      return (
        e.target.closest &&
        e.target.closest(".svg-tour__ui,.svg-tour__help,.svg-tour__toast")
      );
    }

    this._onDown = function (e) {
      if (onUi(e)) return;
      if (e.pointerType === "mouse" && e.button !== 0) return;
      if (self.mode !== "free") {
        if (
          self._anchored ||
          (self.opts.freeMode &&
            self.opts.dragToFree &&
            e.pointerType === "mouse")
        ) {
          pending = { id: e.pointerId, p: local(e), e: e };
        }
        return;
      }
      startDrag(e, local(e));
    };

    this._onMove = function (e) {
      if (pending && pending.id === e.pointerId) {
        var p = local(e);
        if (Math.hypot(p.x - pending.p.x, p.y - pending.p.y) > 5) {
          // passo ancorado: arrasta dentro do passo, sem sair do tour
          if (!self._anchored) self.setMode("free");
          startDrag(e, pending.p);
          pending = null;
        } else return;
      }
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, local(e));
      var g = gesture();
      if (pts.size >= 2 && last.d && g.d && self.mode === "free")
        self._zoomAt(g.d / last.d, g.x, g.y);
      var dx = g.x - last.x,
        dy = g.y - last.y;
      self.panBy(dx, dy);
      var now = performance.now(),
        dt = Math.max(1, now - vel.t);
      vel = {
        x: 0.8 * (dx / dt) + 0.2 * vel.x,
        y: 0.8 * (dy / dt) + 0.2 * vel.y,
        t: now,
      };
      last = g;
    };

    this._onUp = function (e) {
      if (pending && pending.id === e.pointerId) pending = null;
      if (!pts.has(e.pointerId)) return;
      pts.delete(e.pointerId);
      if (pts.size) {
        last = gesture();
        return;
      }
      self.root.classList.remove("svg-tour--dragging");
      if (!self.opts.inertia || performance.now() - vel.t > 80) return;
      var vx = vel.x * 16,
        vy = vel.y * 16;
      (function glide() {
        vx *= 0.92;
        vy *= 0.92;
        if (Math.abs(vx) < 0.3 && Math.abs(vy) < 0.3) return;
        self.panBy(vx, vy);
        inertiaRaf = requestAnimationFrame(glide);
      })();
    };

    this._onWheel = function (e) {
      if (onUi(e)) return;
      if (self.mode !== "free") {
        // prevenção de erro: não sequestra a rolagem da página
        if (!e.ctrlKey || !self.opts.freeMode) {
          var now = Date.now();
          // intervalo maior que o tempo em tela do aviso, senão ele vira um banner fixo
          if (!self._lastWheelHint || now - self._lastWheelHint > 9000) {
            self._lastWheelHint = now;
            self.toast(self.opts.labels.wheelHint, 2400);
          }
          return;
        }
        self.setMode("free", true);
      }
      e.preventDefault();
      cancelAnimationFrame(self._raf);
      cancelAnimationFrame(inertiaRaf);
      var p = local(e),
        delta = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
      self._zoomAt(Math.exp(-delta * 0.0015), p.x, p.y);
    };

    this._onDbl = function (e) {
      if (onUi(e) || self.mode !== "free") return;
      var p = local(e);
      self.zoomBy(e.shiftKey ? 0.5 : 2, p.x, p.y);
    };

    this._lastPointer = "mouse";
    stage.addEventListener("pointerdown", function (e) {
      self._lastPointer = e.pointerType;
    });
    stage.addEventListener("pointerdown", this._onDown);
    stage.addEventListener("pointermove", this._onMove);
    stage.addEventListener("pointerup", this._onUp);
    stage.addEventListener("pointercancel", this._onUp);
    stage.addEventListener("wheel", this._onWheel, { passive: false });
    stage.addEventListener("dblclick", this._onDbl);
  };

  /* ------------------------------------------------------------------ */
  /* Geometria                                                          */
  /* ------------------------------------------------------------------ */
  SvgTour.prototype._homeW = function () {
    return this._fit(this.home, 0, true).width;
  };

  SvgTour.prototype._clamp = function (v) {
    var W = this.stage.clientWidth || 1,
      H = this.stage.clientHeight || 1,
      homeW = this._homeW(),
      w = Math.min(
        homeW / this.opts.freeMinZoom,
        Math.max(homeW / this.opts.freeMaxZoom, v.width),
      ),
      h = (w * H) / W,
      cx = v.x + v.width / 2,
      cy = v.y + v.height / 2,
      hm = this.home;
    cx = Math.min(hm.x + hm.width, Math.max(hm.x, cx));
    cy = Math.min(hm.y + hm.height, Math.max(hm.y, cy));
    return { x: cx - w / 2, y: cy - h / 2, width: w, height: h };
  };

  SvgTour.prototype._zoomTarget = function (factor, px, py) {
    var c = this.current,
      W = this.stage.clientWidth,
      H = this.stage.clientHeight;
    if (px == null) {
      px = W / 2;
      py = H / 2;
    }
    var k = c.width / W,
      sx = c.x + px * k,
      sy = c.y + py * k,
      size = this._clamp({
        x: 0,
        y: 0,
        width: c.width / factor,
        height: c.height / factor,
      }),
      k2 = size.width / W;
    return this._clamp({
      x: sx - px * k2,
      y: sy - py * k2,
      width: size.width,
      height: size.height,
    });
  };

  SvgTour.prototype._zoomAt = function (factor, px, py) {
    this._set(this._zoomTarget(factor, px, py));
  };

  /** Move a vista em pixels de tela. */
  SvgTour.prototype.panBy = function (dx, dy) {
    var c = this.current,
      k = c.width / (this.stage.clientWidth || 1);
    var v = {
      x: c.x - dx * k,
      y: c.y - dy * k,
      width: c.width,
      height: c.height,
    };
    this._set(
      this.mode === "tour" && this._bounds
        ? this._clampStep(v)
        : this._clamp(v),
    );
    return this;
  };

  /** Zoom animado (factor > 1 aproxima). No tour, entra em Explorar. */
  SvgTour.prototype.zoomBy = function (factor, px, py) {
    if (this.mode !== "free" && this.opts.freeMode) this.setMode("free", true);
    this._animate(this._zoomTarget(factor, px, py), false, 280);
    return this;
  };

  /** Mostra o desenho inteiro. */
  SvgTour.prototype.fitAll = function () {
    if (this.mode === "free")
      this._animate(this._clamp(this._fit(this.home, 0, true)), false, 450);
    else this.overview();
    return this;
  };

  SvgTour.prototype._resolve = function (target) {
    if (!target) return [];
    if (target instanceof Element) return [target];
    if (/^[\w-]+$/.test(target)) {
      var byId = this.svg.querySelector(
        "#" + (global.CSS && CSS.escape ? CSS.escape(target) : target),
      );
      if (byId) return [byId];
    }
    try {
      return Array.prototype.slice.call(this.svg.querySelectorAll(target));
    } catch (e) {
      return [];
    }
  };

  SvgTour.prototype._bbox = function (els) {
    var inv = this.svg.getScreenCTM().inverse();
    var x1 = Infinity,
      y1 = Infinity,
      x2 = -Infinity,
      y2 = -Infinity;
    els.forEach(function (e) {
      if (typeof e.getBBox !== "function") return;
      var b = e.getBBox(),
        m = inv.multiply(e.getScreenCTM());
      [
        [b.x, b.y],
        [b.x + b.width, b.y],
        [b.x, b.y + b.height],
        [b.x + b.width, b.y + b.height],
      ].forEach(function (c) {
        var x = m.a * c[0] + m.c * c[1] + m.e,
          y = m.b * c[0] + m.d * c[1] + m.f;
        if (x < x1) x1 = x;
        if (y < y1) y1 = y;
        if (x > x2) x2 = x;
        if (y > y2) y2 = y;
      });
    });
    return isFinite(x1)
      ? { x: x1, y: y1, width: x2 - x1, height: y2 - y1 }
      : null;
  };

  // viewBox que encaixa a caixa com padding fixo em px de tela
  SvgTour.prototype._fit = function (b, padding, ignoreMax, minScale) {
    var W = this.stage.clientWidth || 1,
      H = this.stage.clientHeight || 1;
    var p = Math.min(padding, W / 4, H / 4);
    var s = Math.min(
      (W - 2 * p) / Math.max(b.width, 1e-6),
      (H - 2 * p) / Math.max(b.height, 1e-6),
    );
    if (this.opts.maxZoom && !ignoreMax) {
      s = Math.min(
        s,
        Math.min(W / this.home.width, H / this.home.height) * this.opts.maxZoom,
      );
    }
    var anchored = false;
    if (minScale && s < minScale) {
      s = minScale;
      anchored = true;
    }
    var w = W / s,
      h = H / s;
    var v = {
      x: b.x + b.width / 2 - w / 2,
      y: b.y + b.height / 2 - h / 2,
      width: w,
      height: h,
    };
    if (anchored) {
      // o eixo que não cabe começa no canto do bloco; o que cabe continua centralizado
      var pu = p / s;
      if (b.width + 2 * pu > w) v.x = b.x - pu;
      if (b.height + 2 * pu > h) v.y = b.y - pu;
      v.bounds = {
        x1: b.x - pu,
        y1: b.y - pu,
        x2: b.x + b.width + pu,
        y2: b.y + b.height + pu,
      };
    }
    return v;
  };

  /** Limita a vista de um passo ancorado ao bloco (mais o padding). */
  SvgTour.prototype._clampStep = function (v) {
    var b = this._bounds;
    function axis(pos, size, lo, hi) {
      return hi - lo <= size
        ? (lo + hi) / 2 - size / 2
        : Math.min(hi - size, Math.max(lo, pos));
    }
    return {
      x: axis(v.x, v.width, b.x1, b.x2),
      y: axis(v.y, v.height, b.y1, b.y2),
      width: v.width,
      height: v.height,
    };
  };

  /** Vista do passo; guarda se ficou ancorada (piso de leitura) e seus limites. */
  SvgTour.prototype._stepView = function (t) {
    var v = this._fit(t.box, t.pad, false, t.minScale);
    this._bounds = v.bounds || null;
    this._anchored = !!v.bounds;
    this.root.classList.toggle("svg-tour--anchored", this._anchored);
    return v;
  };

  SvgTour.prototype._targetBox = function (i) {
    if (i < 0) return { box: this.home, pad: 0, els: [] };
    var els = this._resolve(this.steps[i].target),
      box = this._bbox(els);
    if (!box) {
      console.warn("SvgTour: alvo não encontrado:", this.steps[i].target);
      return { box: this.home, pad: 0, els: [], missing: true };
    }
    var pad =
      this.steps[i].padding != null ? this.steps[i].padding : this.opts.padding;
    var minScale =
      this.steps[i].minScale != null
        ? this.steps[i].minScale
        : this.opts.minScale;
    // palco estreito: com piso de leitura, margem grande come a largura útil (mas ainda livre dos controles)
    if (minScale && this.root.classList.contains("svg-tour--compact"))
      pad = Math.min(pad, 56);
    return { box: box, pad: pad, els: els, minScale: minScale };
  };

  SvgTour.prototype._set = function (v) {
    this.current = v;
    this._lastW = this.stage.clientWidth;
    this.svg.setAttribute(
      "viewBox",
      v.x + " " + v.y + " " + v.width + " " + v.height,
    );
    this._updateStatus();
  };

  // zoom % e retângulo do minimapa
  SvgTour.prototype._updateStatus = function () {
    var v = this.current;
    if (this.elZoom)
      this.elZoom.textContent =
        Math.round((this._homeW() / v.width) * 100) + "%";
    if (this.elMinimap) {
      var wrap = this.elMinimap.parentNode,
        hidden = wrap.style.display === "none";
      wrap.style.display = v.width >= this._homeW() * 0.95 ? "none" : "";
      // todo movimento da vista passa por aqui; resize não conta como movimento
      if (this.opts.minimapAuto && !this._quiet)
        this._pingMinimap(wrap, hidden && wrap.style.display === "");
    }
    if (this.elViewport) {
      var h = this.home,
        mw = this.elMinimap.clientWidth,
        mh = this.elMinimap.clientHeight;
      var l = ((v.x - h.x) / h.width) * mw,
        t = ((v.y - h.y) / h.height) * mh;
      var w = (v.width / h.width) * mw,
        hh = (v.height / h.height) * mh;
      var s = this.elViewport.style;
      s.left = Math.max(0, l) + "px";
      s.top = Math.max(0, t) + "px";
      s.width = Math.max(4, Math.min(mw, l + w) - Math.max(0, l)) + "px";
      s.height = Math.max(4, Math.min(mh, t + hh) - Math.max(0, t)) + "px";
    }
  };

  // mostra o minimapa e agenda o sumiço (mais folga em Explorar; mouse em cima segura)
  SvgTour.prototype._pingMinimap = function (wrap, reveal) {
    var self = this;
    if (reveal) void wrap.offsetWidth; // saiu de display:none: força o fade-in
    wrap.classList.add("svg-tour__bl--on");
    clearTimeout(this._mmTimer);
    (function arm() {
      self._mmTimer = setTimeout(
        function () {
          if (wrap.matches(":hover")) return arm();
          wrap.classList.remove("svg-tour__bl--on");
        },
        self.mode === "free" ? 3000 : 1500,
      );
    })();
  };

  SvgTour.prototype._animate = function (to, instant, duration) {
    var self = this;
    cancelAnimationFrame(this._raf);
    var reduce =
      global.matchMedia &&
      matchMedia("(prefers-reduced-motion: reduce)").matches;
    var from = this.current,
      d = duration != null ? duration : this.opts.duration;
    if (instant || !from || reduce || !d) {
      this._set(to);
      return;
    }
    var fcx = from.x + from.width / 2,
      fcy = from.y + from.height / 2;
    var tcx = to.x + to.width / 2,
      tcy = to.y + to.height / 2;
    var aspect = to.height / to.width,
      t0 = performance.now();
    (function frame(now) {
      var t = Math.min(1, (now - t0) / d),
        k = ease(t);
      var w = from.width * Math.pow(to.width / from.width, k);
      var cx = fcx + (tcx - fcx) * k,
        cy = fcy + (tcy - fcy) * k;
      self._set({
        x: cx - w / 2,
        y: cy - (w * aspect) / 2,
        width: w,
        height: w * aspect,
      });
      if (t < 1) self._raf = requestAnimationFrame(frame);
    })(t0);
  };

  /* ------------------------------------------------------------------ */
  /* Tour e modos                                                       */
  /* ------------------------------------------------------------------ */
  SvgTour.prototype._clearHighlight = function () {
    var cls = this.opts.activeClass;
    this.svg.querySelectorAll("." + cls).forEach(function (e) {
      e.classList.remove(cls);
    });
    this.svg.querySelectorAll(".svg-tour__dimmable").forEach(function (e) {
      e.classList.remove("svg-tour__dimmable");
    });
  };

  SvgTour.prototype._markDimmable = function (els) {
    if (!els.length) return;
    var keep = new Set(),
      svg = this.svg;
    els.forEach(function (e) {
      for (var n = e; n && n !== svg; n = n.parentNode) keep.add(n);
    });
    keep.forEach(function (n) {
      var p = n.parentNode;
      if (!p) return;
      Array.prototype.forEach.call(p.children, function (c) {
        if (!keep.has(c) && !/^(defs|style|title|desc)$/i.test(c.tagName))
          c.classList.add("svg-tour__dimmable");
      });
    });
  };

  SvgTour.prototype._emitMode = function () {
    this.root.classList.toggle("svg-tour--free", this.mode === "free");
    if (typeof this.opts.onModeChange === "function")
      this.opts.onModeChange(this.mode, this);
    this.root.dispatchEvent(
      new CustomEvent("svgtour:mode", { detail: { mode: this.mode } }),
    );
  };

  /** "tour" | "free". Entrar em Explorar mantém a vista atual; voltar ao tour retorna à etapa. */
  SvgTour.prototype.setMode = function (mode, silent) {
    if (mode === this.mode || (mode === "free" && !this.opts.freeMode))
      return this;
    if (mode === "free") {
      this.mode = "free";
      this._clearHighlight();
      this._emitMode();
      this._updateUi();
      if (!silent && !this._freeHintShown) {
        this._freeHintShown = true;
        var L = this.opts.labels;
        this.toast(
          this._lastPointer === "touch" ? L.freeHintTouch : L.freeHintMouse,
          2600,
        );
      }
    } else {
      this.go(this.index == null ? -1 : this.index);
    }
    return this;
  };

  SvgTour.prototype.go = function (i, instant) {
    var n = this.steps.length;
    if (i >= n) i = this.opts.loop ? 0 : n - 1;
    if (i < -1) i = this.opts.loop ? n - 1 : -1;
    if (i >= 0) this._done = false;

    if (this.mode === "free") {
      this.mode = "tour";
      this._emitMode();
    }

    var t = this._targetBox(i);
    this.index = i;
    this._missing = !!t.missing;
    this._clearHighlight();
    var cls = this.opts.activeClass;
    t.els.forEach(function (e) {
      e.classList.add(cls);
    });
    if (this.opts.dimOthers) this._markDimmable(t.els);

    this._animate(this._stepView(t), instant);
    this._updateUi();
    if (this._anchored && !this._dragHintShown) {
      this._dragHintShown = true;
      this.toast(this.opts.labels.dragHint, 3200);
    }

    var step = i >= 0 ? this.steps[i] : null;
    if (typeof this.opts.onChange === "function")
      this.opts.onChange(i, step, this);
    this.root.dispatchEvent(
      new CustomEvent("svgtour:change", { detail: { index: i, step: step } }),
    );
    return this;
  };

  SvgTour.prototype._mainAction = function () {
    var i = this.index,
      n = this.steps.length;
    if (this.mode === "free") return this.setMode("tour");
    if (i === -1) return this.go(0);
    if (i >= n - 1 && !this.opts.loop) {
      this._done = true;
      return this.go(-1);
    }
    return this.next();
  };

  SvgTour.prototype._updateUi = function () {
    var self = this,
      L = this.opts.labels,
      i = this.index,
      n = this.steps.length,
      free = this.mode === "free",
      s = i >= 0 ? this.steps[i] : null,
      intro = this.opts.intro || {};

    if (this.btnModeTour) {
      this.btnModeTour.setAttribute("aria-pressed", free ? "false" : "true");
      this.btnModeFree.setAttribute("aria-pressed", free ? "true" : "false");
    }
    this.segs.forEach(function (b, j) {
      b.classList.toggle("is-done", j < i || (i === -1 && self._done));
      if (j === i && !free) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });

    var main, mainIcon, meta, title, text;
    if (free) {
      meta = L.freeMeta;
      title = "";
      text = L.freeText;
      main = i >= 0 ? L.backToStep + " " + (i + 1) : L.backToTour;
      mainIcon = "back";
    } else if (i === -1) {
      meta = n ? n + " " + (n === 1 ? "etapa" : "etapas") : "";
      title = this._done ? L.doneTitle : intro.title || L.introTitle;
      text = this._done
        ? L.doneText
        : intro.text != null
          ? intro.text
          : L.introText;
      main = this._done ? L.restart : L.start;
      mainIcon = this._done ? "restart" : "right";
    } else {
      meta = L.step + " " + (i + 1) + " " + L.of + " " + n;
      title = s.title || "";
      text = s.text || "";
      var last = i >= n - 1 && !this.opts.loop;
      main = last ? L.finish : L.next;
      mainIcon = last ? null : "right";
    }

    this.elMeta.textContent = meta;
    this.elTitle.textContent = title;
    if (!free && s && s.html) this.elText.innerHTML = s.html;
    else this.elText.textContent = text;
    this.elNote.textContent = L.notFound;
    this.elNote.classList.toggle("is-on", !free && this._missing);

    this.btnMain.innerHTML =
      (mainIcon === "back" ? icon("back") : "") +
      "<span>" +
      main +
      "</span>" +
      (mainIcon && mainIcon !== "back" ? icon(mainIcon) : "");
    this.btnMain.hidden = n === 0 && !free;
    this.btnPrev.hidden = free || i === -1;
    this.elProgress.style.visibility = free ? "hidden" : "";
  };

  SvgTour.prototype._refit = function () {
    if (this.index === null || !this.current) return;
    cancelAnimationFrame(this._raf);
    if (this.mode === "free") {
      var c = this.current,
        W = this.stage.clientWidth || 1,
        H = this.stage.clientHeight || 1,
        k = c.width / (this._lastW || W),
        cx = c.x + c.width / 2,
        cy = c.y + c.height / 2;
      this._set(
        this._clamp({
          x: cx - (W * k) / 2,
          y: cy - (H * k) / 2,
          width: W * k,
          height: H * k,
        }),
      );
    } else {
      this._set(this._stepView(this._targetBox(this.index)));
    }
  };

  SvgTour.prototype.next = function () {
    return this.go(this.index + 1);
  };
  SvgTour.prototype.prev = function () {
    return this.go(this.index - 1);
  };
  SvgTour.prototype.overview = function () {
    return this.go(-1);
  };

  SvgTour.prototype.destroy = function () {
    cancelAnimationFrame(this._raf);
    if (this._ro) this._ro.disconnect();
    if (this._onKey) this.root.removeEventListener("keydown", this._onKey);
    if (this._onFs)
      document.removeEventListener("fullscreenchange", this._onFs);
    if (this._onFocusIn)
      document.removeEventListener("focusin", this._onFocusIn);
    if (this._mmUrl) URL.revokeObjectURL(this._mmUrl);
    this._set(this.home);
  };

  SvgTour.load = function (url, container, options) {
    return fetch(url)
      .then(function (r) {
        return r.text();
      })
      .then(function (markup) {
        return new SvgTour(
          container,
          Object.assign({}, options, { svg: markup }),
        );
      });
  };

  global.SvgTour = SvgTour;
})(typeof window !== "undefined" ? window : this);
