import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { readFile, readdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const rootPath = fileURLToPath(new URL("../", import.meta.url));

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

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
    "scripts/runtime-config.js",
    "scripts/creator.js",
    "scripts/site-header.js",
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
    "docker-compose.yml",
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
    ["creator.js", "main.js", "runtime-config.js", "site-header.js"],
  );
  assert.equal(existsSync(new URL("../dist/assets/", import.meta.url)), true);
});

test("committed env examples do not contain real secret values", async () => {
  const envExamples = [
    await readText(".env.example"),
    await readText("backend/.env.example"),
  ];

  for (const content of envExamples) {
    assert.doesNotMatch(content, /sk-or-v1-[A-Za-z0-9_-]{20,}/);
    assert.doesNotMatch(content, /S3_SECRET_ACCESS_KEY=.*[A-Za-z0-9_-]{20,}/);
    assert.doesNotMatch(content, /GOOGLE_CLIENT_SECRET=.*[A-Za-z0-9_-]{20,}/);
    assert.doesNotMatch(content, /YANDEX_CLIENT_SECRET=.*[A-Za-z0-9_-]{20,}/);
    assert.doesNotMatch(content, /YOOKASSA_API_KEY=.*[A-Za-z0-9_-]{20,}/);
  }
});

test("backend env example names VPS production variables", async () => {
  const env = await readText("backend/.env.example");
  const requiredNames = [
    "DATABASE_URL",
    "MIGRATION_DATABASE_URL",
    "CORS_ORIGINS",
    "SESSION_SECRET",
    "SESSION_COOKIE_DOMAIN",
    "SESSION_COOKIE_SECURE",
    "OAUTH_CALLBACK_BASE_URL",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "YANDEX_CLIENT_ID",
    "YANDEX_CLIENT_SECRET",
    "OPENROUTER_API_KEY",
    "S3_ENDPOINT_URL",
    "S3_BUCKET",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_PUBLIC_BASE_URL",
    "YOOKASSA_SHOP_ID",
    "YOOKASSA_API_KEY",
    "YOOKASSA_RETURN_URL",
    "YOOKASSA_WEBHOOK_IP_CHECK_ENABLED",
  ];

  for (const name of requiredNames) {
    assert.match(env, new RegExp(`^#?\\s*${name}=`, "m"), `${name} documented`);
  }
});

test("VPS Caddy S3 profile is the primary deployment shape", async () => {
  const compose = await readText("docker-compose.yml");
  const caddyfile = await readText("deploy/caddy/Caddyfile");
  const runbook = await readText("backend/docs/deployment.md");
  const backendReadme = await readText("backend/README.md");
  const requirements = await readText("backend/requirements-runtime.txt");

  assert.match(compose, /caddy:2\.8-alpine/);
  assert.match(compose, /backend-api/);
  assert.match(compose, /\.\/backend\/\.env/);
  assert.match(caddyfile, /reverse_proxy backend-api:8000/);
  assert.match(caddyfile, /try_files \{path\} \{path\}\.html \/index\.html/);
  assert.match(runbook, /docker compose up -d --build/);
  assert.match(runbook, /Managed PostgreSQL/);
  assert.match(runbook, /S3-compatible/);
  assert.match(backendReadme, /S3-compatible object storage/);
});

test("smoke helper separates automated checks from manual provider checks", async () => {
  const smoke = await readText("backend/scripts/smoke_production.py");

  assert.match(smoke, /--api-base-url/);
  assert.match(smoke, /--frontend-url/);
  assert.match(smoke, /\/health/);
  assert.match(smoke, /\/ready/);
  assert.match(smoke, /Live OAuth callbacks require provider credentials/);
  assert.match(smoke, /S3 storage/);
});
