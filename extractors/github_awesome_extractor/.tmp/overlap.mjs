import fs from "node:fs";
const decode = (s) => String(s).replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/<[^>]+>/g, "");
const titles = [];
for (let p = 1; p <= 4; p++) {
  const u = `https://blog.naver.com/PostTitleListAsync.naver?blogId=ryusi79&viewdate=&currentPage=${p}&categoryNo=0&parentCategoryNo=&countPerPage=30`;
  const r = await fetch(u, { headers: { "user-agent": "Mozilla/5.0" } });
  const t = await r.text();
  const body = t.slice(t.indexOf("{"));
  let j = null;
  try { j = JSON.parse(body); } catch { break; }
  const list = j.titleList || [];
  if (!list.length) break;
  for (const it of list) titles.push(decode(it.title));
}
console.log("blog titles:", titles.length);
const published = titles.join(" | ").toLowerCase();
const arr = JSON.parse(fs.readFileSync("output/manuagi_repos.enriched.json", "utf8").replace(/^\uFEFF/, ""));
const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
const rows = arr.map((r) => {
  const repo = (r.full_name || "").split("/")[1] || "";
  const owner = (r.full_name || "").split("/")[0] || "";
  const keys = [norm(repo), norm(owner)].filter((k) => k.length >= 4);
  const hit = keys.some((k) => norm(published).includes(k));
  return { stars: r.stars ?? 0, full: r.full_name, lang: r.language, cat: r.analysis?.category || "", dom: r.analysis?.domain || "", ko: (r.analysis?.summary_ko || r.description || "").slice(0, 60), hit };
});
const A = rows.filter((r) => r.stars >= 10000);
console.log(`tierA(>=10k): ${A.length}, published: ${A.filter((r) => r.hit).length}`);
console.log(`tierB(1k~10k): ${rows.filter((r) => r.stars >= 1000 && r.stars < 10000).length}, tierC(<1k): ${rows.filter((r) => r.stars < 1000).length}`);
const cluster = (s) => {
  const x = s.toLowerCase();
  if (/ollama|local|llm|webui|model|inference|self.?host|gateway|router/.test(x)) return "로컬LLM";
  if (/workflow|automation|n8n|scrap|crawl|ppt|slide|doc|office|excel/.test(x)) return "자동화";
  if (/design|ui|ux|front|figma|css|landing/.test(x)) return "디자인";
  if (/agent|coding|claude|codex|harness|skill|mcp|token|context/.test(x)) return "에이전트";
  if (/image|video|3d|cad|audio|render/.test(x)) return "미디어";
  return "기타";
};
const pub = A.filter((r) => r.hit), un = A.filter((r) => !r.hit);
const cnt = (list) => list.reduce((m, r) => { const c = cluster(r.full + " " + r.cat + " " + r.ko); m[c] = (m[c] || 0) + 1; return m; }, {});
console.log("A-published clusters:", JSON.stringify(cnt(pub)));
console.log("A-unpublished clusters:", JSON.stringify(cnt(un)));
console.log("--- A 미발행 상위 (stars desc) ---");
for (const r of un.slice().sort((a, b) => b.stars - a.stars).slice(0, 40)) console.log(`  ${r.stars}\t${r.full}\t${cluster(r.full + " " + r.cat + " " + r.ko)}\t${r.cat}\t${r.ko}`);
fs.writeFileSync(".tmp/titles.txt", titles.join("\n"));
