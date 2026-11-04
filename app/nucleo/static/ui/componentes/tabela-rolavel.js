// U10a: tabela rolável. <div class="tabela-rolavel" x-data="tabelaRolavel"><table class="tabela">: liga
// data-rolou-esq (há coluna escondida à esquerda) e data-rolou-dir (há à direita); o ui.css desenha a
// sombra da borda daquele lado. Sem rolagem lateral, nenhum dos dois. Mede no scroll e quando a caixa ou a
// tabela mudam de tamanho (janela, linha nova, troca do HTMX). Carregado antes do Alpine (base.html).
document.addEventListener("alpine:init", () => {
  "use strict";

  Alpine.data("tabelaRolavel", () => ({
    observador: null, // build CSP: declarado aqui, senão o this.observador iria para o componente de fora

    init() {
      const caixa = this.$el;
      const medir = () => {
        const x = Math.abs(caixa.scrollLeft); // abs: em rtl o scrollLeft é negativo
        caixa.toggleAttribute("data-rolou-esq", x >= 1);
        caixa.toggleAttribute("data-rolou-dir", caixa.scrollWidth - caixa.clientWidth - x >= 1);
      };
      caixa.addEventListener("scroll", medir, { passive: true });
      this.observador = new ResizeObserver(medir);
      this.observador.observe(caixa);
      if (caixa.firstElementChild) this.observador.observe(caixa.firstElementChild);
      medir();
    },

    destroy() {
      this.observador?.disconnect();
    },
  }));
});
