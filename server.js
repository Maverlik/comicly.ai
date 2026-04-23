const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const rootDir = __dirname;
const port = Number(process.env.PORT || 3000);

function loadEnv() {
  const envPath = path.join(rootDir, ".env");
  if (!fs.existsSync(envPath)) return;

  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const separatorIndex = trimmed.indexOf("=");
    if (separatorIndex === -1) continue;

    const key = trimmed.slice(0, separatorIndex).trim();
    const value = trimmed
      .slice(separatorIndex + 1)
      .trim()
      .replace(/^["']|["']$/g, "");

    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

loadEnv();

const DEFAULT_IMAGE_MODEL = "google/gemini-2.5-flash-image-preview";
const DEFAULT_TEXT_MODEL = "google/gemini-2.5-flash";

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  response.end(JSON.stringify(payload));
}

function readJson(request) {
  return new Promise((resolve, reject) => {
    let body = "";

    request.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) {
        request.destroy();
        reject(new Error("Request body is too large."));
      }
    });

    request.on("end", () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new Error("Invalid JSON body."));
      }
    });

    request.on("error", reject);
  });
}

function buildImagePrompt(payload) {
  const toneMap = {
    funny: "witty, expressive, energetic",
    emotional: "emotional, dramatic, cinematic",
    epic: "epic, high stakes, heroic",
  };

  const scenesBlock = Array.isArray(payload.scenes) && payload.scenes.length
    ? `Panel breakdown:\n${payload.scenes.map((scene, index) => `${index + 1}. ${scene}`).join("\n")}`
    : "";

  return [
    "Create a complete, publication-ready comic book page.",
    "The page must contain 4-6 clearly bordered panels with polished composition, cinematic lighting, varied shot sizes, and readable speech bubbles placed inside panels.",
    `Story: ${payload.story}`,
    `Visual style: ${payload.style || "Anime"}.`,
    `Tone: ${toneMap[payload.tone] || payload.tone || "emotional"}.`,
    `Current page: ${payload.page || 1}. Focus scene: ${payload.selectedScene || 1}.`,
    scenesBlock,
    payload.dialogue ? `Key dialogue to include (Russian if non-Latin): ${payload.dialogue}` : "",
    payload.caption ? `Scene caption: ${payload.caption}` : "",
    payload.layout ? `Layout direction: ${payload.layout}` : "",
    "Keep character design consistent across panels. Avoid watermarks, UI chrome, page numbers, or any explanatory text outside the comic art.",
  ]
    .filter(Boolean)
    .join("\n");
}

function extractImageUrl(data) {
  const message = data?.choices?.[0]?.message;
  if (!message) return null;

  const direct = message?.images?.[0]?.image_url?.url
    || message?.images?.[0]?.url
    || message?.image_url?.url;
  if (direct) return direct;

  if (Array.isArray(message.content)) {
    for (const part of message.content) {
      if (typeof part !== "object" || part === null) continue;
      if (part.type === "image_url") {
        const url = typeof part.image_url === "string" ? part.image_url : part.image_url?.url;
        if (url) return url;
      }
      if (part.type === "output_image" && (part.image_url || part.url)) {
        return part.image_url || part.url;
      }
      if (part.type === "image" && (part.image_url || part.url || part.source?.data)) {
        if (part.source?.data && part.source?.media_type) {
          return `data:${part.source.media_type};base64,${part.source.data}`;
        }
        return part.image_url || part.url;
      }
    }
  }

  return null;
}

function extractText(data) {
  const message = data?.choices?.[0]?.message;
  if (!message) return "";
  if (typeof message.content === "string") return message.content;
  if (Array.isArray(message.content)) {
    return message.content
      .filter((part) => part?.type === "text" && part.text)
      .map((part) => part.text)
      .join("\n")
      .trim();
  }
  return "";
}

async function callOpenRouter({ model, messages, modalities, imageConfig }) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    const error = new Error(
      "OPENROUTER_API_KEY не найден. Создайте файл .env на основе .env.example и добавьте ключ OpenRouter."
    );
    error.statusCode = 503;
    error.code = "MISSING_KEY";
    throw error;
  }

  const body = { model, messages };
  if (modalities) body.modalities = modalities;
  if (imageConfig) body.image_config = imageConfig;

  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": process.env.OPENROUTER_SITE_URL || "http://localhost:3000",
      "X-Title": process.env.OPENROUTER_APP_NAME || "comicly.ai",
    },
    body: JSON.stringify(body),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(
      data?.error?.message || data?.message || `OpenRouter ответил статусом ${response.status}.`
    );
    error.statusCode = response.status;
    throw error;
  }
  return data;
}

async function generateComicPage(request, response) {
  try {
    const payload = await readJson(request);
    if (!payload.story || typeof payload.story !== "string") {
      sendJson(response, 400, { error: "Поле story обязательно." });
      return;
    }

    const model = process.env.OPENROUTER_IMAGE_MODEL || DEFAULT_IMAGE_MODEL;
    const prompt = buildImagePrompt(payload);

    const supportsText = /^google\//i.test(model);
    const modalities = supportsText ? ["image", "text"] : ["image"];

    const data = await callOpenRouter({
      model,
      modalities,
      imageConfig: {
        aspect_ratio: process.env.OPENROUTER_IMAGE_ASPECT_RATIO || "1:1",
      },
      messages: [{ role: "user", content: prompt }],
    });

    const imageUrl = extractImageUrl(data);
    if (!imageUrl) {
      sendJson(response, 502, {
        error: "Модель не вернула изображение. Попробуйте другую модель в OPENROUTER_IMAGE_MODEL.",
      });
      return;
    }

    sendJson(response, 200, { imageUrl, model, text: extractText(data) });
  } catch (error) {
    sendJson(response, error.statusCode || 500, {
      error: error.message || "Ошибка сервера.",
      code: error.code,
    });
  }
}

