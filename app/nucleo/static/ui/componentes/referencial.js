// D-303: grade "Referencial por etapa" do infográfico (parciais/revista_infograficos.html). O elo entre duas
// etapas é o checkbox junta_* da de baixo, gravado pelo autosave; aqui só o desenho: a célula juntada some e a
// de cima cresce (grid-row span). A regra é a de infografico.grade_referencial, que entrega as spans iniciais.
// O número da linha vai em data-ref-linha, nunca em data-linha: esse o autosave reserva para a linha nova, e o
// checkbox virava uma "linha" sem campos dentro (o status ficava em "Salvando…" para sempre).
document.addEventListener("alpine:init", () => {
  "use strict";

  Alpine.data("referencial", () => ({
    init() {
      // "input": o Cancelar do modal de impacto volta o checkbox e avisa por input, não por change.
      const redesenhar = (e) => { if (e.target.matches("[data-junta]")) this.desenhar(); };
      this.$root.addEventListener("change", redesenhar);
      this.$root.addEventListener("input", redesenhar);
    },
    desenhar() {
      for (const col of ["marca", "habilidade"]) {
        let cabeca = null;
        let span = 0;
        const fechar = () => {
          if (!cabeca) return;
          cabeca.style.gridRow = `${cabeca.dataset.refLinha} / span ${span}`;
          cabeca.dataset.span = span;
        };
        for (const cel of this.$root.querySelectorAll(`.inf-ref-cel[data-coluna="${col}"]`)) {
          const elo = this.$root.querySelector(`[data-junta="${col}"][data-ref-linha="${cel.dataset.refLinha}"]`);
          if (elo && elo.checked && cabeca) {
            cel.hidden = true;
            cel.dataset.span = 0;
            span += 1;
          } else {
            fechar();
            cabeca = cel;
            span = 1;
            cel.hidden = false;
          }
        }
        fechar();
      }
    },
  }));
});
