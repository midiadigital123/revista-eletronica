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
// Campos do modal (ex.: a frase "descartar N cópia(s)") vão junto ao confirmar. Resposta 200 com
// `trocar` ({id: html}): troca essas partes da página (o que a gravação mudou fora do campo).
// Arquivo só dentro de [data-soltar] (componente `arquivoSoltar`, abaixo): envia o arquivo em `valor`.
// Eventos no campo, para os componentes de cima: autosave:salvo, autosave:falhou, autosave:cancelado.
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

  // U8b: troca partes da página pelo HTML que a resposta trouxe (o Alpine inicia o que entrar).
  const trocar = (pedacos) => {
    for (const [id, html] of Object.entries(pedacos)) {
      const velho = document.getElementById(id);
      if (!velho) continue;
      const molde = document.createElement("template");
      molde.innerHTML = html.trim();
      const novo = molde.content.firstElementChild;
      velho.replaceWith(novo);
      if (window.htmx) window.htmx.process(novo); // links da lista de seções, form da seção, Validar
    }
  };

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
        !this.desligado && c.name && c.form === this.$root && c.type !== "hidden" && (c.type !== "file" || !!c.closest("[data-soltar]")) &&
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
      if (confirmar?.value === "on") {
        if (!this.impacto) return; // modal do envio da página (U2, ex.: Incluir tarefa): segue o POST
        e.preventDefault();
        confirmar.value = "";
        const { campo, dialogo } = this.impacto;
        const extra = controles(dialogo).map((o) => [o.name, o.value]); // ex.: a frase de descarte
        this.impacto = null; // o `close` do modal, que chega depois, não é cancelamento
        this.enfileirar(campo, true, extra);
      } else if (!e.submitter) {
        e.preventDefault(); // sem botão (requestSubmit, Enter): nada sai pelo POST da página
      }
    },
    enfileirar(c, confirmar, extra = []) {
      const chave = daLinha(c) || c; // linha nova: o 2º campo espera o id que o 1º recebe
      const fila = (this.filas.get(chave) || Promise.resolve()).then(() => this.enviar(c, confirmar, extra));
      this.filas.set(chave, fila);
      return fila;
    },
    async enviar(c, confirmar, extra = []) {
      if (this.desligado) return;
      if (!confirmar && this.impacto?.campo === c) return; // Enter manda e o change do Enter também: um modal só
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
      const sessao = this.$root.querySelector("[name=_bloqueio_sessao]"); // ui_bloqueio.CAMPO_SESSAO
      if (sessao) d.append(sessao.name, sessao.value);
      d.append("form_id", this.$root.id);
      d.append("campo", c.name.startsWith(prefixo) ? c.name.slice(prefixo.length) : c.name);
      d.append("valor", c.type === "file" ? c.files[0] : atual);
      d.append("original", gravado(c));
      const linha = daLinha(c);
      if (linha) for (const o of controles(linha)) if (o.type !== "checkbox" || o.checked) d.append(o.name, o.value);
      if (confirmar) d.append("confirmar_impacto", "on");
      for (const [nome, v] of extra) d.append(nome, v);

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
      c.dispatchEvent(new CustomEvent("autosave:salvo", { bubbles: true, detail: { valor: valor(c) } })); // nomeInline (U5)
      if (corpo.trocar) trocar(corpo.trocar);
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
      c.dispatchEvent(new CustomEvent("autosave:falhou", { bubbles: true }));
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
        campo.dispatchEvent(new CustomEvent("autosave:cancelado", { bubbles: true }));
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

  // U4: <ul|ol|tbody x-data="ordenavel" id="…" data-ordem-url="…/reordenar/">, filhos [data-id] com
  // _componentes/ordem.html: a alça <button class="alca" data-rotulo> arrasta (SortableJS) e, com o foco
  // nela, ↑/↓ movem o item; um aria-live (no body, um por lista) anuncia a posição nova. Cada mudança manda a lista inteira (ids) pelo protocolo do autosave e entra no mesmo status da página.
  // Impacto: o modal do U2 aponta para um form oculto deste componente; confirmar reenvia confirmado,
  // Cancelar/Esc volta a ordem gravada. 422/409/403 também voltam; sem conexão, a ordem fica e o
  // "Tentar de novo" reenvia.
  Alpine.data("ordenavel", () => ({
    init() {
      this.chave = document.createElement("i"); // chave deste componente em `enviando`/`falhas`
      this.gravada = this.ids();
      this.fila = Promise.resolve();
      this.impacto = null;
      this.foco = null;
      const id = `ordem-${this.$root.id}`;
      document.getElementById(id)?.remove(); // troca HTMX da lista: um form e um aviso por lista
      document.getElementById(`${id}-aviso`)?.remove();
      this.form = Object.assign(document.createElement("form"), { id, hidden: true });
      this.form.addEventListener("submit", (e) => this.aoConfirmar(e));
      this.aviso = Object.assign(document.createElement("p"), { id: `${id}-aviso`, className: "sr-only" });
      this.aviso.setAttribute("aria-live", "polite");
      document.body.append(this.form, this.aviso);
      this.sortable = Sortable.create(this.$root, {
        handle: ".alca", draggable: "[data-id]", animation: 120,
        onEnd: (e) => {
          this.foco = e.item.querySelector(".alca");
          if (e.oldIndex !== e.newIndex) this.enfileirar(false);
        },
      });
      this.$root.addEventListener("keydown", (e) => {
        const passo = { ArrowUp: -1, ArrowDown: 1 }[e.key];
        if (!passo || !e.target.matches(".alca") || e.altKey || e.ctrlKey || e.metaKey) return;
        e.preventDefault(); // a seta não rola a página
        this.mover(e.target, passo);
      });
      window.addEventListener("autosave:tentar", () => {
        if (falhas.has(this.chave)) this.enfileirar(false);
      });
    },
    itens() {
      return [...this.$root.children].filter((e) => e.matches("[data-id]"));
    },
    ids() {
      return this.itens().map((e) => e.dataset.id);
    },
    mover(alca, passo) {
      const item = alca.closest("[data-id]");
      const itens = this.itens();
      const vizinho = itens[itens.indexOf(item) + passo];
      if (!vizinho) return;
      if (passo < 0) vizinho.before(item);
      else vizinho.after(item);
      alca.focus(); // mover o nó tira o foco da alça
      this.foco = alca;
      this.aviso.textContent = `${alca.dataset.rotulo} na posição ${this.itens().indexOf(item) + 1} de ${itens.length}`;
      this.enfileirar(false);
    },
    restaurar() {
      const porId = new Map(this.itens().map((e) => [e.dataset.id, e]));
      const marca = document.createComment("");
      this.itens()[0]?.before(marca);
      for (const id of this.gravada) if (porId.has(id)) marca.before(porId.get(id));
      marca.remove();
      this.foco?.focus();
    },
    enfileirar(confirmar) {
      this.fila = this.fila.then(() => this.enviar(confirmar));
    },
    async enviar(confirmar) {
      const ids = this.ids();
      if (!confirmar && ids.join() === this.gravada.join()) {
        falhas.delete(this.chave);
        return avisar();
      }
      enviando.add(this.chave);
      falhas.delete(this.chave);
      avisar();
      const d = new FormData();
      d.append("csrfmiddlewaretoken", document.querySelector("[name=csrfmiddlewaretoken]").value);
      const sessao = document.querySelector("[name=_bloqueio_sessao]"); // ui_bloqueio.CAMPO_SESSAO
      if (sessao) d.append(sessao.name, sessao.value);
      d.append("form_id", this.form.id);
      for (const id of ids) d.append("ids", id);
      if (confirmar) d.append("confirmar_impacto", "on");
      let r;
      let corpo = {};
      try {
        r = await fetch(this.$root.dataset.ordemUrl, { method: "POST", body: d, credentials: "same-origin", headers: { Accept: "application/json" } });
        corpo = await r.json().catch(() => ({}));
      } catch {
        return this.falhou("Não salvo: sem conexão");
      }
      if (r.ok && corpo.ok) {
        this.gravada = ids;
        salvoEm = corpo.salvo_em;
        enviando.delete(this.chave);
        return avisar();
      }
      if (r.ok && corpo.impacto) return this.pedirConfirmacao(corpo.impacto);
      this.restaurar();
      if (r.status === 422) return this.falhou(`Não salvo: ${(corpo.erros || ["ordem recusada"]).join(" ")}`);
      if (r.status === 409 || r.status === 403) {
        this.sortable.option("disabled", true);
        for (const b of this.$root.querySelectorAll(".alca")) b.disabled = true;
        return this.falhou(corpo.conflito || "Não salvo: a página ficou somente leitura. Recarregue a página.");
      }
      return this.falhou("Não salvo: erro no servidor");
    },
    falhou(texto) {
      enviando.delete(this.chave);
      falhas.set(this.chave, texto);
      avisar();
    },
    pedirConfirmacao(impacto) {
      const molde = document.createElement("template");
      molde.innerHTML = impacto.html;
      const dialogo = molde.content.querySelector("dialog");
      dialogo.addEventListener("close", () => {
        if (this.impacto === dialogo) { // Cancelar ou Esc: nada foi gravado
          this.impacto = null;
          enviando.delete(this.chave);
          this.restaurar();
          avisar();
        }
        dialogo.remove();
      });
      this.impacto = dialogo;
      document.body.append(dialogo); // o Alpine inicia o `impacto` do U2, que abre sozinho
    },
    aoConfirmar(e) {
      e.preventDefault(); // o `impacto` chama requestSubmit() no form oculto: reenvia confirmado
      const campo = this.form.elements.namedItem("confirmar_impacto");
      if (campo) campo.value = "";
      if (!this.impacto) return;
      this.impacto = null; // o `close` do modal, que chega depois, não é cancelamento
      this.enfileirar(true);
      this.foco?.focus();
    },
  }));

  // U8b: <div x-data="arquivoSoltar" data-soltar data-max data-tipo> com um input file dentro de um
  // form `campoAuto`: área de soltar e clique. Quem envia é o campoAuto (ao escolher, com o modal de
  // impacto e o erro inline do 422); aqui só o arrastar, o limite de tamanho antes de enviar e a barra.
  Alpine.data("arquivoSoltar", () => ({
    sobre: false,
    enviando: false,
    nome: "",
    erro: "",
    init() {
      const campo = this.$root.querySelector("input[type=file]");
      const max = Number(this.$root.dataset.max);
      this.$root.addEventListener("dragover", (e) => {
        e.preventDefault();
        this.sobre = true;
      });
      this.$root.addEventListener("dragleave", () => (this.sobre = false));
      this.$root.addEventListener("drop", (e) => {
        e.preventDefault();
        this.sobre = false;
        if (!e.dataTransfer.files.length) return;
        campo.files = e.dataTransfer.files;
        campo.dispatchEvent(new Event("change", { bubbles: true }));
      });
      // Antes do campoAuto (que ouve no form): arquivo grande nem sai daqui.
      campo.addEventListener("change", (e) => {
        const arquivo = campo.files[0];
        this.erro = "";
        if (!arquivo) return;
        if (arquivo.size > max) {
          e.stopPropagation();
          this.erro = `${this.$root.dataset.tipo} maior que ${Math.floor(max / 2 ** 20)} MB: reduza e envie de novo.`;
          campo.value = "";
          return;
        }
        this.nome = arquivo.name;
        this.enviando = true;
      });
      for (const fim of ["autosave:salvo", "autosave:falhou", "autosave:cancelado"]) {
        this.$root.addEventListener(fim, () => (this.enviando = false));
      }
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
