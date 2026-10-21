import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { chaves } from "../api/chaves";
import { useUsuario } from "../auth/useUsuario";
import type { Usuario } from "../contrato/schemas";
import { Pencil, Trash2, UserPlus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useTituloPagina } from "../layout/useTituloPagina";
import { Aviso } from "../ui";
import { FormCriar, FormEditar } from "./Formularios";
import { ExcluirUsuario } from "./ExcluirUsuario";
import { usuariosApi } from "./api";

export function Usuarios() {
  const { data: eu } = useUsuario();
  const admin = eu?.perfil === "admin";
  const lista = useQuery({
    queryKey: chaves.usuarios,
    queryFn: usuariosApi.listar,
    enabled: admin,
  });
  useTituloPagina("Usuários");
  const [criando, setCriando] = useState(false);
  const [editando, setEditando] = useState<Usuario | null>(null);
  const [excluindo, setExcluindo] = useState<Usuario | null>(null);

  if (!admin)
    return (
      <Aviso tom="alerta">
        <strong>Acesso restrito.</strong> Apenas administradores gerenciam usuários.
      </Aviso>
    );

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-3xl font-semibold tracking-tight">Usuários</h1>
        <Button onClick={() => setCriando(true)}>
          <UserPlus data-icon="inline-start" />
          Novo usuário
        </Button>
      </div>
      {lista.isError && <Aviso tom="erro">Não foi possível carregar os usuários.</Aviso>}
      {lista.isPending && (
        <div role="status" className="flex flex-col gap-2">
          <span className="sr-only">Carregando…</span>
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      )}
      {lista.data && (
        <div className="rounded-lg border">
          <Table>
            <TableCaption className="sr-only">Usuários cadastrados</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead scope="col">Nome</TableHead>
                <TableHead scope="col">E-mail</TableHead>
                <TableHead scope="col">Perfil</TableHead>
                <TableHead scope="col">Situação</TableHead>
                <TableHead scope="col">
                  <span className="sr-only">Ações</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {lista.data.map((u) => (
                <TableRow key={u.id}>
                  <TableHead scope="row">{u.nome}</TableHead>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>
                    <Badge variant={u.perfil === "admin" ? "default" : "secondary"}>
                      {u.perfil === "admin" ? "Administrador" : "Editor"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{u.ativo ? "Ativo" : "Inativo"}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            size="icon"
                            variant="ghost"
                            aria-label={`Editar ${u.nome}`}
                            onClick={() => setEditando(u)}
                          >
                            <Pencil />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Editar nome, perfil e senha</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            size="icon"
                            variant="ghost"
                            aria-label={`Excluir ${u.nome}`}
                            onClick={() => setExcluindo(u)}
                          >
                            <Trash2 />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Excluir conta</TooltipContent>
                      </Tooltip>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
      <FormCriar aberto={criando} aoFechar={() => setCriando(false)} />
      <FormEditar usuario={editando} aoFechar={() => setEditando(null)} />
      <ExcluirUsuario usuario={excluindo} aoFechar={() => setExcluindo(null)} />
    </section>
  );
}
