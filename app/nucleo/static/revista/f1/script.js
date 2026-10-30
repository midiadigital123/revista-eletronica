/**
 * ==========================================
 * REVISTA ELETRÔNICA - SISTEMA DE DESCRITORES
 * Sistema interativo para análise de resultados
 * ==========================================
 *
 * Formato do JSON em <script type="application/json" id="dados-revista"> (gerado pelo resolver, S07):
 *
 *   {
 *     "<etapa>": {                                   // "5ef", "9ef", "3em"...; uma aba por etapa
 *       "scaleRange": { "min": 0, "max": 500 },
 *       "cortes": { "padrao-1": 125, ..., "padrao-<n-1>": 450 },  // 1 a 4 cortes, crescentes
 *       "padroes": [                                 // n = cortes + 1 (2 a 5), de baixo para cima
 *         { "chave": "padrao-1", "rotulo": "Padrão 01" }, ...
 *       ],
 *       "D01": { topic, description, prerequisites[], bncc,
 *                scale: { "padrao-1": [{ level, content, item? }], ..., "padrao-<n>": [...] } }
 *     }
 *   }
 *
 * O padrão k vai de cortes["padrao-<k-1>"] (ou min) até cortes["padrao-<k>"] (ou max).
 * `scale` já vem dividido por padrão e com as linhas vazias ("---") prontas.
 * Cores: uma variável CSS por padrão (--color-padrao-k e --color-padrao-k-bg), sobrescritas num
 * <style>:root{...}</style> da página; o styles.css traz o padrão de 1 a 5.
 */

// ==========================================
// CONFIGURAÇÃO
// ==========================================

const ETAPA = /^(\d+)(ef|em)$/;

/** prefers-reduced-motion: sem animações em linha e rolagem instantânea. */
const reduzMovimento = () =>
  typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
const comportamento = () => (reduzMovimento() ? "auto" : "smooth");

/** Rótulo curto da etapa: "5ef" → "5º EF", "3em" → "3ª EM"; fora do formato, a própria chave. */
function rotuloAno(ano) {
  const m = ETAPA.exec(ano);
  if (!m) return ano;
  return m[2] === "ef" ? `${m[1]}º EF` : `${m[1]}ª EM`;
}

/** Rótulo longo: "5º Ano do Ensino Fundamental", "3ª Série do Ensino Médio". */
function rotuloAnoLongo(ano) {
  const m = ETAPA.exec(ano);
  if (!m) return ano;
  return m[2] === "ef"
    ? `${m[1]}º Ano do Ensino Fundamental`
    : `${m[1]}ª Série do Ensino Médio`;
}
const CHAVE_DESCRITOR = /^D\d{2}$/;

/** Escapa texto dos dados antes de ir para innerHTML. */
function escapeHtml(valor) {
  return String(valor).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
}

/** Códigos de descritor de um ano (ignora scaleRange, cortes e demais chaves). */
function descriptorKeys(filterData) {
  return Object.keys(filterData || {})
    .filter((k) => CHAVE_DESCRITOR.test(k))
    .sort();
}

// ==========================================
// RÉGUA DA ESCALA (função pura, testada em regua.test.mjs)
// ==========================================

/** Chaves dos padrões de cima para baixo: n = cortes + 1 ("padrao-n", ..., "padrao-1"). */
function padroesDeCima(cortes) {
  const n = Object.keys(cortes).length + 1;
  return Array.from({ length: n }, (_, i) => `padrao-${n - i}`);
}

/**
 * Motivo pelo qual o JSON de uma etapa não serve para a régua; null se está certo.
 * Sem rótulo ou corte de reserva: JSON errado é bug do resolver e tem que aparecer.
 */
function problemaDaEtapa({ scaleRange, cortes, padroes }) {
  if (!scaleRange) return "scaleRange ausente";
  const k = Object.keys(cortes || {}).length;
  if (k < 1 || k > 4) return `cortes deve ter de 1 a 4 chaves (veio ${k})`;
  let anterior = scaleRange.min;
  for (let i = 1; i <= k; i++) {
    const v = cortes[`padrao-${i}`];
    if (v === undefined) return `cortes sem a chave padrao-${i}`;
    if (typeof v !== "number" || v <= anterior || v >= scaleRange.max)
      return `cortes.padrao-${i} = ${v}: os cortes devem crescer dentro de (${scaleRange.min}, ${scaleRange.max})`;
    anterior = v;
  }
  if (!Array.isArray(padroes)) return "padroes ausente";
  if (padroes.length !== k + 1) return `padroes deve ter ${k + 1} itens (veio ${padroes.length})`;
  const i = padroes.findIndex((p, j) => !p || p.chave !== `padrao-${j + 1}`);
  if (i >= 0) return `padroes[${i}].chave deve ser padrao-${i + 1}`;
  return null;
}

/**
 * Régua da escala, de cima para baixo.
 * n padrões contíguos (n = cortes + 1, de 2 a 5): P01 = [min, cortes.padrao-1],
 * Pk = [padrao-(k-1), padrao-k], Pn = [padrao-(n-1), max].
 * As faixas vêm só dos níveis das linhas (todos os padrões juntos): base = nível,
 * topo = nível de cima (ou max). Corte que não cai num nível fica dentro da faixa
 * que o contém, sem criar faixa nova. Padrão sem linhas ganha uma faixa "---"
 * (com preenchimento acima, se preciso); sobra até o mínimo vira preenchimento.
 * Preenchimento (conteudo null) e linha sem habilidade ("---") têm meia altura.
 * rotuloBase é o número do tick na base: null quando é o mínimo ou o máximo
 * (aparecem fora da régua) ou quando a faixa seguinte tem a mesma base (o número sai só nela).
 * Retorna { faixas, cortes: [{padrao, valor, y, exato}], padroes: [{padrao, y0, y1}] },
 * com y em alturas de linha a partir do topo.
 */
