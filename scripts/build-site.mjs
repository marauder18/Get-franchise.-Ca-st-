import { cp, mkdir, readdir, rm, stat } from "node:fs/promises";
import { basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appDir = join(root, "GetfranchiseAi");
const exportDir = join(root, "output", "franchises");
const siteDir = join(root, "site");
const requiredAppFiles = ["index.html", "app.js", "styles.css", "Logo of Getfranchise.jpg"];

async function assertFile(path) {
  try {
    if (!(await stat(path)).isFile()) throw new Error("not a file");
  } catch {
    throw new Error(`Required launch file is missing: ${path}`);
  }
}

async function latestPublicExport() {
  const entries = await readdir(exportDir);
  const candidates = entries
    .filter((name) => /^GETFRANCHISE_BRAND_DATA_\d{4}-\d{2}-\d{2}\.json$/i.test(name))
    .sort();
  const name = candidates.at(-1);
  if (!name) throw new Error("No GETFRANCHISE_BRAND_DATA_YYYY-MM-DD.json export was found.");
  const path = join(exportDir, name);
  await assertFile(path);
  return path;
}

await rm(siteDir, { recursive: true, force: true });
await mkdir(join(siteDir, "data"), { recursive: true });

for (const name of requiredAppFiles) {
  const source = join(appDir, name);
  await assertFile(source);
  await cp(source, join(siteDir, name));
}

const publicImageDir = join(appDir, "assets", "images");
const publicImages = [
  "pexels-business-partners-cafe.jpg",
  "pexels-happy-business-team.jpg",
  "pexels-business-document-review.jpg",
  "pexels-business-team-thinking-office.jpg",
];
await mkdir(join(siteDir, "assets", "images"), { recursive: true });
for (const name of publicImages) {
  const source = join(publicImageDir, name);
  await assertFile(source);
  await cp(source, join(siteDir, "assets", "images", name));
}

// Hash routing needs an HTML fallback when a visitor reloads a shared route.
await cp(join(appDir, "index.html"), join(siteDir, "404.html"));
const dataFile = await latestPublicExport();
await cp(dataFile, join(siteDir, "data", "brands.json"));

console.log(`Built ${basename(dataFile)} for GitHub Pages in ${siteDir}`);
