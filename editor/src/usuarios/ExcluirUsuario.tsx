import { useMutation, useQueryClient } from "@tanstack/react-query";
import { chaves } from "../api/chaves";
import type { Usuario } from "../contrato/schemas";
import { Aviso, Confirmacao } from "../ui";
import { usuariosApi } from "./api";

export function ExcluirUsuario({ usuario, aoFechar }: { usuario: Usuario | null; aoFechar: () => void }) {
  const qc = useQueryClient();
  const excluir = useMutation({
    mutationFn: (id: string) => usuariosApi.excluir(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: chaves.usuarios });
      aoFechar();
    },
  });
  const fechar = () => {
    excluir.reset();
    aoFechar();
  };
  return (
    <Confirmacao
      aberto={usuario !== null}
      titulo="Excluir usuário"
      mensagem={
        <>
          Excluir <strong>{usuario?.nome}</strong> ({usuario?.email})? Esta ação não pode ser desfeita.
          {excluir.error && (
            <span className="mt-3 block">
              <Aviso tom="erro">{excluir.error.message}</Aviso>
            </span>
          )}
        </>
      }
      aoConfirmar={() => usuario && excluir.mutate(usuario.id)}
      aoCancelar={fechar}
    />
  );
}
