import { anosDaRevista } from "../contrato/revista";
import {
  BLOQUEIO_TTL_MS,
  Revista,
  type AnoProjeto,
  type BloqueioPublico,
  type Pagina,
  type Usuario,
} from "../contrato/schemas";
import revistaFixture from "./revista.json";

/**
 * Banco em memória dos mocks MSW. Segue as regras do contrato (docs/contrato.md),
 * inclusive o bloqueio. Testes podem manipular `mockDb` diretamente e chamar
 * `resetarMockDb()` entre casos.
 */

export interface UsuarioMock extends Usuario {
  senha: string;
}

export interface BloqueioMock extends BloqueioPublico {
  sessaoEdicao: string;
}

export interface ProjetoMock {
  slug: string;
  nome: string;
  pagina: Pagina;
  anos: AnoProjeto[];
  bloqueio: BloqueioMock | null;
  criadoEm: string;
  atualizadoEm: string;
  imagens: Record<string, Blob>;
}

export const SENHA_MOCK = "senha1234";

function estadoInicial() {
  const agora = new Date().toISOString();
  const usuarios: UsuarioMock[] = [
    {
      id: "000000000000000000000001",
      email: "admin@exemplo.org",
      nome: "Admin",
      perfil: "admin",
      ativo: true,
      senha: SENHA_MOCK,
    },
    {
      id: "000000000000000000000002",
      email: "ana@exemplo.org",
      nome: "Ana",
      perfil: "editor",
      ativo: true,
      senha: SENHA_MOCK,
    },
    {
      id: "000000000000000000000003",
      email: "bia@exemplo.org",
      nome: "Bia",
      perfil: "editor",
      ativo: true,
      senha: SENHA_MOCK,
    },
  ];
  const revista = Revista.parse(revistaFixture);
  const projetos = new Map<string, ProjetoMock>([
    [
      "exemplo",
      {
        slug: "exemplo",
        nome: "Exemplo",
        pagina: { ...(revista.pagina ?? {}) } as Pagina,
        anos: anosDaRevista(revista),
        bloqueio: null,
        criadoEm: agora,
        atualizadoEm: agora,
        imagens: {},
      },
    ],
  ]);
  return {
    usuarios,
    projetos,
    /** Usuário logado (cookie de sessão simulado). Em dev com mocks começa logado como admin. */
    sessaoUsuarioId: null as string | null,
  };
}

export let mockDb = estadoInicial();

export function resetarMockDb(opcoes: { logadoComo?: string | null } = {}) {
  mockDb = estadoInicial();
  if (opcoes.logadoComo !== undefined) mockDb.sessaoUsuarioId = opcoes.logadoComo;
}

export const usuarioLogado = () => mockDb.usuarios.find((u) => u.id === mockDb.sessaoUsuarioId);

export function bloqueioPublico(projeto: ProjetoMock, agora = Date.now()): BloqueioPublico | null {
  const b = projeto.bloqueio;
  if (!b || Date.parse(b.expiraEm) <= agora) return null;
  return { usuarioId: b.usuarioId, nome: b.nome, desde: b.desde, expiraEm: b.expiraEm };
}

/** Simula outra pessoa editando o projeto (útil em testes do modo leitura). */
export function bloquearPorOutro(
  slug: string,
  nome = "Bia",
  usuarioId = "000000000000000000000003",
) {
  const projeto = mockDb.projetos.get(slug);
  if (!projeto) throw new Error(`Projeto ${slug} não existe no mock`);
  const agora = Date.now();
  projeto.bloqueio = {
    usuarioId,
    nome,
    sessaoEdicao: "outra-aba",
    desde: new Date(agora).toISOString(),
    expiraEm: new Date(agora + BLOQUEIO_TTL_MS).toISOString(),
  };
}
