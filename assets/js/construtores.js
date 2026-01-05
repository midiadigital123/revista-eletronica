/**
 * Esse arquivo concentras as funções responsáveis por construir cada parte da página.
 */

import { pageStandartStructure, textStructure, destaqueStructure, linkStructure, titleNodeStructure, centralNodeStructure  } from "./estruturas.js";
import { SELECTORS } from "./definicoes.js";
import { renderTitleNode, renderCentralNode, renderLegendaProgressaoNode, renderLegendaAcertoNode, renderDescricaoHabilidadesNode, renderProgressaoHabilidadesNode, renderTarefasNivelNode, renderSerieHistoricaNode, renderPercentualAcertoNode } from "./renderizadores.js";

const buildPageStandartStructure = () => {
    return pageStandartStructure();
}

const buildRevista = (data) => {
let pageContent = ``;
  
   let TITULO = data[0].fasciculo_conteudo.TITLE;
   let BLOCOS = data[0].fasciculo_conteudo.BLOCOS;
   pageContent += buildTitle(TITULO);
   BLOCOS.forEach(bloco => {
       pageContent += buildBloco(bloco);
   });
   return pageContent;
}

const buildTitle = (title) => {
    return `<h1>${title}</h1>`;
}

const buildBloco = (bloco) => {
    console.log(bloco)
    let blocoHTML = ``;
    const { type, content, nodes } = bloco;
    switch (type) {
        case "texto":
            blocoHTML = content ? buildText(content) : ``;
            break;
        case "destaque":
             blocoHTML = content ? buildDestaque(content) : ``;
            break;
        case "link":
             blocoHTML = content ? buildLink(content) : ``;
            break;
        case "infografico":
             blocoHTML = buildInfografico(nodes);
            break;
        default:
            blocoHTML = `<div>Unsupported content type</div>`;
    }
    return blocoHTML;
}

const buildText = (text) => {
    return textStructure(text);
}

const buildDestaque = (text) => {
    return destaqueStructure(text);
}

const buildLink = (text) => {
    return linkStructure(text);
}

const buildInfografico = (nodes) => {

    nodes.forEach(node => {
        const { id, type, title, content } = node;
        buildNode(id, type, title, content);
    });
    return ""
}

const buildNode = (id, type, title, content) => {
    switch (id){
        case "titulo-revista":
            renderTitleNode(buildTitleNode(title), document.querySelector(SELECTORS[id]));
            break;
        case "descritor-destaque":
            renderCentralNode(buildCentralNode(title), document.querySelector(SELECTORS[id]));
            break;
        case "legenda-progressao":
            renderLegendaProgressaoNode(content, document.querySelector(SELECTORS[id]));
            break;
        case "legenda-acerto":
            renderLegendaAcertoNode(content, document.querySelector(SELECTORS[id]));
            break;
        case "descricao-habilidades":
             renderDescricaoHabilidadesNode(content, document.querySelector(SELECTORS[id]));
            break;
        case "progressao-habilidades":
             renderProgressaoHabilidadesNode(content, document.querySelector(SELECTORS[id]));
            break;
        case "tarefas-nivel":
             renderTarefasNivelNode(content, document.querySelector(SELECTORS[id]));
            break;
        case "serie-historica":
             renderSerieHistoricaNode(content, document.querySelector(SELECTORS[id]));
            break;
        case "percentual-acerto":
             renderPercentualAcertoNode(content, document.querySelector(SELECTORS[id]));
            break;
    }

}

const buildTitleNode = (title) => {
    return titleNodeStructure(title);
}

const buildCentralNode = (title) => {
    return centralNodeStructure (title);
}

export { buildPageStandartStructure, buildRevista };