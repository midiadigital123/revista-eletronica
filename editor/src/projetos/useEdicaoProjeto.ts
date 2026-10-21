import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import type { Projeto } from "../contrato/schemas";
import type { Edicao, EstadoSalvamento, OperacaoSalvamento } from "./edicao";
import { mensagemDeErro } from "./formato";
import { useBloqueio } from "./useBloqueio";

/** Escrita perdida por 423: mostrada para o usuário copiar. */
export interface NaoSalvo {
  id: number;
  descricao: string;
  valor?: string;
}

/**
 * Implementação de `Edicao` (edicao.tsx) para um projeto, mais o que só a casca
 * usa (faixas de modo leitura, não salvos, tentar de novo). O ProjetoLayout
 * chama este hook e entrega `edicao` ao EdicaoContext.
 */
export function useEdicaoProjeto(slug: string) {
  const queryClient = useQueryClient();
  const fila = useRef<Promise<unknown>>(Promise.resolve());
  const proximoId = useRef(0);
  const [salvamento, setSalvamento] = useState<EstadoSalvamento>({ status: "ocioso" });
  const [naoSalvos, setNaoSalvos] = useState<NaoSalvo[]>([]);
  /** Escritas que falharam (exceto 423), por descrição; a última falha de cada uma vale. */
  const [falhas, setFalhas] = useState<Map<string, { erro: string; repetir: () => void }>>(
    new Map(),
  );
  const emAndamento = useRef(0);

  const aguardarFila = useCallback(() => fila.current, []);
  const bloqueio = useBloqueio(slug, aguardarFila);
  const { perder } = bloqueio;

  const salvar = useCallback(
    <T>(operacao: OperacaoSalvamento<T>): Promise<T> => {
      const esquecerFalha = () =>
        setFalhas((m) => {
          if (!m.has(operacao.descricao)) return m;
          const copia = new Map(m);
          copia.delete(operacao.descricao);
          return copia;
        });
      const executar = async (): Promise<T> => {
        setSalvamento((s) => ({ ...s, status: "salvando", erro: undefined }));
        try {
          const resposta = await operacao.executar();
          const { aplicar } = operacao;
          if (aplicar)
            queryClient.setQueryData<Projeto>(
              chaves.projeto(slug),
              (p) => p && aplicar(p, resposta),
            );
          else await queryClient.invalidateQueries({ queryKey: chaves.projeto(slug) });
          esquecerFalha();
          setSalvamento({ status: "salvo", salvoEm: new Date() });
          return resposta;
        } catch (e) {
          if (ehErroApi(e, 423)) {
            perder(e.bloqueio ?? null);
            const id = ++proximoId.current;
            setNaoSalvos((l) => [
              ...l,
              { id, descricao: operacao.descricao, valor: operacao.valor },
            ]);
            esquecerFalha();
          } else {
            const falha = {
              erro: mensagemDeErro(e),
              repetir: () => void enfileirar().catch(() => undefined),
            };
            setFalhas((m) => new Map(m).set(operacao.descricao, falha));
          }
          setSalvamento({ status: "erro", erro: mensagemDeErro(e) });
          throw e;
        }
      };
      // Fila serial: cada escrita espera a anterior terminar (com sucesso ou não).
      const enfileirar = () => {
        emAndamento.current++;
        const resultado = fila.current.then(executar).finally(() => emAndamento.current--);
        fila.current = resultado.catch(() => undefined);
        return resultado;
      };
      return enfileirar();
    },
    [queryClient, slug, perder],
  );

  // Com falha pendente, um sucesso de outra escrita não pode mostrar "Salvo".
  const pendente = [...falhas.values()].at(-1);
  const estado: EstadoSalvamento = useMemo(
    () =>
      pendente && salvamento.status !== "salvando"
        ? { status: "erro", erro: pendente.erro }
        : salvamento,
    [pendente, salvamento],
  );

  const edicao: Edicao = useMemo(
    () => ({ slug, modo: bloqueio.modo, bloqueio: bloqueio.bloqueio, salvamento: estado, salvar }),
    [slug, bloqueio.modo, bloqueio.bloqueio, estado, salvar],
  );

  // Fechar a aba com escrita na fila, falha pendente ou campo editado sem blur
  // perde dados (o pagehide não espera a fila): pede confirmação ao navegador.
  const temFalhas = falhas.size > 0;
  useEffect(() => {
    let sujo = false;
    const editou = () => (sujo = true);
    const saiu = () => (sujo = false); // o blur do campo já enfileirou a escrita
    const avisar = (e: BeforeUnloadEvent) => {
      if (sujo || emAndamento.current > 0 || temFalhas) e.preventDefault();
    };
    window.addEventListener("input", editou);
    window.addEventListener("focusout", saiu);
    window.addEventListener("beforeunload", avisar);
    return () => {
      window.removeEventListener("input", editou);
      window.removeEventListener("focusout", saiu);
      window.removeEventListener("beforeunload", avisar);
    };
  }, [temFalhas]);

  return {
    edicao,
    inativo: bloqueio.inativo,
    tentarEditar: bloqueio.tentarEditar,
    naoSalvos,
    descartarNaoSalvo: (id: number) => setNaoSalvos((l) => l.filter((n) => n.id !== id)),
    /** Repete todas as escritas com falha pendente (exceto 423). */
    repetir: temFalhas ? () => falhas.forEach((f) => f.repetir()) : null,
  };
}
