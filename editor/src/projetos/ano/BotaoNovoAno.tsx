import { useState } from "react";
import { useNavigate } from "react-router";
import { ANOS, ROTULO_ANO, type Ano, type Projeto } from "../../contrato/schemas";
import { Aviso, Botao, Dialogo } from "../../ui";
import { Button } from "@/components/ui/button";
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
      <Button
        type="button"
        size="sm"
        variant="ghost"
        disabled={modo !== "edicao" || faltam.length === 0}
        onClick={() => {
          setErro(undefined);
          setAberto(true);
        }}
      >
        + Ano
      </Button>
      <Dialogo
        aberto={aberto}
        aoFechar={() => setAberto(false)}
        titulo="Novo ano"
        acoes={<Botao onClick={() => setAberto(false)}>Cancelar</Botao>}
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            O ano começa sem descritores, com a faixa e os cortes padrão. Dá para ajustar depois.
          </p>
          {/* Grade que cresce com o catálogo de etapas (N anos), sem largura fixa. */}
          <ul className="grid grid-cols-[repeat(auto-fill,minmax(7rem,1fr))] gap-2">
            {faltam.map((ano) => (
              <li key={ano}>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={() => void criar(ano)}
                >
                  {ROTULO_ANO[ano]}
                </Button>
              </li>
            ))}
          </ul>
          {erro && <Aviso tom="erro">{erro}</Aviso>}
        </div>
      </Dialogo>
    </>
  );
}
