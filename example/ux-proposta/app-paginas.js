

(() => {
  const lista = document.querySelector("#lista-rev");
  if (!lista) return;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const dispara = (el, tipo) => el.dispatchEvent(new Event(tipo, { bubbles: true }));
  const ico = (n) => `<svg class="ic" aria-hidden="true" focusable="false"><use href="#i-${n}"/></svg>`;
  const busca = $('input[data-filtro="#lista-rev"]');
  const selects = $$('select[data-alvo="#lista-rev"]');
  const total = $$(".cartao-rev", lista).length;

  /* resultado do filtro: contagem só das revistas (cartões), vazio, colunas sem cartão */
  const atualiza = () => {
    const n = $$(".cartao-rev:not([hidden])", lista).length;
    $$('[data-contagem="#lista-rev"]').forEach((e) => (e.textContent = n));
    lista.classList.toggle("sem-resultado", n === 0);
    $("#rev-vazio").hidden = n > 0;
    $$(".col-fase", lista).forEach((c) => { $(".col-nada", c).hidden = !!$(".cartao-rev:not([hidden])", c); });
    const filtrando = !!busca.value || selects.some((s) => s.value);
    $$("[data-limpar-filtros]").forEach((b) => { if (b.closest(".rl-filtros")) b.hidden = !filtrando; });
  };
  document.addEventListener("input", (e) => { if (e.target === busca) atualiza(); });
  document.addEventListener("change", (e) => { if (selects.includes(e.target)) atualiza(); });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("[data-limpar-filtros]")) return;
    busca.value = ""; selects.forEach((s) => (s.value = ""));
    dispara(busca, "input"); atualiza();
  });

  /* ?fase=3 e ?parceiro=<id> pré-selecionam os filtros; #tabela já é tratado pelas abas */
  const qs = new URLSearchParams(location.search);
  const fase = qs.get("fase");
  if (fase) { const s = $('select[data-filtra="fase"]'); if (s) { s.value = fase; dispara(s, "change"); } }
  const par = qs.get("parceiro");
  if (par) {
    const c = $(`.cartao-rev[data-parceiro="${CSS.escape(par)}"]`, lista);
    if (c) { busca.value = c.dataset.parceiroNome; dispara(busca, "input"); }
  }
  atualiza();

  /* a barra de seleção só vale na tabela: ao trocar de vista, recalcula */
  $$("[data-aba]", lista).forEach((b) => b.addEventListener("click", () => {
    const c = $("[data-sel]"); if (c) setTimeout(() => dispara(c, "change"), 0);
  }));

  /* aviso de impacto dos diálogos em massa */
  document.addEventListener("click", (e) => {
    if (!e.target.closest('[data-abrir="dlg-matriz"],[data-abrir="dlg-template"]')) return;
    const marcadas = $$("#tab-rev [data-sel]:checked").map((c) => c.closest("tr"));
    const val = marcadas.filter((tr) => Number(tr.dataset.fase) >= 4).length;
    $$("[data-aviso-val]").forEach((d) => {
      d.hidden = val === 0;
      $("[data-aviso-val-txt]", d).textContent = val === 1
        ? "1 das selecionadas está Validada: perde o Validado e volta para Conferir."
        : `${val} das selecionadas estão Validadas: perdem o Validado e voltam para Conferir.`;
    });
  });

  /* gaveta Espiar */
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-espiar]");
    if (!b) return;
    const d = JSON.parse(b.closest("tr").dataset.espia);
    $("#g-espia-t").textContent = d.nome;
    const regua = `<span class="regua" data-f="${d.fase}" role="img" aria-label="Fase ${d.fase} de 5">${"<i></i>".repeat(5)}</span>`;
    const passos = d.passos.map((p) =>
      `<li><span class="st st-${p.ok ? "ok" : "pend"}" role="img" aria-label="${p.ok ? "Pronto" : "Pendente"}">${ico(p.ok ? "ok" : "aberto")}</span>` +
      `<a class="txt" href="${d.href}#${p.id}">${esc(p.nome)}</a><small>${p.ok ? "Pronto" : "Pendente"}</small></li>`).join("");
    const pend = d.pend.length
      ? `<div class="esp-chips">${d.pend.map((t) => `<span class="tag tag-alerta">${esc(t)}</span>`).join("")}</div>`
      : `<p class="mudo">Nenhuma pendência.</p>`;
    const nota = d.editando ? `<p class="aviso aviso-alerta" style="display:flex;gap:8px">${ico("cadeado")}<span>${esc(d.editando)} está editando. Você abre em somente leitura.</span></p>` : "";
    const val = d.validada ? `<p class="mudo">Validada por ${esc(d.validada)}.</p>` : "";
    $("#esp-corpo").innerHTML =
      `<div class="esp-fase">${regua}<span>${esc(d.faseNome)}</span></div>${nota}${val}` +
      `<div class="esp-sec"><h3>Passos</h3><ul class="checklist">${passos}</ul></div>` +
      `<div class="esp-sec"><h3>Pendências</h3>${pend}</div>`;
    $("#esp-abrir").setAttribute("href", d.href);
    $("#esp-preview").setAttribute("href", d.href + "#conferir");
  });
})();


