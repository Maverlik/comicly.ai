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

  return [
    "Create a complete comic book page for comicly.ai.",
    "The page must contain multiple panels with polished composition, clear panel borders, cinematic lighting, and readable speech bubbles.",
    `Story: ${payload.story}`,
    `Visual style: ${payload.style || "Anime"}.`,
    `Tone: ${toneMap[payload.tone] || payload.tone || "emotional"}.`,
    `Current page: ${payload.page || 1}. Selected scene: ${payload.selectedScene || 1}.`,
    payload.dialogue ? `Dialogue to include: ${payload.dialogue}` : "",
    payload.caption ? `Scene caption: ${payload.caption}` : "",
    payload.layout ? `Layout direction: ${payload.layout}` : "",
    "Use a dark purple and blue cinematic palette when it fits the story. Avoid watermarks, UI chrome, or extra explanatory text outside the comic page.",
  ]
    .filter(Boolean)
    .join("\n");
}

function extractImageUrl(data) {
  const message = data?.choices?.[0]?.message;
  const imageUrl = message?.images?.[0]?.image_url?.url;
  if (imageUrl) return imageUrl;

  if (Array.isArray(message?.content)) {
    for (const part of message.content) {
      if (part?.type === "image_url" && part.image_url?.url) return part.image_url.url;
      if (part?.type === "output_image" && part.image_url) return part.image_url;
    }
  }

  return null;
}

async function generateComicPage(request, response) {
  try {
    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
      sendJson(response, 500, {
        error: "OPENROUTER_API_KEY не найден. Добавьте ключ в файл .env.",
      });
      return;
    }

    const payload = await readJson(request);
    if (!payload.story || typeof payload.story !== "string") {
      sendJson(response, 400, { error: "Поле story обязательно." });
      return;
    }

    const model = process.env.OPENROUTER_IMAGE_MODEL || "openai/gpt-5.4-image-2";
    const prompt = buildImagePrompt(payload);

    const openRouterResponse = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "HTTP-Referer": process.env.OPENROUTER_SITE_URL || "http://localhost:3000",
        "X-Title": process.env.OPENROUTER_APP_NAME || "comicly.ai",
      },
      body: JSON.stringify({
        model,
        modalities: ["image", "text"],
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
        image_config: {
          aspect_ratio: process.env.OPENROUTER_IMAGE_ASPECT_RATIO || "1:1",
        },
      }),
    });

    const data = await openRouterResponse.json().catch(() => ({}));
    if (!openRouterResponse.ok) {
      sendJson(response, openRouterResponse.status, {
        error: data?.error?.message || data?.message || "OpenRouter вернул ошибку генерации.",
      });
      return;
    }

    const imageUrl = extractImageUrl(data);
    sendJson(response, 200, {
      imageUrl,
      model,
      text: data?.choices?.[0]?.message?.content || "",
    });
  } catch (error) {
    sendJson(response, 500, { error: error.message || "Ошибка сервера." });
  }
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
  if (request.method === "POST" && request.url === "/api/generate-comic-page") {
    generateComicPage(request, response);
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
