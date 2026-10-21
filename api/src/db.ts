import mongoose from "mongoose";

export async function conectar(url: string): Promise<typeof mongoose> {
  mongoose.set("strictQuery", true);
  return mongoose.connect(url);
}

export async function desconectar(): Promise<void> {
  await mongoose.disconnect();
}
