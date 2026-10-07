import MongoStore from "connect-mongo";
import express, { type Express } from "express";
import session from "express-session";
import helmet from "helmet";
import mongoose from "mongoose";
import { pinoHttp } from "pino-http";
import type { Logger } from "pino";
import type { Config } from "./config.js";
import { errorHandler, rotaNaoEncontrada } from "./middlewares/errorHandler.js";
import { apiRouter } from "./modules/index.js";

/** Monta o app Express. Requer conexão Mongoose já aberta (a sessão usa o mesmo cliente). */
export function criarApp(config: Config, log: Logger): Express {
  const app = express();
  app.disable("x-powered-by");
  // Atrás do nginx do docker-compose: confia no X-Forwarded-Proto (cookie secure "auto").
  app.set("trust proxy", 1);

  app.use(helmet());
  app.use(pinoHttp({ logger: log }));
  app.use(express.json({ limit: "10mb" }));
  app.use(
    session({
      name: "revista.sid",
      secret: config.SESSION_SECRET,
      resave: false,
      saveUninitialized: false,
      rolling: true,
      store: MongoStore.create({
        client: mongoose.connection.getClient(),
        collectionName: "sessoes",
        ttl: 60 * 60 * 12,
      }),
      cookie: {
        httpOnly: true,
        sameSite: "lax",
        // "auto": secure só quando a conexão é HTTPS (via X-Forwarded-Proto); em http://localhost o cookie funciona.
        secure: "auto",
        maxAge: 1000 * 60 * 60 * 12,
      },
    }),
  );

  app.use("/api", apiRouter);
  app.use(rotaNaoEncontrada);
  app.use(errorHandler);
  return app;
}
