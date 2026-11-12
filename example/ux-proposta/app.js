/* Revista Express · proposta de UI/UX (demo). JS puro, sem dependência. Veja o contrato em paginas/shell.py. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const norm = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const guarda = (k, v) => { try { v === undefined ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) {} };
  const le = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };

  const PESSOAS = {
    ped: { nome: "Ana Souza", perfil: "Pedagógica", ini: "AS" },
    mid: { nome: "Bruno Lima", perfil: "Mídias Digitais", ini: "BL" },
    imp: { nome: "Carla Mendes", perfil: "Impresso", ini: "CM" },
    adm: { nome: "Diego Rocha", perfil: "Admin", ini: "DR" },
  };

  /* ── Aviso passageiro ─────────────────────────────────────────────── */
  window.toast = (msg) => {
    const caixa = $("#toasts");
    if (!caixa) return;
    const t = document.createElement("div");
    t.className = "toast";
    t.textContent = msg;
    caixa.appendChild(t);
    setTimeout(() => t.remove(), 3600);
  };
  const hora = () => new Date().toTimeString().slice(0, 5);
  const salvou = () => {
    $$("[data-salvo]").forEach((s) => { s.textContent = "Salvo às " + hora(); s.classList.add("on"); });
  };

  /* ── Perfil da demo: muda o que aparece, não o que existe ─────────── */
  function aplicaPerfil(p) {
    const pe = PESSOAS[p] || PESSOAS.ped;
    document.documentElement.dataset.perfil = p;
    $$("[data-p]").forEach((el) => { el.hidden = !el.dataset.p.split(/\s+/).includes(p); });
    $$("[data-n-ped]").forEach((el) => { el.textContent = el.dataset["n" + p[0].toUpperCase() + p.slice(1)]; });
    $$("[data-href-imp]").forEach((a) => {
      if (!a.dataset.hrefOrig) a.dataset.hrefOrig = a.getAttribute("href");
      a.setAttribute("href", p === "imp" ? a.dataset.hrefImp : a.dataset.hrefOrig);
    });
    const ro = p === "imp";
    document.body.classList.toggle("so-leitura", ro);
    $$("[data-edita]").forEach((el) => {
      if (el.dataset.dis0 === undefined) el.dataset.dis0 = ("disabled" in el && el.disabled) ? "1" : "0";
      const trava = ro || el.dataset.dis0 === "1";
      el.setAttribute("aria-disabled", trava ? "true" : "false");
      if ("disabled" in el) el.disabled = trava;
      if (ro) el.title = el.title || "Só leitura: o perfil Impresso vê, mas não altera";
    });
    const sel = $("[data-perfil-sel]"); if (sel) sel.value = p;
    $$("[data-pessoa]").forEach((el) => (el.textContent = pe.nome));
    $$("[data-perfil-nome]").forEach((el) => (el.textContent = pe.perfil));
    $$("[data-avatar]").forEach((el) => (el.textContent = pe.ini));
  }
  const sel = $("[data-perfil-sel]");
  if (sel) sel.addEventListener("change", () => { guarda("perfil", sel.value); aplicaPerfil(sel.value); });
  aplicaPerfil(document.documentElement.dataset.perfil || "ped");

  /* ── Abas e passos: o botão mostra o painel de mesmo id ────────────── */
  $$("[data-abas]").forEach((grupo) => {
    const botoes = $$("[data-aba]", grupo);
    const ids = botoes.map((b) => b.dataset.aba);
    const mostra = (id, marcaUrl) => {
      botoes.forEach((b) => b.setAttribute("aria-selected", String(b.dataset.aba === id)));
      ids.forEach((i) => { const p = $(`[data-painel="${i}"]`); if (p) p.hidden = i !== id; });
      if (marcaUrl) { try { history.replaceState(null, "", "#" + id); } catch (e) {} }
    };
    botoes.forEach((b) => b.addEventListener("click", () => mostra(b.dataset.aba, true)));
    const dehash = location.hash.slice(1);
    const atual = ids.includes(dehash) ? dehash : (botoes.find((b) => b.getAttribute("aria-selected") === "true") || botoes[0]).dataset.aba;
    mostra(atual, false);
    grupo._mostra = mostra;
  });
  window.addEventListener("hashchange", () => {
    const id = location.hash.slice(1);
    $$("[data-abas]").forEach((g) => { if ($$("[data-aba]", g).some((b) => b.dataset.aba === id)) g._mostra(id, false); });
  });
  document.addEventListener("click", (e) => {
    const ir = e.target.closest("[data-ir-aba]");
    if (!ir) return;
    e.preventDefault();
    $$("[data-abas]").forEach((g) => { if ($$("[data-aba]", g).some((b) => b.dataset.aba === ir.dataset.irAba)) g._mostra(ir.dataset.irAba, true); });
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  /* ── Diálogos e gaveta ────────────────────────────────────────────── */
  document.addEventListener("click", (e) => {
    const ab = e.target.closest("[data-abrir]");
    if (ab) {
      const d = $("#" + ab.dataset.abrir);
      if (d && !ab.matches('[aria-disabled="true"]')) {
        d.showModal();
        const q = $("input", d); if (q && d.id === "paleta") q.focus();
      }
      return;
    }
    const fe = e.target.closest("[data-fechar]");
    if (fe) { const d = fe.closest("dialog"); if (d) d.close(); return; }
    if (e.target.matches("dialog") && e.target.open) e.target.close();
  });

  /* ── Menu lateral no celular ──────────────────────────────────────── */
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-rail]")) document.body.classList.toggle("rail-aberta");
  });
  document.addEventListener("click", (e) => {
    $$(".temp[open], details.menu[open]").forEach((t) => { if (!t.contains(e.target)) t.removeAttribute("open"); });
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") $$(".temp[open], details.menu[open]").forEach((t) => t.removeAttribute("open"));
  });

  /* ── Seleção em massa ─────────────────────────────────────────────── */
  const barra = $(".sel-barra");
  function atualizaSel() {
    if (!barra) return;
    const n = $$("[data-sel]:checked").filter((c) => !c.closest("[hidden]")).length;
    barra.classList.toggle("on", n > 0);
    $$("[data-sel-n]").forEach((el) => (el.textContent = n));
    $$("[data-sel-plural]").forEach((el) => (el.textContent = n === 1 ? "selecionada" : "selecionadas"));
  }
  document.addEventListener("change", (e) => {
    if (e.target.matches("[data-sel-todos]")) {
      const alvo = $(e.target.dataset.selTodos) || document;
      $$("[data-sel]", alvo).forEach((c) => { if (!c.closest("[hidden]")) c.checked = e.target.checked; });
    }
    if (e.target.matches("[data-sel],[data-sel-todos]")) atualizaSel();
  });
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-sel-limpar]")) {
      $$("[data-sel],[data-sel-todos]").forEach((c) => (c.checked = false));
      atualizaSel();
    }
  });

  /* ── Filtros de tabela e esteira ──────────────────────────────────── */
  function filtra(alvo) {
    const raiz = $(alvo); if (!raiz) return;
    const q = norm((($(`input[data-filtro="${alvo}"]`) || {}).value) || "");
    const sels = $$(`select[data-alvo="${alvo}"]`);
    let vis = 0;
    $$("[data-busca]", raiz).forEach((r) => {
      let ok = norm(r.dataset.busca).includes(q);
      sels.forEach((s) => { if (s.value && r.dataset[s.dataset.filtra] !== s.value) ok = false; });
      r.hidden = !ok;
      if (ok) vis++;
    });
    $$(`[data-contagem="${alvo}"]`).forEach((el) => (el.textContent = vis));
    $$("[data-col-n]", raiz).forEach((c) => { c.textContent = $$("[data-busca]", c.closest("[data-col]")).filter((r) => !r.hidden).length; });
    atualizaSel();
  }
  document.addEventListener("input", (e) => { const a = e.target.dataset && e.target.dataset.filtro; if (a) filtra(a); });
  document.addEventListener("change", (e) => { const a = e.target.dataset && e.target.dataset.alvo; if (a && e.target.matches("select")) filtra(a); });

  /* ── Avisos, copiar, autosave e impacto ───────────────────────────── */
  document.addEventListener("click", (e) => {
    const c = e.target.closest("[data-copiar]");
    if (c) { try { navigator.clipboard.writeText(c.dataset.copiar); } catch (x) {} window.toast("Copiado"); return; }
    const t = e.target.closest("[data-toast]");
    if (t && !t.matches('[aria-disabled="true"]')) {
      if (t.hasAttribute("data-salva")) salvou();
      window.toast(t.dataset.toast);
      const f = t.closest("dialog"); if (f && t.hasAttribute("data-fechar")) f.close();
    }
  });
  document.addEventListener("click", (e) => {
    if (e.target.closest('[data-edita][aria-disabled="true"]')) e.preventDefault();
  }, true);

  let pendente = null;
  document.addEventListener("focusin", (e) => { if (e.target.matches("[data-impacto]")) e.target.dataset.orig = e.target.value; });
  document.addEventListener("change", (e) => {
    const el = e.target;
    if (el.matches("[data-impacto]")) {
      pendente = { el, novo: el.value };
      el.value = el.dataset.orig || "";
      const d = $("#" + el.dataset.impacto); if (d) d.showModal();
      return;
    }
    if (el.matches("[data-autosave]")) salvou();
  });
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-impacto-ok]") && pendente) {
      pendente.el.value = pendente.novo; pendente.el.dataset.orig = pendente.novo;
      salvou(); window.toast("Salvo. As revistas listadas perderam o Validado.");
      e.target.closest("dialog").close(); pendente = null;
    } else if (e.target.closest("[data-fechar]") && pendente) {
      pendente = null;
    }
  });

  /* ── Busca global (Ctrl+K ou /) ───────────────────────────────────── */
  const dlg = $("#paleta"), q = $("#paleta-q"), lista = $("#paleta-lista");
  let ativo = 0;
  function pinta() {
    if (!lista) return;
    const termo = norm(q.value);
    const itens = (window.INDICE || []).filter((i) => !termo || norm(i[0] + " " + i[1]).includes(termo)).slice(0, 9);
    lista.innerHTML = itens.map((i, k) => `<li><a href="${i[2]}" class="${k === ativo ? "sel" : ""}">${i[0]}<small>${i[1]}</small></a></li>`).join("") ||
      '<li style="padding:14px;color:var(--txt-2)">Nada encontrado.</li>';
  }
  if (dlg) {
    dlg.addEventListener("close", () => { q.value = ""; ativo = 0; });
    dlg.addEventListener("toggle", () => { if (dlg.open) { ativo = 0; pinta(); q.focus(); } });
    new MutationObserver(() => { if (dlg.open) { ativo = 0; pinta(); setTimeout(() => q.focus(), 0); } }).observe(dlg, { attributes: true, attributeFilter: ["open"] });
    q.addEventListener("input", () => { ativo = 0; pinta(); });
    q.addEventListener("keydown", (e) => {
      const as = $$("a", lista);
      if (e.key === "ArrowDown") { ativo = Math.min(ativo + 1, as.length - 1); pinta(); e.preventDefault(); }
      if (e.key === "ArrowUp") { ativo = Math.max(ativo - 1, 0); pinta(); e.preventDefault(); }
      if (e.key === "Enter" && as[ativo]) location.href = as[ativo].getAttribute("href");
    });
  }
  document.addEventListener("keydown", (e) => {
    const digitando = /^(input|textarea|select)$/i.test(e.target.tagName) || e.target.isContentEditable;
    if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") || (e.key === "/" && !digitando)) {
      e.preventDefault(); if (dlg && !dlg.open) dlg.showModal();
    }
  });
})();
