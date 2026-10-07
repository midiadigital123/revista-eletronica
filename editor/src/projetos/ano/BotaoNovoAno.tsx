import { useState } from "react";
import { useNavigate } from "react-router";
import { ANOS, ROTULO_ANO, type Ano, type Projeto } from "../../contrato/schemas";
import { Aviso, Botao, Dialogo } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { caminhoAno, mensagemDeErro, trocarAnos } from "./dados";

/**
 * Botão "+ Ano" na barra de abas do projeto (renderizado por A6a no
 * ProjetoLayout). Oferece só os anos que faltam; cria com faixa e cortes padrão.
 */
export function BotaoNovoAno({ projeto }: { projeto: Projeto }) {
  const { slug, modo, salvar } = useEdicao();
  const navigate = useNavigate();
  const [aberto, setAberto] = useState(false);
  const [erro, setErro] = useState<string>();
  const faltam = ANOS.filter((a) => !projeto.anos.some((p) => p.ano === a));

  async function criar(ano: Ano) {
    try {
      await salvar({
        descricao: `Criar ano ${ROTULO_ANO[ano]}`,
        executar: () => projetosApi.criarAno(slug, { ano }),
        aplicar: (p, novo) => trocarAnos(p, (anos) => [...anos, novo]),
      });
      setAberto(false);
      navigate(caminhoAno(slug, ano));
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }

  return (
    <>
      <Botao
        tamanho="sm"
        variante="fantasma"
        disabled={modo !== "edicao" || faltam.length === 0}
        onClick={() => {
          setErro(undefined);
          setAberto(true);
        }}
      >
        + Ano
      </Botao>
      <Dialogo
        aberto={aberto}
        aoFechar={() => setAberto(false)}
        titulo="Novo ano"
        acoes={<Botao onClick={() => setAberto(false)}>Cancelar</Botao>}
      >
        <p className="mb-3 text-sm text-tinta-suave">
          O ano começa sem descritores, com a faixa e os cortes padrão. Dá para ajustar depois.
        </p>
        <ul className="flex flex-wrap gap-2">
          {faltam.map((ano) => (
            <li key={ano}>
              <Botao variante="primario" onClick={() => void criar(ano)}>
                {ROTULO_ANO[ano]}
              </Botao>
            </li>
          ))}
        </ul>
        {erro && (
          <div className="mt-3">
            <Aviso tom="erro">{erro}</Aviso>
          </div>
        )}
      </Dialogo>
    </>
  );
}
