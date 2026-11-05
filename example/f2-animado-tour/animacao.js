/**
 * DEMO — cada passo do svg-tour toca a animação do seu bloco.
 *
 * Motor de efeitos vem de example/infografico-animado/fonte/animacao.js; a câmera é só a do tour.
 *  - Visão geral (início): fundo e título se montam; os blocos ainda não vistos ficam escondidos.
 *  - Ao entrar num passo pela 1ª vez: o conector "viaja" do descritor até o bloco
 *    enquanto a câmera do tour se move, e o bloco se monta.
 *  - Passo já visto aparece pronto. Trocar de passo no meio da animação conclui a cena na hora.
 *  - Modo Explorar: tudo o que falta aparece pronto (ninguém fica diante de um bloco vazio).
 *  - Movimento reduzido ou SVG fora da árvore esperada: nada anima, o tour fica como hoje.
 * Sem alterar o svg-tour.js: só os eventos svgtour:change e svgtour:mode.
 */
(() => {
  const t = window.f2Tour;
  const raiz = document.getElementById('revista');
  if (!t || !raiz || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const svg = t.svg;
  const NS = 'http://www.w3.org/2000/svg';
  const $ = s => svg.querySelector(s);
  const kids = el => [...el.children];

  /* ---------- Easing e relógio ---------- */
  const ease = {
    out:   k => 1 - (1 - k) ** 3,
    inOut: k => (k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2),
    back:  k => 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2,
    lin:   k => k,
  };
  function tween(ms, tok, fn) {
    if (ms <= 0) { fn(1); return Promise.resolve(); }
    return new Promise(done => {
      const t0 = performance.now();
      const tick = now => {
        if (tok.cancelled) return done();
        const k = Math.min(1, (now - t0) / ms);
        fn(k);
        k < 1 ? requestAnimationFrame(tick) : done();
      };
      requestAnimationFrame(tick);
    });
  }
  const wait = (ms, tok) => tween(ms, tok, () => {});
  const stagger = (list, gap, fn) => Promise.all(list.map((it, i) => fn(it, i * gap)));
  const el = (tag, attrs, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    parent && parent.appendChild(n);
    return n;
  };

  /* ---------- Peças: cada uma entra no "balde" da cena que está sendo mapeada ---------- */
  const cenas = {};
  let balde = null;
  const cena = nome => (balde = cenas[nome] = { nome, itens: [], feita: false, tok: null });

  function wrap(node) {
    const p = node.parentNode;
    if (p.dataset && p.dataset.wrap && p.childElementCount === 1) return p;
    const g = document.createElementNS(NS, 'g');
    g.dataset.wrap = '1';
    p.insertBefore(g, node);
    g.appendChild(node);
    return g;
  }
  // O svg-tour força `opacity: 1 !important` em tudo dentro do passo ativo; a opacidade vai também
  // em --ab-o, que o animacao.css aplica com seletor mais específico. '' limpa os dois.
  const op = (el, v) => {
    el.style.opacity = v;
    v === '' ? el.style.removeProperty('--ab-o') : el.style.setProperty('--ab-o', v);
  };
  function pose(g, o, x = 0, y = 0, sx = 1, sy = sx) {
    op(g, o);
    g.style.transform = x || y || sx !== 1 || sy !== 1 ? `translate(${x}px, ${y}px) scale(${sx}, ${sy})` : '';
  }
  function fx(node, from, origin) {
    if (!node) throw new Error('peça ausente no SVG');
    const g = wrap(node);
    if (origin) g.style.transformOrigin = origin;
    const f = { o: 0, x: 0, y: 0, sx: 1, sy: 1, ...from };
    if (from.s !== undefined) f.sx = f.sy = from.s;
    const bb = g.getBBox();
    const item = {
      g, f, bb, cx: bb.x + bb.width / 2, cy: bb.y + bb.height / 2,
      // Em repouso, só opacidade: deslocamento e escala (até 0) mudariam a caixa que o tour usa para
      // enquadrar o passo. O estado inicial do movimento entra no 1º quadro do play().
      hide: () => { op(g, 0); g.style.transform = ''; },
      show: () => { op(g, ''); g.style.transform = ''; }, // sem inline: o esmaecimento do tour vale
    };
    balde.itens.push(item);
    return item;
  }
  function play(item, tok, dur = 420, e = ease.out, delay = 0) {
    return (async () => {
      if (delay) await wait(delay, tok);
      const { f, g } = item;
      await tween(dur, tok, k => {
        const v = e(k), lin = Math.min(1, k * 1.8);
        pose(g, f.o + (1 - f.o) * lin, f.x * (1 - v), f.y * (1 - v), f.sx + (1 - f.sx) * v, f.sy + (1 - f.sy) * v);
      });
    })();
  }
  function line(node) {
    if (!node) throw new Error('traço ausente no SVG');
    const L = node.getTotalLength();
    const bb = node.getBBox();
    const item = {
      node, L, bb, cx: bb.x + bb.width / 2, cy: bb.y + bb.height / 2,
      hide() { op(node, 0); node.style.strokeDasharray = `${L} ${L}`; node.style.strokeDashoffset = L; },
      show() { op(node, ''); node.style.strokeDasharray = ''; node.style.strokeDashoffset = ''; },
    };
    balde.itens.push(item);
    return item;
  }
  function draw(item, tok, dur = 600, e = ease.inOut, delay = 0, onFrame) {
    return (async () => {
      if (delay) await wait(delay, tok);
      if (tok.cancelled) return;
      op(item.node, 1);
      await tween(dur, tok, k => {
        item.node.style.strokeDashoffset = item.L * (1 - e(k));
        onFrame && onFrame(e(k));
      });
      if (!tok.cancelled) item.show();
    })();
  }

  /* ---------- Efeitos ---------- */
  const layer = el('g', { class: 'fx-layer', 'pointer-events': 'none' }, svg);
  function ring(x, y, tok, { color = '#f0cf00', r = 18, width = 1.8 } = {}) {
    if (tok.cancelled) return Promise.resolve();
    const c = el('circle', { cx: x, cy: y, r: 3, fill: 'none', stroke: color, 'stroke-width': width }, layer);
    return tween(720, tok, k => {
      c.setAttribute('r', 3 + (r - 3) * ease.out(k));
      c.setAttribute('opacity', 0.9 * (1 - k));
    }).then(() => c.remove());
  }
  function makePacket() {
    const g = el('g', {}, layer);
    const trail = [2.6, 2, 1.4].map((r, i) =>
      el('circle', { r, fill: '#ffed00', stroke: '#1d1d1b', 'stroke-width': 0.4, opacity: 0.85 - i * 0.25 }, g));
    el('circle', { r: 8, fill: '#ffed00', opacity: 0.35, class: 'halo' }, g);
    const dot = el('circle', { r: 3.8, fill: '#ffed00', stroke: '#1d1d1b', 'stroke-width': 0.8 }, g);
    return { g, dot, halo: g.querySelector('.halo'), trail };
  }
  async function travel(route, tok, dur = 1300) {
    if (tok.cancelled) return;
    const pk = makePacket();
    const at = d => route.node.getPointAtLength(Math.max(0, d));
    await draw(route, tok, dur, ease.inOut, 0, v => {
      const p = at(route.L * v);
      for (const c of [pk.dot, pk.halo]) { c.setAttribute('cx', p.x); c.setAttribute('cy', p.y); }
      pk.trail.forEach((c, i) => {
        const q = at(route.L * v - (i + 1) * 7);
        c.setAttribute('cx', q.x); c.setAttribute('cy', q.y);
      });
    });
    const end = at(route.L);
    ring(end.x, end.y, tok);
    await tween(220, tok, k => pk.g.setAttribute('opacity', 1 - k));
    pk.g.remove();
  }
  // O ponto viaja enquanto a câmera do tour chega (700 ms);
  // o bloco começa a se montar quando a câmera pousa, sem esperar o ponto terminar.
  const chegar = (route, tok) => {
    travel(route, tok, t.opts.duration);
    return wait(Math.max(0, t.opts.duration - 50), tok);
  };
  const header = async (mark, texts, tok) => {
    await play(mark, tok, 380, ease.back);
    ring(mark.cx, mark.cy, tok);
    await stagger(texts, 70, (x, d) => play(x, tok, 420, ease.out, d));
  };

  /* ---------- Mapeamento (pela ordem dos filhos: é o ponto frágil, ver LEIA-ME) ---------- */
  const byX = (a, b) => a.cx - b.cx;
  const byY = (a, b) => a.cy - b.cy;
  let m;
  try {
    m = mapear();
  } catch (erro) {
    console.warn('animação: SVG fora da árvore esperada; tour sem animação.', erro);
    Object.values(cenas).forEach(c => c.itens.forEach(i => i.show()));
    return;
  }

  function mapear() {
    const fk = kids($('#f2-fundo'));
    const [ruleLineNode, ruleMarkNode] = kids(fk[9]);
    const [subNode, titleNode, underlineNode] = kids($('#f2-titulo'));
    const p1 = $('#f2-passo1');
    const p1k = kids(p1);
    const [btn3Node, c3] = kids($('#f2-passo3'));
    const [h3Node, tableNode, leg3Node] = kids(c3);
    const tk = kids(tableNode);
    const [c2, btn2Node] = kids($('#f2-passo2'));
    const [h2Node, leg2Node, tlNode] = kids(c2);
    const tl = kids(tlNode);
    const [left4, right4] = kids($('#f2-passo4'));
    const [h4Node, rows4Node] = kids(left4);
    const [h4bNode, itemsNode] = kids(right4);
    const ik = kids(itemsNode);
    // Contagens que o roteiro assume; se o design mudar o arquivo, a animação desliga sozinha.
    if (fk.length !== 11 || p1k.length !== 11 || tk.length < 58 || tl.length < 28 || ik.length < 5)
      throw new Error(`contagens: fundo ${fk.length}, passo1 ${p1k.length}, tabela ${tk.length}, linha ${tl.length}, itens ${ik.length}`);
    const linesG = $('#f2-linhas').firstElementChild;
    const originais = kids(linesG);
    const route = (d, cls) => line(el('path', { d, class: cls }, linesG));
    const r = {};

    cena('abertura');
    r.blobs = fk.slice(0, 4).map(n => fx(n, { s: 0.88 }));
    r.ruleLine = line(ruleLineNode);
    r.ruleMark = fx(ruleMarkNode, { sx: 0, sy: 1 }, 'left center');
    r.tinySquare = fx(fk[10], {});
    r.titleLetters = kids(titleNode).map(n => fx(n, { y: 12 })).sort(byX);
    r.subLetters = kids(subNode).map(n => fx(n, { y: 6 })).sort(byX);
    r.underline = line(underlineNode);

    cena('f2-passo1');
    r.photo = fx(fk[5], { x: -14 });
    r.deco = [fk[6], fk[8]].map(n => fx(n, { s: 0.2 }));
    r.sparks = kids(fk[7]).map(n => fx(n, { s: 0.2 }));
    r.card = fx(p1, { s: 0.82 });
    r.cardText = p1k.slice(1, 7).map(n => fx(n, { y: 6 }));
    r.cardDots = p1k.slice(8).map(n => fx(n, { s: 0.1 }));

    cena('f2-passo2');
    r.toProgress = route('M405.7 250.8 H550.6 V594.5 H640.6', 'f2-st8');
    r.h2Mark = fx(h2Node.lastElementChild, { s: 0.1 });
    r.h2Text = kids(h2Node).slice(0, -1).map(n => fx(n, { x: -8 }));
    r.barSegs = tl.slice(0, 4).map(n => fx(n, { o: 1, sx: 0, sy: 1 }, 'left center')).sort(byX);
    r.ticks = tl.slice(4, 15).map(n => fx(n, { y: -4 })).sort(byX);
    r.years = tl.slice(15, 27).map(n => fx(n, { y: -4 })).sort(byX);
    r.levels = tl.slice(27).map(n => fx(n, { s: 0.3, y: 4 })).sort(byX);
    r.leg2 = kids(leg2Node).map(n => fx(n, { y: 4 })).sort(byX);
    r.btn2 = fx(btn2Node, { s: 0.2 });

    cena('f2-passo3');
    r.toSkills = route('M405.7 216.3 H486.5 V73.8 H640.6', 'f2-st6');
    r.h3Mark = fx(h3Node.lastElementChild, { s: 0.1 });
    r.h3Text = kids(h3Node).slice(0, -1).map(n => fx(n, { x: -8 }));
    r.bars = tk.slice(0, 5).map(n => fx(n, { o: 1, sx: 1, sy: 0 }, 'center top'));
    r.barCuts = tk.slice(5, 29).map(n => fx(n, {}));
    r.rules3 = tk.slice(29, 57).map(line);
    r.cells = tk.slice(57).map(n => fx(n, { x: 6 }));
    r.leg3 = kids(leg3Node).map(n => fx(n, { y: 4 })).sort(byX);
    r.btn3 = fx(btn3Node, { s: 0.2 });

    cena('f2-passo4');
    r.toTasks = route('M262.8 216.8 H111.9 V445', 'f2-st6');
    r.toItems = route('M205.8 484.1 H413.1', 'f2-st6');
    r.h4Mark = fx(h4Node.lastElementChild, { s: 0.1 });
    r.h4Text = kids(h4Node).slice(0, -1).map(n => fx(n, { x: -8 }));
    r.rows4 = kids(rows4Node).map(row => {
      const [div, code, dash, text] = kids(row);
      return { div: line(div), code: fx(code, { s: 0.5 }), dash: line(dash), text: fx(text, { x: -6 }) };
    });
    r.h4bMark = fx(h4bNode.lastElementChild, { s: 0.1 });
    r.h4bText = kids(h4bNode).slice(0, -1).map(n => fx(n, { x: -8 }));
    r.itemRules = ik.slice(0, 4).map(line).sort(byY);
    r.itemCards = ik.slice(4).map(n => fx(n, { s: 0.6 })).sort(byY);

    // Conectores originais dão lugar aos caminhos com direção (do card para fora). Só depois de tudo achado.
    originais.forEach(n => (n.style.display = 'none'));
    return r;
  }

  /* ---------- Roteiro de cada cena ---------- */
  cenas.abertura.run = async tok => {
    m.blobs.forEach((b, i) => play(b, tok, 1500, ease.out, i * 160));
    play(m.tinySquare, tok, 300);
    draw(m.ruleLine, tok, 1000, ease.inOut, 100);
    play(m.ruleMark, tok, 520, ease.out, 200);
    await wait(350, tok);
    await stagger(m.titleLetters, 38, (l, d) => play(l, tok, 520, ease.back, d));
    draw(m.underline, tok, 620);
    await stagger(m.subLetters, 18, (l, d) => play(l, tok, 380, ease.out, d));
  };

  cenas['f2-passo1'].run = async tok => {
    play(m.photo, tok, 800);
    await play(m.card, tok, 640, ease.back, 120);
    await stagger(m.cardText, 90, (x, d) => play(x, tok, 420, ease.out, d));
    m.deco.forEach((d, i) => play(d, tok, 420, ease.back, i * 120));
    m.sparks.forEach((s, i) => play(s, tok, 380, ease.back, 80 + i * 110));
    await stagger(m.cardDots, 130, (dot, d) =>
      play(dot, tok, 360, ease.back, d).then(() => ring(dot.cx, dot.cy, tok, { color: '#1d1d1b', r: 12, width: 0.8 })));
  };

  cenas['f2-passo2'].run = async tok => {
    await chegar(m.toProgress, tok);
    await header(m.h2Mark, m.h2Text, tok);
    stagger(m.ticks, 40, (x, d) => play(x, tok, 300, ease.out, d));
    await stagger(m.years, 40, (y, d) => play(y, tok, 340, ease.out, d + 60));
    const x0 = 680, span = 448, total = 1500;
    const fill = (async () => {
      for (const s of m.barSegs) await play(s, tok, (s.bb.width / span) * total, ease.lin);
    })();
    m.levels.forEach(l => play(l, tok, 420, ease.back, ((l.cx - x0) / span) * total));
    await fill;
    await stagger(m.leg2, 35, (l, d) => play(l, tok, 340, ease.out, d));
    await play(m.btn2, tok, 420, ease.back);
    ring(m.btn2.cx, m.btn2.cy, tok);
  };

  cenas['f2-passo3'].run = async tok => {
    await chegar(m.toSkills, tok);
    await header(m.h3Mark, m.h3Text, tok);
    const top = 134, span = 363, scan = 1100;
    const at = y => ((y - top) / span) * scan;
    m.bars.forEach(b => play(b, tok, 720, ease.out, at(b.bb.y)));
    m.barCuts.forEach(b => play(b, tok, 300, ease.out, at(b.cy) + 260));
    m.rules3.forEach(r => draw(r, tok, 520, ease.out, at(r.cy)));
    await Promise.all(m.cells.map(c => play(c, tok, 420, ease.out, at(c.cy) + 80)));
    await stagger(m.leg3, 35, (l, d) => play(l, tok, 340, ease.out, d));
    await play(m.btn3, tok, 420, ease.back);
    ring(m.btn3.cx, m.btn3.cy, tok);
  };

  cenas['f2-passo4'].run = async tok => {
    await chegar(m.toTasks, tok);
    await header(m.h4Mark, m.h4Text, tok);
    await stagger(m.rows4, 170, (r, d) => Promise.all([
      draw(r.div, tok, 520, ease.out, d),
      play(r.code, tok, 440, ease.back, d + 60),
      draw(r.dash, tok, 300, ease.out, d + 180),
      play(r.text, tok, 420, ease.out, d + 220),
    ]));
    await travel(m.toItems, tok, 750);
    await header(m.h4bMark, m.h4bText, tok);
    await stagger(m.itemCards, 170, (c, d) => Promise.all([
      draw(m.itemRules[m.itemCards.indexOf(c)], tok, 420, ease.out, d),
      play(c, tok, 480, ease.back, d + 80).then(() => ring(c.bb.x + c.bb.width - 5, c.bb.y + c.bb.height - 5, tok, { r: 14, width: 1.4 })),
    ]));
  };

  /* ---------- Estados: escondido → animando → pronto ---------- */
  function concluir(c) {
    if (c.feita) return;
    if (c.tok) c.tok.cancelled = true;
    c.itens.forEach(i => i.show());
    c.feita = true;
    c.tok = null;
  }

  async function tocar(c) {
    if (c.feita || c.tok) return;
    const tok = (c.tok = { cancelled: false });
    await c.run(tok);
    if (!tok.cancelled) concluir(c);
  }

  raiz.addEventListener('svgtour:change', e => {
    const alvo = e.detail.step && e.detail.step.target;
    Object.values(cenas).forEach(c => c.tok && c.nome !== alvo && concluir(c)); // trocou no meio: conclui na hora
    if (cenas[alvo]) tocar(cenas[alvo]);
  });
  raiz.addEventListener('svgtour:mode', e => {
    if (e.detail.mode === 'free') Object.values(cenas).forEach(concluir);
  });

  /* ---------- Início: tudo escondido no mesmo quadro em que o tour foi montado; o título se monta ---------- */
  Object.values(cenas).forEach(c => c.itens.forEach(i => i.hide()));
  tocar(cenas.abertura);
})();
