/**
 * Esse arquivo concentra as estruturas HTML que podem ser requeridas pelo arquivo construtores.js para cada parte da página.
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

export const textStructure = (text) => {
    return `${text}` 
}

export const destaqueStructure = (text) => {
    return `<div class="destaque">${text}</div>` 
}

export const linkStructure = (text) => {
    return `<div class="link">${text}</div>` 
}

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

export const titleNodeStructure = (title) => {
    return `<h1>${title}</h1>`;
}

export const centralNodeStructure
 = (title) => {
    return `<h1>${title}</h1>`;
}

