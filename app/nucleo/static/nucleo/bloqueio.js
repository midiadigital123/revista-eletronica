// Renovação do bloqueio de edição no change form do admin (BloqueioAdminMixin) e nas
// páginas próprias (ui_bloqueio.com_bloqueio, include ui/_componentes/bloqueio.html).
// Portado de editor/src/projetos/useBloqueio.ts: renova a cada 10 s (o bloqueio
// expira em 30 s), libera no pagehide e, se o servidor disser que perdemos o
// bloqueio (409, ou 403 por logout/CSRF), desliga o formulário (somente
// leitura, com o texto ainda copiável). Ao voltar a ficar visível, renova na
// hora: o navegador atrasa o setInterval de abas em segundo plano.
// A sessão da aba vem do servidor (gerada ao adquirir no GET); por isso não há
// crypto.randomUUID aqui (só existe em contexto seguro; o sistema roda em http).
(() => {
  "use strict";
  const campo = document.getElementById("bloqueio-sessao");
  if (!campo) return;
  const form = campo.form;
  const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;
  const { alvo, id, renovar: urlRenovar, liberar: urlLiberar } = campo.dataset;
  let enviando = false;
  let desligado = false;

  const dados = () => {
    const d = new FormData();
    d.append("csrfmiddlewaretoken", csrf);
    d.append("alvo", alvo);
    d.append("id", id);
    d.append("sessao", campo.value);
    return d;
  };

  const avisar = (texto) => {
    // ul.messagelist/li.error no admin; ul.mensagens/li.aviso.aviso-erro nas páginas B.
    let lista = document.querySelector("ul.messagelist, ul.mensagens");
    if (!lista) {
      lista = document.createElement("ul");
      lista.className = "messagelist mensagens";
      form.before(lista);
    }
    const item = document.createElement("li");
    item.className = "error aviso aviso-erro";
    item.setAttribute("role", "alert");
    item.textContent = texto;
    lista.append(item);
  };

  // readOnly (não disabled) para o texto continuar selecionável e copiável. Onde
  // readOnly não vale (select, checkbox, arquivo, botões), disabled.
  const SO_LEITURA = new Set(["text", "search", "url", "tel", "email", "password", "number", "date", "datetime-local", "time", "month", "week"]);
  const desligar = () => {
    if (desligado) return;
    desligado = true;
    clearInterval(intervalo);
    form.querySelectorAll("input, select, textarea, button").forEach((c) => {
      if (c.type === "hidden") return;
      if (c.tagName === "TEXTAREA" || (c.tagName === "INPUT" && SO_LEITURA.has(c.type))) c.readOnly = true;
      else c.disabled = true;
    });
    form.addEventListener("submit", (e) => e.preventDefault());
    avisar("Você perdeu o bloqueio de edição: o formulário ficou somente leitura. Copie o que precisar e recarregue a página.");
  };

  const renovar = async () => {
    if (desligado) return;
    try {
      const r = await fetch(urlRenovar, { method: "POST", body: dados(), credentials: "same-origin" });
      if (r.status === 409 || r.status === 403) desligar();
    } catch {
      // Rede: o TTL de 30 s dá margem para o próximo ciclo.
    }
  };
  const intervalo = setInterval(() => void renovar(), 10_000);

  // Ao enviar, o servidor confere e libera depois de salvar; liberar aqui criaria corrida.
  form.addEventListener("submit", () => {
    enviando = true;
  });
  // HTMX: todo pedido leva a sessão da aba (GET de fragmento e POST fora deste form); envio
  // por HTMX não sai da página, então o pagehide volta a liberar; desligado, nada sai.
  document.addEventListener("htmx:configRequest", (e) => {
    e.detail.parameters[campo.name] = campo.value;
  });
  document.addEventListener("htmx:afterRequest", () => {
    enviando = false;
  });
  document.addEventListener("htmx:confirm", (e) => {
    if (desligado) e.preventDefault();
  });
  window.addEventListener("pagehide", () => {
    if (!enviando) navigator.sendBeacon(urlLiberar, dados());
  });
  // Volta pelo bfcache: o envio anterior acabou; a renovação dirá se o bloqueio ainda é nosso.
  window.addEventListener("pageshow", (e) => {
    enviando = false;
    if (e.persisted) void renovar();
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") void renovar();
  });
})();
