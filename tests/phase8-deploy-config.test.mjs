import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { readFile, readdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const rootPath = fileURLToPath(new URL("../", import.meta.url));

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");
const readJson = async (path) => JSON.parse(await readText(path));

test("root Vercel config builds an explicit static output", async () => {
  const config = await readJson("vercel.json");
  const packageJson = await readJson("package.json");

  assert.equal(config.buildCommand, "npm run build:frontend");
  assert.equal(config.outputDirectory, "dist");
  assert.equal(packageJson.scripts["build:frontend"], "node scripts/build-frontend.mjs");
});

test("frontend build copies only public static files", async () => {
  const distPath = new URL("../dist/", import.meta.url);
  await rm(distPath, { recursive: true, force: true });

  await import(`${pathToFileURL(join(rootPath, "scripts/build-frontend.mjs")).href}?${Date.now()}`);

  const expectedPublicFiles = [
    "index.html",
    "create.html",
    "pricing.html",
    "contacts.html",
    "offer.html",
    "privacy.html",
    "styles.css",
    "creator.css",
    "scripts/main.js",
    "scripts/creator.js",
  ];

  for (const file of expectedPublicFiles) {
    assert.equal(existsSync(new URL(`../dist/${file}`, import.meta.url)), true, `${file} copied`);
  }

  const privatePaths = [
    ".env",
    ".planning",
    "backend",
    "package.json",
    "server.js",
    "vercel.json",
    ".git",
  ];

  for (const privatePath of privatePaths) {
    assert.equal(
      existsSync(new URL(`../dist/${privatePath}`, import.meta.url)),
      false,
      `${privatePath} is not published`,
    );
  }

  assert.deepEqual(
    (await readdir(new URL("../dist/scripts/", import.meta.url))).sort(),
    ["creator.js", "main.js"],
  );
  assert.equal(existsSync(new URL("../dist/assets/", import.meta.url)), true);
});

test("backend Vercel config targets FastAPI app without Docker Compose", async () => {
  const backendConfig = await readJson("backend/vercel.json");
  const pythonVersion = (await readText("backend/.python-version")).trim();

  assert.equal(pythonVersion, "3.12");
  assert.equal(backendConfig.functions["app/main.py"].maxDuration, 300);
  assert.deepEqual(backendConfig.routes, [{ src: "/(.*)", dest: "app/main.py" }]);
  assert.doesNotMatch(JSON.stringify(backendConfig), /docker|compose/i);
});

test("committed env examples do not contain real secret values", async () => {
  const envExamples = [await readText(".env.example"), await readText("backend/.env.example")];

  for (const content of envExamples) {
    assert.doesNotMatch(content, /sk-or-v1-[A-Za-z0-9_-]{20,}/);
    assert.doesNotMatch(content, /BLOB_READ_WRITE_TOKEN=.*[A-Za-z0-9_-]{20,}/);
    assert.doesNotMatch(content, /GOOGLE_CLIENT_SECRET=.*[A-Za-z0-9_-]{20,}/);
    assert.doesNotMatch(content, /YANDEX_CLIENT_SECRET=.*[A-Za-z0-9_-]{20,}/);
  }
});

test("backend env example names production deployment variables", async () => {
  const env = await readText("backend/.env.example");
  const requiredNames = [
    "DATABASE_URL",
    "MIGRATION_DATABASE_URL",
    "CORS_ORIGINS",
    "SESSION_SECRET",
    "SESSION_COOKIE_DOMAIN",
    "SESSION_COOKIE_SECURE",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "YANDEX_CLIENT_ID",
    "YANDEX_CLIENT_SECRET",
    "OPENROUTER_API_KEY",
    "BLOB_READ_WRITE_TOKEN",
  ];

  for (const name of requiredNames) {
    assert.match(env, new RegExp(`^#?\\s*${name}=`, "m"), `${name} documented`);
  }
});
