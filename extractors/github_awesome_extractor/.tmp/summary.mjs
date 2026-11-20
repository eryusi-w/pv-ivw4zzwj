import fs from "node:fs";
const load = (p) => JSON.parse(fs.readFileSync(p, "utf8").replace(/^\uFEFF/, ""));
const en = load("output/manuagi_repos.enriched.json");
const arr = Array.isArray(en) ? en : (en.repos || en.items || en.data || []);
console.log("shape:", Array.isArray(en) ? "array" : Object.keys(en).slice(0, 6));
console.log("count:", arr.length);
console.log("keys:", Object.keys(arr[0] || {}).join(", "));
console.log("sample:", JSON.stringify(arr[0], null, 1).slice(0, 1000));
const lang = {};
for (const r of arr) { const l = r.language || r.lang || "-"; lang[l] = (lang[l] || 0) + 1; }
console.log("langs:", Object.entries(lang).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([k, v]) => `${k}:${v}`).join(" "));
const st = arr.map((r) => r.stars ?? r.stargazers_count ?? 0).sort((a, b) => b - a);
console.log("stars>=10000:", st.filter((s) => s >= 10000).length, " >=1000:", st.filter((s) => s >= 1000).length, " <100:", st.filter((s) => s < 100).length, " max:", st[0], " median:", st[Math.floor(st.length / 2)]);
console.log("top30:");
for (const r of arr.slice().sort((a, b) => (b.stars ?? 0) - (a.stars ?? 0)).slice(0, 30)) console.log(`  ${r.stars ?? 0}\t${r.full_name || r.name}\t${(r.description || "").slice(0, 80)}`);
const ex = load("output/extracted_tools.json");
const exArr = Array.isArray(ex) ? ex : (ex.tools || ex.items || []);
console.log("extracted_tools count:", exArr.length, "keys:", Object.keys(exArr[0] || {}).join(", "));
console.log("extracted sample:", JSON.stringify(exArr[0], null, 1).slice(0, 600));
