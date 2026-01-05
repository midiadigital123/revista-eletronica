// /**
//  * Esse arquivo contém funções específicar para renderizar cada parte da página.
//  * Ele recebe chamadas de construtores.js, o qual passa o HTML do componente e o tipo, depois consulta definicoes.js para obter os seletores, e então renderiza na página corretamente aquele componente. 
//  */

// import { buildRevista } from "./construtores.js";


// // const renderStandartPage = (selector) => {
// //     if (!selector) return;
// //     let html = buildPageStandartStructure();
// //     // Inserir no root
// //     selector.insertAdjacentHTML('afterbegin', html);
// // }

// export const renderRevista = (data, selector) => {
//     if (!selector) return;
//     let html = buildRevista(data)
//     // Inserir na revista content
//     selector.insertAdjacentHTML('afterbegin', html);

// }

// export const renderTitleNode = (html, selector) => {
//     console.log(html, selector)
//     if (!selector) return;
//     if (!html) return;
//     if (selector === false) return html;
//     selector.insertAdjacentHTML('afterbegin', html);
// }

// export const renderCentralNode = (html, selector) => {
//     if (!selector) return;
//     selector.insertAdjacentHTML('afterbegin', html);
// }

// export const renderLegendaProgressaoNode = (html, selector) => {
//     if (!selector) return;
//     selector.innerHTML = html;
// }

// export const renderLegendaAcertoNode = (html, selector) => {
//     if (!selector) return;
//     selector.innerHTML = html;
// }

// export const renderDescricaoHabilidadesNode = (html, selector) => {
//     if (!selector) return;
//     selector.innerHTML = html;
// }

// export const renderProgressaoHabilidadesNode = (html, selector) => {
//     if (!selector) return;
//     selector.innerHTML = html;
// }

// export const renderTarefasNivelNode = (html, selector) => {
//     if (!selector) return;
//     selector.innerHTML = html;
// }

// export const renderSerieHistoricaNode = (html, selector) => { 
//     if (!selector) return;
//     selector.innerHTML = html;
// }

// export const renderPercentualAcertoNode = (html, selector) => { 
//     if (!selector) return;
//     selector.innerHTML = html;
// }

