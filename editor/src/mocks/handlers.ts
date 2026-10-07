import { http, HttpResponse, type HttpResponseResolver } from "msw";
import { ZodError } from "zod";
import { CAMPOS_PAGINA } from "../contrato/campos-pagina";
import { anosDaRevista, revistaDosAnos } from "../contrato/revista";
import {
  AtualizarAnoEntrada,
  AtualizarDescritorEntrada,
  AtualizarProjetoEntrada,
  AtualizarUsuarioEntrada,
  BLOQUEIO_TTL_MS,
  compararAnos,
  CriarAnoEntrada,
  CriarDescritorEntrada,
  CriarProjetoEntrada,
  CriarUsuarioEntrada,
  HEADER_SESSAO_EDICAO,
  IMAGEM_MAX_BYTES,
  IMAGEM_MIMES,
  LinhasPadrao,
  LoginEntrada,
  nomeArquivoImagem,
  PaginaPatch,
  ParamsAno,
  ParamsDescritor,
  ParamsPadrao,
  ParamsProjeto,
  problemasDoAno,
  type AnoProjeto,
  type ErroApi,
  type Pagina,
  type Problema,
  type Projeto,
  type ProjetoResumo,
  type Usuario,
} from "../contrato/schemas";
import { bloqueioPublico, mockDb, usuarioLogado, type ProjetoMock, type UsuarioMock } from "./db";

/**
 * Implementação em memória de TODAS as rotas de docs/contrato.md, com as mesmas
 * validações (schemas do contrato) e a mesma regra de bloqueio da API real.
 */

class ErroMock extends Error {
  constructor(
    readonly status: number,
    readonly corpo: ErroApi,
  ) {
    super(corpo.erro);
  }
}
const falha = (status: number, erro: string, extra: Omit<ErroApi, "erro"> = {}) => {
  throw new ErroMock(status, { erro, ...extra });
};
const invalido = (problemas: Problema[]) =>
  falha(400, problemas[0]?.erro ?? "Dados inválidos", {
    campo: problemas[0]?.campo,
    detalhes: problemas,
  });

/** Envolve um resolver: converte ErroMock/ZodError no formato ErroApi. */
const rota =
  (fn: HttpResponseResolver): HttpResponseResolver =>
  async (info) => {
    try {
      return await fn(info);
    } catch (e) {
      if (e instanceof ErroMock) return HttpResponse.json(e.corpo, { status: e.status });
      if (e instanceof ZodError)
        return invalido(
          e.issues.map((i) => ({ campo: i.path.join("."), erro: i.message })),
        ) as never;
      throw e;
    }
  };

const json = async (request: Request) => {
  try {
    return await request.json();
  } catch {
    return {};
  }
};

const semSenha = ({ senha: _s, ...u }: UsuarioMock): Usuario => u;

