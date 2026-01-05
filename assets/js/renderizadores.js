/**
 * Esse arquivo contém funções específicar para renderizar cada parte da página.
 * Ele recebe chamadas de construtores.js, o qual passa o HTML do componente e o tipo, depois consulta definicoes.js para obter os seletores, e então renderiza na página corretamente aquele componente. 
 */

import { buildPageStandartStructure, buildRevista } from "./construtores.js";


const renderStandartPage = (selector) => {
    if (!selector) return;
    let html = buildPageStandartStructure();
    // Inserir no root
    selector.insertAdjacentHTML('afterbegin', html);
}

const renderRevista = (data, selector) => {
    if (!selector) return;
    let html = buildRevista(data)
    // Inserir na revista content
    selector.insertAdjacentHTML('afterbegin', html);

}

const renderTitleNode = (html, selector) => {
    console.log(html, selector)
    if (!selector) return;
    selector.insertAdjacentHTML('afterbegin', html);
}

const renderCentralNode = (html, selector) => {
    if (!selector) return;
    selector.insertAdjacentHTML('afterbegin', html);
}

const renderLegendaProgressaoNode = (html, selector) => {
    if (!selector) return;
    selector.innerHTML = html;
}

const renderLegendaAcertoNode = (html, selector) => {
    if (!selector) return;
    selector.innerHTML = html;
}

const renderDescricaoHabilidadesNode = (html, selector) => {
    if (!selector) return;
    selector.innerHTML = html;
}

const renderProgressaoHabilidadesNode = (html, selector) => {
    if (!selector) return;
    selector.innerHTML = html;
}

const renderTarefasNivelNode = (html, selector) => {
    if (!selector) return;
    selector.innerHTML = html;
}

const renderSerieHistoricaNode = (html, selector) => { 
    if (!selector) return;
    selector.innerHTML = html;
}

const renderPercentualAcertoNode = (html, selector) => { 
    if (!selector) return;
    selector.innerHTML = html;
}

export { renderStandartPage, renderRevista, renderTitleNode, renderCentralNode, renderLegendaProgressaoNode, renderLegendaAcertoNode, renderDescricaoHabilidadesNode, renderProgressaoHabilidadesNode, renderTarefasNivelNode, renderSerieHistoricaNode, renderPercentualAcertoNode };