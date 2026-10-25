import { createReadStream, existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { spawn } from "node:child_process";
import { dirname, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const appDir = dirname(fileURLToPath(import.meta.url));
const root = resolve(appDir, "..");
const preferredPort = Number(process.env.PORT || 5174);
const exportDirectory = resolve(root, "output", "franchises");

function latestPublicDataFile() {
  const fileName = readdirSync(exportDirectory)
    .filter((name) => /^GETFRANCHISE_BRAND_DATA_\d{4}-\d{2}-\d{2}\.json$/i.test(name))
    .sort()
    .at(-1);

  return fileName ? resolve(exportDirectory, fileName) : null;
}

const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
};

const server = createServer((request, response) => {
  const url = new URL(request.url || "/", `http://${request.headers.host}`);
  if (url.pathname === "/") {
    response.writeHead(302, { Location: "/GetfranchiseAi/" });
    response.end();
    return;
  }
  const requested = normalize(decodeURIComponent(url.pathname)).replace(/^[/\\]+/, "");
  const publicDataRoute = requested.replaceAll("\\", "/");
  const isPublicDataRequest = publicDataRoute === "GetfranchiseAi/data/brands.json";
  let filePath = isPublicDataRequest ? latestPublicDataFile() : resolve(root, requested);

  // This is a local preview server, but it must still behave like a public
  // site: only UI assets and the public directory export are readable.
  // Research reports, workspace artifacts, SQLite files, and .env files stay
  // outside the served surface.
  const relativeToApp = filePath === appDir || filePath.startsWith(`${appDir}\\`) || filePath.startsWith(`${appDir}/`);
  const hasHiddenSegment = requested.split(/[\\/]+/).some((segment) => segment.startsWith("."));
  if (!filePath || hasHiddenSegment || (!relativeToApp && !isPublicDataRequest)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  if (existsSync(filePath) && statSync(filePath).isDirectory()) {
    filePath = join(filePath, "index.html");
  }

  if (!existsSync(filePath)) {
    response.writeHead(404);
    response.end("Not found");
    return;
  }

  // This hash is supplied by the preview/build environment. Never place a raw
  // founder passphrase in the repository or in client markup.
  if (extname(filePath).toLowerCase() === ".html") {
    const betaConfig = JSON.stringify({ founderPassphraseHash: process.env.GETFRANCHISE_FOUNDER_TIER_HASH || "" });
    const html = readFileSync(filePath, "utf8").replace("<script src=\"app.js\" defer></script>", `<script>window.__GETFRANCHISE_BETA_CONFIG__=${betaConfig};</script><script src="app.js" defer></script>`);
    response.writeHead(200, { "Content-Type": types[".html"], "Cache-Control": "no-store" });
    response.end(html);
    return;
  }

  response.writeHead(200, {
    "Content-Type": types[extname(filePath).toLowerCase()] || "application/octet-stream",
    "Cache-Control": "no-store",
  });
  createReadStream(filePath).pipe(response);
});

function listen(port, attemptsLeft = 10) {
  server.once("error", (error) => {
    if (error.code === "EADDRINUSE" && attemptsLeft > 0) {
      listen(port + 1, attemptsLeft - 1);
      return;
    }
    console.error(error.message);
    process.exitCode = 1;
  });

  server.listen(port, () => {
    const url = `http://localhost:${port}/GetfranchiseAi/`;
    console.log("");
    console.log("Getfranchise local site is running.");
    console.log(url);
    console.log("");
    console.log("Keep this window open while using the site.");
    openBrowser(url);
  });
}

listen(preferredPort);

function openBrowser(url) {
  if (process.env.NO_OPEN === "1") return;

  const command =
    process.platform === "win32"
      ? ["cmd", ["/c", "start", "", url]]
      : process.platform === "darwin"
        ? ["open", [url]]
        : ["xdg-open", [url]];

  const child = spawn(command[0], command[1], {
    detached: true,
    stdio: "ignore",
    shell: false,
  });
  child.unref();
}
