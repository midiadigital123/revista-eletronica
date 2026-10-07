import { pino, type Logger } from "pino";
import type { Config } from "./config.js";

export const criarLogger = (config: Config): Logger =>
  pino({
    level: config.NODE_ENV === "test" ? "silent" : config.LOG_LEVEL,
    redact: ["req.headers.cookie", "req.body.senha"],
    ...(config.NODE_ENV === "development" ? { transport: { target: "pino-pretty" } } : {}),
  });
