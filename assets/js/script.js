/**
 * Carrega os dados de um arquivo JSON e envia para a função loadData.
 */
async function getData() {
  const file =
    "https://recursos-moodle.caeddigital.net/projetos/dev/revista/data.json";
  try {
    const response = await fetch(file);

    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error(error.message);
  }
}

const SELECTORS = {
  revistaContainer: document.getElementById("revista"),
  tituloRevista: document.querySelector('[data-node="titulo-revista"]'),
    descritorDestaque: document.querySelector('[data-node="descritor-destaque"]'),
    legendaProgresso: document.querySelector('[data-node="legenda-progressao"]'),
    legendaAcerto: document.querySelector('[data-node="legenda-acerto"]'),
    descricaoHabilidades: document.querySelector('[data-node="descricao-habilidades"]'),
    progressaoHabilidades: document.querySelector('[data-node="progressao-habilidades"]'),
    tarefasNivel: document.querySelector('[data-node="tarefas-nivel"]'),
    serieHistorica: document.querySelector('[data-node="serie-historica"]'),
    percentualAcerto: document.querySelector('[data-node="percentual-acerto"]'),
};

const buildRevista = (data) => {
  let pageContent = "";

  const { fasciculo_conteudo } = data[0];
  const { TITLE, BLOCOS } = fasciculo_conteudo;
  const titleHTML = renderTitle(TITLE);
  const blocosHTML = BLOCOS.map((bloco) => renderBloco(bloco)).join("");
  console.log(blocosHTML)
  pageContent += titleHTML;
  pageContent += blocosHTML;
  renderPage(pageContent);
};

/**
 *  Renderizar página
 * - Título
 * - Blocos
 */

const renderTitle = (title) => {
  return `<h1>${title}</h1>`;
};

const renderBloco = (bloco) => {
  let blocoHTML = "";
  const { type, content, nodes } = bloco;
  console.log(type);
  switch (type) {
    case "texto":
      blocoHTML = content ? renderText(content) : "";
      break;
    case "destaque":
      blocoHTML = content ? renderDestaque(content) : "";
      break;
    case "link":
      blocoHTML = content ? renderLink(content) : "";
      break;
    case "infografico":
      blocoHTML = renderInfografico(nodes);
      break;
    default:
      blocoHTML = `<div>Unsupported content type</div>`;
  }

  return blocoHTML;
};

const renderText = (text) => {
  return text;
};

const renderDestaque = (destaque) => {
    let destaqueHTML = `<div class="destaque">${destaque}</div>`;
  return destaqueHTML;
};

const renderLink = (link) => {};

const renderInfografico = (infografico) => {
    console.log(infografico)
    infografico.map((node) => {
        const {id} = node;
        switch (id) {
            case "titulo-revista":
                renderTituloRevista(node, SELECTORS.tituloRevista);
                break;
            case "descritor-destaque":
                 renderDescritorDestaque(node, SELECTORS.descritorDestaque);
                break;
            case "legenda-progressao":
                 renderLegendaProgresso(node, SELECTORS.legendaProgresso);
                break;
            case "legenda-acerto":
                 renderLegendaAcerto(node, SELECTORS.legendaAcerto);
                break;
            case "descricao-habilidades": 
                 renderDescricaoHabilidades(node, SELECTORS.descricaoHabilidades);
                break;
            case "progressao-habilidades":
                 renderProgressaoHabilidades(node, SELECTORS.progressaoHabilidades);
                break;
            case "tarefas-nivel":
                 renderTarefasNivel(node, SELECTORS.tarefasNivel);
                break;
            case "serie-historica":
                 renderSerieHistorica(node, SELECTORS.serieHistorica);
                break;
            case "percentual-acerto":
                 renderPercentualAcerto(node, SELECTORS.percentualAcerto);
                break;
            default:
                break;
                
        }
    });
};

const renderDescricaoHabilidades = (node, container) => {
    const { content } = node;
    if (!content || !container) return;
    container.innerHTML = `${content}`;
}

const renderProgressaoHabilidades = (node, container) => {
    const { content } = node;
    if (!content || !container) return;
    container.innerHTML = `${content}`;
}

const renderTarefasNivel = (node, container) => {
    const { content } = node;
    if (!content || !container) return;
    container.innerHTML = `${content}`;
}

const renderPercentualAcerto = (node, container) => {
    const { content } = node;
    if (!content || !container) return;
    container.innerHTML = `${content}`;
}

const renderSerieHistorica = (node, container) => {
    const { content } = node;
    if (!content || !container) return;
    container.innerHTML = `${content}`;
}

const renderTituloRevista = (node, container) => {
    const { title } = node;
    if (!title || !container) return;
    console.log(container)
    container.innerHTML = `<h2>${title}</h2>`;
}

const renderDescritorDestaque = (node, container) => {
    const { title } = node;
    if (!title || !container) return;
    container.innerHTML = `<p>${title}</p>`;
}

const renderLegendaProgresso = (node, container) => {
    console.log(node, container)
    const { content } = node;
    if (!content || !container) return;
    container.innerHTML = `${content}`;
}

const renderLegendaAcerto = (node, container) => {
    console.log(node, container)
    const { content } = node;
    if (!content || !container) return;
    container.innerHTML = `${content}`;
}

const renderPage = (html) => {
  if (!SELECTORS.revistaContainer) return;
  SELECTORS.revistaContainer.innerHTML += html;
};

const init = async () => {
  buildRevista(await getData());
};

document.addEventListener("DOMContentLoaded", () => {
  init();
});
