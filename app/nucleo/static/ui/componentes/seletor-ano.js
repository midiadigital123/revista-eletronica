// U6: seletor de ano do cabeçalho (_componentes/anos.html). Arquivo próprio, com o próprio
// alpine:init, carregado antes do Alpine (base.html). Abrir e fechar (Enter/Espaço, Esc, clique
// fora) é do popover nativo; aqui só a posição sob o botão e o foco.
document.addEventListener("alpine:init", () => {
  "use strict";

  Alpine.data("seletorAno", () => ({
    alternou(e) {
      const { botao, painel } = this.$refs;
      if (e.newState === "open") {
        // Filtro por HTMX (hx-push-url) muda a query sem renderizar o cabeçalho: o link leva a atual.
        if ("mesmaRota" in painel.dataset) for (const a of painel.querySelectorAll("a[data-ano]")) a.search = location.search;
        // ponytail: posição por JS; trocar por CSS anchor positioning quando todos os navegadores tiverem.
        const r = botao.getBoundingClientRect();
        painel.style.top = `${r.bottom + 4}px`;
        painel.style.left = `${Math.min(r.left, window.innerWidth - painel.offsetWidth - 8)}px`;
        (painel.querySelector('[aria-current="page"]') || painel.querySelector("a"))?.focus();
      } else if (!document.activeElement || document.activeElement === document.body || painel.contains(document.activeElement)) {
        botao.focus();
      }
    },
  }));
});
