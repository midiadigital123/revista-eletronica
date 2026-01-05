/**
 * Esse arquivo concentras as funções responsáveis por construir cada parte da página.
 */

import { pageStandartStructure, textStructure, destaqueStructure, linkStructure } from "./estruturas.js";

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
            // blocoHTML = buildInfografico(nodes);
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


export { buildPageStandartStructure, buildRevista };