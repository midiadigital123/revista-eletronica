import { useState } from "react";
import { Link } from "react-router";
import { FolderOpen, Lock, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Empty, EmptyContent, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ROTULO_ANO } from "../contrato/schemas";
import { useTituloPagina } from "../layout/useTituloPagina";
import { Aviso } from "../ui";
import { useProjetos } from "./consultas";
import { mensagemDeErro, tempoRelativo } from "./formato";
import { NovoProjeto } from "./NovoProjeto";

/** /projetos: lista com quem está editando cada projeto + "Novo projeto". */
export function ListaProjetos() {
  const { data: projetos, isPending, error } = useProjetos();
  const [criando, setCriando] = useState(false);
  const novo = () => setCriando(true);
  useTituloPagina("Projetos");

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold tracking-tight">Projetos</h1>
        <Button onClick={novo}>
          <Plus data-icon="inline-start" />
          Novo projeto
        </Button>
      </header>

      {isPending && (
        <div role="status" className="flex flex-col gap-2">
          <span className="sr-only">Carregando…</span>
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}
      {error && (
        <Aviso tom="erro">Não foi possível carregar os projetos: {mensagemDeErro(error)}</Aviso>
      )}
      {projetos?.length === 0 && (
        <Empty className="border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <FolderOpen />
            </EmptyMedia>
            <EmptyTitle>Nenhum projeto ainda</EmptyTitle>
          </EmptyHeader>
          <EmptyContent>
            <Button onClick={novo}>
              <Plus data-icon="inline-start" />
              Novo projeto
            </Button>
          </EmptyContent>
        </Empty>
      )}

      {projetos && projetos.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Projeto</TableHead>
              <TableHead>Anos</TableHead>
              <TableHead>Atualizado</TableHead>
              <TableHead>Situação</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {projetos.map((p) => (
              <TableRow key={p.slug} className="relative">
                <TableCell className="max-w-80">
                  <h2 className="truncate font-medium">
                    {/* after:inset-0 estende o link para a linha inteira. */}
                    <Link
                      to={`/projetos/${p.slug}`}
                      className="outline-none after:absolute after:inset-0 focus-visible:after:ring-3 focus-visible:after:ring-ring focus-visible:after:ring-inset"
                    >
                      {p.nome}
                    </Link>
                  </h2>
                  <p className="truncate text-muted-foreground">{p.slug}</p>
                </TableCell>
                <TableCell className="whitespace-normal">
                  <div className="flex flex-wrap gap-1">
                    {p.anos.map((ano) => (
                      <Badge key={ano} variant="secondary">
                        {ROTULO_ANO[ano]}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  atualizado {tempoRelativo(p.atualizadoEm)}
                </TableCell>
                <TableCell>
                  {p.bloqueio && (
                    <Badge variant="warning">
                      <Lock data-icon="inline-start" />
                      Em edição por {p.bloqueio.nome}
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <NovoProjeto aberto={criando} aoFechar={() => setCriando(false)} projetos={projetos ?? []} />
    </section>
  );
}
