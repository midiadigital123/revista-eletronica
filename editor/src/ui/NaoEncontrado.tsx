import { Link } from "react-router";

export function NaoEncontrado() {
  return (
    <section className="p-8">
      <h1 className="text-2xl">Página não encontrada</h1>
      <Link className="text-acento underline mt-4 inline-block" to="/projetos">
        Voltar aos projetos
      </Link>
    </section>
  );
}