function exigirLogin(): UsuarioMock {
  const u = usuarioLogado();
  if (!u?.ativo) return falha(401, "Faça login para continuar");
  return u;
}
function exigirAdmin(): UsuarioMock {
  const u = exigirLogin();
  if (u.perfil !== "admin") return falha(403, "Acesso restrito a administradores");
  return u;
}
function obterProjeto(slug: string): ProjetoMock {
  const projeto = mockDb.projetos.get(slug);
  if (!projeto) return falha(404, "Projeto não encontrado");
  return projeto;
}
/** Regra do contrato: escrita só com bloqueio válido deste usuário + aba. */
function exigirBloqueio(request: Request, slug: string): ProjetoMock {
  const usuario = exigirLogin();
  const projeto = obterProjeto(slug);
  const b = projeto.bloqueio;
  const aba = request.headers.get(HEADER_SESSAO_EDICAO);
  const valido =
    b &&
    Date.parse(b.expiraEm) > Date.now() &&
    b.usuarioId === usuario.id &&
    b.sessaoEdicao === aba;
  if (!valido) {
    const atual = bloqueioPublico(projeto);
    return falha(
      423,
      atual ? `Projeto em edição por ${atual.nome}` : "Você não está editando este projeto",
      {
        bloqueio: atual,
      },
    );
  }
  return projeto;
}
const tocar = (projeto: ProjetoMock) => {
  projeto.atualizadoEm = new Date().toISOString();
};
const paraProjeto = (p: ProjetoMock): Projeto => ({
  slug: p.slug,
  nome: p.nome,
  pagina: p.pagina,
  anos: structuredClone(p.anos),
  bloqueio: bloqueioPublico(p),
  criadoEm: p.criadoEm,
  atualizadoEm: p.atualizadoEm,
});
const paraResumo = (p: ProjetoMock): ProjetoResumo => ({
  slug: p.slug,
  nome: p.nome,
  anos: p.anos.map((a) => a.ano),
  atualizadoEm: p.atualizadoEm,
  bloqueio: bloqueioPublico(p),
});
function obterAno(projeto: ProjetoMock, ano: string): AnoProjeto {
  const encontrado = projeto.anos.find((a) => a.ano === ano);
  if (!encontrado) return falha(404, "Ano não encontrado");
  return encontrado;
}
function validarAno(ano: AnoProjeto) {
  const problemas = problemasDoAno(ano);
  if (problemas.length) invalido(problemas);
}
function adquirir(request: Request, projeto: ProjetoMock, usuario: UsuarioMock) {
  const aba = request.headers.get(HEADER_SESSAO_EDICAO);
  if (!aba)
    return falha(400, `Header ${HEADER_SESSAO_EDICAO} ausente`, { campo: HEADER_SESSAO_EDICAO });
  const atual = bloqueioPublico(projeto);
  const meu =
    atual && projeto.bloqueio?.usuarioId === usuario.id && projeto.bloqueio.sessaoEdicao === aba;
  if (atual && !meu) falha(423, `Projeto em edição por ${atual.nome}`, { bloqueio: atual });
  const agora = Date.now();
  projeto.bloqueio = {
    usuarioId: usuario.id,
    nome: usuario.nome,
    sessaoEdicao: aba,
    desde: new Date(agora).toISOString(),
    expiraEm: new Date(agora + BLOQUEIO_TTL_MS).toISOString(),
  };
  return bloqueioPublico(projeto)!;
}

const P = "/api/projetos/:slug";
const D = `${P}/anos/:ano/descritores/:codigo`;

