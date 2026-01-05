/**
 * Esse arquivo concentras as funções responsáveis por construir cada parte da página.
 */

import {
  pageStandartStructure,
  destaqueStructure,
  linkStructure,
} from "./estruturas.js";
import { SELECTORS } from "./definicoes.js";


export const buildStandartPage = ({
  seletor: seletor,
  position: position = "afterbegin",
}) => {
  let html = pageStandartStructure();
  seletor.insertAdjacentHTML(position, html);
};

const buildEl = ({ tag, className, content }) => {
  return `<${tag} class="${className}">${content}</${tag}>`;
};

export const buildRevista = (data, selector) => {
  let pageContent = ``; // Armazena o conteúdo completo da página

  let TITULO = buildEl({
    tag: "h1",
    className: "titulo-revista",
    content: data[0].fasciculo_conteudo.TITLE,
  }); // Constrói o título da revista
  pageContent += TITULO;
  let BLOCOS = data[0].fasciculo_conteudo.BLOCOS; // Armazena os blocos de conteúdo da revista
  BLOCOS.forEach((bloco) => {
    pageContent += renderBloco(bloco);
  });
  selector.insertAdjacentHTML("afterbegin", pageContent);
};

const renderBloco = (bloco, selector) => {
  console.log(bloco);
  let blocoHTML = ``;
  const { type, content, nodes } = bloco;
  switch (type) {
    case "texto":
      blocoHTML = content ? content : ``;
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
};

const buildDestaque = (text) => {
  return destaqueStructure(text);
};

const buildLink = (text) => {
  return linkStructure(text);
};

const buildInfografico = (nodes) => {
  nodes.forEach((node) => {
    const { id, type, title, content } = node;
    buildNode(id, title, content);
  });
  return "";
};

const insertEl = ({ selector, position = "afterbegin", html }) => {
  selector.insertAdjacentHTML(position, html);
};

const buildNode = (id, title, content) => {
  const selector = document.querySelector(SELECTORS[id]);

  // Casos especiais: criam um elemento <h1>
  if (id === "titulo-revista" || id === "descritor-destaque") {
    insertEl({
      selector,
      html: buildEl({
        tag: "h1",
        className: id, // A className no original era igual ao id
        content: title,
      }),
    });
    return;
  }

  // Caso padrão: insere o conteúdo diretamente
  insertEl({
    selector,
    html: content,
  });
};