const ehVazia = (conteudo) => conteudo === null || conteudo === "---";

function montarFaixasRegua({ min, max, cortes, escala }) {
  const PADROES_DE_CIMA = padroesDeCima(cortes);
  const n = PADROES_DE_CIMA.length;
  // [topo, base] de cada padrão: padrão k vai de cortes[padrao-(k-1)] (ou min) a cortes[padrao-k] (ou max)
  const limites = Object.fromEntries(
    PADROES_DE_CIMA.map((p, i) => {
      const k = n - i;
      return [p, [k === n ? max : cortes[`padrao-${k}`], k === 1 ? min : cortes[`padrao-${k - 1}`]]];
    }),
  );
  const entradas = [];
  for (const padrao of PADROES_DE_CIMA) {
    const linhas = (escala && escala[padrao]) || [];
    for (const { level, fim, content, item } of linhas)
      entradas.push({ padrao, base: level, fim, conteudo: content || "---", item });
    if (!linhas.length) {
      const [topoPadrao, basePadrao] = limites[padrao];
      entradas.push({ padrao, base: topoPadrao, conteudo: null });
      entradas.push({ padrao, base: basePadrao, conteudo: "---" });
    }
  }
  // sort estável: mesmo nível mantém a ordem dos padrões e das linhas
  entradas.sort((a, b) => b.base - a.base);

  const faixas = [];
  let topo = max;
  for (const e of entradas) {
    if (e.conteudo === null && e.base === topo) continue; // preenchimento de altura zero
    // preenchimento acima de um padrão vazio pertence ao padrão de cima
    if (e.conteudo === null)
      e.padrao = PADROES_DE_CIMA.find((p) => limites[p][1] <= e.base) || e.padrao;
    // habilidade que cruza um corte tem a cor do padrão da âncora maior: o `fim` da tarefa, como
    // padrao_da_tarefa do resolver (D-154); sem `fim`, o topo da faixa. Limite aberto: âncora
    // exatamente no corte não sobe de padrão
    else if (!ehVazia(e.conteudo))
      e.padrao = PADROES_DE_CIMA.find((p) => limites[p][1] < (e.fim ?? topo)) || e.padrao;
    faixas.push({ ...e, topo });
    topo = e.base;
  }
  if (topo > min) faixas.push({ padrao: "padrao-1", topo, base: min, conteudo: null });

  let y = 0;
  const valoresCorte = Object.values(cortes);
  const comY = faixas.map((f, i) => {
    const proxima = faixas[i + 1];
    const mesmoNivel = Boolean(proxima && proxima.base === f.base);
    const mostrar = f.base !== min && f.base !== max && !mesmoNivel;
    const altura = ehVazia(f.conteudo) ? 0.5 : 1;
    const y0 = y;
    y += altura;
    return {
      ...f,
      y0,
      altura,
      mesmoNivel, // tick e número saem só na última faixa do nível
      rotuloBase: mostrar ? f.base : null,
      ehCorte: mostrar && valoresCorte.includes(f.base),
    };
  });

  // Corte que não cai num nível fica solto dentro da faixa que o contém. Os n cortes da mesma
  // faixa ocupam as posições k/(n+1) (o maior em cima) e o CSS dá à faixa (n+1) × 1,75rem de
  // altura mínima (`.tem-corte`): o selo não encosta no número vizinho nem em outro selo.
  const faixaDoCorte = (v) => comY.find((f) => f.topo > v && v > f.base);
  const soltos = valoresCorte
    .filter((v) => v > min && v < max && !comY.some((f) => f.base === v))
    .sort((a, b) => b - a);
  for (const f of comY) f.cortesDentro = soltos.filter((v) => faixaDoCorte(v) === f).length;

  // y de um valor: na borda se coincide com um nível; senão no slot do selo dentro da faixa
  const posicao = (v) => {
    if (v >= max) return { y: 0, exato: true };
    if (v <= min) return { y, exato: true };
    const borda = comY.findLast((f) => f.base === v);
    if (borda) return { y: borda.y0 + borda.altura, exato: true };
    const f = faixaDoCorte(v);
    const k = soltos.filter((s) => faixaDoCorte(s) === f).indexOf(v) + 1;
    return { y: f.y0 + (f.altura * k) / (f.cortesDentro + 1), exato: false };
  };

  return {
    faixas: comY,
    cortes: PADROES_DE_CIMA.slice(1).map((padrao) => ({
      padrao,
      valor: cortes[padrao],
      ...posicao(cortes[padrao]),
    })),
    padroes: PADROES_DE_CIMA.map((padrao) => ({
      padrao,
      y0: posicao(limites[padrao][0]).y,
      y1: posicao(limites[padrao][1]).y,
    })),
  };
}

/**
 * Cor do texto sobre um fundo "#rgb"/"#rrggbb": preto ou branco, o de maior razão de contraste
 * WCAG 2 (D-158). Com as 5 cores atuais dá sempre preto (ex.: #f72628 → preto, 5,3:1).
 */