export const handlers = [
  // ---------- auth
  http.post(
    "/api/auth/login",
    rota(async ({ request }) => {
      const { email, senha } = LoginEntrada.parse(await json(request));
      const u = mockDb.usuarios.find((x) => x.email === email);
      if (!u || !u.ativo || u.senha !== senha) return falha(401, "E-mail ou senha incorretos");
      mockDb.sessaoUsuarioId = u.id;
      return HttpResponse.json(semSenha(u));
    }),
  ),
  http.post(
    "/api/auth/logout",
    rota(() => {
      mockDb.sessaoUsuarioId = null;
      return new HttpResponse(null, { status: 204 });
    }),
  ),
  http.get(
    "/api/auth/me",
    rota(() => HttpResponse.json(semSenha(exigirLogin()))),
  ),

  // ---------- usuários (admin)
  http.get(
    "/api/usuarios",
    rota(() => {
      exigirAdmin();
      return HttpResponse.json(mockDb.usuarios.map(semSenha));
    }),
  ),
  http.post(
    "/api/usuarios",
    rota(async ({ request }) => {
      exigirAdmin();
      const dados = CriarUsuarioEntrada.parse(await json(request));
      if (mockDb.usuarios.some((u) => u.email === dados.email))
        falha(409, "E-mail já cadastrado", { campo: "email" });
      const novo: UsuarioMock = {
        id: crypto.randomUUID().replace(/-/g, "").slice(0, 24),
        ativo: true,
        ...dados,
      };
      mockDb.usuarios.push(novo);
      return HttpResponse.json(semSenha(novo), { status: 201 });
    }),
  ),
  http.patch(
    "/api/usuarios/:id",
    rota(async ({ request, params }) => {
      exigirAdmin();
      const u = mockDb.usuarios.find((x) => x.id === params.id);
      if (!u) return falha(404, "Usuário não encontrado");
      const dados = AtualizarUsuarioEntrada.parse(await json(request));
      const deixaDeSerAdminAtivo =
        u.perfil === "admin" && (dados.perfil === "editor" || dados.ativo === false);
      const admins = mockDb.usuarios.filter((x) => x.perfil === "admin" && x.ativo);
      if (deixaDeSerAdminAtivo && admins.length === 1)
        falha(400, "É preciso manter ao menos um admin ativo");
      Object.assign(u, dados);
      return HttpResponse.json(semSenha(u));
    }),
  ),
  http.delete(
    "/api/usuarios/:id",
    rota(({ params }) => {
      const eu = exigirAdmin();
      const u = mockDb.usuarios.find((x) => x.id === params.id);
      if (!u) return falha(404, "Usuário não encontrado");
      if (u.id === eu.id) falha(400, "Você não pode excluir a própria conta");
      if (
        u.perfil === "admin" &&
        mockDb.usuarios.filter((x) => x.perfil === "admin" && x.ativo).length === 1
      )
        falha(400, "É preciso manter ao menos um admin ativo");
      mockDb.usuarios = mockDb.usuarios.filter((x) => x.id !== u.id);
      return new HttpResponse(null, { status: 204 });
    }),
  ),

  // ---------- página
  http.get(
    "/api/pagina/campos",
    rota(() => {
      exigirLogin();
      return HttpResponse.json(CAMPOS_PAGINA);
    }),
  ),

  // ---------- projetos
  http.get(
    "/api/projetos",
    rota(() => {
      exigirLogin();
      const lista = [...mockDb.projetos.values()].sort((a, b) =>
        a.nome.localeCompare(b.nome, "pt"),
      );
      return HttpResponse.json(lista.map(paraResumo));
    }),
  ),
  http.post(
    "/api/projetos",
    rota(async ({ request }) => {
      const usuario = exigirLogin();
      const { slug, nome, origem } = CriarProjetoEntrada.parse(await json(request));
      if (mockDb.projetos.has(slug))
        falha(409, "Já existe um projeto com esse identificador", { campo: "slug" });
      const agora = new Date().toISOString();
      let pagina: Pagina = {};
      let anos: AnoProjeto[];
      let imagens: Record<string, Blob> = {};
      if (origem.tipo === "copiar") {
        const base = obterProjeto(origem.de);
        pagina = structuredClone(base.pagina);
        anos = structuredClone(base.anos);
        imagens = { ...base.imagens };
      } else if (origem.tipo === "importar") {
        pagina = { ...(origem.revista.pagina ?? {}) } as Pagina;
        anos = anosDaRevista(origem.revista);
        anos.forEach(validarAno);
      } else {
        anos = CriarAnoEntrada.array()
          .parse(origem.anos.map((ano) => ({ ano })))
          .map((a) => ({ ...a, descritores: [] }));
      }
      const projeto: ProjetoMock = {
        slug,
        nome,
        pagina,
        anos,
        bloqueio: null,
        criadoEm: agora,
        atualizadoEm: agora,
        imagens,
      };
      mockDb.projetos.set(slug, projeto);
      adquirir(request, projeto, usuario);
      return HttpResponse.json(paraProjeto(projeto), { status: 201 });
    }),
  ),
  http.get(
    P,
    rota(({ params }) => {
      exigirLogin();
      return HttpResponse.json(paraProjeto(obterProjeto(ParamsProjeto.parse(params).slug)));
    }),
  ),
  http.patch(
    P,
    rota(async ({ request, params }) => {
      const { slug } = ParamsProjeto.parse(params);
      const projeto = exigirBloqueio(request, slug);
      const dados = AtualizarProjetoEntrada.parse(await json(request));
      if (dados.slug && dados.slug !== slug) {
        if (mockDb.projetos.has(dados.slug))
          falha(409, "Já existe um projeto com esse identificador", { campo: "slug" });
        mockDb.projetos.delete(slug);
        projeto.slug = dados.slug;
        mockDb.projetos.set(dados.slug, projeto);
      }
      if (dados.nome) projeto.nome = dados.nome;
      tocar(projeto);
      return HttpResponse.json(paraProjeto(projeto));
    }),
  ),
  http.delete(
    P,
    rota(({ request, params }) => {
      const { slug } = ParamsProjeto.parse(params);
      exigirBloqueio(request, slug);
      mockDb.projetos.delete(slug);
      return new HttpResponse(null, { status: 204 });
    }),
  ),
  http.get(
    `${P}/revista`,
    rota(({ params }) => {
      exigirLogin();
      const projeto = obterProjeto(ParamsProjeto.parse(params).slug);
      return HttpResponse.json(revistaDosAnos(projeto.anos, projeto.pagina));
    }),
  ),

  // ---------- bloqueio
  http.post(
    `${P}/bloqueio`,
    rota(({ request, params }) => {
      const usuario = exigirLogin();
      const projeto = obterProjeto(ParamsProjeto.parse(params).slug);
      return HttpResponse.json(adquirir(request, projeto, usuario), { status: 201 });
    }),
  ),
  http.put(
    `${P}/bloqueio`,
    rota(({ request, params }) => {
      const projeto = exigirBloqueio(request, ParamsProjeto.parse(params).slug);
      projeto.bloqueio!.expiraEm = new Date(Date.now() + BLOQUEIO_TTL_MS).toISOString();
      return HttpResponse.json(bloqueioPublico(projeto));
    }),
  ),
  http.delete(
    `${P}/bloqueio`,
    rota(({ request, params }) => {
      const usuario = exigirLogin();
      const projeto = obterProjeto(ParamsProjeto.parse(params).slug);
      const aba = request.headers.get(HEADER_SESSAO_EDICAO);
      if (projeto.bloqueio?.usuarioId === usuario.id && projeto.bloqueio.sessaoEdicao === aba)
        projeto.bloqueio = null;
      return new HttpResponse(null, { status: 204 });
    }),
  ),

  // ---------- página do projeto
  http.patch(
    `${P}/pagina`,
    rota(async ({ request, params }) => {
      const projeto = exigirBloqueio(request, ParamsProjeto.parse(params).slug);
      const patch = PaginaPatch.parse(await json(request));
      for (const [chave, valor] of Object.entries(patch)) {
        if (valor === undefined) continue;
        if (valor === null || valor === "" || (Array.isArray(valor) && valor.length === 0))
          delete projeto.pagina[chave];
        else projeto.pagina[chave] = valor;
      }
      tocar(projeto);
      return HttpResponse.json(projeto.pagina);
    }),
  ),
  http.get(
    `${P}/pagina/:chave/imagem`,
    rota(({ params }) => {
      exigirLogin();
      const imagem = obterProjeto(String(params.slug)).imagens[String(params.chave)];
      if (!imagem) return falha(404, "Imagem não encontrada");
      return new HttpResponse(imagem, { headers: { "Content-Type": imagem.type } });
    }),
  ),
  http.put(
    `${P}/pagina/:chave/imagem`,
    rota(async ({ request, params }) => {
      const projeto = exigirBloqueio(request, String(params.slug));
      const chave = String(params.chave);
      if (!CAMPOS_PAGINA.some((c) => c.chave === chave && c.tipo === "imagem"))
        falha(404, "Campo de imagem não encontrado");
      const arquivo = (await request.formData()).get("arquivo");
      // No jsdom, formData() devolve o File do undici (instanceof File falha): checa pelo formato.
      if (!arquivo || typeof arquivo === "string")
        return falha(400, "Envie o arquivo no campo 'arquivo'", { campo: "arquivo" });
      if (!(IMAGEM_MIMES as readonly string[]).includes(arquivo.type))
        falha(400, "Envie PNG, JPEG ou WebP", { campo: "arquivo" });
      if (arquivo.size > IMAGEM_MAX_BYTES) falha(413, "Arquivo grande demais");
      const mime = arquivo.type as (typeof IMAGEM_MIMES)[number];
      projeto.imagens[chave] = arquivo;
      projeto.pagina[chave] = { nome: nomeArquivoImagem(chave, mime), mime, tamanho: arquivo.size };
      tocar(projeto);
      return HttpResponse.json(projeto.pagina);
    }),
  ),
  http.delete(
    `${P}/pagina/:chave/imagem`,
    rota(({ request, params }) => {
      const projeto = exigirBloqueio(request, String(params.slug));
      const chave = String(params.chave);
      delete projeto.imagens[chave];
      delete projeto.pagina[chave];
      tocar(projeto);
      return HttpResponse.json(projeto.pagina);
    }),
  ),

  // ---------- anos
  http.post(
    `${P}/anos`,
    rota(async ({ request, params }) => {
      const projeto = exigirBloqueio(request, ParamsProjeto.parse(params).slug);
      const dados = CriarAnoEntrada.parse(await json(request));
      if (projeto.anos.some((a) => a.ano === dados.ano))
        falha(409, "Esse ano já existe no projeto", { campo: "ano" });
      const ano: AnoProjeto = { ...dados, descritores: [] };
      validarAno(ano);
      projeto.anos.push(ano);
      projeto.anos.sort((a, b) => compararAnos(a.ano, b.ano));
      tocar(projeto);
      return HttpResponse.json(ano, { status: 201 });
    }),
  ),
  http.patch(
    `${P}/anos/:ano`,
    rota(async ({ request, params }) => {
      const { slug, ano } = ParamsAno.parse(params);
      const projeto = exigirBloqueio(request, slug);
      const atual = obterAno(projeto, ano);
      const dados = AtualizarAnoEntrada.parse(await json(request));
      const novo = { ...atual, ...dados };
      validarAno(novo);
      Object.assign(atual, novo);
      tocar(projeto);
      return HttpResponse.json(atual);
    }),
  ),
  http.delete(
    `${P}/anos/:ano`,
    rota(({ request, params }) => {
      const { slug, ano } = ParamsAno.parse(params);
      const projeto = exigirBloqueio(request, slug);
      obterAno(projeto, ano);
      if (projeto.anos.length === 1)
        falha(400, "O projeto precisa ter ao menos um ano", { campo: "ano" });
      projeto.anos = projeto.anos.filter((a) => a.ano !== ano);
      tocar(projeto);
      return new HttpResponse(null, { status: 204 });
    }),
  ),

  // ---------- descritores
  http.post(
    `${P}/anos/:ano/descritores`,
    rota(async ({ request, params }) => {
      const { slug, ano } = ParamsAno.parse(params);
      const projeto = exigirBloqueio(request, slug);
      const alvo = obterAno(projeto, ano);
      const descritor = CriarDescritorEntrada.parse(await json(request));
      if (alvo.descritores.some((d) => d.codigo === descritor.codigo))
        falha(409, "Esse código já existe neste ano", { campo: "codigo" });
      validarAno({ ...alvo, descritores: [...alvo.descritores, descritor] });
      alvo.descritores.push(descritor);
      alvo.descritores.sort((a, b) => a.codigo.localeCompare(b.codigo));
      tocar(projeto);
      return HttpResponse.json(descritor, { status: 201 });
    }),
  ),
  http.patch(
    D,
    rota(async ({ request, params }) => {
      const { slug, ano, codigo } = ParamsDescritor.parse(params);
      const projeto = exigirBloqueio(request, slug);
      const alvo = obterAno(projeto, ano);
      const atual = alvo.descritores.find((d) => d.codigo === codigo);
      if (!atual) return falha(404, "Descritor não encontrado");
      const { bncc, ...dados } = AtualizarDescritorEntrada.parse(await json(request));
      if (
        dados.codigo &&
        dados.codigo !== codigo &&
        alvo.descritores.some((d) => d.codigo === dados.codigo)
      )
        falha(409, "Esse código já existe neste ano", { campo: "codigo" });
      Object.assign(atual, dados, bncc ? { bncc: { ...atual.bncc, ...bncc } } : {});
      alvo.descritores.sort((a, b) => a.codigo.localeCompare(b.codigo));
      tocar(projeto);
      return HttpResponse.json(atual);
    }),
  ),
  http.delete(
    D,
    rota(({ request, params }) => {
      const { slug, ano, codigo } = ParamsDescritor.parse(params);
      const projeto = exigirBloqueio(request, slug);
      const alvo = obterAno(projeto, ano);
      if (!alvo.descritores.some((d) => d.codigo === codigo))
        falha(404, "Descritor não encontrado");
      alvo.descritores = alvo.descritores.filter((d) => d.codigo !== codigo);
      tocar(projeto);
      return new HttpResponse(null, { status: 204 });
    }),
  ),
  http.put(
    `${D}/escala/:padrao`,
    rota(async ({ request, params }) => {
      const { slug, ano, codigo, padrao } = ParamsPadrao.parse(params);
      const projeto = exigirBloqueio(request, slug);
      const alvo = obterAno(projeto, ano);
      const descritor = alvo.descritores.find((d) => d.codigo === codigo);
      if (!descritor) return falha(404, "Descritor não encontrado");
      const linhas = LinhasPadrao.parse(await json(request));
      validarAno({
        ...alvo,
        descritores: [{ ...descritor, scale: { ...descritor.scale, [padrao]: linhas } }],
      });
      descritor.scale[padrao] = linhas;
      tocar(projeto);
      return HttpResponse.json(linhas);
    }),
  ),
];
