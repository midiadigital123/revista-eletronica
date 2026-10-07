import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import {
  BLOQUEIO_HEARTBEAT_MS,
  BLOQUEIO_INATIVIDADE_MS,
  type BloqueioPublico,
} from "../contrato/schemas";
import { projetosApi } from "./api";
import type { ModoEdicao } from "./edicao";

export interface EstadoBloqueio {
  modo: ModoEdicao;
  /** Quem detém o bloqueio quando estamos em leitura (null se ninguém/desconhecido). */
  bloqueio: BloqueioPublico | null;
  /** Saímos da edição por inatividade (BLOQUEIO_INATIVIDADE_MS sem interação). */
  inativo: boolean;
}

/**
 * Bloqueio de edição do projeto (docs/contrato.md, "Bloqueio de edição"):
 * POST ao montar, PUT a cada BLOQUEIO_HEARTBEAT_MS, DELETE no pagehide/unmount
 * e por inatividade. O pagehide não espera a fila: o aviso de beforeunload fica
 * em useEdicaoProjeto. `aguardarFila` resolve quando não há escrita pendente.
 */
export function useBloqueio(slug: string, aguardarFila: () => Promise<unknown>) {
  const queryClient = useQueryClient();
  const [estado, setEstado] = useState<EstadoBloqueio>({
    modo: "carregando",
    bloqueio: null,
    inativo: false,
  });

  // Último slug/modo, para o unmount saber se ainda detemos o bloqueio.
  const atual = useRef({ slug, modo: estado.modo });
  useEffect(() => {
    atual.current = { slug, modo: estado.modo };
  });

  /**
   * POST do bloqueio. `valido` (opcional) diz se o resultado ainda interessa: se o
   * efeito que pediu já acabou (inatividade, unmount), o resultado é descartado e
   * um bloqueio obtido é devolvido.
   */
  const adquirir = useCallback(async (alvo: string, valido: () => boolean = () => true) => {
    try {
      await projetosApi.adquirirBloqueio(alvo);
      if (!valido()) return void projetosApi.liberarBloqueio(alvo).catch(() => undefined);
      setEstado({ modo: "edicao", bloqueio: null, inativo: false });
    } catch (e) {
      if (!valido()) return;
      setEstado({
        modo: "leitura",
        bloqueio: ehErroApi(e, 423) ? (e.bloqueio ?? null) : null,
        inativo: false,
      });
    }
  }, []);

  const recarregarProjeto = useCallback(
    (alvo: string) => queryClient.invalidateQueries({ queryKey: chaves.projeto(alvo) }),
    [queryClient],
  );

  /** Perdemos o bloqueio (423 numa escrita): leitura + projeto recarregado do servidor. */
  const perder = useCallback(
    (bloqueio: BloqueioPublico | null) => {
      setEstado({ modo: "leitura", bloqueio, inativo: false });
      void recarregarProjeto(atual.current.slug);
    },
    [recarregarProjeto],
  );

  /** "Tentar editar" / "Voltar a editar": recarrega o projeto e só então pede o bloqueio. */
  const tentarEditar = useCallback(async () => {
    await recarregarProjeto(atual.current.slug);
    await adquirir(atual.current.slug);
  }, [adquirir, recarregarProjeto]);

  // Entrada: adquire uma vez por montagem. Renomear o slug não readquire (o bloqueio
  // acompanha o projeto). O POST é idempotente para esta aba (StrictMode monta 2x).
  // `montado` é ref (não `let` do efeito) para o remonte do StrictMode não liberar
  // o bloqueio que a 2ª montagem quer; se sairmos antes do POST responder, o
  // `adquirir` devolve o bloqueio obtido.
  // Saída: só libera se de fato detemos o bloqueio, depois da fila de escrita.
  const montado = useRef(false);
  useEffect(() => {
    montado.current = true;
    void adquirir(atual.current.slug, () => montado.current);
    return () => {
      montado.current = false;
      const { slug: alvo, modo } = atual.current;
      if (modo === "edicao")
        void aguardarFila().finally(() => {
          if (!montado.current)
            void projetosApi.liberarBloqueio(alvo, { keepalive: true }).catch(() => undefined);
        });
    };
  }, [adquirir, aguardarFila]);

  // Enquanto editamos: heartbeat, pagehide e inatividade. Um só efeito para que
  // `ativo` impeça o heartbeat de readquirir o bloqueio que a inatividade liberou.
  useEffect(() => {
    if (estado.modo !== "edicao") return;
    let ativo = true;

    const renovar = async () => {
      try {
        await projetosApi.renovarBloqueio(slug);
      } catch (e) {
        // PUT nunca readquire: recarrega o projeto e tenta o POST (que decide o modo).
        if (!ehErroApi(e, 423) || !ativo) return; // rede/5xx: o TTL dá margem para o próximo ciclo
        await recarregarProjeto(slug);
        if (ativo) await adquirir(slug, () => ativo);
      }
    };
    const intervalo = setInterval(() => void renovar(), BLOQUEIO_HEARTBEAT_MS);

    const aoSair = () =>
      void projetosApi.liberarBloqueio(slug, { keepalive: true }).catch(() => undefined);

    // Sem keydown/pointerdown por BLOQUEIO_INATIVIDADE_MS → termina a fila de salvamento e libera.
    let inatividade: ReturnType<typeof setTimeout> | undefined;
    const expirar = async () => {
      await aguardarFila();
      if (!ativo) return;
      ativo = false;
      clearInterval(intervalo);
      await projetosApi.liberarBloqueio(slug).catch(() => undefined);
      setEstado({ modo: "leitura", bloqueio: null, inativo: true });
    };
    const reiniciar = () => {
      clearTimeout(inatividade);
      inatividade = setTimeout(() => void expirar(), BLOQUEIO_INATIVIDADE_MS);
    };
    reiniciar();

    window.addEventListener("pagehide", aoSair);
    window.addEventListener("keydown", reiniciar);
    window.addEventListener("pointerdown", reiniciar);
    return () => {
      ativo = false;
      clearInterval(intervalo);
      clearTimeout(inatividade);
      window.removeEventListener("pagehide", aoSair);
      window.removeEventListener("keydown", reiniciar);
      window.removeEventListener("pointerdown", reiniciar);
    };
  }, [estado.modo, slug, adquirir, recarregarProjeto, aguardarFila]);

  return { ...estado, perder, tentarEditar };
}
