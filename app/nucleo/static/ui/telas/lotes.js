// Lotes (Escolher matriz / template): marcar todos, contador e prévia "→ nova" nas linhas marcadas.
// Por delegação no document: vale depois que o hx-post troca o form. A regra fica no servidor.
(() => {
  "use strict";

  const atualizar = (form) => {
    const caixas = [...form.querySelectorAll("input[name=alvos]")];
    const marcadas = caixas.filter((c) => c.checked).length;
    const todos = form.querySelector("[data-todos]");
    if (todos) {
      todos.checked = marcadas > 0 && marcadas === caixas.length;
      todos.indeterminate = marcadas > 0 && marcadas < caixas.length;
    }
    const contador = form.querySelector("[data-contador]");
    if (contador) contador.textContent = `${marcadas} selecionado(s)`;
    const escolhas = {};
    for (const s of form.querySelectorAll("[data-previa]")) {
      escolhas[s.dataset.previa] = s.value ? { valor: s.value, nome: s.selectedOptions[0].text } : null;
    }
    for (const c of caixas) {
      const tr = c.closest("tr");
      tr.setAttribute("aria-selected", c.checked);
      for (const td of tr.querySelectorAll("[data-atual]")) {
        const nova = escolhas[td.dataset.atual];
        const muda = c.checked && nova && nova.valor !== td.dataset.valor;
        const pula = td.hasAttribute("data-copias") || tr.hasAttribute("data-pulado");
        const alvo = td.querySelector("[data-novo]");
        alvo.hidden = !muda;
        alvo.textContent = muda ? `→ ${nova.nome}${pula ? " (será pulado)" : ""}` : "";
        alvo.classList.toggle("lote-pulado", Boolean(muda && pula));
      }
    }
  };

  document.addEventListener("change", (e) => {
    const form = e.target.closest("[data-lote]");
    if (!form) return;
    if (e.target.matches("[data-todos]")) {
      form.querySelectorAll("input[name=alvos]").forEach((c) => { c.checked = e.target.checked; });
    }
    atualizar(form);
  });
  const iniciar = () => document.querySelectorAll("[data-lote]").forEach(atualizar);
  document.addEventListener("DOMContentLoaded", iniciar);
  document.addEventListener("htmx:afterSettle", iniciar);
})();
