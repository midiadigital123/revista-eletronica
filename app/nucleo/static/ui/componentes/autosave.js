// Autosave por campo (U3): componentes Alpine `campoAuto` e `saida`. Build CSP: o HTML só nomeia o
// componente; a lógica fica aqui. Protocolo das respostas: nucleo/ui_autosave.py e
// docs/telas/design-system.md. Carregado antes do Alpine (base.html), por isso registra no alpine:init.
//
// <form x-data="campoAuto" id="…" data-url="/…/campo/">: todo controle com name do form salva sozinho
// no `change` (o texto, ao sair do campo), um envio por vez por campo. Ancestral com data-url troca a
// rota (a planilha tem uma por projeto) e data-prefixo tira o prefixo do formset do nome do campo.
// [data-linha]: manda a linha inteira (passo, cor, tarefa). [data-manual]: fica de fora (linha nova
// que ainda grava pelo botão). Impacto: o servidor devolve o modal do U2 (componente `impacto`), que
// ao confirmar põe confirmar_impacto=on no form e chama requestSubmit(): o submit é interceptado
// aqui e o campo vai de novo, confirmado. Cancelar/Esc volta o valor gravado e o foco ao campo.
// 409 sem `atual` (bloqueio perdido) e 403: o form inteiro vira só leitura, como no bloqueio.js.
document.addEventListener("alpine:init", () => {
  "use strict";

  const enviando = new Set(); // campos em envio ou esperando o modal de impacto
  const falhas = new Map(); // campo -> texto do status ("Não salvo: …")
  const salvos = new WeakMap(); // campo -> último valor gravado (sem isso: o valor da carga da página)
  let salvoEm = "";

  const valor = (c) => (c.type === "checkbox" ? (c.checked ? "on" : "") : c.value);
  const daCarga = (c) => {
    if (c.type === "checkbox") return c.defaultChecked ? "on" : "";
    if (c.tagName === "SELECT") return ([...c.options].find((o) => o.defaultSelected) || c.options[0])?.value ?? "";
    return c.defaultValue;
  };
  const gravado = (c) => (salvos.has(c) ? salvos.get(c) : daCarga(c));
  const definir = (c, v) => {
    if (c.type === "checkbox") c.checked = v === "on";
    else c.value = v;
  };
  const daLinha = (c) => c.closest("[data-linha]");
  const controles = (raiz) => [...raiz.querySelectorAll("input[name], select[name], textarea[name]")];

  // Um status para a página inteira: erro vence envio, envio vence salvo.
  const avisar = () => {
    let detalhe;
    if (falhas.size) {
      const texto = [...falhas.values()][0];
      detalhe = { estado: "erro", texto, podeTentar: !texto.includes("somente leitura") };
    } else if (enviando.size) detalhe = { estado: "salvando", texto: "Salvando…" };
    else detalhe = { estado: salvoEm ? "salvo" : "", texto: "" };
    window.dispatchEvent(new CustomEvent("autosave:estado", { detail: { podeTentar: false, salvoEm, ...detalhe } }));
  };

  Alpine.data("campoAuto", () => ({
    init() {
      this.filas = new Map(); // campo ou linha -> Promise do último envio
      this.impacto = null; // { campo, dialogo } esperando o modal
      this.desligado = false;
      this.$root.addEventListener("change", (e) => this.mudou(e.target));
      this.$root.addEventListener("submit", (e) => this.aoEnviarForm(e));
      this.$root.addEventListener("keydown", (e) => this.aoTeclar(e));
      window.addEventListener("autosave:tentar", () => this.tentarDeNovo());
    },
    automatico(c) {
      return (
        !this.desligado && c.name && c.form === this.$root && c.type !== "hidden" && c.type !== "file" &&
        c.type !== "submit" && !c.disabled && !c.readOnly && !c.closest("[data-manual]") && !!c.closest("[data-url]")
      );
    },
    mudou(c) {
      if (this.automatico(c)) this.enfileirar(c, false);
    },
    // Enter num campo de texto salva o campo (não envia a página nem o botão da linha nova).
    aoTeclar(e) {
      const c = e.target;
      if (e.key !== "Enter" || c.tagName !== "INPUT" || !this.automatico(c)) return;
      e.preventDefault();
      this.mudou(c);
    },
    aoEnviarForm(e) {
      const confirmar = this.$root.elements.namedItem("confirmar_impacto");
      if (this.impacto && confirmar?.value === "on") {
        e.preventDefault();
        confirmar.value = "";
        const { campo } = this.impacto;
        this.impacto = null; // o `close` do modal, que chega depois, não é cancelamento
        this.enfileirar(campo, true);
      } else if (!e.submitter) {
        e.preventDefault(); // sem botão (requestSubmit, Enter): nada sai pelo POST da página
      }
    },
    enfileirar(c, confirmar) {
      const chave = daLinha(c) || c; // linha nova: o 2º campo espera o id que o 1º recebe
      const fila = (this.filas.get(chave) || Promise.resolve()).then(() => this.enviar(c, confirmar));
      this.filas.set(chave, fila);
      return fila;
    },
    async enviar(c, confirmar) {
      if (this.desligado) return;
      const atual = valor(c);
      if (!confirmar && atual === gravado(c)) {
        this.limpar(c); // voltou ao gravado: nada a enviar
        return;
      }
      enviando.add(c);
      falhas.delete(c);
      avisar();
      const alvo = c.closest("[data-url]");
      const prefixo = alvo.dataset.prefixo || "";
      const d = new FormData();
      d.append("csrfmiddlewaretoken", this.$root.querySelector("[name=csrfmiddlewaretoken]").value);
      const sessao = this.$root.querySelector("#bloqueio-sessao");
      if (sessao) d.append(sessao.name, sessao.value);
      d.append("form_id", this.$root.id);
      d.append("campo", c.name.startsWith(prefixo) ? c.name.slice(prefixo.length) : c.name);
      d.append("valor", atual);
      d.append("original", gravado(c));
      const linha = daLinha(c);
      if (linha) for (const o of controles(linha)) if (o.type !== "checkbox" || o.checked) d.append(o.name, o.value);
      if (confirmar) d.append("confirmar_impacto", "on");

      let r;
      let corpo = {};
      try {
        r = await fetch(alvo.dataset.url, { method: "POST", body: d, credentials: "same-origin", headers: { Accept: "application/json" } });
        corpo = await r.json().catch(() => ({}));
      } catch {
        return this.falhou(c, "Não salvo: sem conexão");
      }
      if (r.ok && corpo.ok) return this.salvou(c, atual, corpo);
      if (r.ok && corpo.impacto) return this.pedirConfirmacao(c, corpo.impacto);
      if (r.status === 422) return this.falhou(c, "Não salvo: corrija o campo marcado", corpo.erros);
      if (r.status === 409 && "atual" in corpo) {
        salvos.set(c, corpo.atual); // "Tentar de novo" sobrescreve de propósito o que a outra pessoa gravou
        return this.falhou(c, "Não salvo: outra pessoa mudou este valor", [corpo.conflito]);
      }
      if (r.status === 409 || r.status === 403) {
        this.desligar(corpo.conflito || "Não salvo: sua sessão ou permissão mudou. Recarregue a página.");
        return this.falhou(c, "Não salvo: a página ficou somente leitura");
      }
      return this.falhou(c, "Não salvo: erro no servidor");
    },
    salvou(c, enviado, corpo) {
      const linha = daLinha(c);
      if (corpo.removida && linha) {
        if (linha.nextElementSibling?.matches(".pj-erros")) linha.nextElementSibling.remove();
        linha.remove();
      }
      if (corpo.id && linha) {
        const id = linha.querySelector('input[name$="-id"]');
        if (id) id.value = corpo.id;
      }
      if ("valor" in corpo && valor(c) === enviado) definir(c, corpo.valor); // "350 400" -> "350, 400"
      salvos.set(c, "valor" in corpo ? corpo.valor : enviado);
      if (linha) for (const o of controles(linha)) if (o !== c && !enviando.has(o)) salvos.set(o, valor(o));
      salvoEm = corpo.salvo_em;
      this.limpar(c);
    },
    limpar(c) {
      const linha = daLinha(c);
      for (const o of linha ? controles(linha) : [c]) {
        enviando.delete(o);
        falhas.delete(o);
        o.removeAttribute("aria-invalid");
        o.removeAttribute("aria-describedby");
        o.parentElement?.querySelector(":scope > [data-erro-auto]")?.remove();
      }
      avisar();
    },
    falhou(c, texto, erros) {
      enviando.delete(c);
      falhas.set(c, texto);
      if (erros?.length) {
        c.setAttribute("aria-invalid", "true");
        let p = c.parentElement.querySelector(":scope > [data-erro-auto]");
        if (!p) {
          p = Object.assign(document.createElement("p"), { className: "erro", id: `${c.id || c.name}-erro-auto` });
          p.setAttribute("data-erro-auto", "");
          p.setAttribute("role", "alert");
          c.after(p);
        }
        p.textContent = erros.join(" ");
        c.setAttribute("aria-describedby", p.id);
      }
      avisar();
    },
    pedirConfirmacao(c, impacto) {
      const molde = document.createElement("template");
      molde.innerHTML = impacto.html;
      const dialogo = molde.content.querySelector("dialog");
      dialogo.setAttribute("data-autosave", "");
      dialogo.addEventListener("close", () => this.fechouImpacto(dialogo));
      this.impacto = { campo: c, dialogo };
      this.$root.append(dialogo); // o Alpine inicia o `impacto` do U2, que abre sozinho
    },
    fechouImpacto(dialogo) {
      if (this.impacto?.dialogo === dialogo) {
        const { campo } = this.impacto; // Cancelar ou Esc: nada foi gravado
        this.impacto = null;
        const linha = daLinha(campo);
        for (const o of linha ? controles(linha) : [campo]) definir(o, gravado(o));
        this.limpar(campo);
        campo.focus();
      }
      dialogo.remove();
    },
    tentarDeNovo() {
      for (const c of [...falhas.keys()]) if (this.$root.contains(c)) this.enfileirar(c, false);
    },
    // Mesmo efeito do desligar() do bloqueio.js: readOnly onde dá (o texto segue copiável).
    desligar(texto) {
      if (this.desligado) return;
      this.desligado = true;
      const LEITURA = new Set(["text", "search", "url", "tel", "email", "number", "date"]);
      for (const c of this.$root.querySelectorAll("input, select, textarea, button")) {
        if (c.type === "hidden") continue;
        if (c.tagName === "TEXTAREA" || (c.tagName === "INPUT" && LEITURA.has(c.type))) c.readOnly = true;
        else c.disabled = true;
      }
      let lista = document.querySelector("ul.mensagens");
      if (!lista) {
        lista = Object.assign(document.createElement("ul"), { className: "mensagens" });
        this.$root.before(lista);
      }
      const item = Object.assign(document.createElement("li"), { className: "aviso aviso-erro", textContent: texto });
      item.setAttribute("role", "alert");
      lista.append(item);
    },
  }));

  // <div x-data="saida"> (_componentes/status_salvo.html): mostra o status e só avisa ao sair da
  // página com envio pendente ou com erro (nunca com tudo salvo).
  Alpine.data("saida", () => ({
    estado: "",
    texto: "",
    salvoEm: "",
    podeTentar: false,
    init() {
      window.addEventListener("autosave:estado", (e) => Object.assign(this, e.detail));
      window.addEventListener("beforeunload", (e) => {
        if (enviando.size || falhas.size) e.preventDefault();
      });
    },
    get ocioso() {
      return this.estado === "";
    },
    get salvando() {
      return this.estado === "salvando";
    },
    get salvo() {
      return this.estado === "salvo";
    },
    get erro() {
      return this.estado === "erro";
    },
    tentar() {
      window.dispatchEvent(new CustomEvent("autosave:tentar"));
    },
  }));
});
