import fs from "node:fs";
const titles = [];
for (let p = 1; p <= 3; p++) {
  const u = `https://blog.naver.com/PostTitleListAsync.naver?blogId=ryusi79&viewdate=&currentPage=${p}&categoryNo=0&parentCategoryNo=&countPerPage=30`;
  const t = await (await fetch(u, { headers: { "user-agent": "Mozilla/5.0" } })).text();
  for (const s of t.match(/"title":"(?:[^"\]|\.)*"/g) || []) {
    const raw = s.slice(9, -1).replace(/\\"/g, '"');
    titles.push(decodeURIComponent(raw.replace(/\+/g, " ")));
  }
}
console.log("titles:", titles.length);
const flat = titles.join("|").toLowerCase().replace(/[^a-z0-9가-힣]/g, "");
const en = JSON.parse(fs.readFileSync("output/manuagi_repos.enriched.json", "utf8").replace(/^\uFEFF/, ""));
const rows = (en.repos || []).map((x) => {
  const [owner, repo] = (x.full_name || "").split("/");
  const keys = [repo, owner].filter((s) => s && s.length >= 4).map((s) => s.toLowerCase().replace(/[^a-z0-9]/g, ""));
  return { stars: x.stars ?? 0, full: x.full_name, cat: x.analysis?.category || "", hit: keys.some((k) => flat.includes(k)) };
});
const A = rows.filter((x) => x.stars >= 10000).sort((a, b) => b.stars - a.stars);
const pub = A.filter((x) => x.hit);
console.log(`tierA ${A.length} published ${pub.length} unpublished ${A.length - pub.length}`);
console.log("발행됨:", pub.map((x) => x.full).join(", "));
console.log("--- 미발행 tierA (stars | repo | category) ---");
for (const x of A.filter((y) => !y.hit)) console.log(`${x.stars}\t${x.full}\t${x.cat}`);
