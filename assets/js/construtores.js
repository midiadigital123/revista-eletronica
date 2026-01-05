/**
 * Esse arquivo concentras as funções responsáveis por construir cada parte da página.
 */

import {
  pageStandartStructure,
  destaqueStructure,
  linkStructure,
} from "./estruturas.js";
import { SELECTORS } from "./definicoes.js";

/**
 *
 * @param {Object} param0
 * @param {HTMLElement} param0.seletor - Seletor onde a estrutura padrão da página será inserida.
 * @param {string} param0.position - Posição onde a estrutura será inserida (padrão: 'afterbegin').
 *
 * Essa função constrói a estrutura padrão da página e a insere no seletor especificado.
 */
export const buildStandartPage = ({
  seletor: seletor,
  position: position = "afterbegin",
}) => {
  let html = pageStandartStructure();
  seletor.insertAdjacentHTML(position, html);
};

/**
 *
 * @param {Object} param0
 * @param {string} param0.tag - Tag HTML do elemento a ser construído.
 * @param {string} param0.className - Classe CSS do elemento a ser construído.
 * @param {string} param0.content - Conteúdo HTML do elemento a ser construído.
 * @returns {string} - HTML do elemento construído.
 *
 * Essa função constrói um elemento HTML genérico com a tag, classe e conteúdo especificados.
 */
const buildEl = ({ tag, className, content }) => {
  return `<${tag} class="${className}">${content}</${tag}>`;
};

/**
 * Essa função constrói o conteúdo completo da revista com base nos dados fornecidos e o insere no seletor especificado.
 *
 */

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
  insertEl({ selector, html: pageContent });
  adicionaClassesAoInfografico(BLOCOS);
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
  });
  return "";
};

const insertEl = ({ selector, position = "afterbegin", html }) => {
  selector.insertAdjacentHTML(position, html);
};

const adicionaClassesAoInfografico = (BLOCOS) => {
  const addDescricaoHabilidadesClass = (selector) => {
    const table = document.querySelector(selector);
    if (!table) return;

    const rows = table.querySelectorAll("tr");

    rows.forEach((row) => {
      row.classList.add("linha");
      const [colYear, colLetter, colDesc] = row.querySelectorAll("td");

      if (colYear) colYear.classList.add("col-anos");

      if (colLetter) {
        colLetter.classList.add("col-letra");
        const text = colLetter.textContent.trim();
        const specificClass = ["I", "A", "R"].includes(text)
          ? `col-${text}`
          : "col-C";
        colLetter.classList.add(specificClass);
      }

      if (colDesc) colDesc.classList.add("col-descricao");
    });
  };

  const addProgressaoHabilidadesClass = (selector) => {
    const table = document.querySelector(selector);
    if (!table) return;

    const rows = table.querySelectorAll("tr");

    rows.forEach((row, index) => {
      row.classList.add("linha");
      let cols = row.querySelectorAll("td");
      if (index === 0) {
        cols.forEach((col) => {
          col.classList.add("col-letra");
        });
      } else {
        cols.forEach((col) => {
          col.classList.add("col-letra");
          const text = col.textContent.trim();
          const specificClass = ["I", "A", "R"].includes(text)
            ? `col-${text}`
            : "col-C";
          col.classList.add(specificClass);
        });
      }
    });
  };

  const container = document.querySelector(SELECTORS.infografico);
  if (!container) return;
  BLOCOS.forEach((bloco) => {
    if (bloco.type === "infografico" && bloco.nodes) {
      bloco.nodes.forEach((node) => {
        const { id, className } = node;
        switch (id) {
          case "descricao-habilidades":
            addDescricaoHabilidadesClass(SELECTORS[id]);
            break;
          case "progressao-habilidades":
            addProgressaoHabilidadesClass(SELECTORS[id]);
            break;
          case "tarefas-nivel":
            // Implementar se necessário
            break;
          case "serie-historica":
            // Implementar se necessário
            break;
          case "percentual-acerto":
            // Implementar se necessário
            break;
          default:
            break;
        }
      });
    }
  });
};
