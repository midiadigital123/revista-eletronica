/**
 * ==========================================
 * REVISTA ELETRÔNICA - SISTEMA DE DESCRITORES
 * Sistema interativo para análise de resultados
 * ==========================================
 */

// ==========================================
// CONFIGURAÇÃO
// ==========================================

const API_URL = "./descritores.json"; // <- Substituir pela URL real do JSON

// ==========================================
// ESTADO DA APLICAÇÃO
// ==========================================

const appState = {
  currentFilter: "5ef",
  currentDescriptor: null,
  scrolling: false,
};

const FILTER_LABELS = {
  "5ef": { short: "5º EF", long: "5º Ano do Ensino Fundamental" },
  "9ef": { short: "9º EF", long: "9º Ano do Ensino Fundamental" },
  "3em": { short: "3ª EM", long: "3ª Série do Ensino Médio" },
};

// ==========================================
// SERVIÇO DE DADOS
// ==========================================

class DataService {
  constructor(url) {
    this.url = url;
  }

  async load() {
    const response = await fetch(this.url);
    if (!response.ok)
      throw new Error(`Erro ao carregar dados: ${response.status}`);
    return await response.json();
  }
}

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
      btn.setAttribute("aria-selected", String(isActive));
      btn.textContent = isActive
        ? FILTER_LABELS[filter].long
        : FILTER_LABELS[filter].short;
    });
  }

  animateFilterChange() {
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
    this.initVerMais();
    this.initDropdown();
    this.initModal();

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
    const corpo = document.getElementById("itemModalBody");
    if (!modal) return;

    const abrirModal = (nivel, conteudo) => {
      titulo.textContent = `Item — nível ${nivel}`;
      corpo.textContent = conteudo;
      modal.hidden = false;
      document.body.style.overflow = "hidden";
    };

    const fecharModal = () => {
      modal.hidden = true;
      document.body.style.overflow = "";
    };

    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".ver-item-btn");
      if (!btn) return;
      abrirModal(btn.dataset.nivelItem, btn.dataset.conteudoItem);
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
    const filterData = this.data[appState.currentFilter] || {};
    return Object.keys(filterData)
      .filter((k) => k !== "scaleRange")
      .sort();
  }

  initDropdown() {
    const toggle = document.getElementById("dropdownToggle");
    const card = document.getElementById("descritoresCard");

    if (toggle) {
      toggle.addEventListener("click", () => {
        this.dropdownOpen = !this.dropdownOpen;
        this.updateDropdownUI();
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

  initVerMais() {
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".ver-mais-btn");
      if (!btn) return;

      const conteudo = btn.closest(".linha-conteudo");
      const paragrafo = conteudo.querySelector("p");
      const textoBtn = btn.querySelector(".btn-texto");
      const iconeBtn = btn.querySelector(".btn-icone");
      const vaiExpandir = !conteudo.classList.contains("expandido");
      const alturaColapsada = getComputedStyle(document.documentElement)
        .getPropertyValue("--escala-linha-height")
        .trim();

      if (vaiExpandir) {
        paragrafo.textContent = conteudo.dataset.textoCompleto;
        conteudo.classList.add("expandido");
        if (window.innerWidth <= 500) {
          // No mobile o card ocupa a largura total da tela
          const linhaRect = conteudo.closest(".linha").getBoundingClientRect();
          conteudo.style.left = `${-linhaRect.left}px`;
          conteudo.style.right = `${linhaRect.right - document.documentElement.clientWidth}px`;
        }
        conteudo.style.maxHeight = alturaColapsada;
        void conteudo.offsetHeight; // força o navegador a registrar a altura inicial
        conteudo.style.maxHeight = `${conteudo.scrollHeight}px`;
        textoBtn.textContent = "Ver menos";
        iconeBtn.classList.add("aberto");
      } else {
        conteudo.style.maxHeight = `${conteudo.scrollHeight}px`;
        void conteudo.offsetHeight;
        conteudo.style.maxHeight = alturaColapsada;
        textoBtn.textContent = "Ver mais";
        iconeBtn.classList.remove("aberto");
        conteudo.addEventListener(
          "transitionend",
          () => {
            conteudo.classList.remove("expandido");
            conteudo.style.maxHeight = "";
            conteudo.style.left = "";
            conteudo.style.right = "";
            paragrafo.textContent = conteudo.dataset.textoTruncado;
          },
          { once: true },
        );
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
            `<button class="descritor-btn${d === appState.currentDescriptor ? " active" : ""}" data-descritor="${d}">${d}</button>`,
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
            `<button class="descritor-btn-lateral${d === appState.currentDescriptor ? " active" : ""}" data-descritor="${d}">${d}</button>`,
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

    this.dropdownOpen = false;
    this.updateDropdownUI();
  }

  updateActiveDescriptor(descriptor) {
    document
      .querySelectorAll(".descritor-btn, .descritor-btn-lateral")
      .forEach((btn) => {
        btn.classList.toggle(
          "active",
          btn.getAttribute("data-descritor") === descriptor,
        );
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
      topicTitle.textContent = FILTER_LABELS[appState.currentFilter].long;

    const descriptorBadge = document.querySelector(
      ".descritor-detalhado .descritor-badge",
    );
    if (descriptorBadge) descriptorBadge.textContent = descriptor;

    const descriptorDetail = document.querySelector(".descritor-detalhado p");
    if (descriptorDetail) descriptorDetail.textContent = data.description;

    if (data.prerequisites) this.updatePrerequisites(data.prerequisites);
    if (data.scale) this.updateScale(data.scale);
    if (data.bncc) this.updateBNCC(data.bncc);
    if (filterData.scaleRange) this.updateScaleRange(filterData.scaleRange);

    this.animateContentChange();
  }

  updateScaleRange({ min, max }) {
    const top = document.querySelector(".escala-label-top");
    const bottom = document.querySelector(".escala-label-bottom");
    if (top) top.textContent = max;
    if (bottom) bottom.textContent = min;
  }

  updatePrerequisites(prerequisites) {
    const ul = document.querySelector(".prerequisitos-content ul");
    if (!ul) return;
    ul.innerHTML = prerequisites.map((p) => `<li>${p}</li>`).join("");
  }

  updateScale(scale) {
    const escalaContent = document.querySelector(".escala-content");
    if (!escalaContent) return;

    const LIMITE_CARACTERES = window.innerWidth <= 500 ? 40 : 56;
    const textosCompletos = [];
    const itensCompletos = [];

    const padroes = ["padrao-4", "padrao-3", "padrao-2", "padrao-1"];
    const labels = {
      "padrao-4": "Padrão 04",
      "padrao-3": "Padrão 03",
      "padrao-2": "Padrão 02",
      "padrao-1": "Padrão 01",
    };
    // Corte que marca o início de cada padrão (o topo do padrão 04 já é o "500")
    const cortes = {
      "padrao-3": 375,
      "padrao-2": 250,
      "padrao-1": 125,
    };

    escalaContent.innerHTML = padroes
      .map((padrao, indicePadrao) => {
        const linhas = scale[padrao] || [];
        const proximoPadrao = padroes[indicePadrao + 1];
        const ocultarUltimoValor = Boolean(cortes[proximoPadrao]);

        const linhasHTML = linhas
          .map(({ level, content }, indiceLinha) => {
            const excedeLimite = content.length > LIMITE_CARACTERES;
            const textoExibido = excedeLimite
              ? `${content.slice(0, LIMITE_CARACTERES).trimEnd()}...`
              : content;

            if (excedeLimite) textosCompletos.push(content);

            const temItem = content !== "---";
            if (temItem) itensCompletos.push({ level, content });

            const ocultarValor =
              ocultarUltimoValor && indiceLinha === linhas.length - 1;

            return `
                <div class="linha">
                    <div class="linha-cor cor-${padrao}"></div>
                    <div class="linha-marcador"></div>
                    <span class="proficiencia-valor">${ocultarValor ? "" : `<span class="proficiencia-valor-numero">${level}</span>`}</span>
                    <div class="linha-conteudo${excedeLimite ? " tem-ver-mais" : ""}${temItem ? " tem-ver-item" : ""}">
                        <p>${textoExibido}</p>
                        ${
                          temItem || excedeLimite
                            ? `<div class="linha-acoes">
                                ${
                                  temItem
                                    ? `<button type="button" class="ver-item-btn">
                                        <svg class="btn-icone" width="12" height="12" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                            <path d="M1 7C1 7 3.5 2.5 7 2.5C10.5 2.5 13 7 13 7C13 7 10.5 11.5 7 11.5C3.5 11.5 1 7 1 7Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                                            <circle cx="7" cy="7" r="1.8" stroke="currentColor" stroke-width="1.3"/>
                                        </svg>
                                        <span class="btn-texto">Ver item</span>
                                    </button>`
                                    : ""
                                }
                                ${
                                  excedeLimite
                                    ? `<button type="button" class="ver-mais-btn">
                                        <svg class="btn-icone" width="12" height="12" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                            <path d="M3.5 5.25L7 8.75L10.5 5.25" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                        <span class="btn-texto">Ver mais</span>
                                    </button>`
                                    : ""
                                }
                            </div>`
                            : ""
                        }
                    </div>
                </div>`;
          })
          .join("");

        const linhaVazia =
          padrao === "padrao-1"
            ? `
                <div class="linha linha-vazia">
                    <div class="linha-cor cor-padrao-1"></div>
                    <div class="linha-marcador-vazio"></div>
                    <span class="proficiencia-valor"></span>
                    <div class="linha-conteudo-vazio"></div>
                </div>`
            : "";

        const corteHTML = cortes[padrao]
          ? `<span class="padrao-corte">${cortes[padrao]}</span>`
          : "";

        return `
                <div class="padrao ${padrao}">
                    <div class="padrao-label"><span>${labels[padrao]}</span></div>
                    <div class="padrao-linhas">${corteHTML}${linhasHTML}${linhaVazia}</div>
                </div>`;
      })
      .join("");

    escalaContent.querySelectorAll(".ver-mais-btn").forEach((btn, i) => {
      const conteudo = btn.closest(".linha-conteudo");
      const paragrafo = conteudo.querySelector("p");
      conteudo.dataset.textoCompleto = textosCompletos[i];
      conteudo.dataset.textoTruncado = paragrafo.textContent;
    });

    escalaContent.querySelectorAll(".ver-item-btn").forEach((btn, i) => {
      const { level, content } = itensCompletos[i];
      btn.dataset.nivelItem = level;
      btn.dataset.conteudoItem = content;
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
        value.innerHTML = bncc.skills.map((s) => `<p>${s}</p>`).join("");
    }
  }

  animateContentChange() {
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
      contentWrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
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
  }

  navigate(direction) {
    const filterData = this.data[appState.currentFilter] || {};
    const descriptors = Object.keys(filterData)
      .filter((k) => k !== "scaleRange")
      .sort();
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
    this.menu.style.scrollBehavior = "smooth";
    window.addEventListener("scroll", () => this.updateMenuPosition());
  }

  updateMenuPosition() {
    const activeButton = this.menu.querySelector(
      ".descritor-btn-lateral.active",
    );
    if (activeButton && !this.isInViewport(activeButton)) {
      activeButton.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }

  isInViewport(element) {
    const rect = element.getBoundingClientRect();
    const menuRect = this.menu.getBoundingClientRect();
    return rect.top >= menuRect.top && rect.bottom <= menuRect.bottom;
  }
}

// ==========================================
// ACESSIBILIDADE
// ==========================================

class AccessibilityManager {
  constructor(navigationManager) {
    this.navigationManager = navigationManager;
    this.init();
  }

  init() {
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.key === "ArrowLeft")
        this.navigationManager.navigate(-1);
      if (e.ctrlKey && e.key === "ArrowRight")
        this.navigationManager.navigate(1);
    });

    document.querySelectorAll(".filtro-btn").forEach((btn) => {
      btn.setAttribute("role", "button");
      btn.setAttribute("aria-pressed", btn.classList.contains("active"));
    });
  }
}

// ==========================================
// PERFORMANCE
// ==========================================

class PerformanceManager {
  constructor() {
    const images = document.querySelectorAll("img[data-src]");
    if (!images.length) return;

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute("data-src");
          obs.unobserve(img);
        }
      });
    });

    images.forEach((img) => observer.observe(img));
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

  async bootstrap() {
    console.log("🚀 Inicializando aplicação...");

    try {
      const data = await new DataService(API_URL).load();

      const descriptorManager = new DescriptorManager(data);
      const navigationManager = new NavigationManager(data);
      new FilterManager(data);
      new StickyMenuManager();
      new AccessibilityManager(navigationManager);
      new PerformanceManager();

      document.body.classList.add("app-initialized");
      console.log("✅ Aplicação inicializada com sucesso!");
    } catch (error) {
      console.error("❌ Erro ao inicializar aplicação:", error);
    }
  }
}

const app = new App();