(() => {
  const lista = document.querySelector("[data-secoes]");
  if (!lista) return;
  const btns = [...lista.querySelectorAll("[data-sec]")];
  const mostra = (id) => {
    btns.forEach((b) => b.setAttribute("aria-current", String(b.dataset.sec === id)));
    document.querySelectorAll("[data-sec-p]").forEach((p) => { p.hidden = p.dataset.secP !== id; });
  };
  btns.forEach((b) => b.addEventListener("click", () => mostra(b.dataset.sec)));
})();


(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* Cortes: 1 a 4 inteiros crescentes, abaixo da escala máxima. Valida antes do autosave/impacto. */
  function checaCortes(el) {
    const t = el.value.trim();
    if (!t) return { ok: true, vals: [] };
    const partes = t.split(",").map((s) => s.trim());
    if (partes.length > 4) return { ok: false, msg: `${partes.length} cortes passam do limite de 4. Apague os que sobram.` };
    if (!partes.every((p) => /^\d+$/.test(p))) return { ok: false, msg: "use só números inteiros separados por vírgula, como 150, 175, 200." };
    const v = partes.map(Number);
    for (let i = 1; i < v.length; i++) if (v[i] <= v[i - 1]) return { ok: false, msg: `${v[i]} não é maior que ${v[i - 1]}. Os cortes precisam crescer.` };
    const max = Number(el.dataset.max || 0);
    if (max && v[v.length - 1] >= max) return { ok: false, msg: `${v[v.length - 1]} chega ao fim da escala (${max}). Use um valor menor.` };
    return { ok: true, vals: v };
  }
  document.addEventListener("change", (e) => {
    const el = e.target;
    if (!el.matches || !el.matches("[data-corte]")) return;
    const r = checaCortes(el);
    el.classList.toggle("cel-erro", !r.ok);
    el.setAttribute("aria-invalid", String(!r.ok));
    if (!r.ok) { e.stopImmediatePropagation(); window.toast(`Cortes de ${el.dataset.rot} não gravados: ${r.msg}`); return; }
    if (r.vals.length) el.value = r.vals.join(", ");
  }, true);

  /* Células vazias: destaque e contagem ao vivo */
  function conta() {
    $$("[data-vazias]").forEach((w) => {
      const n = $$(w.dataset.vazias + ".cel-vazia").length;
      w.hidden = n === 0;
      const b = $("[data-n]", w);
      if (b) b.textContent = `${n} ${n === 1 ? w.dataset.um : w.dataset.varios}`;
    });
  }
  document.addEventListener("input", (e) => {
    const el = e.target;
    if (el.matches && el.matches("[data-vazio]")) { el.classList.toggle("cel-vazia", !el.value.trim()); conta(); }
    /* escala ao vivo (mesmo número de cortes) */
    const alvo = el.dataset && el.dataset.escalaAlvo;
    if (alvo) {
      const r = checaCortes(el), box = $(alvo);
      if (!box || !r.ok || !r.vals.length) return;
      const segs = $$(".esc-seg", box);
      if (segs.length !== r.vals.length + 1) return;
      const max = Number(box.dataset.max), pts = [0, ...r.vals, max];
      segs.forEach((s, k) => { s.style.flex = String(pts[k + 1] - pts[k]); s.title = s.title.replace(/:.*$/, `: ${pts[k]} a ${pts[k + 1]}`); });
      $$(".esc-rot span", box).forEach((sp, k) => { sp.style.left = (r.vals[k] / max * 100).toFixed(2) + "%"; sp.textContent = r.vals[k]; });
    }
    /* origem: "da matriz"/"do ano" x "sobrescrito/sobrescrita" */
    const cel = el.closest && el.closest("[data-origem-cel]");
    if (cel && el.matches("[data-origem]")) {
      const ov = $$("[data-origem]", cel).some((i) => i.value !== i.dataset.ano);
      $$("[data-so-ov],[data-voltar]", cel).forEach((x) => (x.hidden = !ov));
      $$("[data-so-base]", cel).forEach((x) => (x.hidden = ov));
    }
  });

  document.addEventListener("click", (e) => {
    const ir = e.target.closest("[data-ir-cel]");
    if (ir) {
      const alvo = $(ir.dataset.irCel);
      if (alvo) { alvo.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" }); setTimeout(() => alvo.focus({ preventScroll: true }), 350); }
      return;
    }
    /* conflito: sobrescrever o valor de quem gravou antes */
    const rt = e.target.closest("[data-conflito]");
    if (rt) {
      const td = rt.closest("td"), i = $("input", td);
      i.value = rt.dataset.conflito;
      i.classList.remove("cel-conflito"); i.removeAttribute("aria-invalid");
      td.classList.remove("td-conflito");
      const c = rt.closest(".conf"); if (c) c.remove();
      const av = $("[data-aviso-conflito]"); if (av) av.hidden = true;
      window.toast("Salvo: seu valor substituiu o de Elisa Prado.");
      i.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    /* copiar valores vazios de 2025 */
    if (e.target.closest("[data-copiar-2025]")) {
      let ok = 0, sem = 0, ultimo = null;
      $$(".cel-var.cel-vazia").forEach((i) => {
        if (i.dataset.v25) { i.value = i.dataset.v25; i.classList.remove("cel-vazia"); ok++; ultimo = i; } else sem++;
      });
      conta();
      if (ultimo) ultimo.dispatchEvent(new Event("change", { bubbles: true }));
      window.toast(ok ? `${ok} ${ok === 1 ? "valor copiado" : "valores copiados"} de 2025.` + (sem ? ` ${sem} ${sem === 1 ? "ficou vazio" : "ficaram vazios"}: não existiam em 2025.` : "") : "Nada para copiar: esses valores não existiam em 2025.");
      return;
    }
    /* voltar ao da matriz / do ano */
    const v = e.target.closest("[data-voltar]");
    if (v) {
      const cel = v.closest("[data-origem-cel]");
      $$("[data-origem]", cel).forEach((i) => { i.value = i.dataset.ano; i.dispatchEvent(new Event("input", { bubbles: true })); i.dispatchEvent(new Event("change", { bubbles: true })); });
      return;
    }
    /* renomear e desativar: preenche o diálogo com o nome da linha */
    const nm = e.target.closest("[data-nome-atual]");
    if (nm) {
      const n = nm.dataset.nomeAtual, i = $("#dlg-renomear input[name=nome]");
      if (i) i.value = n;
      $$("[data-nome-alvo]").forEach((el) => (el.textContent = n));
    }
    const it = e.target.closest(".menu-lista button, .menu-lista a");
    if (it) { const m = it.closest("details.menu"); if (m) m.removeAttribute("open"); }
  });
})();


(() => {
  /* menu de âncoras: marca a seção que está no topo */
  const nav = document.querySelector("[data-ancoras]");
  if (nav) {
    const links = [...nav.querySelectorAll("a")];
    const secoes = links.map((a) => document.querySelector(a.getAttribute("href")));
    const marca = () => {
      let i = 0;
      secoes.forEach((s, k) => { if (s && s.getBoundingClientRect().top <= 140) i = k; });
      if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) i = secoes.length - 1;
      links.forEach((a, k) => a.setAttribute("aria-current", String(k === i)));
    };
    window.addEventListener("scroll", marca, { passive: true });
    marca();
  }
  /* "Abrir": deixa o aviso aparecer antes de seguir para a próxima página */
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-atraso]");
    if (!a) return;
    e.preventDefault();
    setTimeout(() => { location.href = a.getAttribute("href"); }, 1100);
  });
})();


