import { readFile } from "node:fs/promises";
import test from "node:test";
import assert from "node:assert/strict";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("creator has a soft auth overlay and landing remains public", async () => {
  const [creatorHtml, landingHtml] = await Promise.all([
    read("create.html"),
    read("index.html"),
  ]);

  assert.match(creatorHtml, /data-auth-overlay/);
  assert.match(creatorHtml, /Войдите, чтобы создавать комиксы/);
  assert.match(creatorHtml, /data-auth-login="google"/);
  assert.match(creatorHtml, /data-auth-login="yandex"/);
  assert.doesNotMatch(landingHtml, /data-auth-overlay/);
  assert.doesNotMatch(landingHtml, /api\/v1\/me/);
});

test("creator API helper targets FastAPI v1 with cookies", async () => {
  const script = await read("scripts/creator.js");

  assert.match(script, /COMICLY_API_BASE_URL/);
  assert.match(script, /https:\/\/api\.comicly\.ai/);
  assert.match(script, /credentials:\s*"include"/);
  assert.match(script, /\/api\/v1\/me/);
  assert.match(script, /\/api\/v1\/auth\/\$\{provider\}\/login/);
  assert.match(script, /\/api\/v1\/comics/);
  assert.match(script, /\/api\/v1\/ai-text/);
  assert.match(script, /\/api\/v1\/generations/);
  assert.match(script, /Idempotency-Key/);
});

test("creator no longer calls legacy root AI routes or mutates demo balance", async () => {
  const script = await read("scripts/creator.js");
  const html = await read("create.html");

  assert.doesNotMatch(script, /"\/api\/ai-text"/);
  assert.doesNotMatch(script, /"\/api\/generate-comic-page"/);
  assert.doesNotMatch(script, /credits\s*\+=/);
  assert.doesNotMatch(script, /credits\s*=\s*Math\.max\(0,\s*credits\s*-/);
  assert.doesNotMatch(script, /демо-профиля/i);
  assert.doesNotMatch(html, /240 кредитов/);
  assert.doesNotMatch(`${script}\n${html}`, /OPENROUTER_API_KEY|sk-or-v1-/);
});

test("generation UX keeps editing available and uses backend result state", async () => {
  const script = await read("scripts/creator.js");

  assert.match(script, /Генерируем страницу\/изображение/);
  assert.match(script, /data\.image_url \|\| data\.page\?\.image_url/);
  assert.match(script, /typeof data\.balance === "number"/);
  assert.doesNotMatch(script, /generatePageButton\)\s*generatePageButton\.disabled = isLoading/);
  assert.doesNotMatch(script, /regenerateSceneButton\)\s*regenerateSceneButton\.disabled = isLoading/);
});
