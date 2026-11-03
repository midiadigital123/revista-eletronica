// Valor herdado × sobrescrito (página do projeto, aba Passos e cores): <div x-data="sobrescrita"
// data-herdado="…"> com um controle [data-valor] e, no passo, a caixa [data-sem] ("sem linhas vazias").
// Quem grava é o campoAuto do form (autosave.js); aqui só o estado mostrado (selo, "Voltar…") e o
// "Voltar", que põe o valor herdado no controle e dispara o `change` que o campoAuto já envia.
// Carregado sem defer no bloco cabeca, para o alpine:init rodar antes do Alpine.
document.addEventListener("alpine:init", () => {
  "use strict";

  Alpine.data("sobrescrita", () => ({
    sobrescrito: false,
    herdado: true,
    hex: "",
    // Declarados aqui: atribuir no init uma chave que o objeto não tem cai no componente de fora
    // (o campoAuto do form), e todas as amostras passariam a mexer no mesmo controle.
    valor: null,
    sem: null,
    init() {
      this.valor = this.$root.querySelector("[data-valor]");
      this.sem = this.$root.querySelector("[data-sem]");
      // Antes do campoAuto (que ouve no form): marcar "sem linhas vazias" limpa o número.
      this.$root.addEventListener("change", (e) => {
        if (e.target === this.sem && this.sem.checked) this.valor.value = "";
        this.sincronizar();
      });
      this.$root.addEventListener("input", () => this.sincronizar());
      for (const fim of ["autosave:salvo", "autosave:cancelado", "autosave:falhou"]) {
        this.$root.addEventListener(fim, () => this.sincronizar());
      }
      this.sincronizar();
    },
    sincronizar() {
      const herdado = this.$root.dataset.herdado.toLowerCase();
      this.sobrescrito = this.valor.value.toLowerCase() !== herdado || !!this.sem?.checked;
      this.herdado = !this.sobrescrito;
      this.hex = this.valor.value.toUpperCase();
      if (this.sem) this.valor.disabled = this.sem.checked;
    },
    voltar() {
      const alvo = this.sem?.checked ? this.sem : this.valor;
      if (alvo === this.sem) this.sem.checked = false;
      else this.valor.value = this.$root.dataset.herdado;
      alvo.dispatchEvent(new Event("change", { bubbles: true }));
      this.valor.focus();
    },
  }));
});