const TEXT_TASKS = {
  enhance: {
    system:
      "Ты помощник сценариста комиксов. Дорабатывай историю пользователя: добавляй кинематографичный ритм, визуальные детали и эмоциональный конфликт. Отвечай одним связным абзацем на русском. Без префиксов, без кавычек, без списков.",
    instruction: (payload) =>
      `Доработай эту историю для комикса в жанре "${payload.tone || "эмоциональный"}" и стиле "${payload.style || "Аниме"}":\n\n${payload.story}`,
    max: 600,
  },
  dialogue: {
    system:
      "Ты мастер коротких реплик для комиксов. Возвращай одну мощную реплику на русском, в верхнем регистре, без кавычек, 3-14 слов. Без комментариев.",
    instruction: (payload) =>
      `История: ${payload.story}\n${payload.sceneTitle ? `Сцена: ${payload.sceneTitle}\n` : ""}${payload.sceneDescription ? `Описание: ${payload.sceneDescription}\n` : ""}Тон: ${payload.tone || "эмоциональный"}. Дай новую реплику главного героя.`,
    max: 80,
  },
  caption: {
    system:
      "Ты пишешь авторские подписи к кадрам комикса. Одно предложение на русском, 10-20 слов, образно и визуально. Без кавычек и без префиксов.",
    instruction: (payload) =>
      `История: ${payload.story}\n${payload.sceneTitle ? `Сцена: ${payload.sceneTitle}\n` : ""}${payload.sceneDescription ? `Описание: ${payload.sceneDescription}\n` : ""}Стиль: ${payload.style || "Аниме"}. Дай подпись, задающую атмосферу.`,
    max: 120,
  },
  scenes: {
    system:
      'Ты раскадровщик комиксов. Возвращай строго JSON-массив из 4-5 сцен без пояснений. Формат каждого элемента: {"title": "Сцена N", "description": "одно предложение на русском, 8-16 слов, без кавычек"}. Никакого текста до или после массива.',
    instruction: (payload) =>
      `История: ${payload.story}\nТон: ${payload.tone || "эмоциональный"}. Стиль: ${payload.style || "Аниме"}. Разбей страницу на сцены.`,
    max: 700,
  },
};

async function handleAiText(request, response) {
  try {
    const payload = await readJson(request);
    const task = TEXT_TASKS[payload.task];
    if (!task) {
      sendJson(response, 400, { error: "Неизвестная AI-задача." });
      return;
    }
    if (!payload.story || typeof payload.story !== "string") {
      sendJson(response, 400, { error: "Поле story обязательно." });
      return;
    }

    const model = process.env.OPENROUTER_TEXT_MODEL || DEFAULT_TEXT_MODEL;
    const data = await callOpenRouter({
      model,
      messages: [
        { role: "system", content: task.system },
        { role: "user", content: task.instruction(payload) },
      ],
    });

    const text = extractText(data).trim();
    if (!text) {
      sendJson(response, 502, { error: "Модель вернула пустой ответ." });
      return;
    }

    if (payload.task === "scenes") {
      const jsonMatch = text.match(/\[[\s\S]*\]/);
      try {
        const scenes = JSON.parse(jsonMatch ? jsonMatch[0] : text);
        sendJson(response, 200, { scenes, model });
        return;
      } catch {
        sendJson(response, 502, { error: "Не удалось разобрать сцены от модели." });
        return;
      }
    }

    sendJson(response, 200, { text, model });
  } catch (error) {
    sendJson(response, error.statusCode || 500, {
      error: error.message || "Ошибка сервера.",
      code: error.code,
    });
  }
}

function handleHealth(response) {
  sendJson(response, 200, {
    ok: true,
    hasApiKey: Boolean(process.env.OPENROUTER_API_KEY),
    imageModel: process.env.OPENROUTER_IMAGE_MODEL || DEFAULT_IMAGE_MODEL,
    textModel: process.env.OPENROUTER_TEXT_MODEL || DEFAULT_TEXT_MODEL,
  });
}

function serveStatic(request, response) {
  const url = new URL(request.url, `http://${request.headers.host}`);
  let pathname = decodeURIComponent(url.pathname);
  if (pathname === "/") pathname = "/index.html";

  const requestedPath = path.normalize(path.join(rootDir, pathname));
  if (!requestedPath.startsWith(rootDir)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  fs.stat(requestedPath, (statError, stat) => {
    if (statError || !stat.isFile()) {
      response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Not found");
      return;
    }

    const extension = path.extname(requestedPath).toLowerCase();
    response.writeHead(200, {
      "Content-Type": contentTypes[extension] || "application/octet-stream",
    });
    fs.createReadStream(requestedPath).pipe(response);
  });
}

const server = http.createServer((request, response) => {
  if (request.method === "GET" && request.url === "/api/health") {
    handleHealth(response);
    return;
  }

  if (request.method === "POST" && request.url === "/api/generate-comic-page") {
    generateComicPage(request, response);
    return;
  }

  if (request.method === "POST" && request.url === "/api/ai-text") {
    handleAiText(request, response);
    return;
  }

  if (request.method === "GET" || request.method === "HEAD") {
    serveStatic(request, response);
    return;
  }

  response.writeHead(405, { "Content-Type": "text/plain; charset=utf-8" });
  response.end("Method not allowed");
});

server.listen(port, () => {
  console.log(`comicly.ai running at http://localhost:${port}`);
});