(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const ico = (n) => `<svg class="ic" aria-hidden="true" focusable="false"><use href="#i-${n}"/></svg>`;
  const pl = (n, s, p) => `${n} ${n === 1 ? s : (p || s + "s")}`;
  const sel = $("[data-perfil-sel]");

  /* Duplicar: o diálogo diz de qual matriz sai a cópia */
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-duplicar]");
    if (!b) return;
    const n = b.dataset.duplicar, i = $("#dup-nome"), o = $("#dup-origem");
    if (i) i.value = "Cópia de " + n;
    if (o) o.textContent = n;
  });

  /* Gaveta de versões abre por #versoes (vem do menu da lista) */
  const abreVersoes = () => { const d = $("#versoes"); if (d && location.hash === "#versoes" && !d.open) d.showModal(); };
  abreVersoes();
  window.addEventListener("hashchange", abreVersoes);

  /* ── Criar e importar / reimportar ─────────────────────────────────── */
  const imp = $("[data-importar]");
  if (imp) {
    const nome = $("#imp-nome"), matriz = $("#imp-matriz"), conf = $("#imp-confirma"), ir = $("#imp-ir"), falta = $("#imp-falta");
    const entrada = $("#imp-arquivo"), soltar = $("#imp-soltar"), erro = $("#imp-erro");
    let arquivo = "";
    const reimp = () => location.hash === "#reimportar";
    const opt = () => matriz.selectedOptions[0];
    const atualiza = () => {
      const r = reimp();
      $$("[data-so-modo]").forEach((el) => { el.hidden = el.dataset.soModo !== (r ? "reimp" : "novo"); });
      $$("[data-so-arq]").forEach((el) => { el.hidden = el.dataset.soArq !== (arquivo ? "com" : "sem"); });
      $("#imp-arq-ok").hidden = !arquivo;
      $("#imp-exemplo-p").hidden = !!arquivo;
      $("#imp-arq-nome").textContent = arquivo;
      const o = opt();
      $("#imp-conf-nome").textContent = o.dataset.nome;
      $("#sum-copia").textContent = o.dataset.nome;
      const rev = +o.dataset.rev, val = +o.dataset.val;
      $("#sum-rev").textContent = pl(rev, "revista");
      $("#sum-val").textContent = pl(val, "Validada");
      $("#sum-mecs").textContent = o.dataset.mecs + " etapas × componente";
      $("#sum-desc").textContent = o.dataset.desc + " descritores";
      $("#sum-nome").textContent = nome.value.trim() || "nova";
      const nomeOk = r ? conf.value.trim() === o.dataset.nome : nome.value.trim().length >= 3;
      const ok = nomeOk && !!arquivo;
      const passo1 = $('[data-passo="1"]'), passo2 = $('[data-passo="2"]');
      passo1.dataset.feito = String(r ? true : nome.value.trim().length >= 3);
      passo2.dataset.feito = String(!!arquivo);
      ir.setAttribute("aria-disabled", String(!ok));
      const f = [];
      if (!(r || nome.value.trim().length >= 3)) f.push("dar um nome");
      if (!arquivo) f.push("escolher o arquivo");
      if (r && !nomeOk) f.push("digitar o nome da matriz");
      falta.textContent = ok ? "" : "Falta: " + f.join(", ") + ".";
    };
    const aceita = (f) => {
      erro.hidden = true;
      if (!f) return;
      if (!/\.(pdf|xlsx)$/i.test(f.name)) { erro.textContent = "Formato não aceito: envie um PDF ou uma planilha XLSX."; erro.hidden = false; return; }
      if (f.size > 20 * 1024 * 1024) { erro.textContent = "Arquivo maior que 20 MB: reduza o PDF ou envie só as páginas da matriz."; erro.hidden = false; return; }
      arquivo = f.name + " · " + (f.size / 1048576).toFixed(1).replace(".", ",") + " MB";
      atualiza();
    };
    entrada.addEventListener("change", () => aceita(entrada.files[0]));
    ["dragenter", "dragover"].forEach((t) => soltar.addEventListener(t, (e) => { e.preventDefault(); soltar.classList.add("sobre"); }));
    ["dragleave", "drop"].forEach((t) => soltar.addEventListener(t, (e) => { e.preventDefault(); soltar.classList.remove("sobre"); }));
    soltar.addEventListener("drop", (e) => aceita(e.dataTransfer.files[0]));
    $("#imp-exemplo").addEventListener("click", () => { arquivo = "matriz-comunitaria-2027.xlsx · 4,2 MB"; atualiza(); });
    $("#imp-trocar").addEventListener("click", () => { arquivo = ""; entrada.value = ""; atualiza(); soltar.scrollIntoView({ block: "center" }); });
    [nome, conf, matriz].forEach((el) => el.addEventListener("input", atualiza));
    matriz.addEventListener("change", () => { conf.value = ""; atualiza(); });
    window.addEventListener("hashchange", atualiza);
    if (sel) sel.addEventListener("change", atualiza);
    atualiza();
  }

  /* ── Editor de template: seções, variáveis, pré-visualização, validação ─ */
  const mod = $("[data-modelo]");
  if (mod) {
    const VARS = JSON.parse(mod.dataset.vars), AMOSTRAS = JSON.parse(mod.dataset.amostras);
    const VAR = /\{\{\s*([a-z0-9_]+)\s*\}\}/gi;
    const salvar = $("#salvar-versao"), erroBox = $("#sv-erro"), erroTxt = $("#sv-erro-txt"), pv = $("#pv"), valida = $("#pv-valida"), parc = $("#pv-parceiro");
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const painelAtivo = () => $$("[data-painel]", mod).find((p) => !p.hidden) || $("[data-painel]", mod);
    const erros = (txt) => {
      const out = [], vistos = new Set();
      for (const m of txt.matchAll(VAR)) { if (!(m[1] in VARS) && !vistos.has(m[1])) { vistos.add(m[1]); out.push(m[1]); } }
      const a = (txt.match(/\{\{/g) || []).length, f = (txt.match(/\}\}/g) || []).length;
      if (a !== f) out.push(null);
      return out;
    };
    const textos = (p) => ({ t: $('[data-campo="titulo"]', p).value, x: $('[data-campo="texto"]', p).value });
    const msgErro = (k) => k === null
      ? "Há <b>{{</b> sem o <b>}}</b> correspondente. Feche a variável com <b>}}</b>."
      : `A variável <span class="var var-vazia">{{${esc(k)}}}</span> não existe. Escolha outra em “Variável…” ou peça a criação ao Admin do ano.`;
    const fmt = (txt, am) => {
      let h = esc(txt).replace(VAR, (_, k) => {
        if (!(k in VARS)) return `<span class="var var-vazia">{{${k}}}</span>`;
        const v = am[k];
        return v ? `<span class="var">${esc(v)}</span>` : `<span class="var var-vazia">{{${k}}} vazia</span>`;
      });
      h = h.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|[^*])\*(?!\*)(.+?)\*(?!\*)/g, "$1<em>$2</em>");
      return h.split(/\n{2,}/).filter((b) => b.trim()).map((b) => {
        const ls = b.split("\n");
        if (ls.every((l) => /^-\s+/.test(l))) return "<ul>" + ls.map((l) => "<li>" + l.replace(/^-\s+/, "") + "</li>").join("") + "</ul>";
        return "<p>" + ls.join("<br>") + "</p>";
      }).join("") || '<p class="mudo">(sem texto)</p>';
    };
    const marca = () => {
      let total = 0, primeiro = "";
      $$("[data-painel]", mod).forEach((p) => {
        const { t, x } = textos(p), e = [...erros(t), ...erros(x)];
        total += e.length;
        const id = p.dataset.painel, alvo = $(`[data-idx="${id}"]`, mod);
        if (e.length && !primeiro) primeiro = $(".chip-travado", p).textContent.trim();
        if (alvo) alvo.innerHTML = e.length
          ? `<span class="tag tag-erro">${pl(e.length, "erro")}</span>`
          : `<span class="st st-ok" title="Sem erros" role="img" aria-label="Sem erros">${ico("ok")}</span>`;
      });
      salvar.setAttribute("aria-disabled", String(total > 0));
      erroBox.hidden = total === 0;
      erroTxt.textContent = `${pl(total, "erro")}${primeiro ? " em " + primeiro : ""}: corrija para salvar`;
    };
    const desenha = () => {
      const p = painelAtivo(), { t, x } = textos(p), am = AMOSTRAS[parc.value];
      pv.innerHTML = `<h3>${fmt(t, am).replace(/^<p>|<\/p>$/g, "")}</h3>${fmt(x, am)}`;
      const es = [...erros(t), ...erros(x)];
      const vazias = [...new Set([...(t + " " + x).matchAll(VAR)].map((m) => m[1]).filter((k) => k in VARS && !am[k]))];
      let h = "";
      if (es.length) h += `<div class="aviso aviso-erro" role="status">${ico("alerta")}<div class="aviso-txt"><b>${pl(es.length, "erro")} nesta seção.</b><ul>${es.map((k) => "<li>" + msgErro(k) + "</li>").join("")}</ul></div></div>`;
      else h += `<div class="aviso aviso-ok" role="status">${ico("confirmado")}<div class="aviso-txt">Sem erros: todas as variáveis desta seção existem.</div></div>`;
      if (vazias.length) h += `<div class="aviso aviso-alerta" style="margin-top:8px" role="status">${ico("alerta")}<div class="aviso-txt">${vazias.map((k) => `<span class="var var-vazia">{{${k}}}</span>`).join(" ")} ${vazias.length === 1 ? "está vazia" : "estão vazias"} em ${esc(am.nome_parceiro)}: a frase sai incompleta na revista. <a href="parceiro-boa-terra.html">Preencher em Parceiros</a>.</div></div>`;
      valida.innerHTML = h;
    };
    let tempo;
    const agenda = () => { clearTimeout(tempo); tempo = setTimeout(() => { marca(); desenha(); }, 120); };
    mod.addEventListener("input", agenda);
    parc.addEventListener("change", desenha);
    mod.addEventListener("click", (e) => { if (e.target.closest("[data-aba]")) setTimeout(desenha, 0); });
    window.addEventListener("hashchange", () => setTimeout(desenha, 0));

    let alvo = null;
    mod.addEventListener("focusin", (e) => { if (e.target.matches("[data-campo]")) alvo = e.target; });
    const poe = (ta, ini, fim, novo) => {
      ta.setRangeText(novo, ini, fim, "end");
      ta.focus();
      ta.dispatchEvent(new Event("input", { bubbles: true }));
      ta.dispatchEvent(new Event("change", { bubbles: true }));
    };
    mod.addEventListener("click", (e) => {
      const b = e.target.closest("[data-fmt]");
      if (!b || b.disabled) return;
      const ta = $('[data-campo="texto"]', painelAtivo()), a = ta.selectionStart, z = ta.selectionEnd, s = ta.value.slice(a, z);
      if (b.dataset.fmt === "n") poe(ta, a, z, `**${s || "negrito"}**`);
      if (b.dataset.fmt === "i") poe(ta, a, z, `*${s || "itálico"}*`);
      if (b.dataset.fmt === "l") poe(ta, a, z, (s || "item").split("\n").map((l) => "- " + l.replace(/^-\s+/, "")).join("\n"));
    });
    mod.addEventListener("change", (e) => {
      const s = e.target.closest("[data-var-ins]");
      if (!s || !s.value) return;
      const p = painelAtivo(), ta = alvo && p.contains(alvo) ? alvo : $('[data-campo="texto"]', p);
      poe(ta, ta.selectionStart, ta.selectionEnd, `{{${s.value}}}`);
      s.value = "";
    });
    if (sel) sel.addEventListener("change", () => { setTimeout(marca, 0); });
    marca();
    desenha();
  }
})();


