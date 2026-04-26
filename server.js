const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const rootDir = __dirname;
const port = Number(process.env.PORT) || 3000;

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

const DEFAULT_IMAGE_MODEL = "google/gemini-3-pro-image-preview";
const DEFAULT_TEXT_MODEL = "google/gemini-3.1-flash-lite-preview";

const ALLOWED_IMAGE_MODELS = new Set([
  "bytedance-seed/seedream-4.5",
  "google/gemini-3-pro-image-preview",
  "openai/gpt-5.4-image-2",
]);

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

const LANGUAGE_LABELS = {
  ru: "Russian",
  en: "English",
  es: "Spanish",
  fr: "French",
  de: "German",
  ja: "Japanese",
  zh: "Chinese",
  ko: "Korean",
};

function languageLabel(code) {
  if (!code) return "Russian";
  return LANGUAGE_LABELS[code] || code;
}

function buildImagePrompt(payload) {
  const scenesBlock = Array.isArray(payload.scenes) && payload.scenes.length
    ? `Panel breakdown:\n${payload.scenes.map((scene, index) => `${index + 1}. ${scene}`).join("\n")}`
    : "No panel breakdown was provided. Create a clear 4-6 panel sequence from the story.";

  const language = languageLabel(payload.language);
  const pagesTotal = Math.max(1, Number(payload.pagesTotal) || 1);
  const currentPage = Math.max(1, Number(payload.page) || 1);
  const pageContext = pagesTotal > 1
    ? `This is page ${currentPage} of a ${pagesTotal}-page comic. Cover only the portion of the story that corresponds to this page so the full arc unfolds smoothly across all pages, and keep visual continuity with the other pages.`
    : `Current page: ${currentPage}.${payload.selectedScene ? ` Focus scene: ${payload.selectedScene}.` : ""}`;

  const previousPagesBlock = Array.isArray(payload.previousPagesContext) && payload.previousPagesContext.length
    ? `Continuity from earlier pages — preserve the same characters, locations, and visual world; do not retell, just continue:\n${payload.previousPagesContext.map((s, i) => `Page ${i + 1}: ${s}`).join("\n")}`
    : "";

  return [
    "Create a complete, publication-ready comic book page.",
    "The page must contain 4-6 clearly bordered panels with polished composition, cinematic lighting, varied shot sizes, and readable speech bubbles placed inside panels.",
    `Story: ${payload.story}`,
    payload.characters ? `Character reference: ${payload.characters}` : "If character references are not provided, design distinct characters and keep them visually consistent across panels.",
    `Visual style: ${payload.style || "Anime"}.`,
    `Speech bubble language: ${language}. All dialogue and captions must be written in ${language}.`,
    pageContext,
    previousPagesBlock,
    scenesBlock,
    payload.dialogue ? `Key dialogue to include as speech bubbles, preserving speakers when named: ${payload.dialogue}` : `If dialogue is not provided, write natural ${language} speech bubbles for the characters.`,
    payload.caption ? `Scene caption: ${payload.caption}` : "",
    payload.layout ? `Layout direction: ${payload.layout}` : "",
    "Keep character design consistent across panels. Avoid watermarks, UI chrome, page numbers, or any explanatory text outside the comic art.",
  ]
    .filter(Boolean)
    .join("\n");
}

function asDataUrlIfBase64(value, mediaType = "image/png") {
  if (typeof value !== "string" || !value) return null;
  if (value.startsWith("data:") || value.startsWith("http://") || value.startsWith("https://")) {
    return value;
  }
  // Похоже на голый base64
  if (/^[A-Za-z0-9+/=\s]+$/.test(value) && value.length > 100) {
    return `data:${mediaType};base64,${value.replace(/\s+/g, "")}`;
  }
  return value;
}

function pickImageFromObject(obj) {
  if (!obj || typeof obj !== "object") return null;
  // Стандартные варианты от OpenRouter / Anthropic / OpenAI
  if (typeof obj.url === "string" && obj.url) return asDataUrlIfBase64(obj.url);
  if (typeof obj.image_url === "string" && obj.image_url) return asDataUrlIfBase64(obj.image_url);
  if (obj.image_url && typeof obj.image_url.url === "string" && obj.image_url.url) {
    return asDataUrlIfBase64(obj.image_url.url);
  }
  if (typeof obj.b64_json === "string" && obj.b64_json) {
    return `data:${obj.media_type || "image/png"};base64,${obj.b64_json}`;
  }
  if (obj.source && typeof obj.source.data === "string") {
    return `data:${obj.source.media_type || obj.media_type || "image/png"};base64,${obj.source.data}`;
  }
  if (typeof obj.b64 === "string" && obj.b64) {
    return `data:${obj.media_type || "image/png"};base64,${obj.b64}`;
  }
  if (typeof obj.data === "string" && obj.data) {
    return asDataUrlIfBase64(obj.data, obj.media_type || "image/png");
  }
  return null;
}

