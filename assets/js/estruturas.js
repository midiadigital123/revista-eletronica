/**
 * Esse arquivo concentra as estruturas HTML que podem ser requeridas pelo arquivo construtores.js para cada parte da página.
 */



/**
 * 
 * Define a estrutura padrão da página, com as divs principais, containers e colunas.
 * Essa estrutura será renderizada primeiro, e depois o conteúdo da revista será inserido dentro dela.  
 */
export const pageStandartStructure = () => {
    return `
<div class="revista-container">
    <div class="row">
        <div class="col-10 revista-content mx-auto" >
        ${infograficoStructure()}
        </div>
    </div>
</div>
` 
}

/**
 * Todos os textos simples da página vem do Coda já com as tags HTML apropriadas, então aqui só retornamos o texto como está.
 * Talvez seja interessante remover esse função. !!!!!!!!
 */
export const textStructure = (text) => {
    return `${text}` 
}

export const titleNodeStructure = (title) => {
    return `<h1>${title}</h1>`;
}

export const centralNodeStructure
 = (title) => {
    return `<h1>${title}</h1>`;
}

/**
 * Tanto titleNodeStructure quanto centralNodeStructure fazem a mesma coisa, isto é, inserem em um par de tags h1 o texto passado como parâmetro.
 * A ideia de existir esse arquivo é para os casos onde é necessário uma estrutura mais complexa, com várias divs e classes. 
 * Não é o caso atualmente. Acredito que o melhor a fazer é levar esse par de tags h1 para o construtores.js e eliminar essas duas funções.
 */


/**
 * Serve para retornar a estrutura de destaque inserindo o texto passado como parâmetro dentro dela. 
 */
export const destaqueStructure = (text) => {
    return `<div class="destaque">${text}</div>` 
}

/**
 * Serve para retornar a estrutura do link inserindo o texto passado como parâmetro dentro dela. 
 */
export const linkStructure = (text) => {
    return `<div class="link">${text}</div>` 
}

/**
 * Define a estrutura do infográfico, com todas as divs necessárias para inserir os dados dinâmicos posteriormente.
 */
export const infograficoStructure = () => {
    return ` <div id="container-revista" class=" revista-bncc-tabela">
      <div id="titulo-revista" class="titulo1" data-node="titulo-revista"></div>

      <div id="node0" class="centro" data-type="central-node" data-node="descritor-destaque"></div>

      <div id="node1" class="tabela1 revista-bncc-tabela tp-1" data-type="table-node" data-node="descricao-habilidades"></div>

      <div id="node2" class="tabela2" data-type="table-node" data-node="progressao-habilidades"></div>

      <div id="caption1" class="legenda12" data-node="legenda-progressao">
      </div>
      
      <div id="node3" class="tabela3" data-type="table-node" data-node="tarefas-nivel">
      </div>
      <div id="node4" class="tabela4" data-type="table-node" data-node="serie-historica">
      </div>
      <div id="node5" class="tabela5" data-type="table-node" data-node="percentual-acerto">
      </div>
      <div id="caption2" class="legenda45" data-node="legenda-acerto">
      </div>
    </div>
    `
}