(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const plural = (n, um, varios) => n + " " + (n === 1 ? um : varios);
  /* troca o hash sem o navegador rolar até o painel */
  const marca = (rid) => { const y = window.scrollY; try { history.replaceState(null, "", "#" + rid); } catch (e) {} const volta = () => window.scrollTo(0, y); volta(); requestAnimationFrame(volta); setTimeout(volta, 60); };
  const sobe = () => { if (location.hash) window.addEventListener("load", () => setTimeout(() => window.scrollTo(0, 0), 0)); };
  const celular = () => window.matchMedia("(max-width: 960px)").matches;

  /* ── Entrega › Validar ─────────────────────────────────────────── */
  const val = $("[data-validar]");
  if (val) {
    const itens = $$(".en-item[data-rid]", val);
    const paineis = $$("[data-rev]", val);
    const barra = $(".en-barra");
    const feito = (i) => i.classList.contains("feito");
    const pendentes = () => itens.filter((i) => !feito(i));
    const nome = (i) => $(".nm", i).textContent;
    let atual = null;

    function contagens() {
      const n = pendentes().length;
      $$("[data-n-fila]", val).forEach((e) => (e.textContent = n));
      const aba = $('.abas a[aria-current="page"] .n');
      if (aba) aba.textContent = n;
      const m = $$("[data-marca]:checked", val).filter((c) => !feito(c.closest(".en-item"))).length;
      $$("[data-n-marcadas]").forEach((e) => (e.textContent = m));
    }
    function mostra(rid, url) {
      const item = itens.find((i) => i.dataset.rid === rid);
      if (!item) return;
      atual = item;
      const bt = $("[data-validar-prox]");
      if (bt && !document.body.classList.contains("so-leitura")) {
        bt.disabled = item.dataset.bloq === "1";
        bt.title = bt.disabled ? "Outra pessoa está editando esta revista; valide quando ela terminar" : "";
      }
      itens.forEach((i) => i.setAttribute("aria-current", String(i === item)));
      paineis.forEach((p) => (p.hidden = p.dataset.rev !== rid));
      $$("[data-atual]").forEach((e) => (e.textContent = nome(item)));
      if (barra) barra.hidden = false;
      if (url) {
        marca(rid);
        if (celular()) $(`[data-rev="${rid}"]`, val).scrollIntoView({ block: "start" });
      }
    }
    function fim() {
      atual = null;
      paineis.forEach((p) => (p.hidden = p.dataset.rev !== "fim"));
      itens.forEach((i) => i.setAttribute("aria-current", "false"));
      if (barra) barra.hidden = true;
    }
    function proxima() {
      const p = pendentes();
      if (!p.length) return null;
      const k = atual ? itens.indexOf(atual) : -1;
      return p.find((i) => itens.indexOf(i) > k) || p[0];
    }
    function valida(item) {
      item.classList.add("feito");
      const c = $("[data-marca]", item); c.checked = false; c.disabled = true;
      $(".en-estado", item).innerHTML = '<span class="tag tag-ok">Validada</span>';
      const r = $(".regua", item);
      r.dataset.f = "4"; r.setAttribute("aria-label", "Fase 4 de 5: Validada");
    }
    const vai = (i) => (i ? mostra(i.dataset.rid, true) : fim());

    val.addEventListener("click", (e) => {
      const a = e.target.closest(".en-nome");
      if (a) { e.preventDefault(); mostra(a.closest(".en-item").dataset.rid, true); }
    });
    document.addEventListener("click", (e) => {
      if (e.target.closest("[data-validar-prox]") && atual) {
        const v = atual; valida(v);
        const prox = proxima();
        window.toast(nome(v) + " validada");
        vai(prox); contagens();
      } else if (e.target.closest("[data-validar-marcadas]")) {
        const alvo = pendentes().filter((i) => $("[data-marca]", i).checked);
        if (!alvo.length) { window.toast("Marque ao menos uma revista na fila"); return; }
        $("[data-lote-lista]").innerHTML = alvo.map((i) => '<li><span class="txt">' + nome(i) + "</span></li>").join("");
        $("[data-lote-n]").textContent = plural(alvo.length, "revista marcada", "revistas marcadas");
        $("#dlg-lote").showModal();
      } else if (e.target.closest("[data-lote-ok]")) {
        const alvo = pendentes().filter((i) => $("[data-marca]", i).checked);
        alvo.forEach(valida);
        $("#dlg-lote").close();
        window.toast(plural(alvo.length, "revista validada", "revistas validadas"));
        if (atual && feito(atual)) vai(proxima());
        contagens();
      } else if (e.target.closest("[data-pular]")) {
        const prox = proxima();
        if (prox && prox !== atual) vai(prox);
        else window.toast("Não há outra revista pendente na fila");
      }
    });
    val.addEventListener("change", (e) => { if (e.target.matches("[data-marca]")) contagens(); });
    const inicial = () => { const h = location.hash.slice(1); return itens.find((i) => i.dataset.rid === h && !feito(i)) || pendentes()[0]; };
    window.addEventListener("hashchange", () => { const i = inicial(); if (i && location.hash.slice(1) === i.dataset.rid) mostra(i.dataset.rid, false); });
    const ini = inicial();
    if (ini) mostra(ini.dataset.rid, false);
    if (!celular()) sobe();
    contagens();
  }

  /* ── Entrega › Impresso ────────────────────────────────────────── */
  const imp = $("[data-impresso]");
  if (imp) {
    const itens = $$(".en-item[data-rid]", imp);
    const paineis = $$("[data-rev]", imp);
    const filtro = $("select[data-alvo='#fila-imp']");
    const ROT = { "": "Todas", atualizar: "Para atualizar", aguardando: "Aguardando Validado", dia: "Em dia" };
    const SIT = {
      atualizar: '<span class="tag tag-cobalto">Para atualizar</span>',
      aguardando: '<span class="tag tag-alerta">Aguardando Validado</span>',
      dia: '<span class="tag tag-ok">Em dia</span>',
    };
    let atual = null;
    const refiltra = () => filtro && filtro.dispatchEvent(new Event("change", { bubbles: true }));
    function recontar() {
      if (filtro) $$("option", filtro).forEach((o) => {
        const n = o.value ? itens.filter((i) => i.dataset.sit === o.value).length : itens.length;
        o.textContent = ROT[o.value] + " (" + n + ")";
      });
      const aba = $('.abas a[aria-current="page"] .n');
      if (aba) aba.textContent = itens.filter((i) => i.dataset.sit === "atualizar").length;
    }
    function mostra(rid, url) {
      const item = itens.find((i) => i.dataset.rid === rid);
      if (!item) return;
      atual = item;
      if (item.hidden && filtro) { filtro.value = item.dataset.sit; refiltra(); }
      itens.forEach((i) => i.setAttribute("aria-current", String(i === item)));
      paineis.forEach((p) => (p.hidden = p.dataset.rev !== rid));
      if (url) {
        marca(rid);
        if (window.matchMedia("(max-width: 960px)").matches) $(`[data-rev="${rid}"]`, imp).scrollIntoView({ block: "start" });
      }
    }
    imp.addEventListener("click", (e) => {
      const a = e.target.closest(".en-nome");
      if (a) { e.preventDefault(); mostra(a.closest(".en-item").dataset.rid, true); }
    });
    document.addEventListener("click", (e) => {
      const b = e.target.closest("[data-marcar]");
      if (!b || b.disabled) return;
      const p = b.closest("[data-rev]"), item = itens.find((i) => i.dataset.rid === p.dataset.rev);
      item.dataset.sit = "dia";
      $(".en-sit", item).innerHTML = SIT.dia;
      $$("[data-sit-tag]", p).forEach((t) => (t.innerHTML = SIT.dia));
      $$("[data-marcar], [data-leitura-imp]", p).forEach((t) => (t.hidden = true));
      const ok = $("[data-feito-msg]", p); if (ok) ok.hidden = false;
      window.toast($(".nm", item).textContent + " marcada como impressa");
      recontar(); refiltra();
      const prox = itens.find((i) => i.dataset.sit === "atualizar");
      if (prox) mostra(prox.dataset.rid, false);
    });
    const h = location.hash.slice(1);
    const ini = itens.find((i) => i.dataset.rid === h) || itens.find((i) => i.dataset.sit === "atualizar") || itens[0];
    if (filtro) { filtro.value = ini.dataset.sit; refiltra(); }
    mostra(ini.dataset.rid, false);
    if (!celular()) sobe();
    window.addEventListener("hashchange", () => { if (itens.some((i) => i.dataset.rid === location.hash.slice(1))) mostra(location.hash.slice(1), false); });
    recontar();
  }
})();


