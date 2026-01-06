/**
 * Esse arquivo concentras as funções responsáveis por construir cada parte da página.
 */

import {
  pageStandartStructure,
  destaqueStructure,
  linkStructure,
} from "./estruturas.js";
import { SELECTORS } from "./definicoes.js";

let colorScheme = {
  caption1: {},
  caption2: {}
};
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
  // Adiciona classes específicas às tabelas do infográfico
  adicionaClassesAoInfografico(BLOCOS);
};



const renderBloco = (bloco, selector) => {
 // console.log(bloco);
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

/**
 * Atualiza o objeto colorScheme com base nos dados da legenda
 */
const updateColorScheme = (data, targetKey, prefix) => {
  data.forEach((item, index) => {
    // Ex: colorScheme.caption1['l1-color1'] = 'red'
    colorScheme[targetKey][`${prefix}-color${index + 1}`] = item.color;
  });
};

const buildInfografico = (nodes) => {
  let shouldInjectStyles = false;

  nodes.forEach((node) => {
    const { id, title, content, captionData } = node;
    const selector = document.querySelector(SELECTORS[id]);

    if (!selector) return; // Segurança caso o seletor não exista

    // --- Lógica de Inserção de HTML ---
    const isSpecialCase = id === "titulo-revista" || id === "descritor-destaque";
    const htmlToInsert = isSpecialCase
      ? buildEl({ tag: "h1", className: id, content: title })
      : content;

    insertEl({ selector, html: htmlToInsert });

    // --- Lógica de Cores (Caption) ---
    if (captionData) {
      if (id === "legenda-progressao") {
        updateColorScheme(captionData, "caption1", "l1");
        shouldInjectStyles = true;
      } else if (id === "legenda-acerto") {
        updateColorScheme(captionData, "caption2", "l2");
        shouldInjectStyles = true;
      }
    }
  });

  // Otimização: Injeta as variáveis CSS apenas uma vez após processar todos os nós
  if (shouldInjectStyles) {
    injectCSSVariables();
  }

  return "";
};

/**
 * Injeta CSS Variables dinamicamente no :root
 * (Mantido a lógica original, removido apenas o log excessivo se desejado)
 */
const injectCSSVariables = () => {
  const root = document.documentElement;
  
  Object.keys(colorScheme).forEach((captionKey) => {
    const captionColors = colorScheme[captionKey];
    Object.keys(captionColors).forEach((varName) => {
      root.style.setProperty(`--${varName}`, captionColors[varName]);
    });
  });
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

  // const addSerieHistoricaClass = (selector) => {
  //   const table = document.querySelector(selector);
  //   if (!table) return;

  //   const rows = table.querySelectorAll("tr");

  //   rows.forEach((row, index) => {
  //     if (index === 0) {
  //       row.classList.add("header-row");
  //     } else{
  //       row.classList.add("data-row");
  //       let cols = row.querySelectorAll("td");
  //       cols.forEach((col) => {
  //         col.classList.add("data-col");
  //       });
  //     }
  //   });
  // } 

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
            //  addSerieHistoricaClass(SELECTORS[id]);
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
