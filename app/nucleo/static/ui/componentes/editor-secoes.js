// Editor de template por seção (U9b): <form x-data="editorSecoes" @click="acao" @focusin="focar">
// em templates/ui/templates/editar.html. Build CSP: o HTML só chama acao/focar; os botões dizem o que
// fazem em data-acao. O id da seção é estrutura (hidden), nunca campo editável. A prévia é HTMX no
// próprio form (hx-trigger input); cada mudança aqui dispara um input para ela e para o aviso.
// Uma seção por vez: o servidor marca a ativa (a 1ª com erro); clicar no índice troca. As outras ficam
// hidden, mas no form (o Salvar manda tudo), e a prévia mostra só a ativa. Sem pode_gravar o componente
// também liga, só para trocar de seção (não há [data-estado] nem prévia HTMX).
// Carregado sem defer no bloco cabeca, para o alpine:init rodar antes do Alpine.
document.addEventListener("alpine:init", () => {
  "use strict";

  const MARCAS = { negrito: "**", italico: "*" };

  Alpine.data("editorSecoes", () => {
    // Fora do estado reativo: elementos do DOM dentro do proxy do Alpine quebram setRangeText.
    let alvo = null; // último Título/Texto focado (o "{ } Variável" insere nele)
    let ativa = ""; // id da seção visível
    let inicial = "";
    let enviando = false;

    return {
      init() {
        const form = this.$root;
        ativa = this.secoes().find((s) => !s.hidden)?.dataset.secao || "";
        this.mostrar();
        // A prévia e o índice chegam do HTMX com todas as seções: filtra antes de pintar.
        document.body.addEventListener("htmx:afterSwap", () => this.mostrar());
        const aviso = form.querySelector("[data-estado]");
        if (!aviso) return; // só leitura
        const padrao = aviso.textContent;
        inicial = this.estado();
        form.addEventListener("input", () => {
          aviso.textContent = this.mudou() ? "Alterações não salvas." : padrao;
        });
        form.addEventListener("submit", () => { enviando = true; });
        addEventListener("beforeunload", (e) => { if (!enviando && this.mudou()) e.preventDefault(); });
        document.body.addEventListener("htmx:afterSettle", () => this.marcarInvalidos());
      },

      // --- uma seção por vez ---
      ativar(id) {
        ativa = id;
        this.mostrar();
      },
      mostrar() {
        for (const s of this.secoes()) s.hidden = s.dataset.secao !== ativa;
        for (const p of this.$root.querySelectorAll("#previa [data-previa]")) p.hidden = p.dataset.previa !== ativa;
        for (const a of this.$root.querySelectorAll("#tpl-indice a")) {
          if (a.hash === `#secao-${ativa}`) a.setAttribute("aria-current", "true");
          else a.removeAttribute("aria-current");
        }
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
        const indice = e.target.closest("#tpl-indice a");
        if (indice) {
          e.preventDefault();
          this.ativar(indice.hash.slice("#secao-".length));
          return;
        }
        const botao = e.target.closest("[data-acao]");
        if (!botao) return;
        const tipo = botao.dataset.acao;
        if (tipo in MARCAS) this.marcar(botao, MARCAS[tipo]);
        else if (tipo === "lista") this.lista(botao);
        else if (tipo === "variavel") this.variavel(botao);
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

      // --- estrutura: só remover (seção que sobrou de um texto antigo); a ordem segue a do fascículo ---
      secoes() {
        return [...this.$root.querySelectorAll("[data-secao]")];
      },
      remover(botao) {
        // Nada é gravado aqui: o Salvar leva à tela de impacto, e recarregar a página desfaz.
        const secao = botao.closest("[data-secao]");
        const vizinha = secao.previousElementSibling || secao.nextElementSibling;
        if (alvo && secao.contains(alvo)) alvo = null;
        secao.remove();
        this.renumerar();
        if (vizinha) this.ativar(vizinha.dataset.secao);
        vizinha?.querySelector("[data-campo=titulo]")?.focus();
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
