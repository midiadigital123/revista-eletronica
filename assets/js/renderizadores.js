/**
 * Esse arquivo contém funções específicar para renderizar cada parte da página.
 * Ele recebe chamadas de construtores.js, o qual passa o HTML do componente e o tipo, depois consulta definicoes.js para obter os seletores, e então renderiza na página corretamente aquele componente. 
 */

import { buildPageStandartStructure, buildRevista } from "./construtores.js";


const renderStandartPage = (selector) => {
    if (!selector) return;
    let html = buildPageStandartStructure();
    // Inserir no root
    selector.innerHTML = html;

}

const renderRevista = (data, selector) => {
    if (!selector) return;
    let html = buildRevista(data)
    // Inserir no root
    selector.innerHTML = html;

}


export { renderStandartPage, renderRevista };