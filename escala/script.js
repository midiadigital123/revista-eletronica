/**
 * ==========================================
 * REVISTA ELETRÔNICA - SISTEMA DE DESCRITORES
 * Sistema interativo para análise de resultados
 * ==========================================
 */

// ==========================================
// CONFIGURAÇÃO
// ==========================================

const API_URL =
  "https://recursos-moodle.caeddigital.net/projetos/revista-digital/2026-1/Escala/data/data.json"; // <- Substituir pela URL real do JSON

// ==========================================
// ESTADO DA APLICAÇÃO
// ==========================================

const appState = {
  currentFilter: "5ef",
  currentDescriptor: null,
  scrolling: false,
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
    this.init();
  }

  init() {
    this.renderButtons();

    window.addEventListener("filterChanged", () => {
      appState.currentDescriptor = null;
      this.renderButtons();
    });
  }

  renderButtons() {
    const filterData = this.data[appState.currentFilter] || {};
    const descriptors = Object.keys(filterData).filter((k) => k !== "scaleRange").sort();

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

    if (descriptor === appState.currentDescriptor) return;

    appState.currentDescriptor = descriptor;
    this.updateActiveDescriptor(descriptor);
    this.updateContent(descriptor);
    this.scrollToContent();
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
    if (topicTitle) topicTitle.textContent = data.topic;

    const descriptorDetail = document.querySelector(".descritor-detalhado p");
    if (descriptorDetail) {
      descriptorDetail.innerHTML = `<strong>${descriptor} - </strong>${data.description}`;
    }

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

    const padroes = ["padrao-4", "padrao-3", "padrao-2", "padrao-1"];
    const labels = {
      "padrao-4": "Padrão 04",
      "padrao-3": "Padrão 03",
      "padrao-2": "Padrão 02",
      "padrao-1": "Padrão 01",
    };

    escalaContent.innerHTML = padroes
      .map((padrao) => {
        const linhas = scale[padrao] || [];

        const linhasHTML = linhas
          .map(
            ({ level, content }) => `
                <div class="linha">
                    <span class="proficiencia-valor">${level}</span>
                    <div class="linha-marcador"></div>
                    <div class="linha-cor cor-${padrao}"></div>
                    <div class="linha-conteudo"><p>${content}</p></div>
                </div>`,
          )
          .join("");

        const linhaVazia =
          padrao === "padrao-1"
            ? `
                <div class="linha linha-vazia">
                    <span class="proficiencia-valor"></span>
                    <div class="linha-marcador-vazio"></div>
                    <div class="linha-cor cor-padrao-1"></div>
                    <div class="linha-conteudo-vazio"></div>
                </div>`
            : "";

        return `
                <div class="padrao ${padrao}">
                    <div class="padrao-label"><span>${labels[padrao]}</span></div>
                    <div class="padrao-linhas">${linhasHTML}${linhaVazia}</div>
                </div>`;
      })
      .join("");
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
    const descriptors = Object.keys(filterData).filter((k) => k !== "scaleRange").sort();
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
