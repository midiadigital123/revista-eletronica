// Demo da escala: comportamento extra das opções 1, 3, 4 e 5. Carrega depois de
// ../revista/script.js (usa appState, escapeHtml e DescriptorManager, que são globais dele).
// Nada aqui vai para a revista como está: na implementação real, o padrão de cada linha
// (opções 1 e 5) viria de uma classe em faixaHTML, e as zonas e faixas, de montarFaixasRegua.
(() => {
  const opcao = document.body.dataset.opcao;
  if (!/^[1-5]$/.test(opcao)) return;

  const alvo = document.querySelector(".escala-content");
  const padraoDe = (el) => [...el.classList].find((c) => /^padrao-\d$/.test(c));
  // top/height das faixas vêm no style como "calc(var(--escala-linha-height) * <y>)"
  const ys = (el) =>
    [...el.getAttribute("style").matchAll(/\*\s*([-\d.e]+)\)/g)].map((m) => parseFloat(m[1]));
  const barras = () =>
    [...alvo.querySelectorAll(".escala-barra")].map((el) => {
      const [y0, h] = ys(el);
      return { el, n: padraoDe(el), y0, y1: y0 + h };
    });

  // 1 e 5: --p (cor do padrão) em cada linha, pelo centro da linha dentro das barras
  const marcarLinhas = () => {
    const bs = barras();
    if (!bs.length) return;
    let y = 0;
    const linhas = [...alvo.querySelectorAll(".padrao-linhas > .linha")];
    const cores = linhas.map((linha) => {
      const h = linha.classList.contains("preenchimento") ? 0.5 : 1;
      const centro = y + h / 2;
      y += h;
      const b = bs.find((b) => centro >= b.y0 && centro < b.y1) || bs[bs.length - 1];
      return `var(--color-${b.n})`;
    });
    linhas.forEach((linha, i) => {
      linha.style.setProperty("--p", cores[i]);
      linha.style.setProperty("--p-prox", cores[i + 1] || cores[i]); // 1: número de fim usa a cor da linha de baixo
    });
  };

  // 1: a linha cresce no hover; barras, rótulos e cortes (posicionados em "alturas de linha")
  // passam a seguir a altura real das linhas. ResizeObserver dispara a cada quadro da transição.
  let observador;
  const seguirLinhas = () => {
    const linhas = alvo.querySelector(".padrao-linhas");
    if (!linhas) return;
    if (!observador) observador = new ResizeObserver(reposicionar);
    observador.disconnect();
    observador.observe(linhas);
    reposicionar();
  };
  const reposicionar = () => {
    let y = 0;
    const trechos = [...alvo.querySelectorAll(".padrao-linhas > .linha")].map((l) => {
      const h = l.classList.contains("preenchimento") ? 0.5 : 1;
      return { l, y0: (y += h) - h, h };
    });
    if (!trechos.length) return;
    const px = (v) => {
      const t = trechos.find((t) => v < t.y0 + t.h - 1e-9) || trechos[trechos.length - 1];
      return t.l.offsetTop + ((v - t.y0) / t.h) * t.l.offsetHeight;
    };
    alvo.querySelectorAll(".escala-barra, .padrao-label, .escala-corte").forEach((el) => {
      if (!el.dataset.y) el.dataset.y = JSON.stringify(ys(el)); // y original, em alturas de linha
      const [a, h] = JSON.parse(el.dataset.y);
      el.style.top = `${px(a)}px`;
      if (h !== undefined) el.style.height = `${px(a + h) - px(a)}px`;
    });
  };

  // 3: zona tingida e divisa por padrão, criadas a partir das barras
  const marcarZonas = () => {
    const linhas = alvo.querySelector(".padrao-linhas");
    if (!linhas) return;
    barras().forEach(({ el, n, y1 }) => {
      const zona = document.createElement("div");
      zona.className = `escala-zona ${n}`;
      zona.setAttribute("style", el.getAttribute("style"));
      linhas.prepend(zona);
      const divisa = document.createElement("div");
      divisa.className = "escala-divisa";
      divisa.style.top = `calc(var(--escala-linha-height) * ${y1})`;
      linhas.append(divisa);
    });
  };

  // 4: intervalo do padrão sob o nome (≥ início, < fim), como no editor (D-018)
  const marcarFaixas = () => {
    const dados = JSON.parse(document.getElementById("dados-revista").textContent);
    const c = (dados[appState.currentFilter] || {}).cortes;
    if (!c) return;
    const intervalos = {
      "padrao-1": [`< ${c["padrao-1"]}`],
      "padrao-2": [`≥ ${c["padrao-1"]}`, `< ${c["padrao-2"]}`],
      "padrao-3": [`≥ ${c["padrao-2"]}`, `< ${c["padrao-3"]}`],
      "padrao-4": [`≥ ${c["padrao-3"]}`],
    };
    alvo.querySelectorAll(".padrao-label").forEach((rotulo) => {
      const altura = ys(rotulo)[1];
      if (altura < 0.5) return; // faixa baixa demais: só o nome cabe
      // < 1 linha: sem amostra de cor e só o início; < 1,5: só o início; senão início e fim
      rotulo.classList.toggle("compacto", altura < 1);
      const linhas = intervalos[padraoDe(rotulo)];
      const small = document.createElement("small");
      small.innerHTML = (altura >= 1.5 ? linhas : linhas.slice(0, 1)).map(escapeHtml).join("<br>");
      rotulo.append(small);
    });
  };

  const aoRenderizar = () => {
    if (opcao === "1" || opcao === "5") marcarLinhas();
    if (opcao === "1") seguirLinhas();
    if (opcao === "3") marcarZonas();
    if (opcao === "4") marcarFaixas();
  };
  // a escala é refeita (innerHTML) a cada descritor ou ano: marca de novo a cada render
  new MutationObserver(aoRenderizar).observe(alvo, { childList: true });
  aoRenderizar();

  // 5: com 2 linhas não há estouro de largura; o texto é "truncado" quando estoura a altura
  if (opcao === "5") {
    DescriptorManager.prototype.atualizarTruncamentos = function () {
      document.querySelectorAll(".linha-conteudo.tem-texto").forEach((c) => {
        if (c.classList.contains("expandido")) return;
        const p = c.querySelector("p");
        const trunca = p.scrollHeight > p.clientHeight + 1;
        c.classList.toggle("tem-ver-mais", trunca);
        if (trunca) c.setAttribute("tabindex", "0");
        else c.removeAttribute("tabindex");
      });
    };
  }
})();
