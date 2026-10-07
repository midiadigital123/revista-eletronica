import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { chaves } from "../api/chaves";
import { useUsuario } from "../auth/useUsuario";
import type { Usuario } from "../contrato/schemas";
import { Aviso, Botao } from "../ui";
import { FormCriar, FormEditar } from "./Formularios";
import { ExcluirUsuario } from "./ExcluirUsuario";
import { usuariosApi } from "./api";

export function Usuarios() {
  const { data: eu } = useUsuario();
  const admin = eu?.perfil === "admin";
  const lista = useQuery({ queryKey: chaves.usuarios, queryFn: usuariosApi.listar, enabled: admin });
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
      <div className="flex items-end justify-between">
        <h1 className="text-3xl">Usuários</h1>
        <Botao variante="primario" onClick={() => setCriando(true)}>
          Novo usuário
        </Botao>
      </div>
      {lista.isError && <Aviso tom="erro">Não foi possível carregar os usuários.</Aviso>}
      {lista.isPending && <p role="status" className="text-sm text-tinta-suave">Carregando…</p>}
      {lista.data && (
        <div className="overflow-x-auto rounded-lg border border-linha bg-superficie">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Usuários cadastrados</caption>
            <thead className="border-b border-linha text-xs uppercase tracking-wide text-tinta-suave">
              <tr>
                <th scope="col" className="px-4 py-3">Nome</th>
                <th scope="col" className="px-4 py-3">E-mail</th>
                <th scope="col" className="px-4 py-3">Perfil</th>
                <th scope="col" className="px-4 py-3">Ativo</th>
                <th scope="col" className="px-4 py-3"><span className="sr-only">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              {lista.data.map((u) => (
                <tr key={u.id} className="border-b border-linha last:border-0">
                  <th scope="row" className="px-4 py-3 font-medium">{u.nome}</th>
                  <td className="px-4 py-3">{u.email}</td>
                  <td className="px-4 py-3">{u.perfil === "admin" ? "Administrador" : "Editor"}</td>
                  <td className="px-4 py-3">{u.ativo ? "Sim" : "Não"}</td>
                  <td className="flex justify-end gap-2 px-4 py-2">
                    <Botao tamanho="sm" aria-label={`Editar ${u.nome}`} onClick={() => setEditando(u)}>Editar</Botao>
                    <Botao tamanho="sm" variante="fantasma" aria-label={`Excluir ${u.nome}`} onClick={() => setExcluindo(u)}>Excluir</Botao>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <FormCriar aberto={criando} aoFechar={() => setCriando(false)} />
      <FormEditar usuario={editando} aoFechar={() => setEditando(null)} />
      <ExcluirUsuario usuario={excluindo} aoFechar={() => setExcluindo(null)} />
    </section>
  );
}
