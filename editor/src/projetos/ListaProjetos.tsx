import { useState } from "react";
import { Link } from "react-router";
import { ROTULO_ANO } from "../contrato/schemas";
import { Aviso, Botao } from "../ui";
import { useProjetos } from "./consultas";
import { mensagemDeErro, tempoRelativo } from "./formato";
import { NovoProjeto } from "./NovoProjeto";

export function Cadeado({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={`size-4 ${className}`} fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="7" width="10" height="7" rx="1.5" />
      <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" />
    </svg>
  );
}

/** /projetos: lista com quem está editando cada projeto + "Novo projeto". */
export function ListaProjetos() {
  const { data: projetos, isPending, error } = useProjetos();
  const [criando, setCriando] = useState(false);

  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-10">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-tinta pb-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-tinta-suave">Revista eletrônica</p>
          <h1 className="mt-1 text-4xl font-medium tracking-tight">Projetos</h1>
        </div>
        <Botao variante="primario" onClick={() => setCriando(true)}>
          Novo projeto
        </Botao>
      </header>

      {isPending && <p className="py-8 text-tinta-suave">Carregando projetos…</p>}
      {error && (
        <div className="py-6">
          <Aviso tom="erro">Não foi possível carregar os projetos: {mensagemDeErro(error)}</Aviso>
        </div>
      )}
      {projetos?.length === 0 && (
        <p className="py-10 text-tinta-suave">Nenhum projeto ainda. Crie o primeiro em “Novo projeto”.</p>
      )}

      {projetos && projetos.length > 0 && (
        <ul className="divide-y divide-linha">
          {projetos.map((p) => (
            <li key={p.slug}>
              <Link
                to={`/projetos/${p.slug}`}
                className="group grid gap-x-6 gap-y-1 py-5 sm:grid-cols-[1fr_auto] sm:items-center"
              >
                <div className="min-w-0">
                  <h2 className="truncate text-2xl leading-tight group-hover:text-acento">{p.nome}</h2>
                  <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-tinta-suave">
                    <span className="font-mono text-xs">{p.slug}</span>
                    <span aria-hidden="true">·</span>
                    <span className="flex gap-1.5">
                      {p.anos.map((ano) => (
                        <span key={ano} className="rounded-sm border border-linha px-1.5 font-mono text-xs text-tinta">
                          {ROTULO_ANO[ano]}
                        </span>
                      ))}
                    </span>
                    <span aria-hidden="true">·</span>
                    <span>atualizado {tempoRelativo(p.atualizadoEm)}</span>
                  </p>
                </div>
                {p.bloqueio ? (
                  <span className="inline-flex items-center gap-1.5 text-sm text-alerta">
                    <Cadeado />
                    Em edição por {p.bloqueio.nome}
                  </span>
                ) : (
                  <span className="text-sm text-tinta-suave opacity-0 transition-opacity group-hover:opacity-100" aria-hidden="true">
                    Abrir →
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}

      <NovoProjeto aberto={criando} aoFechar={() => setCriando(false)} projetos={projetos ?? []} />
    </section>
  );
}
