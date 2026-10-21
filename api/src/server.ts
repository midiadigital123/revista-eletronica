import { criarApp } from "./app.js";
import { lerConfig } from "./config.js";
import { conectar, desconectar } from "./db.js";
import { criarLogger } from "./logger.js";
import { garantirAdmin } from "./seed.js";

const config = lerConfig();
const log = criarLogger(config);

await conectar(config.MONGO_URL);
await garantirAdmin(config, log);

const servidor = criarApp(config, log).listen(config.PORT, () =>
  log.info(`API em http://localhost:${config.PORT}/api`),
);

for (const sinal of ["SIGINT", "SIGTERM"] as const)
  process.on(sinal, () => {
    servidor.close(() => void desconectar().then(() => process.exit(0)));
  });