(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const norm = (s) => (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

  /* Entrar: mostra o erro junto do campo (hash #erro ou envio incompleto) */
  const fe = $("form[data-entrar]");
  if (fe) {
    const erro = $("#erro"), campos = $$("input", fe);
    const mostra = (on) => { erro.hidden = !on; campos.forEach((c) => c.setAttribute("aria-invalid", on ? "true" : "false")); };
    mostra(location.hash === "#erro");
    window.addEventListener("hashchange", () => mostra(location.hash === "#erro"));
    campos.forEach((c) => c.addEventListener("input", () => mostra(false)));
    fe.addEventListener("submit", (e) => {
      e.preventDefault();
      const [u, s] = campos;
      if (!u.value.trim() || !s.value || s.value === "errada") { mostra(true); (u.value.trim() ? s : u).focus(); return; }
      location.href = fe.dataset.ir;
    });
  }

  /* Definir senha: regras sempre visíveis, marcam ao digitar */
  const fs = $("form[data-senha]");
  if (fs) {
    const [a, b] = $$("input[type=password]", fs), botao = $("[data-definir]", fs), usuario = $("input[name=usuario]", fs).value;
    const regras = {
      min: (v) => v.length >= 10,
      numeros: (v) => v.length > 0 && !/^\d+$/.test(v),
      usuario: (v) => v.length > 0 && !norm(v).includes(norm(usuario.split(".")[0])),
      igual: (v, w) => v.length > 0 && v === w,
    };
    const confere = () => {
      let todas = true;
      $$("[data-regra]", fs).forEach((li) => {
        const ok = regras[li.dataset.regra](a.value, b.value);
        li.dataset.ok = String(ok);
        const st = $(".st", li); st.classList.toggle("st-ok", ok); st.classList.toggle("st-na", !ok);
        $("use", st).setAttribute("href", ok ? "#i-ok" : "#i-traco");
        $(".co-sr", li).textContent = ok ? "cumprida" : "pendente";
        if (!ok) todas = false;
      });
      botao.disabled = !todas;
    };
    a.addEventListener("input", confere); b.addEventListener("input", confere);
    fs.addEventListener("submit", (e) => { e.preventDefault(); if (!botao.disabled) location.href = fs.dataset.ir; });
    confere();
  }

  /* Novo usuário: sem senha inicial */
  const ss = $("[data-sem-senha]");
  if (ss) ss.addEventListener("change", () => {
    const c = $("input[name=senha_inicial]"); c.disabled = ss.checked; if (ss.checked) c.value = "";
  });

  /* Usuários: estado vazio da busca (o filtro em si vem do app.js) */
  const tu = $("#tab-usuarios");
  if (tu) {
    const vazio = $("#usuarios-vazio");
    const atualiza = () => setTimeout(() => { const n = $$("tr[data-busca]", tu).filter((r) => !r.hidden).length; vazio.hidden = n > 0; tu.closest(".tab-caixa").hidden = n === 0; }, 0);
    document.addEventListener("input", (e) => { if (e.target.matches('[data-filtro="#tab-usuarios"]')) atualiza(); });
    document.addEventListener("change", (e) => { if (e.target.matches('[data-alvo="#tab-usuarios"]')) atualiza(); });
  }

  /* Excluir: o botão perigo só habilita quando o nome digitado bate */
  const cn = $("[data-confirma-nome]");
  if (cn) {
    const botao = $("[data-excluir]");
    cn.addEventListener("input", () => { botao.disabled = norm(cn.value) !== norm(cn.dataset.confirmaNome); });
    botao.addEventListener("click", () => { if (!botao.disabled) location.href = botao.dataset.excluir; });
  }
})();

