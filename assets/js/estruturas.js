/**
 * Esse arquivo concentra as estruturas HTML que podem ser requeridas pelo arquivo construtores.js para cada parte da página.
 */


export const pageStandartStructure = () => {
    return `
<div class="revista-container">
    <div class="row">
        <div class="col-12 revista-content">
        
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