function corTextoSobre(hex) {
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(String(hex).trim());
  if (!m) return "#000";
  const h = m[1].length === 3 ? [...m[1]].map((c) => c + c).join("") : m[1];
  const canal = (i) => {
    const c = parseInt(h.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  const L = 0.2126 * canal(0) + 0.7152 * canal(2) + 0.0722 * canal(4); // luminância relativa
  // razão sobre branco (L=1) contra razão sobre preto (L=0); empate fica no preto
  return 1.05 / (L + 0.05) > (L + 0.05) / 0.05 ? "#fff" : "#000";
}

const TIPOS_ITEM = ["pdf", "png", "jpg"];

/** Tipo válido do item (lista fixa); ausente ou desconhecido cai em "pdf" (itens antigos). */
function tipoDoItem(tipo) {
  return TIPOS_ITEM.includes(tipo) ? tipo : "pdf";
}

/** "nível 556" ou "níveis 556 a 616": âncora menor e maior da habilidade (fim igual ao início = um só). */
function rotuloNiveis(inicio, fim) {
  return fim == null || String(fim) === String(inicio) ? `nível ${inicio}` : `níveis ${inicio} a ${fim}`;
}

/** URL do arquivo do item no pacote; só interpola id escapado e tipo validado. */
function urlDoItem(id, tipo) {
  return `arquivos/itens/${encodeURIComponent(id)}.${tipoDoItem(tipo)}`;
}

function alturaLinhaColapsada() {
  return getComputedStyle(document.documentElement)
    .getPropertyValue("--escala-linha-height")
    .trim();
}

// Exporta para o teste em Node; no navegador (script clássico) `module` não existe.
if (typeof module !== "undefined") module.exports = { montarFaixasRegua, padroesDeCima, problemaDaEtapa, rotuloAno, rotuloAnoLongo, corTextoSobre, tipoDoItem, urlDoItem, rotuloNiveis };

// ==========================================
// ESTADO DA APLICAÇÃO
// ==========================================

const appState = {
  currentFilter: null, // definido em App.bootstrap (primeiro ano presente)
  currentDescriptor: null,
  scrolling: false,
  etapasInvalidas: new Set(), // etapas cujo JSON falhou em problemaDaEtapa: sem escala

};

// ==========================================
// GERENCIAMENTO DE FILTROS
// ==========================================

class FilterManager {
  constructor(data) {
    this.data = data;
    this.filterButtons = document.querySelectorAll(".filtro-btn");
    this.init();
  }

  init() {
    this.filterButtons.forEach((button) => {
      const presente = Boolean(this.data[button.dataset.filter]);
      button.hidden = !presente;
      button.classList.toggle(
        "active",
        button.dataset.filter === appState.currentFilter,
      );
      button.addEventListener("click", (e) => this.handleFilterClick(e));
    });
    this.renderLabels();
  }

  handleFilterClick(event) {
    const button = event.currentTarget;
    const filter = button.getAttribute("data-filter");

    if (filter === appState.currentFilter) return;

    appState.currentFilter = filter;
    this.updateActiveFilter(button);
    this.animateFilterChange();

    window.dispatchEvent(
      new CustomEvent("filterChanged", { detail: { filter } }),
    );
  }

  updateActiveFilter(activeButton) {
    this.filterButtons.forEach((btn) => btn.classList.remove("active"));
    activeButton.classList.add("active");
    this.renderLabels();
  }

  renderLabels() {
    this.filterButtons.forEach((btn) => {
      const filter = btn.getAttribute("data-filter");
      const isActive = btn.classList.contains("active");
      btn.setAttribute("aria-pressed", String(isActive));
      btn.textContent = isActive ? rotuloAnoLongo(filter) : rotuloAno(filter);
    });
  }

  animateFilterChange() {
    if (reduzMovimento()) return;
    const contentWrapper = document.querySelector(".content-wrapper");
    if (contentWrapper) {
      contentWrapper.style.opacity = "0";
      contentWrapper.style.transform = "translateY(10px)";
      setTimeout(() => {
        contentWrapper.style.transition =
          "opacity 0.3s ease, transform 0.3s ease";
        contentWrapper.style.opacity = "1";
        contentWrapper.style.transform = "translateY(0)";
      }, 50);
    }
  }
}

// ==========================================
// GERENCIAMENTO DE DESCRITORES
// ==========================================

class DescriptorManager {
  constructor(data) {
    this.data = data;
    this.dropdownOpen = false;
    this.init();
  }

  init() {
    this.renderButtons();
    this.initHabilidadeHover();
    this.initDestaqueNumeros();
    this.initDropdown();
    this.initModal();

    // A largura disponível muda com fontes e redimensionamento: reavalia onde há "..."
    let timerResize = null;
    window.addEventListener("resize", () => {
      clearTimeout(timerResize);
      timerResize = setTimeout(() => this.atualizarTruncamentos(), 150);
    });
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => this.atualizarTruncamentos());
    }

    window.addEventListener("filterChanged", () => {
      appState.currentDescriptor = null;
      this.dropdownOpen = false;
      this.renderButtons();
      this.updateDropdownUI();
    });
  }

  initModal() {
    const modal = document.getElementById("itemModal");
    const closeBtn = document.getElementById("itemModalClose");
    const titulo = document.getElementById("itemModalTitle");
    const frame = document.getElementById("itemModalFrame");
    const imagem = document.getElementById("itemModalImagem");
    if (!modal) return;

    let abridor = null;

    // Fundo inerte: o foco e o leitor de tela ficam presos no diálogo (sem focus trap manual)
    const fundoInerte = (inerte) =>
      [...document.body.children].forEach((el) => {
        if (el !== modal) el.inert = inerte;
      });

    const abrirModal = (nivel, fim, id, tipoBruto, origem) => {
      abridor = origem;
      const tipo = tipoDoItem(tipoBruto);
      const ehImagem = tipo !== "pdf";
      const rotulo = `${ehImagem ? "Imagem" : "PDF"} do item — ${rotuloNiveis(nivel, fim)}`;
      titulo.textContent = rotulo;
      frame.hidden = ehImagem;
      imagem.hidden = !ehImagem;
      const alvo = ehImagem ? imagem : frame;
      alvo.src = urlDoItem(id, tipo);
      if (ehImagem) imagem.alt = rotulo;
      else frame.title = rotulo;
      modal.hidden = false;
      fundoInerte(true);
      document.body.style.overflow = "hidden";
      closeBtn.focus();
    };

    const fecharModal = () => {
      modal.hidden = true;
      frame.removeAttribute("src");
      imagem.removeAttribute("src");
      document.body.style.overflow = "";
      fundoInerte(false);
      if (abridor && abridor.isConnected) abridor.focus({ preventScroll: true });
      abridor = null;
    };

    // O item só abre pelo botão; clicar na habilidade não faz nada (o hover já expande o texto).
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".ver-item-btn");
      if (btn) abrirModal(btn.dataset.nivelItem, btn.dataset.nivelFim, btn.dataset.itemId, btn.dataset.itemTipo, btn);
    });

    closeBtn.addEventListener("click", fecharModal);

    modal.addEventListener("click", (e) => {
      if (e.target === modal) fecharModal();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !modal.hidden) fecharModal();
    });
  }

  getDescriptorList() {
    return descriptorKeys(this.data[appState.currentFilter]);
  }

  initDropdown() {
    const toggle = document.getElementById("dropdownToggle");
    const card = document.getElementById("descritoresCard");

    if (toggle) {
      toggle.addEventListener("click", () => {
        this.dropdownOpen = !this.dropdownOpen;
        this.updateDropdownUI();
      });
      // Esc fecha o painel e devolve o foco ao botão
      card?.addEventListener("keydown", (e) => {
        if (e.key !== "Escape" || !this.dropdownOpen) return;
        this.dropdownOpen = false;
        this.updateDropdownUI();
        toggle.focus();
      });
    }

    document.addEventListener("click", (e) => {
      if (!this.dropdownOpen) return;
      if (card && !card.contains(e.target)) {
        this.dropdownOpen = false;
        this.updateDropdownUI();
      }
    });
  }

  updateDropdownUI() {
    const toggle = document.getElementById("dropdownToggle");
    const panel = document.getElementById("tagPanel");
    const chevron = document.getElementById("chevronIcon");
    if (toggle)
      toggle.setAttribute("aria-expanded", String(this.dropdownOpen));
    if (panel) panel.hidden = !this.dropdownOpen;
    if (chevron) chevron.classList.toggle("open", this.dropdownOpen);
  }

  updateDropdownLabel() {
    const label = document.getElementById("dropdownLabel");
    if (label) label.textContent = appState.currentDescriptor || "";
  }

  // Linhas cujo texto estoura (.tem-ver-mais) expandem no hover/foco/toque.
  abrirHabilidade(conteudo) {
    const estavaExpandido = conteudo.classList.contains("expandido");

    // Reabrir durante o fechamento: cancela a finalização pendente
    clearTimeout(conteudo._timerFim);
    if (conteudo._aoTerminar) {
      conteudo.removeEventListener("transitionend", conteudo._aoTerminar);
    }
    conteudo.classList.remove("fechando");

    conteudo.classList.add("expandido");
    conteudo.setAttribute("aria-expanded", "true");
    if (!estavaExpandido) {
      conteudo.style.maxHeight = alturaLinhaColapsada();
      void conteudo.offsetHeight; // força o navegador a registrar a altura inicial
    }
    conteudo.style.maxHeight = `${conteudo.scrollHeight}px`;
  }

  fecharHabilidade(conteudo) {
    if (!conteudo.classList.contains("expandido")) return;

    // Mantém o card sobreposto durante a animação, mas abaixo do que está abrindo
    conteudo.classList.add("fechando");
    conteudo.style.maxHeight = alturaLinhaColapsada();

    const finalizar = () => {
      clearTimeout(conteudo._timerFim);
      conteudo.removeEventListener("transitionend", aoTerminar);
      conteudo.classList.remove("expandido", "fechando");
      conteudo.setAttribute("aria-expanded", "false");
      conteudo.style.maxHeight = "";
    };
    const aoTerminar = (e) => {
      if (e.target === conteudo && e.propertyName === "max-height") finalizar();
    };
    conteudo._aoTerminar = aoTerminar;
    conteudo.addEventListener("transitionend", aoTerminar);
    // Sem diferença de altura não há transitionend
    conteudo._timerFim = setTimeout(finalizar, 450);
  }

  // Hover/foco numa linha destaca o número de início (o da linha, ou o do primeiro nível abaixo
  // se ela divide o nível com a seguinte) e o de fim (o primeiro número acima), cortes inclusive.
  initDestaqueNumeros() {
    const numero = (l) => l.querySelector(".proficiencia-valor-numero");
    const marcar = (linha) => {
      document.querySelectorAll(".proficiencia-valor-numero.destaque").forEach((n) => n.classList.remove("destaque"));
      if (!linha) return;
      const linhas = [...linha.parentElement.querySelectorAll(":scope > .linha")];
      const i = linhas.indexOf(linha);
      const inicio = linhas.slice(i).map(numero).find(Boolean);
      const fim = linhas.slice(0, i).reverse().map(numero).find(Boolean);
      // texto branco quando o preto não contrasta com a cor do padrão (as cores são do projeto)
      const p = linha.style.getPropertyValue("--p");
      const nome = /--color-padrao-\d/.exec(p);
      const hex = nome && getComputedStyle(document.documentElement).getPropertyValue(nome[0]);
      for (const n of [inicio, fim]) {
        if (!n) continue;
        n.style.setProperty("--destaque", p);
        n.style.setProperty("--destaque-texto", corTextoSobre(hex));
        n.classList.add("destaque");
      }
    };
    const linhaDe = (el) => (el && el.closest ? el.closest(".padrao-linhas > .linha") : null);
    document.addEventListener("pointerover", (e) => {
      if (e.pointerType === "mouse") marcar(linhaDe(e.target));
    });
    document.addEventListener("pointerout", (e) => {
      if (e.pointerType === "mouse" && !linhaDe(e.relatedTarget)) marcar(null);
    });
    document.addEventListener("focusin", (e) => {
      if (e.target.matches(":focus-visible")) marcar(linhaDe(e.target));
    });
    document.addEventListener("focusout", (e) => {
      if (!linhaDe(e.relatedTarget)) marcar(null);
    });
  }

  initHabilidadeHover() {
    const DELAY_ABRIR = 120; // intenção: ignora o mouse só "passando" pela linha
    const DELAY_FECHAR = 140; // tolera o mouse saindo e voltando para o card
    const SELETOR = ".linha-conteudo.tem-ver-mais";

    let aberta = null;
    let alvoPendente = null;
    let timerAbrir = null;
    let timerFechar = null;

    const habilidadeDe = (el) => (el && el.closest ? el.closest(SELETOR) : null);

    // Só uma habilidade aberta por vez: ao trocar, uma fecha enquanto a outra abre
    const trocarPara = (conteudo) => {
      clearTimeout(timerAbrir);
      clearTimeout(timerFechar);
      alvoPendente = null;
      if (aberta && !aberta.isConnected) aberta = null;
      if (aberta === conteudo) return;
      if (aberta) this.fecharHabilidade(aberta);
      aberta = conteudo;
      if (conteudo) this.abrirHabilidade(conteudo);
    };

    // O botão "Ver item" fica fora da linha de texto: passar o mouse nele não
    // abre a habilidade, então o item pode ser consultado direto.
    document.addEventListener("pointerover", (e) => {
      if (e.pointerType !== "mouse") return;
      const conteudo = habilidadeDe(e.target);
      if (!conteudo || conteudo === habilidadeDe(e.relatedTarget)) return;

      if (conteudo === aberta) {
        clearTimeout(timerFechar); // voltou para a que já estava aberta
        return;
      }
      clearTimeout(timerAbrir);
      alvoPendente = conteudo;
      timerAbrir = setTimeout(() => trocarPara(conteudo), DELAY_ABRIR);
    });

    document.addEventListener("pointerout", (e) => {
      if (e.pointerType !== "mouse") return;
      const conteudo = habilidadeDe(e.target);
      if (!conteudo || conteudo === habilidadeDe(e.relatedTarget)) return;

      if (conteudo === alvoPendente) {
        clearTimeout(timerAbrir);
        alvoPendente = null;
      }
      if (conteudo === aberta) {
        clearTimeout(timerFechar);
        timerFechar = setTimeout(() => trocarPara(null), DELAY_FECHAR);
      }
    });

    // Toque (sem hover): tocar na habilidade alterna; tocar fora fecha
    document.addEventListener("click", (e) => {
      if (e.pointerType !== "touch" && e.pointerType !== "pen") return;
      if (e.target.closest(".ver-item-btn")) return;
      const conteudo = habilidadeDe(e.target);
      if (conteudo) trocarPara(conteudo === aberta ? null : conteudo);
      else if (aberta) trocarPara(null);
    });

    // Teclado: Enter/Espaço na habilidade alterna a expansão (o item abre pelo botão)
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const conteudo = e.target.closest?.(".linha-conteudo.tem-ver-mais");
      if (!conteudo || e.target !== conteudo) return;
      e.preventDefault();
      trocarPara(conteudo === aberta ? null : conteudo);
    });

    // Teclado: foco na habilidade abre, sair do foco fecha
    document.addEventListener("focusin", (e) => {
      const conteudo = habilidadeDe(e.target);
      if (conteudo && e.target.matches(":focus-visible")) trocarPara(conteudo);
    });
    document.addEventListener("focusout", (e) => {
      const conteudo = habilidadeDe(e.target);
      if (conteudo && conteudo === aberta && !conteudo.contains(e.relatedTarget)) {
        trocarPara(null);
      }
    });
  }

  // O texto ocupa toda a largura da coluna; só se estourar (aparecem os "...")
  // a habilidade passa a ser expansível
  atualizarTruncamentos() {
    document.querySelectorAll(".linha-conteudo.tem-texto").forEach((c) => {
      if (c.classList.contains("expandido")) return;
      const p = c.querySelector("p");
      const trunca = p.scrollWidth > p.clientWidth + 1;
      c.classList.toggle("tem-ver-mais", trunca);
      if (trunca) {
        c.setAttribute("tabindex", "0");
        c.setAttribute("role", "button");
        c.setAttribute("aria-expanded", "false");
      } else {
        for (const a of ["tabindex", "role", "aria-expanded"]) c.removeAttribute(a);
      }
    });
  }

  renderButtons() {
    const filterData = this.data[appState.currentFilter] || {};
    const descriptors = this.getDescriptorList();

    // Grid principal
    const grid = document.querySelector(".descritores-grid");
    if (grid) {
      grid.innerHTML = descriptors
        .map(
          (d) =>
            `<button class="descritor-btn${d === appState.currentDescriptor ? " active" : ""}"${d === appState.currentDescriptor ? ' aria-current="true"' : ""} data-descritor="${escapeHtml(d)}">${escapeHtml(d)}</button>`,
        )
        .join("");
      grid.querySelectorAll(".descritor-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => this.handleDescriptorClick(e));
      });
    }

    // Menu lateral
    const lateralGrid = document.querySelector(".menu-lateral-grid");
    if (lateralGrid) {
      lateralGrid.innerHTML = descriptors
        .map(
          (d) =>
            `<button class="descritor-btn-lateral${d === appState.currentDescriptor ? " active" : ""}" data-descritor="${escapeHtml(d)}">${escapeHtml(d)}</button>`,
        )
        .join("");
      lateralGrid.querySelectorAll(".descritor-btn-lateral").forEach((btn) => {
        btn.addEventListener("click", (e) => this.handleDescriptorClick(e));
      });
    }

    // Selecionar o primeiro descritor automaticamente ao iniciar ou trocar filtro
    if (
      !appState.currentDescriptor ||
      !filterData[appState.currentDescriptor]
    ) {
      const first = descriptors[0];
      if (first) {
        appState.currentDescriptor = first;
        this.updateActiveDescriptor(first);
        this.updateContent(first);
      }
    }
  }

  handleDescriptorClick(event) {
    const button = event.currentTarget;
    const descriptor = button.getAttribute("data-descritor");

    if (descriptor !== appState.currentDescriptor) {
      appState.currentDescriptor = descriptor;
      this.updateActiveDescriptor(descriptor);
      this.updateContent(descriptor);
      this.scrollToContent();
    }

    // Escolha no painel: fecha e devolve o foco ao botão do seletor
    if (this.dropdownOpen && button.closest("#tagPanel")) document.getElementById("dropdownToggle")?.focus();
    this.dropdownOpen = false;
    this.updateDropdownUI();
  }

  updateActiveDescriptor(descriptor) {
    document
      .querySelectorAll(".descritor-btn, .descritor-btn-lateral")
      .forEach((btn) => {
        const ativo = btn.getAttribute("data-descritor") === descriptor;
        btn.classList.toggle("active", ativo);
        if (ativo) btn.setAttribute("aria-current", "true");
        else btn.removeAttribute("aria-current");
      });
    this.updateDropdownLabel();
  }

  updateContent(descriptor) {
    const filterData = this.data[appState.currentFilter];
    if (!filterData || !filterData[descriptor]) {
      console.warn(
        `Dados não encontrados para ${appState.currentFilter} - ${descriptor}`,
      );
      return;
    }

    const data = filterData[descriptor];

    const topicTitle = document.querySelector(".titulo-topico h3");
    if (topicTitle)
      topicTitle.textContent = rotuloAnoLongo(appState.currentFilter);

    const descriptorBadge = document.querySelector(
      ".descritor-detalhado .descritor-badge",
    );
    if (descriptorBadge) descriptorBadge.textContent = descriptor;

    const descriptorDetail = document.querySelector(".descritor-detalhado p");
    if (descriptorDetail) descriptorDetail.textContent = data.description;
    const anuncio = document.getElementById("anuncio");
    if (anuncio) anuncio.textContent = `${descriptor}: ${data.description ?? ""}`;

    if (data.prerequisites) this.updatePrerequisites(data.prerequisites);
    if (appState.etapasInvalidas.has(appState.currentFilter)) {
      const escala = document.querySelector(".escala-content");
      if (escala) escala.innerHTML = "";
    } else if (data.scale && filterData.scaleRange)
      this.updateScale(data.scale, filterData.cortes, filterData.scaleRange, filterData.padroes);
    if (data.bncc) this.updateBNCC(data.bncc);
    if (filterData.scaleRange) this.updateScaleRange(filterData.scaleRange);

    this.animateContentChange();
  }

  updateScaleRange({ min, max }) {
    const top = document.querySelector(".escala-label-top");
    const bottom = document.querySelector(".escala-label-bottom");
    const comRotulo = (el, rotulo, v) => {
      el.innerHTML = `<span class="rv-sr-only">${rotulo}: </span>${escapeHtml(v)}`;
    };
    if (top) comRotulo(top, "Máximo da escala", max);
    if (bottom) comRotulo(bottom, "Mínimo da escala", min);
  }

  updatePrerequisites(prerequisites) {
    const ul = document.querySelector(".prerequisitos-content ul");
    if (!ul) return;
    ul.innerHTML = prerequisites.map((p) => `<li>${escapeHtml(p)}</li>`).join("");
  }

  updateScale(scale, cortes, { min, max }, padroes) {
    const escalaContent = document.querySelector(".escala-content");
    if (!escalaContent) return;

    // Rótulos vêm do JSON ("padroes": [{chave, rotulo}]); "{{pdNN}}" = pdNN vazio no projeto (destaque D-116)
    const labels = Object.fromEntries((padroes || []).map(({ chave, rotulo }) => [chave, rotulo]));

    // Início de cada padrão (o fim é o início do de cima): combina com a leitura "nota ≥ nível"
    const intervalos = Object.fromEntries(
      padroesDeCima(cortes).map((p) => {
        const k = Number(p.slice(7));
        return [p, `≥ ${k === 1 ? min : cortes[`padrao-${k - 1}`]}`];
      }),
    );

    const regua = montarFaixasRegua({ min, max, cortes, escala: scale });
    const emLinhas = (y) => `calc(var(--escala-linha-height) * ${y})`;

    // --p: cor do padrão da linha (tinge a linha e os números de início/fim no hover)
    const faixaHTML = ({ base, topo, rotuloBase, ehCorte, conteudo, item, mesmoNivel, padrao, cortesDentro }) => {
      const tick =
        rotuloBase === null
          ? ""
          : `<span class="proficiencia-valor-numero${ehCorte ? " eh-corte" : ""}">${escapeHtml(rotuloBase)}</span>`;
      const texto = conteudo === "---" || conteudo === null ? "" : conteudo;
      const temItem = Boolean(item && item.id);

      // O "..." vem do CSS; atualizarTruncamentos marca as linhas que estouram
      return `
                <div class="linha${ehVazia(conteudo) ? " preenchimento" : ""}${mesmoNivel ? " mesmo-nivel" : ""}${cortesDentro ? " tem-corte" : ""}" style="--p:var(--color-${padrao})${cortesDentro ? `;--cortes:${cortesDentro}` : ""}">
                    <div class="linha-cor"></div>
                    <div class="linha-marcador"></div>
                    <span class="proficiencia-valor" aria-hidden="true">${tick}</span>
                    <div class="linha-conteudo${texto ? " tem-texto" : ""}${temItem ? " tem-ver-item" : ""}">
                        <p>${texto ? `<span class="rv-sr-only">${escapeHtml(`${labels[padrao] ?? ""}, ${rotuloNiveis(base, topo)}: `)}</span>` : ""}${escapeHtml(texto)}</p>
                    </div>
                    ${
                      temItem
                        ? `<button type="button" class="ver-item-btn" aria-label="Ver item, ${escapeHtml(rotuloNiveis(base, topo))}" data-legenda="Ver item" data-nivel-item="${escapeHtml(base)}" data-nivel-fim="${escapeHtml(topo)}" data-item-id="${escapeHtml(item.id)}" data-item-tipo="${escapeHtml(item.tipo || "pdf")}">
                            <svg viewBox="4 0 44.3506 44.3506" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                <rect x="16.6117" y="12.2362" width="19.1273" height="19.8787" rx="2.36459" stroke="black" stroke-width="0.910823"/>
                                <path d="M19.8918 15.424V17.997H32.4548V15.424H19.8918ZM33.4599 17.997C33.4598 18.5 33.0099 18.9079 32.4548 18.9079H19.8918C19.3367 18.9079 18.8868 18.5 18.8867 17.997V15.424C18.8867 14.921 19.3367 14.5132 19.8918 14.5132H32.4548C33.0099 14.5132 33.4599 14.921 33.4599 15.424V17.997Z" fill="black"/>
                                <path d="M32.9574 21.6406C33.2349 21.6406 33.4599 21.8445 33.4599 22.096C33.4599 22.3476 33.2349 22.5514 32.9574 22.5514H19.3892C19.1117 22.5514 18.8867 22.3476 18.8867 22.096C18.8867 21.8445 19.1117 21.6406 19.3892 21.6406H32.9574Z" fill="black"/>
                                <path d="M27.5315 25.2837C27.783 25.2837 27.9869 25.4876 27.9869 25.7391C27.9869 25.9906 27.783 26.1945 27.5315 26.1945H19.3421C19.0906 26.1945 18.8867 25.9906 18.8867 25.7391C18.8867 25.4876 19.0906 25.2837 19.3421 25.2837H27.5315Z" fill="black"/>
                                <path d="M27.5315 27.1055C27.783 27.1055 27.9869 27.3094 27.9869 27.5609C27.9869 27.8124 27.783 28.0163 27.5315 28.0163H19.3421C19.0906 28.0163 18.8867 27.8124 18.8867 27.5609C18.8867 27.3094 19.0906 27.1055 19.3421 27.1055H27.5315Z" fill="black"/>
                                <path d="M27.5315 28.9268C27.783 28.9268 27.9869 29.1307 27.9869 29.3822C27.9869 29.6337 27.783 29.8376 27.5315 29.8376H19.3421C19.0906 29.8376 18.8867 29.6337 18.8867 29.3822C18.8867 29.1307 19.0906 28.9268 19.3421 28.9268H27.5315Z" fill="black"/>
                            </svg>
                        </button>`
                        : ""
                    }
                </div>`;
    };

    // Linhas só pelos níveis; rótulos, barra de cor e cortes ficam por cima, posicionados por y.
    const faixaDoPadrao = (classe) => ({ padrao, y0, y1 }) =>
      `<div class="${classe} ${padrao}" aria-hidden="true" style="top:${emLinhas(y0)};height:${emLinhas(y1 - y0)}" data-y="${y0},${y1 - y0}">${
        classe === "padrao-label" ? `<span${/^\{\{pd\d\d\}\}$/.test(labels[padrao] ?? "") ? ' class="variavel-vazia"' : ""}>${escapeHtml(labels[padrao] ?? "")}</span><small>${escapeHtml(intervalos[padrao])}</small>` : ""
      }</div>`;
    escalaContent.innerHTML = `
                <div class="escala-rotulos" aria-hidden="true">${regua.padroes.map(faixaDoPadrao("padrao-label")).join("")}</div>
                <div class="padrao-linhas">
                    ${regua.faixas.map(faixaHTML).join("")}
                    ${regua.padroes.map(faixaDoPadrao("escala-barra")).join("")}
                    ${regua.cortes
                      .filter((c) => !c.exato)
                      .map(
                        (c) => `<div class="escala-corte" aria-hidden="true" style="top:${emLinhas(c.y)}" data-y="${c.y}"><span class="proficiencia-valor-numero eh-corte">${escapeHtml(c.valor)}</span></div>`,
                      )
                      .join("")}
                </div>`;

    this.atualizarTruncamentos();
    this.seguirLinhas();
  }

  // A linha aberta cresce: barras, rótulos e cortes (posicionados em "alturas de linha", data-y)
  // passam a seguir a altura real das linhas. O ResizeObserver dispara a cada quadro da transição.
  seguirLinhas() {
    const linhas = document.querySelector(".padrao-linhas");
    if (!linhas) return;
    this.observadorLinhas ??= new ResizeObserver(() => this.reposicionarCamadas());
    this.observadorLinhas.disconnect();
    this.observadorLinhas.observe(linhas);
    this.reposicionarCamadas();
  }

  reposicionarCamadas() {
    let y = 0;
    const trechos = [...document.querySelectorAll(".padrao-linhas > .linha")].map((l) => {
      const h = l.classList.contains("preenchimento") ? 0.5 : 1;
      return { l, y0: (y += h) - h, h };
    });
    if (!trechos.length) return;
    const px = (v) => {
      const t = trechos.find((t) => v < t.y0 + t.h - 1e-9) || trechos[trechos.length - 1];
      return t.l.offsetTop + ((v - t.y0) / t.h) * t.l.offsetHeight;
    };
    document.querySelectorAll(".escala-barra, .padrao-label, .escala-corte").forEach((el) => {
      const [a, h] = el.dataset.y.split(",").map(Number);
      el.style.top = `${px(a)}px`;
      if (h !== undefined) el.style.height = `${px(a + h) - px(a)}px`;
    });
  }

  updateBNCC(bncc) {
    const bnccSection = document.querySelector(".bncc-section");
    if (!bnccSection) return;

    const rows = bnccSection.querySelectorAll(".bncc-row");

    if (rows[0]) {
      const value = rows[0].querySelector(".bncc-value");
      if (value) value.textContent = bncc.practices;
    }
    if (rows[1]) {
      const value = rows[1].querySelector(".bncc-value");
      if (value) value.textContent = bncc.knowledge;
    }
    if (rows[2] && bncc.skills) {
      const value = rows[2].querySelector(".bncc-value");
      if (value)
        value.innerHTML = bncc.skills.map((s) => `<p>${escapeHtml(s)}</p>`).join("");
    }
  }

  animateContentChange() {
    if (reduzMovimento()) return;
    const selectors = [
      ".titulo-topico",
      ".descritor-detalhado",
      ".prerequisitos-box",
      ".bncc-section",
    ];
    selectors.forEach((selector, index) => {
      const el = document.querySelector(selector);
      if (!el) return;
      el.style.opacity = "0";
      el.style.transform = "translateX(-20px)";
      setTimeout(() => {
        el.style.transition = "opacity 0.4s ease, transform 0.4s ease";
        el.style.opacity = "1";
        el.style.transform = "translateX(0)";
      }, index * 100);
    });
  }

  scrollToContent() {
    if (appState.scrolling) return;
    appState.scrolling = true;
    const contentWrapper = document.querySelector(".content-wrapper");
    if (contentWrapper) {
      contentWrapper.scrollIntoView({ behavior: comportamento(), block: "nearest" });
    }
    setTimeout(() => {
      appState.scrolling = false;
    }, 1000);
  }
}

