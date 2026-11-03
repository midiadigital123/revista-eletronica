// Componentes Alpine das telas B (D-195). Build CSP: cada x-data aponta para um nome
// registrado aqui com Alpine.data, e as expressões no HTML são só propriedade ou método.
// Carregado antes do Alpine (base.html), por isso registra no alpine:init.
// Referência: docs/telas/design-system.md.
document.addEventListener("alpine:init", () => {
  "use strict";

  // U2: <dialog x-data="impacto" data-form data-campo data-abrir-ao-carregar> (_componentes/impacto.html).
  // O servidor recusou o envio sem confirmação: o modal abre sozinho. Confirmar marca o campo e
  // reenvia o form (HTMX ou não); Cancelar/Esc volta os campos com data-original e o foco.
  Alpine.data("impacto", () => ({
    init() {
      if (this.$root.hasAttribute("data-abrir-ao-carregar") && !this.$root.open) this.$root.showModal();
    },
    form() {
      return document.getElementById(this.$root.dataset.form);
    },
    confirmar() {
      const form = this.form();
      const nome = this.$root.dataset.campo;
      let campo = form.elements.namedItem(nome);
      if (!campo) {
        campo = Object.assign(document.createElement("input"), { type: "hidden", name: nome });
        form.append(campo);
      }
      campo.value = "on";
      this.$root.close();
      form.requestSubmit();
    },
    cancelar() {
      const form = this.form();
      const mudados = [...form.elements].filter((c) => "original" in c.dataset && c.value !== c.dataset.original);
      for (const c of mudados) {
        c.value = c.dataset.original;
        c.dispatchEvent(new Event("input", { bubbles: true })); // contadores da tela (grade de cortes)
      }
      this.$root.close();
      (mudados[0] || form.querySelector("[type=submit]") || document.querySelector(`[form="${form.id}"][type=submit]`))?.focus();
    },
  }));
});
