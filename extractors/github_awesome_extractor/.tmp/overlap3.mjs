import fs from "node:fs";
const titles = [];
for (let p = 1; p <= 4; p++) {
  const u = `https://blog.naver.com/PostTitleListAsync.naver?blogId=ryusi79&viewdate=&currentPage=${p}&categoryNo=0&parentCategoryNo=&countPerPage=30`;
  const r = await fetch(u, { headers: { "user-agent": "Mozilla/5.0" } });
  const j = JSON.parse((await r.text()).slice((await r.text ? 0 : 0)) || "{}");
  for (const it of j.postList || []) titles.push(decodeURIComponent(it.title.replace(/\+/g, " ")));
}
console.log("blog titles:", titles.length);
const flat = titles.map((t) => t.toLowerCase().replace(/[^a-z0-9가-힣]/g, "")).join("|");
const en = JSON.parse(fs.readFileSync("output/manuagi_repos.enriched.json", "utf8").replace(/^\uFEFF/, ""));
const rows = (en.repos || []).map((x) => {
  const [owner, repo] = (x.full_name || "").split("/");
  const k = [repo, owner].filter((s) => s && s.length >= 4).map((s) => s.toLowerCase().replace(/[^a-z0-9]/g, ""));
  const hit = k.some((s) => flat.includes(s));
  return { stars: x.stars ?? 0, full: x.full_name, cat: x.analysis?.category || "", ko: (x.analysis?.summary_ko || x.description || "").slice(0, 50), hit };
});
const A = rows.filter((x) => x.stars >= 10000).sort((a, b) => b.stars - a.stars);
const p = A.filter((x) => x.hit), u = A.filter((x) => !x.hit);
console.log(`tierA ${A.length} / published ${p.length} / unpublished ${u.length}`);
console.log("--- tierA 미발행 ---");
for (const x of u) console.log(`  ${x.stars}\t${x.full}\t${x.cat}\t${x.ko}`);
console.log("--- tierA 발행됨 ---");
for (const x of p) console.log(`  ${x.stars}\t${x.full}`);
