// globalTeardown (D-224): no fim de toda execução, apaga do banco de dev os parceiros e templates "E2E …"
// que o usuário de teste criou (manage.py limpar_e2e), mesmo quando um spec parou no meio.
// Stack de worktree (docker compose -p <nome>): defina E2E_COMPOSE_PROJECT=<nome>.
// Falhar aqui não derruba a execução: só avisa, e dá para rodar o comando à mão.
import { execFileSync } from "node:child_process";
import path from "node:path";

export default function limpar() {
  const projeto = process.env.E2E_COMPOSE_PROJECT;
  const usuario = process.env.E2E_ADMIN_USUARIO ?? "e2e";
  const args = [
    "compose", ...(projeto ? ["-p", projeto] : []),
    "exec", "-T", "app", "python", "manage.py", "limpar_e2e", "--usuario", usuario,
  ];
  try {
    const saida = execFileSync("docker", args, { cwd: path.resolve(__dirname, "../.."), encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
    console.log(`[limpar_e2e] ${saida.trim()}`);
  } catch (e) {
    console.warn(`[limpar_e2e] não rodou (${(e as Error).message.split("\n")[0]}). À mão: docker compose exec app python manage.py limpar_e2e`);
  }
}
