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

  // U4: <div x-data="linhaNova" data-total="id_<prefixo>-TOTAL_FORMS"> com <template data-molde> (a
  // linha do empty_form, com __prefix__), o alvo [data-linhas] e o botão [data-abrir-linha] @click="abrir".
  // Não há linha vazia na tela: ela nasce no fim, com o foco no 1º campo, e grava pelo botão submit
  // dela (o Enter usa o mesmo botão). Esc ou "Descartar" tira a linha. Sem data-total (Cortes), o
  // molde é um form próprio. Itens [data-vazio] do alvo ("Nenhuma tarefa") somem com a linha aberta.
  Alpine.data("linhaNova", () => ({
    init() {
      this.$root.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && e.target.closest?.("[data-linha-nova]")) {
          e.preventDefault();
          this.descartar();
        }
      });
    },
    total() {
      return document.getElementById(this.$root.dataset.total || "");
    },
    alvo() {
      return this.$root.querySelector("[data-linhas]");
    },
    abrir() {
      let linha = this.alvo().querySelector("[data-linha-nova]");
      if (!linha) {
        const total = this.total();
        const molde = document.createElement("template");
        molde.innerHTML = this.$root.querySelector("template[data-molde]").innerHTML.replaceAll("__prefix__", total ? total.value : "");
        linha = molde.content.firstElementChild;
        linha.setAttribute("data-linha-nova", "");
        this.alvo().append(linha);
        if (total) total.value = Number(total.value) + 1;
        for (const v of this.alvo().querySelectorAll(":scope > [data-vazio]")) v.hidden = true;
      }
      linha.querySelector("input:not([type=hidden]), select, textarea")?.focus();
    },
    descartar() {
      const linha = this.alvo().querySelector("[data-linha-nova]");
      if (!linha) return;
      if (linha.nextElementSibling?.querySelector(":scope > td > .erro, :scope > .erro")) linha.nextElementSibling.remove();
      linha.remove();
      const total = this.total();
      if (total) total.value = Number(total.value) - 1;
      for (const v of this.alvo().querySelectorAll(":scope > [data-vazio]")) v.hidden = false;
      this.$root.querySelector("[data-abrir-linha]")?.focus();
    },
  }));
});
