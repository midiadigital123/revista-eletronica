/**
 * Esse arquivo serve para centralizar as definições(seletores) desse projeto.
 * Assim, caso algum seletor mude, basta alterar aqui.
 */

const SELECTORS = {
    root: "#root",
    infografico: ".infografico",
    revistaContent: ".revista-content",
    revistaContainer: "revista",
    'titulo-revista': '[data-node="titulo-revista"]',
    'descritor-destaque': '[data-node="descritor-destaque"]',
    'legenda-progressao': '[data-node="legenda-progressao"]',
    'legenda-acerto': '[data-node="legenda-acerto"]',
    'descricao-habilidades': '[data-node="descricao-habilidades"]',
    'progressao-habilidades': '[data-node="progressao-habilidades"]',
    'tarefas-nivel': '[data-node="tarefas-nivel"]',
    'serie-historica': '[data-node="serie-historica"]',
    'percentual-acerto': '[data-node="percentual-acerto"]',
};

export { SELECTORS };