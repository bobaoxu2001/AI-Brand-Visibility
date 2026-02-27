import Database from "better-sqlite3";
import path from "path";

let dbInstance: Database.Database | null = null;

function resolveDbPath(): string {
  const envPath = process.env.VISIBILITY_DB_PATH;
  if (envPath && envPath.trim()) {
    return path.resolve(envPath);
  }

  return path.resolve(process.cwd(), "..", "visibility_data.db");
}

export function getDb(): Database.Database {
  if (!dbInstance) {
    dbInstance = new Database(resolveDbPath(), { readonly: true });
    dbInstance.pragma("foreign_keys = ON");
  }
  return dbInstance;
}
