// Botão "Arquivo do item" da tarefa abre o <dialog> dela (D-180). Esc e "Cancelar" fecham (nativo).
document.addEventListener("click", (e) => {
  const botao = e.target.closest("[data-dialogo]");
  if (botao) document.getElementById(botao.dataset.dialogo)?.showModal();
});