function extractImageUrl(data) {
  // Top-level images / data (некоторые модели — OpenAI Images API style)
  if (Array.isArray(data?.data)) {
    for (const item of data.data) {
      const found = pickImageFromObject(item);
      if (found) return found;
    }
  }
  if (Array.isArray(data?.images)) {
    for (const item of data.images) {
      const found = pickImageFromObject(item) || pickImageFromObject(item?.image_url);
      if (found) return found;
    }
  }

  const message = data?.choices?.[0]?.message;
  if (!message) return null;

  if (Array.isArray(message.images)) {
    for (const item of message.images) {
      const found = pickImageFromObject(item) || pickImageFromObject(item?.image_url);
      if (found) return found;
    }
  }

  const directOnMessage = pickImageFromObject(message?.image_url) || pickImageFromObject(message);
  if (directOnMessage && directOnMessage !== message) return directOnMessage;

  if (Array.isArray(message.content)) {
    for (const part of message.content) {
      if (typeof part !== "object" || part === null) continue;
      if (part.type === "image_url") {
        const url = typeof part.image_url === "string" ? part.image_url : part.image_url?.url;
        if (url) return asDataUrlIfBase64(url);
      }
      if (part.type === "output_image") {
        const found = pickImageFromObject(part);
        if (found) return found;
      }
      if (part.type === "image") {
        const found = pickImageFromObject(part);
        if (found) return found;
      }
    }
  }

  // Фолбэк: иногда модель кладёт data:image URL прямо в текст
  if (typeof message.content === "string") {
    const match = message.content.match(/data:image\/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+/);
    if (match) return match[0];
    const urlMatch = message.content.match(/https?:\/\/\S+\.(?:png|jpg|jpeg|webp|gif)/i);
    if (urlMatch) return urlMatch[0];
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

    const requestedModel = typeof payload.model === "string" ? payload.model.trim() : "";
    const model = ALLOWED_IMAGE_MODELS.has(requestedModel)
      ? requestedModel
      : process.env.OPENROUTER_IMAGE_MODEL || DEFAULT_IMAGE_MODEL;
    const prompt = buildImagePrompt(payload);

    const isGoogle = /^google\//i.test(model);
    const modalities = isGoogle ? ["image", "text"] : ["image"];

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
      const finishReason = data?.choices?.[0]?.finish_reason || "";
      const nativeFinishReason = data?.choices?.[0]?.native_finish_reason || "";
      const isContentFilter =
        /content[_-]?filter/i.test(finishReason) ||
        /prohibit|safety|blocked/i.test(nativeFinishReason);
      try {
        const debugDump = JSON.stringify(data).slice(0, 4000);
        console.warn(`[generate-comic-page] Empty image from ${model}. Raw response sample: ${debugDump}`);
      } catch {
        console.warn(`[generate-comic-page] Empty image from ${model}, response not serializable.`);
      }
      const errorMessage = isContentFilter
        ? `Модель ${model} отклонила запрос из-за фильтра безопасности (${nativeFinishReason || finishReason}). Смягчите формулировки сюжета/сцен или выберите другую модель.`
        : `Модель ${model} не вернула изображение. Попробуйте другую модель — формат ответа залогирован в консоли сервера.`;
      sendJson(response, 502, {
        error: errorMessage,
        code: isContentFilter ? "content_filter" : undefined,
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
    instruction: (payload) => {
      const pages = Math.max(1, Number(payload.pageCount) || 1);
      const pageHint = pages > 1
        ? ` История будет растянута на ${pages} страниц комикса — обеспечь достаточный объем и завязку, развитие, кульминацию.`
        : "";
      return `Доработай эту историю для комикса в стиле "${payload.style || "Аниме"}".${payload.characters ? ` Учитывай персонажей: ${payload.characters}` : ""}${pageHint}\n\n${payload.story}`;
    },
    max: 600,
  },
  dialogue: {
    system:
      "Ты мастер диалогов для комиксов. Возвращай 1-4 короткие реплики для речевых пузырей. Если участвуют несколько персонажей, пиши строки в формате Имя: реплика. Без кавычек, без пояснений, без markdown.",
    instruction: (payload) =>
      `История: ${payload.story}\n${payload.characters ? `Персонажи: ${payload.characters}\n` : ""}${payload.sceneTitle ? `Сцена: ${payload.sceneTitle}\n` : ""}${payload.sceneDescription ? `Описание: ${payload.sceneDescription}\n` : ""}Язык диалога: ${languageLabel(payload.language)}. Дай диалог для этой сцены строго на этом языке.`,
    max: 180,
  },
  caption: {
    system:
      "Ты пишешь авторские подписи к кадрам комикса. Одно предложение, 10-20 слов, образно и визуально. Без кавычек и без префиксов.",
    instruction: (payload) =>
      `История: ${payload.story}\n${payload.characters ? `Персонажи: ${payload.characters}\n` : ""}${payload.sceneTitle ? `Сцена: ${payload.sceneTitle}\n` : ""}${payload.sceneDescription ? `Описание: ${payload.sceneDescription}\n` : ""}Стиль: ${payload.style || "Аниме"}. Язык подписи: ${languageLabel(payload.language)}. Дай подпись на этом языке, задающую атмосферу.`,
    max: 120,
  },
  scenes: {
    system:
      'Ты раскадровщик комиксов. Возвращай строго JSON-массив из 4-6 сцен без пояснений. Формат каждого элемента: {"title": "Сцена N", "description": "одно предложение на русском, 8-16 слов", "dialogue": "необязательные 1-2 короткие реплики с именами персонажей или пустая строка", "caption": "необязательная короткая подпись или пустая строка"}. Поля dialogue и caption пиши на языке, указанном пользователем. Никакого текста до или после массива.',
    instruction: (payload) => {
      const pages = Math.max(1, Number(payload.pageCount) || 1);
      const pageHint = pages > 1
        ? ` Сцены должны покрывать только одну страницу из ${pages}-страничного комикса (ту, которую пользователь сейчас редактирует).`
        : "";
      return `История: ${payload.story}\n${payload.characters ? `Персонажи: ${payload.characters}\n` : ""}Стиль: ${payload.style || "Аниме"}. Язык реплик: ${languageLabel(payload.language)}.${pageHint} Разбей страницу на сцены.`;
    },
    max: 900,
  },
  continue: {
    system:
      "Ты сценарист комикса. Получаешь резюме предыдущих страниц и пишешь, что произойдёт на СЛЕДУЮЩЕЙ странице — один связный абзац (3-5 предложений). Сохраняй персонажей, локации, тон. Двигай сюжет вперёд. Без префиксов, без кавычек, без markdown.",
    instruction: (payload) => {
      const summaries = Array.isArray(payload.previousPagesContext) && payload.previousPagesContext.length
        ? payload.previousPagesContext.map((s, i) => `Стр.${i + 1}: ${s}`).join("\n")
        : "(пока ничего не было)";
      return `Исходный замысел истории: ${payload.story}\n${payload.characters ? `Персонажи: ${payload.characters}\n` : ""}Что уже произошло на предыдущих страницах:\n${summaries}\n\nНапиши, что происходит на следующей странице. Стиль: ${payload.style || "Аниме"}. Язык: ${languageLabel(payload.language)}. Добавь конкретные визуальные детали и небольшой драматический поворот, чтобы страница не повторяла предыдущие.`;
    },
    max: 500,
  },
  summarize: {
    system:
      "Ты резюмируешь страницу комикса в 1-2 сухих предложениях. Только факты — кто что сделал и к чему это привело. Без оценок, без префиксов, без кавычек, без markdown.",
    instruction: (payload) =>
      `Сюжет страницы: ${payload.story}\n${payload.characters ? `Персонажи: ${payload.characters}\n` : ""}${payload.sceneDescription ? `Сцены: ${payload.sceneDescription}\n` : ""}${payload.dialogue ? `Диалоги: ${payload.dialogue}\n` : ""}Сделай очень краткий пересказ событий этой страницы.`,
    max: 200,
  },
  characters: {
    system:
      'Ты дизайнер персонажей комиксов. Возвращай строго JSON-массив главных персонажей без пояснений и без текста до/после массива. В массиве должно быть от 1 до 4 элементов — ровно столько, сколько реально есть в истории; если в истории один герой — верни массив из одного элемента, не выдумывай дополнительных. Формат каждого элемента: {"name": "Имя на языке истории ИЛИ пустая строка", "description": "Конкретная внешность: возраст, телосложение, причёска и цвет волос, цвет глаз, одежда и аксессуары, отличительные черты, роль в истории. 2-3 предложения, на русском."}. ВАЖНО: если имя персонажа не названо явно в истории пользователя, поле name должно быть пустой строкой "" — НЕ ВЫДУМЫВАЙ имена. Описание заполняй всегда и делай его настолько конкретным, чтобы модель рисовала персонажа идентично на каждой странице.',
    instruction: (payload) =>
      `История: ${payload.story}\nСтиль: ${payload.style || "Аниме"}. Язык реплик: ${languageLabel(payload.language)}.\nВыдели только тех героев, что реально присутствуют в истории — это может быть и один персонаж. Зафиксируй их внешность, чтобы на всех страницах комикса они выглядели одинаково. Имя бери только если оно прямо упомянуто в истории; иначе оставь name пустой строкой.`,
    max: 900,
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

    if (payload.task === "scenes" || payload.task === "characters") {
      const jsonMatch = text.match(/\[[\s\S]*\]/);
      try {
        const parsed = JSON.parse(jsonMatch ? jsonMatch[0] : text);
        if (payload.task === "characters") {
          sendJson(response, 200, { characters: parsed, model });
        } else {
          sendJson(response, 200, { scenes: parsed, model });
        }
        return;
      } catch {
        const errorMessage = payload.task === "characters"
          ? "Не удалось разобрать персонажей от модели."
          : "Не удалось разобрать сцены от модели.";
        sendJson(response, 502, { error: errorMessage });
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
