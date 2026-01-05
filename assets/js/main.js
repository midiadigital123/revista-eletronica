/**
 * Arquivo principal que inicializa a aplicação da revista eletrônica e orquestra tudo.
 * A ideia é que esse arquivo só chame funções de renderização, visto que, essas funções serão responsáveis por chamar os construtores, e esses, por sua vez, decidirão se será necessário ou não adaptar a estrutura HTML que eles consultares do arquivo de estruturas.
 */

import { getData } from "./busca.js";
import { pageStandartStructure } from "./estruturas.js";
import { SELECTORS } from "./definicoes.js";
import { renderStandartPage, renderRevista } from "./renderizadores.js";

document.addEventListener("DOMContentLoaded", async () => {
    
    const init = async () => {
     let result = await getData("https://recursos-moodle.caeddigital.net/projetos/dev/revista/data.json");
     console.log(result)
     let data = result;
     startRevista(data);
    }
    
    const startRevista = (data) => {
        // Renderize a estrutura padrão da página
        // Chama apenas a função de renderização informando onde deve ser renderizado. Essa função consultará a estrutura, construirá o HTML e renderizará na página.
        if (!SELECTORS.root) return;
        renderStandartPage(document.querySelector(SELECTORS.root));
        // Depois de renderizar a estrutura, constrói o conteúdo da revista
        renderRevista(data, document.querySelector(SELECTORS.revistaContent));
    }

    init();

});