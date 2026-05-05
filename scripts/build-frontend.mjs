import { cp, mkdir, rm, stat, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const outDir = join(rootDir, "dist");

const publicEntries = [
  "index.html",
  "create.html",
  "pricing.html",
  "contacts.html",
  "offer.html",
  "privacy.html",
  "styles.css",
  "creator.css",
  "scripts/main.js",
  "scripts/runtime-config.js",
  "scripts/creator.js",
  "scripts/site-header.js",
  "assets",
];

async function copyEntry(entry) {
  const source = join(rootDir, entry);
  const destination = join(outDir, entry);
  const sourceStat = await stat(source);

  await mkdir(dirname(destination), { recursive: true });
  if (sourceStat.isDirectory()) {
    await cp(source, destination, { recursive: true });
    return;
  }

  await cp(source, destination);
}

await rm(outDir, { recursive: true, force: true });
await mkdir(outDir, { recursive: true });

for (const entry of publicEntries) {
  await copyEntry(entry);
}

const apiBaseUrl = process.env.COMICLY_API_BASE_URL || "";
await writeFile(
  join(outDir, "scripts/runtime-config.js"),
  `window.COMICLY_API_BASE_URL = ${JSON.stringify(apiBaseUrl)};\n`,
);
