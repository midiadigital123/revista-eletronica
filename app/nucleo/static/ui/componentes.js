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

  // U5: <span x-data="nomeInline" data-url> (_componentes/nome_inline.html), dentro de um form
  // `campoAuto`: quem grava é o autosave (Enter ou sair do campo; impacto, 422 e 409 do U3). Aqui só
  // troca texto ↔ campo: Esc volta o nome gravado; o campo fica aberto enquanto o envio não salva.
  Alpine.data("nomeInline", () => ({
    editando: false,
    nome: "",
    init() {
      const c = this.campo();
      this.nome = c.defaultValue;
      this.$root.addEventListener("autosave:salvo", (e) => {
        this.nome = e.detail.valor;
        this.sair();
      });
      c.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          this.cancelar();
        } else if (e.key === "Enter" && c.value === this.nome) {
          e.preventDefault();
          this.sair();
        }
      });
      c.addEventListener("blur", () => {
        if (c.value === this.nome) this.sair(); // mudou: o change já mandou; fecha quando salvar
      });
    },
    campo() {
      return this.$root.querySelector("input");
    },
    get lendo() {
      return !this.editando;
    },
    get rotulo() {
      return `Renomear ${this.nome}`;
    },
    editar() {
      this.editando = true;
      this.depoisDoXShow(() => {
        this.campo().focus();
        this.campo().select();
      });
    },
    cancelar() {
      const c = this.campo();
      c.value = this.nome;
      c.dispatchEvent(new Event("change", { bubbles: true })); // o autosave limpa erro e status do campo
      this.sair();
    },
    // O x-show mostra no próximo quadro (requestAnimationFrame): focar antes disso não pega.
    depoisDoXShow(fn) {
      this.$nextTick(() => requestAnimationFrame(fn));
    },
    sair() {
      if (!this.editando) return;
      const comFoco = this.$root.contains(document.activeElement); // teclado: o foco volta ao lápis
      this.editando = false;
      if (comFoco) this.depoisDoXShow(() => this.$root.querySelector("button").focus());
    },
  }));
});
