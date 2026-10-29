// Editor de template no admin (widget EditorTexto, nucleo/admin/templates.py; D-123).
// "Inserir variável" põe {{nome}} no cursor; o preview chama a rota template_preview
// com debounce. O HTML do preview vem de texto.renderizar (o servidor já escapou);
// os erros de validação entram como texto.
(() => {
  "use strict";
  for (const caixa of document.querySelectorAll(".editor-template")) {
    const area = caixa.querySelector("textarea");
    const preview = caixa.querySelector(".editor-template-preview");
    const erros = caixa.querySelector(".editor-template-erros");
    const csrf = area.form.querySelector("[name=csrfmiddlewaretoken]").value;
    // No "adicionar" o fascículo ainda é um select; na edição vem fixo no data-.
    const select = document.getElementById("id_fasciculo");
    let pedido = 0;
    let espera;

    const atualizar = async () => {
      const meu = ++pedido;
      const dados = new FormData();
      dados.append("csrfmiddlewaretoken", csrf);
      dados.append("texto", area.value);
      dados.append("fasciculo", select ? select.value : caixa.dataset.fasciculo);
      try {
        const r = await fetch(caixa.dataset.preview, { method: "POST", body: dados, credentials: "same-origin" });
        if (meu !== pedido || !r.ok) return; // resposta velha ou erro: mantém o último preview
        const json = await r.json();
        preview.innerHTML = json.html;
        erros.replaceChildren(...json.erros.map((e) => Object.assign(document.createElement("li"), { textContent: e })));
      } catch {
        // Rede: o próximo input tenta de novo.
      }
    };
    const agendar = () => {
      clearTimeout(espera);
      espera = setTimeout(atualizar, 400);
    };

    caixa.querySelector(".editor-template-inserir").addEventListener("click", () => {
      if (area.readOnly) return;
      const nome = caixa.querySelector(".editor-template-variavel").value;
      area.setRangeText(`{{${nome}}}`, area.selectionStart, area.selectionEnd, "end");
      area.focus();
      agendar();
    });
    area.addEventListener("input", agendar);
    if (select) select.addEventListener("change", agendar);
    void atualizar();
  }

  // Tela de impacto: um envio só (o 2º "Confirmar" viraria versão duplicada; o servidor
  // também segura). Não desabilita o botão: botão desabilitado sai do POST (_confirmar).
  for (const form of document.querySelectorAll("form[data-envio-unico]")) {
    form.addEventListener("submit", (e) => {
      if (form.dataset.enviado) e.preventDefault();
      form.dataset.enviado = "1";
    });
    window.addEventListener("pageshow", () => delete form.dataset.enviado); // voltar pelo bfcache
  }
})();