// ==========================================
// NAVEGAÇÃO ENTRE DESCRITORES
// ==========================================

class NavigationManager {
  constructor(data) {
    this.data = data;
    this.prevBtn = document.querySelector(".prev-btn");
    this.nextBtn = document.querySelector(".next-btn");
    this.init();
  }

  init() {
    if (this.prevBtn)
      this.prevBtn.addEventListener("click", () => this.navigate(-1));
    if (this.nextBtn)
      this.nextBtn.addEventListener("click", () => this.navigate(1));
    document.addEventListener("keydown", (e) => {
      // Página única (S08): no F2 as setas são do tour; com modal aberto, de ninguém.
      if (e.target.closest?.("#f2") || document.querySelector("dialog[open]") || !document.getElementById("itemModal")?.hidden)
        return;
      if (e.ctrlKey && e.key === "ArrowLeft") this.navigate(-1);
      if (e.ctrlKey && e.key === "ArrowRight") this.navigate(1);
    });
  }

  navigate(direction) {
    const filterData = this.data[appState.currentFilter] || {};
    const descriptors = descriptorKeys(filterData);
    const currentIndex = descriptors.indexOf(appState.currentDescriptor);
    const newIndex = currentIndex + direction;

    if (newIndex >= 0 && newIndex < descriptors.length) {
      const btn = document.querySelector(
        `.descritor-btn[data-descritor="${descriptors[newIndex]}"]`,
      );
      if (btn) btn.click();
    }
  }
}

