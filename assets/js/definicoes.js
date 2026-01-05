/**
 * Esse arquivo serve para centralizar as definições(seletores) desse projeto.
 * Assim, caso algum seletor mude, basta alterar aqui.
 */

const SELECTORS = {
    root: "#root",
    revistaContent: ".revista-content",
  revistaContainer: "revista",
  tituloRevista: '[data-node="titulo-revista"]',
    descritorDestaque: '[data-node="descritor-destaque"]',
    legendaProgresso: '[data-node="legenda-progressao"]',
    legendaAcerto: '[data-node="legenda-acerto"]',
    descricaoHabilidades: '[data-node="descricao-habilidades"]',
    progressaoHabilidades: '[data-node="progressao-habilidades"]',
    tarefasNivel: '[data-node="tarefas-nivel"]',
    serieHistorica: '[data-node="serie-historica"]',
    percentualAcerto: '[data-node="percentual-acerto"]',
};

export { SELECTORS };