(() => {
  const svg = document.getElementById('info');
  const NS = 'http://www.w3.org/2000/svg';
  const W = 1190.6, H = 793.7;
  const $ = s => svg.querySelector(s);
  const kids = el => [...el.children];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. Curvas de easing ---------- */
  const ease = {
    out:   k => 1 - (1 - k) ** 3,
    inOut: k => (k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2),
    back:  k => 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2,   // passa do ponto e volta
    lin:   k => k,
  };

  /* ---------- 2. Relógio próprio: pausa, velocidade e modo instantâneo ---------- */
  const clock = { speed: 1, paused: false };

  function tween(ms, tok, fn) {
    if (tok.instant || ms <= 0) { fn(1); return Promise.resolve(); }
    return new Promise(done => {
      let last = null, t = 0;
      const tick = now => {
        if (tok.cancelled) return done();
        if (last !== null && !clock.paused) t += (now - last) * clock.speed;
        last = now;
        const k = Math.min(1, t / ms);
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

  /* ---------- 3. Alvos: cada elemento ganha um <g> próprio para animar ---------- */
  const items = [];

  function wrap(node) {
    const p = node.parentNode;
    if (p.dataset && p.dataset.wrap && p.childElementCount === 1) return p;
    const g = document.createElementNS(NS, 'g');
    g.dataset.wrap = '1';
    p.insertBefore(g, node);
    g.appendChild(node);
    return g;
  }

  function pose(g, o, x = 0, y = 0, sx = 1, sy = sx) {
    g.style.opacity = o;
    g.style.transform = x || y || sx !== 1 || sy !== 1
      ? `translate(${x}px, ${y}px) scale(${sx}, ${sy})` : '';
  }

  // Elemento que entra a partir de um estado inicial (opacidade, deslocamento, escala)
  function fx(node, from, origin) {
    const g = wrap(node);
    if (origin) g.style.transformOrigin = origin;
    const f = { o: 0, x: 0, y: 0, sx: 1, sy: 1, ...from };
    if (from.s !== undefined) f.sx = f.sy = from.s;
    const bb = g.getBBox();
    const item = {
      g, f, bb, cx: bb.x + bb.width / 2, cy: bb.y + bb.height / 2,
      hide: () => pose(g, f.o, f.x, f.y, f.sx, f.sy),
      show: () => pose(g, 1),
    };
    items.push(item);
    return item;
  }

  function play(item, tok, dur = 420, e = ease.out, delay = 0) {
    return (async () => {
      if (delay) await wait(delay, tok);
      const { f, g } = item;
      await tween(dur, tok, k => {
        const v = e(k), lin = Math.min(1, k * 1.8);
        pose(g, f.o + (1 - f.o) * lin, f.x * (1 - v), f.y * (1 - v),
             f.sx + (1 - f.sx) * v, f.sy + (1 - f.sy) * v);
      });
    })();
  }

  // Linhas que se desenham (stroke-dasharray / stroke-dashoffset)
  function line(node) {
    const L = node.getTotalLength();
    const bb = node.getBBox();
    const item = {
      node, L, bb, cx: bb.x + bb.width / 2, cy: bb.y + bb.height / 2,
      hide() { node.style.opacity = 0; node.style.strokeDasharray = `${L} ${L}`; node.style.strokeDashoffset = L; },
      show() { node.style.opacity = ''; node.style.strokeDasharray = ''; node.style.strokeDashoffset = ''; },
    };
    items.push(item);
    return item;
  }

  function draw(item, tok, dur = 600, e = ease.inOut, delay = 0, onFrame) {
    return (async () => {
      if (delay) await wait(delay, tok);
      if (tok.cancelled) return;
      item.node.style.opacity = 1;
      await tween(dur, tok, k => {
        const v = e(k);
        item.node.style.strokeDashoffset = item.L * (1 - v);
        onFrame && onFrame(v);
      });
      if (!tok.cancelled) item.show();
    })();
  }

  /* ---------- 4. Efeitos: anel de chegada e "pacote" percorrendo um caminho ---------- */
  const layer = el('g', { class: 'fx-layer' }, svg);

  function ring(x, y, tok, { color = '#f0cf00', r = 18, width = 1.8 } = {}) {
    if (tok.instant) return Promise.resolve();
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

  // A linha se desenha e o pacote viaja na ponta dela
  async function travel(route, tok, dur = 1300, delay = 0) {
    if (delay) await wait(delay, tok);
    if (tok.cancelled) return;
    const pk = tok.instant ? null : makePacket();
    const at = d => route.node.getPointAtLength(Math.max(0, d));
    await draw(route, tok, dur, ease.inOut, 0, v => {
      if (!pk) return;
      const p = at(route.L * v);
      for (const c of [pk.dot, pk.halo]) { c.setAttribute('cx', p.x); c.setAttribute('cy', p.y); }
      pk.trail.forEach((c, i) => {
        const q = at(route.L * v - (i + 1) * 7);
        c.setAttribute('cx', q.x); c.setAttribute('cy', q.y);
      });
    });
    if (!pk) return;
    const end = at(route.L);
    ring(end.x, end.y, tok);
    await tween(220, tok, k => pk.g.setAttribute('opacity', 1 - k));
    pk.g.remove();
  }

  /* ---------- 5. Câmera: interpola o viewBox ---------- */
  let camOn = true;
  let view = [0, 0, W, H];
  let camTok = null;
  const setView = v => { view = v; svg.setAttribute('viewBox', v.map(n => n.toFixed(2)).join(' ')); };

  function fit([x, y, w, h], pad = 22) {
    x -= pad; y -= pad; w += pad * 2; h += pad * 2;
    const ar = W / H;
    if (w / h < ar) { const nw = h * ar; x -= (nw - w) / 2; w = nw; }
    else { const nh = w / ar; y -= (nh - h) / 2; h = nh; }
    if (w > W) { w = W; h = H; }
    x = Math.min(Math.max(x, 0), W - w);
    y = Math.min(Math.max(y, 0), H - h);
    return [x, y, w, h];
  }

  function camera(frame, tok, dur = 1150) {
    const ct = (camTok = { get cancelled() { return tok.cancelled || camTok !== ct; }, instant: tok.instant });
    const target = camOn && !reduced ? fit(frame) : [0, 0, W, H];
    const from = view.slice();
    return tween(dur, ct, k => {
      const v = ease.inOut(k);
      setView(from.map((n, i) => n + (target[i] - n) * v));
    });
  }

  /* ---------- 6. Mapeamento do infográfico ---------- */
  const byX = (a, b) => a.cx - b.cx;
  const byY = (a, b) => a.cy - b.cy;

  // Fundo
  const fk = kids($('#f2-fundo'));
  const blobs = fk.slice(0, 4).map(n => fx(n, { s: 0.88 }));
  const photo = fx(fk[5], { x: -14 });
  const deco = [fk[6], fk[8]].map(n => fx(n, { s: 0.2 }));
  const sparks = kids(fk[7]).map(n => fx(n, { s: 0.2 }));
  const [ruleLineNode, ruleMarkNode] = kids(fk[9]);
  const ruleLine = line(ruleLineNode);
  const ruleMark = fx(ruleMarkNode, { sx: 0, sy: 1 }, 'left center');
  const tinySquare = fx(fk[10], {});

  // Título
  const [subNode, titleNode, underlineNode] = kids($('#f2-titulo'));
  const titleLetters = kids(titleNode).map(n => fx(n, { y: 12 })).sort(byX);
  const subLetters = kids(subNode).map(n => fx(n, { y: 6 })).sort(byX);
  const underline = line(underlineNode);

  // Descritor (passo 1)
  const p1 = $('#f2-passo1');
  const p1k = kids(p1);
  const card = fx(p1, { s: 0.82 });
  const cardText = p1k.slice(1, 7).map(n => fx(n, { y: 6 }));
  const cardDots = p1k.slice(8).map(n => fx(n, { s: 0.1 }));

  // Conectores: os originais dão lugar a caminhos com direção definida (do card para fora)
  const linesG = $('#f2-linhas').firstElementChild;
  kids(linesG).forEach(n => (n.style.display = 'none'));
  const route = (d, cls) => line(el('path', { d, class: cls }, linesG));
  const routes = {
    toSkills:   route('M405.7 216.3 H486.5 V73.8 H640.6', 'f2-st6'),
    toProgress: route('M405.7 250.8 H550.6 V594.5 H640.6', 'f2-st8'),
    toTasks:    route('M262.8 216.8 H111.9 V445', 'f2-st6'),
    toItems:    route('M205.8 484.1 H413.1', 'f2-st6'),
  };

  // Descrição das habilidades (passo 3)
  const [btn3Node, c3] = kids($('#f2-passo3'));
  const [h3Node, tableNode, leg3Node] = kids(c3);
  const h3Mark = fx(h3Node.lastElementChild, { s: 0.1 });
  const h3Text = kids(h3Node).slice(0, -1).map(n => fx(n, { x: -8 }));
  const tk = kids(tableNode);
  const bars = tk.slice(0, 5).map(n => fx(n, { o: 1, sx: 1, sy: 0 }, 'center top'));
  const barCuts = tk.slice(5, 29).map(n => fx(n, {}));
  const rules3 = tk.slice(29, 57).map(line);
  const cells = tk.slice(57).map(n => fx(n, { x: 6 }));
  const leg3 = kids(leg3Node).map(n => fx(n, { y: 4 })).sort(byX);
  const btn3 = fx(btn3Node, { s: 0.2 });

  // Progressão da habilidade (passo 2)
  const [c2, btn2Node] = kids($('#f2-passo2'));
  const [h2Node, leg2Node, tlNode] = kids(c2);
  const h2Mark = fx(h2Node.lastElementChild, { s: 0.1 });
  const h2Text = kids(h2Node).slice(0, -1).map(n => fx(n, { x: -8 }));
  const tl = kids(tlNode);
  const barSegs = tl.slice(0, 4).map(n => fx(n, { o: 1, sx: 0, sy: 1 }, 'left center')).sort(byX);
  const ticks = tl.slice(4, 15).map(n => fx(n, { y: -4 })).sort(byX);
  const years = tl.slice(15, 27).map(n => fx(n, { y: -4 })).sort(byX);
  const levels = tl.slice(27).map(n => fx(n, { s: 0.3, y: 4 })).sort(byX);
  const leg2 = kids(leg2Node).map(n => fx(n, { y: 4 })).sort(byX);
  const btn2 = fx(btn2Node, { s: 0.2 });

  // Tarefas e itens (passo 4)
  const [left4, right4] = kids($('#f2-passo4'));
  const [h4Node, rows4Node] = kids(left4);
  const h4Mark = fx(h4Node.lastElementChild, { s: 0.1 });
  const h4Text = kids(h4Node).slice(0, -1).map(n => fx(n, { x: -8 }));
  const rows4 = kids(rows4Node).map(row => {
    const [div, code, dash, text] = kids(row);
    return { div: line(div), code: fx(code, { s: 0.5 }), dash: line(dash), text: fx(text, { x: -6 }) };
  });
  const [h4bNode, itemsNode] = kids(right4);
  const h4bMark = fx(h4bNode.lastElementChild, { s: 0.1 });
  const h4bText = kids(h4bNode).slice(0, -1).map(n => fx(n, { x: -8 }));
  const ik = kids(itemsNode);
  const itemRules = ik.slice(0, 4).map(line).sort(byY);
  const itemCards = ik.slice(4).map(n => fx(n, { s: 0.6 })).sort(byY);

  /* ---------- 7. Roteiro ---------- */
  const markRing = (m, tok) => ring(m.cx, m.cy, tok);
  const header = async (mark, texts, tok) => {
    await play(mark, tok, 380, ease.back);
    markRing(mark, tok);
    await stagger(texts, 70, (t, d) => play(t, tok, 420, ease.out, d));
  };

  async function idle(tok) {
    if (tok.instant) return;
    const spots = [btn3, btn2].map(b => [b.cx, b.cy])
      .concat(itemCards.map(c => [c.bb.x + c.bb.width - 5, c.bb.y + c.bb.height - 5]));
    while (!tok.cancelled) {
      spots.forEach(([x, y], i) =>
        wait(i * 140, tok).then(() => ring(x, y, tok, { r: 14, width: 1.4 })));
      await wait(2800, tok);
    }
  }

  const steps = [
    {
      name: 'Título',
      frame: [30, 20, 425, 360],
      async run(tok) {
        blobs.forEach((b, i) => play(b, tok, 1500, ease.out, i * 160));
        play(tinySquare, tok, 300);
        draw(ruleLine, tok, 1000, ease.inOut, 100);
        play(ruleMark, tok, 520, ease.out, 200);
        await wait(350, tok);
        await stagger(titleLetters, 38, (l, d) => play(l, tok, 520, ease.back, d));
        draw(underline, tok, 620);
        await stagger(subLetters, 18, (l, d) => play(l, tok, 380, ease.out, d));
        await wait(250, tok);
      },
    },
    {
      name: 'Descritor',
      frame: [30, 20, 425, 360],
      async run(tok) {
        play(photo, tok, 800);
        await play(card, tok, 640, ease.back, 120);
        await stagger(cardText, 90, (t, d) => play(t, tok, 420, ease.out, d));
        deco.forEach((d, i) => play(d, tok, 420, ease.back, i * 120));
        sparks.forEach((s, i) => play(s, tok, 380, ease.back, 80 + i * 110));
        await stagger(cardDots, 130, (dot, d) =>
          play(dot, tok, 360, ease.back, d).then(() => ring(dot.cx, dot.cy, tok, { color: '#1d1d1b', r: 12, width: 0.8 })));
        await wait(350, tok);
      },
    },
    {
      name: 'Conexões',
      frame: [0, 0, W, H],
      async run(tok) {
        await Promise.all([
          travel(routes.toSkills, tok, 1300, 0),
          travel(routes.toProgress, tok, 1500, 160),
          travel(routes.toTasks, tok, 1300, 320),
        ]);
        await wait(400, tok);
      },
    },
    {
      name: 'Descrição das habilidades',
      frame: [655, 60, 480, 495],
      async run(tok) {
        await header(h3Mark, h3Text, tok);
        // Varredura de cima para baixo: o atraso de cada peça depende da altura dela na tabela
        const top = 134, span = 363, scan = 1100;
        const at = y => ((y - top) / span) * scan;
        bars.forEach(b => play(b, tok, 720, ease.out, at(b.bb.y)));
        barCuts.forEach(b => play(b, tok, 300, ease.out, at(b.cy) + 260));
        rules3.forEach(r => draw(r, tok, 520, ease.out, at(r.cy)));
        await Promise.all(cells.map(c => play(c, tok, 420, ease.out, at(c.cy) + 80)));
        await stagger(leg3, 35, (l, d) => play(l, tok, 340, ease.out, d));
        await play(btn3, tok, 420, ease.back);
        ring(btn3.cx, btn3.cy, tok);
        await wait(450, tok);
      },
    },
    {
      name: 'Progressão',
      frame: [655, 582, 480, 172],
      async run(tok) {
        await header(h2Mark, h2Text, tok);
        stagger(ticks, 40, (t, d) => play(t, tok, 300, ease.out, d));
        await stagger(years, 40, (y, d) => play(y, tok, 340, ease.out, d + 60));
        // Barra que se preenche da esquerda para a direita; as letras surgem quando ela passa
        const x0 = 680, span = 448, total = 1500;
        const fill = (async () => {
          for (const s of barSegs) await play(s, tok, (s.bb.width / span) * total, ease.lin);
        })();
        levels.forEach(l => play(l, tok, 420, ease.back, ((l.cx - x0) / span) * total));
        await fill;
        await wait(250, tok);
        await stagger(leg2, 35, (l, d) => play(l, tok, 340, ease.out, d));
        await play(btn2, tok, 420, ease.back);
        ring(btn2.cx, btn2.cy, tok);
        await wait(450, tok);
      },
    },
    {
      name: 'Tarefas e itens',
      frame: [55, 452, 455, 272],
      async run(tok) {
        await header(h4Mark, h4Text, tok);
        await stagger(rows4, 170, (r, d) => Promise.all([
          draw(r.div, tok, 520, ease.out, d),
          play(r.code, tok, 440, ease.back, d + 60),
          draw(r.dash, tok, 300, ease.out, d + 180),
          play(r.text, tok, 420, ease.out, d + 220),
        ]));
        await travel(routes.toItems, tok, 750);
        await header(h4bMark, h4bText, tok);
        await stagger(itemCards, 170, (c, d) => Promise.all([
          draw(itemRules[itemCards.indexOf(c)], tok, 420, ease.out, d),
          play(c, tok, 480, ease.back, d + 80),
        ]));
        await wait(500, tok);
      },
    },
    {
      name: 'Visão geral',
      frame: [0, 0, W, H],
      async run(tok) {
        await wait(900, tok);
        idle(tok);
      },
    },
  ];

  /* ---------- 8. Player ---------- */
  let tok = { cancelled: true };
  let cur = -1, playing = false, finished = false;

  const ui = buildUI();

  function reset() {
    tok.cancelled = true;
    tok = { cancelled: false };
    layer.replaceChildren();
    items.forEach(i => i.hide());
    clock.paused = false;
    finished = false;
    cur = -1;
  }

  async function runFrom(i) {
    const t = tok;
    for (let s = i; s < steps.length; s++) {
      if (t.cancelled) return;
      cur = s; ui.update();
      const cam = camera(steps[s].frame, t);
      if (camOn && s > 0) await wait(450, t);   // a câmera sai na frente
      await steps[s].run(t);
      await cam;
    }
    if (t.cancelled) return;
    finished = true; playing = false; ui.update();
  }

  async function jump(i, autoplay = true) {
    reset();
    const t = tok;
    const instant = { get cancelled() { return t.cancelled; }, instant: true };
    for (let s = 0; s < i; s++) await steps[s].run(instant);
    if (t.cancelled) return;
    const target = steps[Math.min(i, steps.length - 1)].frame;
    setView(camOn && !reduced ? fit(target) : [0, 0, W, H]);
    if (i >= steps.length) {
      cur = steps.length - 1; finished = true; playing = false; ui.update();
      return;
    }
    playing = autoplay; clock.paused = !autoplay;
    runFrom(i);
  }

  function toggle() {
    if (finished) return jump(0);
    playing = !playing;
    clock.paused = !playing;
    ui.update();
  }

  /* ---------- 9. Controles ---------- */
  function buildUI() {
    const playBtn = document.getElementById('play');
    const playIcon = document.getElementById('play-icon');
    const segsEl = document.getElementById('segs');
    const nameEl = document.getElementById('step-name');
    const speedBtn = document.getElementById('speed');
    const camBtn = document.getElementById('camera');
    const speeds = [0.5, 1, 1.5, 2];

    const segs = steps.map((s, i) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'seg';
      b.title = s.name;
      b.setAttribute('aria-label', `Ir para: ${s.name}`);
      b.innerHTML = '<i></i>';
      b.addEventListener('click', () => jump(i));
      segsEl.appendChild(b);
      return b;
    });

    playBtn.addEventListener('click', toggle);
    document.getElementById('restart').addEventListener('click', () => jump(0));
    speedBtn.addEventListener('click', () => {
      clock.speed = speeds[(speeds.indexOf(clock.speed) + 1) % speeds.length];
      speedBtn.textContent = `${clock.speed}×`.replace('.', ',');
    });
    camBtn.addEventListener('click', () => {
      camOn = !camOn;
      camBtn.setAttribute('aria-pressed', camOn);
      const frame = finished ? [0, 0, W, H] : steps[Math.max(cur, 0)].frame;
      camera(frame, { cancelled: false }, 700);
    });

    addEventListener('keydown', e => {
      if (e.target.closest && e.target.closest('button')) return;
      if (e.key === ' ') { e.preventDefault(); toggle(); }
      if (e.key === 'ArrowRight') jump(Math.min(cur + 1, steps.length - 1));
      if (e.key === 'ArrowLeft') jump(Math.max(cur - 1, 0));
    });

    return {
      update() {
        const label = finished ? 'Repetir' : playing ? 'Pausar' : 'Continuar';
        playBtn.setAttribute('aria-label', label);
        playBtn.title = `${label} (Espaço)`;
        playIcon.setAttribute('d', playing && !finished
          ? 'M3 2h3v10H3zM8 2h3v10H8z'
          : 'M3.5 1.8v10.4L12 7z');
        segs.forEach((b, i) => {
          b.classList.toggle('is-current', i === cur && !finished);
          b.firstChild.style.setProperty('--fill', i < cur || finished || i === cur ? 1 : 0);
        });
        nameEl.innerHTML = `<b>${cur + 1} de ${steps.length}</b>&ensp;${steps[Math.max(cur, 0)].name}`;
      },
    };
  }

  /* ---------- Início ---------- */
  if (reduced) {
    jump(steps.length).then(() => (svg.style.visibility = 'visible'));
  } else {
    reset();
    setView(camOn ? fit(steps[0].frame) : [0, 0, W, H]);
    svg.style.visibility = 'visible';
    playing = true;
    runFrom(0);
  }
})();