// ==========================================
// MENU LATERAL STICKY
// ==========================================

class StickyMenuManager {
  constructor() {
    this.menu = document.querySelector(".menu-lateral");
    if (!this.menu) return;
    this.menu.style.scrollBehavior = comportamento();
    window.addEventListener("scroll", () => this.updateMenuPosition());
  }

  updateMenuPosition() {
    const activeButton = this.menu.querySelector(
      ".descritor-btn-lateral.active",
    );
    if (activeButton && !this.isInViewport(activeButton)) {
      activeButton.scrollIntoView({ block: "center", behavior: comportamento() });
    }
  }

  isInViewport(element) {
    const rect = element.getBoundingClientRect();
    const menuRect = this.menu.getBoundingClientRect();
    return rect.top >= menuRect.top && rect.bottom <= menuRect.bottom;
  }
}

// ==========================================
// INICIALIZAÇÃO DO APLICATIVO
// ==========================================

class App {
  constructor() {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => this.bootstrap());
    } else {
      this.bootstrap();
    }
  }

  bootstrap() {
    const data = JSON.parse(document.getElementById("dados-revista").textContent);
    for (const [etapa, dados] of Object.entries(data)) {
      const motivo = problemaDaEtapa(dados);
      if (!motivo) continue;
      appState.etapasInvalidas.add(etapa);
      console.error(`Etapa ${etapa}: JSON da revista inválido: ${motivo}`);
    }
    // Primeira aba (já na ordem das etapas, vinda do template) com dados.
    const primeira = [...document.querySelectorAll(".filtro-btn")].find(
      (btn) => data[btn.dataset.filter],
    );
    appState.currentFilter = primeira?.dataset.filter ?? null;

    new DescriptorManager(data);
    new NavigationManager(data);
    new FilterManager(data);
    new StickyMenuManager();

    document.body.classList.add("app-initialized");
  }
}

if (typeof document !== "undefined") new App();
