// Comportamentos comuns das páginas próprias (opção B). Sem dependência; o HTMX é opcional aqui.
// Referência: docs/telas/design-system.md.
(() => {
  "use strict";

  // Toast curto (erro de rede/servidor do HTMX ou chamado pela página: uiToast("texto", "erro")).
  const toast = (texto, tipo = "") => {
    const area = document.getElementById("toasts");
    if (!area) return;
    const item = document.createElement("div");
    item.className = `toast${tipo ? ` toast-${tipo}` : ""}`;
    item.setAttribute("role", tipo === "erro" ? "alert" : "status");
    item.textContent = texto;
    area.append(item);
    setTimeout(() => item.remove(), 6000);
  };
  window.uiToast = toast;

  // HTMX não troca o alvo em 4xx/5xx: avisa causa + correção.
  document.addEventListener("htmx:responseError", (e) => {
    const s = e.detail.xhr.status;
    toast(
      s === 403
        ? "Não feito: sem permissão ou a sessão expirou. Recarregue a página e entre de novo."
        : `Não feito: o servidor respondeu ${s}. Recarregue a página e tente de novo.`,
      "erro",
    );
  });
  document.addEventListener("htmx:sendError", () => {
    toast("Não feito: sem conexão com o servidor. Confira a rede e tente de novo.", "erro");
  });

  document.addEventListener("click", (e) => {
    // <button data-abrir="id-do-dialog"> abre o <dialog> modal; [data-fechar] dentro dele fecha.
    const abrir = e.target.closest("[data-abrir]");
    if (abrir) document.getElementById(abrir.dataset.abrir)?.showModal();
    const fechar = e.target.closest("dialog [data-fechar]");
    if (fechar) fechar.closest("dialog").close();

    // <button data-copiar="#id-do-campo"><span role="status">rótulo</span></button>: copia o valor do campo;
    // sem área de transferência (http, navegador antigo), seleciona o texto para o Ctrl+C.
    const copiar = e.target.closest("[data-copiar]");
    const campo = copiar && document.querySelector(copiar.dataset.copiar);
    if (campo) {
      const rotulo = copiar.querySelector("span") || copiar;
      const selecionar = () => { campo.focus(); campo.select(); rotulo.textContent = "Selecionado: use Ctrl+C"; };
      const p = navigator.clipboard?.writeText(campo.value);
      p ? p.then(() => { rotulo.textContent = "Copiado"; copiar.dataset.copiado = ""; }, selecionar) : selecionar();
    }
  });

  // Lista + detalhe: link de <nav data-lista> com hx-get troca o detalhe; o link fica ativo
  // (aria-current) e o foco vai ao título do detalhe novo, sem ler o detalhe inteiro.
  document.addEventListener("htmx:afterSwap", (e) => {
    const link = e.detail.requestConfig?.elt;
    const lista = link?.closest?.("[data-lista]");
    if (!lista) return;
    lista.querySelectorAll("[aria-current]").forEach((x) => x.removeAttribute("aria-current"));
    link.setAttribute("aria-current", "page");
    const titulo = e.detail.target.querySelector("h1, h2, h3");
    if (titulo) { titulo.tabIndex = -1; titulo.focus(); }
  });

  // Confirmação forte: <input data-confirmar="texto exato"> libera o botão [data-confirmado] do form.
  // A regra fica no servidor (o form confere o texto); isto só evita o envio por engano.
  const conferir = (campo) => {
    const ok = campo.value.trim() === campo.dataset.confirmar;
    campo.form?.querySelectorAll("[data-confirmado]").forEach((b) => { b.disabled = !ok; });
  };
  document.addEventListener("input", (e) => {
    if (e.target.matches?.("[data-confirmar]")) conferir(e.target);
  });
  const iniciar = (raiz) => raiz.querySelectorAll?.("[data-confirmar]").forEach(conferir);
  document.addEventListener("DOMContentLoaded", () => iniciar(document));
  document.addEventListener("htmx:load", (e) => iniciar(e.target));
})();
