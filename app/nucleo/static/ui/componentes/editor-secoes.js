// Editor de template por seção (U9b): <form x-data="editorSecoes" @click="acao" @focusin="focar">
// em templates/ui/templates/editar.html. Build CSP: o HTML só chama acao/focar; os botões dizem o que
// fazem em data-acao. O id da seção é estrutura (hidden), nunca campo editável. A prévia é HTMX no
// próprio form (hx-trigger input); cada mudança aqui dispara um input para ela e para o aviso.
// Carregado sem defer no bloco cabeca, para o alpine:init rodar antes do Alpine.
document.addEventListener("alpine:init", () => {
  "use strict";

  const MARCAS = { negrito: "**", italico: "*" };
  const PASSO = /^passo(\d+)$/;

  Alpine.data("editorSecoes", () => {
    // Fora do estado reativo: elementos do DOM dentro do proxy do Alpine quebram setRangeText.
    let alvo = null; // último Título/Texto focado (o "{ } Variável" insere nele)
    let inicial = "";
    let enviando = false;

    return {
      init() {
        const form = this.$root;
        const aviso = form.querySelector("[data-estado]");
        const padrao = aviso.textContent;
        inicial = this.estado();
        form.addEventListener("input", () => {
          aviso.textContent = this.mudou() ? "Alterações não salvas." : padrao;
        });
        form.addEventListener("submit", () => { enviando = true; });
        addEventListener("beforeunload", (e) => { if (!enviando && this.mudou()) e.preventDefault(); });
        document.body.addEventListener("htmx:afterSettle", () => this.marcarInvalidos());
      },

      estado() {
        return new URLSearchParams(new FormData(this.$root)).toString();
      },
      mudou() {
        return this.estado() !== inicial;
      },

      focar(e) {
        if (e.target.matches("[data-campo=titulo], [data-campo=corpo]")) alvo = e.target;
      },

      acao(e) {
        const botao = e.target.closest("[data-acao]");
        if (!botao) return;
        const tipo = botao.dataset.acao;
        if (tipo in MARCAS) this.marcar(botao, MARCAS[tipo]);
        else if (tipo === "lista") this.lista(botao);
        else if (tipo === "variavel") this.variavel(botao);
        else if (tipo === "passo") this.adicionarPasso(botao);
        else if (tipo === "dialogo") this.adicionarDialogo();
        else if (tipo === "remover") this.remover(botao);
      },

      // --- texto ---
      campo(botao, soCorpo) {
        const secao = botao.closest("[data-secao]");
        if (!soCorpo && alvo && secao.contains(alvo)) return alvo;
        return secao.querySelector("[data-campo=corpo]");
      },
      trocar(campo, texto, ini, fim, selecionar) {
        campo.focus();
        campo.setRangeText(texto, ini, fim, "end");
        if (selecionar) campo.setSelectionRange(...selecionar);
        campo.dispatchEvent(new Event("input", { bubbles: true }));
      },
      marcar(botao, marca) {
        const c = this.campo(botao, true); // título é texto puro: negrito e itálico só no Texto
        const { selectionStart: a, selectionEnd: z } = c;
        const sel = c.value.slice(a, z) || "texto";
        this.trocar(c, marca + sel + marca, a, z, [a + marca.length, a + marca.length + sel.length]);
      },
      lista(botao) {
        const c = this.campo(botao, true);
        const ini = c.value.lastIndexOf("\n", c.selectionStart - 1) + 1;
        const linhas = c.value.slice(ini, c.selectionEnd).split("\n");
        this.trocar(c, linhas.map((l) => (l.startsWith("- ") ? l : "- " + l)).join("\n"), ini, c.selectionEnd);
      },
      variavel(botao) {
        const c = this.campo(botao, false);
        const nome = botao.closest("[data-secao]").querySelector("[data-variavel]").value;
        this.trocar(c, "{" + "{" + nome + "}" + "}", c.selectionStart, c.selectionEnd);
      },

      // --- estrutura (só F2): passoN e dlg-pN; a ordem segue a do fascículo ---
      secoes() {
        return [...this.$root.querySelectorAll("[data-secao]")];
      },
      nova(id, rotulo) {
        const modelo = this.$root.querySelector("template[data-modelo]").innerHTML;
        const caixa = document.createElement("div");
        caixa.innerHTML = modelo.replaceAll("__ID__", id).replaceAll("__ROTULO__", rotulo);
        return caixa.querySelector("[data-secao]");
      },
      inserir(secao, depoisDe) {
        if (depoisDe) depoisDe.after(secao);
        else this.$root.querySelector("[data-secoes]").append(secao);
        this.renumerar();
        secao.querySelector("[data-campo=titulo]").focus();
        this.$root.dispatchEvent(new Event("input", { bubbles: true }));
      },
      adicionarPasso(botao) {
        const n = Number(botao.dataset.proximo);
        botao.dataset.proximo = n + 1;
        const id = "passo" + n;
        const secoes = this.secoes();
        const ultimo = secoes.filter((s) => PASSO.test(s.dataset.secao)).pop() || secoes.find((s) => s.dataset.secao === "abertura");
        this.$root.querySelector("[data-dlg-passo]").append(new Option("Passo " + n, id));
        this.inserir(this.nova(id, "Passo " + n), ultimo);
      },
      adicionarDialogo() {
        const passo = this.$root.querySelector("[data-dlg-passo]").value;
        if (!passo) return;
        const n = PASSO.exec(passo)[1];
        const id = "dlg-p" + n;
        const existe = this.$root.querySelector(`[data-secao="${id}"]`);
        if (existe) {
          existe.querySelector("[data-campo=titulo]").focus(); // um diálogo por passo
          return;
        }
        const ultimo = this.secoes().filter((s) => s.dataset.secao.startsWith("dlg-")).pop();
        this.inserir(this.nova(id, "Diálogo do passo " + n), ultimo);
      },
      remover(botao) {
        // Nada é gravado aqui: o Salvar leva à tela de impacto, e recarregar a página desfaz.
        const secao = botao.closest("[data-secao]");
        const vizinha = secao.previousElementSibling || secao.nextElementSibling;
        this.$root.querySelector(`[data-dlg-passo] option[value="${secao.dataset.secao}"]`)?.remove();
        if (alvo && secao.contains(alvo)) alvo = null;
        secao.remove();
        this.renumerar();
        (vizinha?.querySelector("[data-campo=titulo]") || this.$root.querySelector("[data-acao=passo]"))?.focus();
        this.$root.dispatchEvent(new Event("input", { bubbles: true }));
      },
      renumerar() {
        this.secoes().forEach((s, i) => {
          for (const c of s.querySelectorAll("[data-campo]")) c.name = `secao-${i}-${c.dataset.campo}`;
        });
      },

      // A prévia troca os erros de cada seção (hx-swap-oob); o campo certo fica aria-invalid.
      marcarInvalidos() {
        for (const s of this.secoes()) {
          for (const campo of ["titulo", "corpo"]) {
            const ruim = s.querySelector(`.tpl-secao-erros [data-alvo=${campo}]`);
            const el = s.querySelector(`[data-campo=${campo}]`);
            if (ruim) el.setAttribute("aria-invalid", "true");
            else el.removeAttribute("aria-invalid");
          }
        }
      },
    };
  });
});
