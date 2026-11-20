"""output/analysis_*.json을 모아 4대 카테고리 통합 viewer.html 대시보드를 생성합니다."""
from __future__ import annotations

import glob
import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import DEFAULT_OUTPUT_DIR

VIEWER_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>4대 카테고리 블로그 글감 뷰어</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Malgun Gothic', sans-serif;
    background: #f1f5f9; color: #1a1a2e; line-height: 1.6;
  }
  .toolbar {
    position: sticky; top: 0; z-index: 10;
    background: #1e293b; color: #fff;
    padding: 0.8rem 1.5rem;
    display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }
  .toolbar .brand { font-weight: 700; font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem; }
  .toolbar select {
    background: #0f172a; color: #e2e8f0; border: 1px solid #475569;
    border-radius: 6px; padding: 0.4rem 0.8rem; font-size: 0.9rem;
    cursor: pointer;
  }
  .toolbar .count { margin-left: auto; font-size: 0.85rem; color: #94a3b8; }

  .layout { display: flex; max-width: 1300px; margin: 1.5rem auto; gap: 1.5rem; padding: 0 1rem; }

  .sidebar {
    width: 240px; flex-shrink: 0;
    background: #fff; border-radius: 12px; padding: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    position: sticky; top: 70px; align-self: flex-start;
  }
  .sidebar h3 { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.8rem; }
  .filter-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0.75rem; border-radius: 8px; cursor: pointer;
    font-size: 0.88rem; margin-bottom: 4px; color: #334155;
  }
  .filter-item:hover { background: #f1f5f9; }
  .filter-item.active { background: #eff6ff; color: #2563eb; font-weight: 600; }
  .badge-count {
    font-size: 0.75rem; background: #e2e8f0; color: #475569;
    border-radius: 10px; padding: 0.1rem 0.5rem;
  }
  .filter-item.active .badge-count { background: #2563eb; color: #fff; }

  .content { flex: 1; min-width: 0; }
  .header-card {
    background: #fff; border-radius: 12px; padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    display: flex; justify-content: space-between; align-items: center;
  }
  .header-card h2 { font-size: 1.25rem; color: #0f172a; }
  .header-card .date { font-size: 0.85rem; color: #64748b; }

  .cards-grid { display: flex; flex-direction: column; gap: 1.2rem; }
  .card {
    background: #fff; border-radius: 12px; padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }
  .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
  .cat-pill {
    background: #e0e7ff; color: #3730a3; padding: 0.2rem 0.6rem;
    border-radius: 6px; font-size: 0.75rem; font-weight: 600;
  }
  .card-source { font-size: 0.8rem; color: #64748b; }
  .card-title { font-size: 1.2rem; font-weight: 700; color: #1e293b; margin-bottom: 0.6rem; line-height: 1.4; }
  .card-summary { font-size: 0.95rem; color: #475569; margin-bottom: 1rem; line-height: 1.5; }

  .sec-heading { font-size: 0.85rem; font-weight: 700; color: #0f172a; margin: 0.8rem 0 0.3rem; }
  .feat-list, .step-list { padding-left: 1.2rem; font-size: 0.9rem; color: #334155; }
  .feat-list li, .step-list li { margin-bottom: 0.25rem; }
  .code-box {
    background: #0f172a; color: #e2e8f0; padding: 0.8rem 1rem;
    border-radius: 8px; font-size: 0.85rem; overflow-x: auto;
    margin-top: 0.4rem; white-space: pre-wrap; font-family: Consolas, monospace;
  }
  .tag-row { margin-top: 1rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .tag { background: #f1f5f9; color: #2563eb; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }

  .card-bottom { margin-top: 1.2rem; display: flex; justify-content: flex-end; }
  .link-btn {
    display: inline-block; padding: 0.4rem 0.8rem; background: #2563eb; color: #fff;
    text-decoration: none; border-radius: 6px; font-size: 0.85rem; font-weight: 500;
  }
  .link-btn:hover { background: #1d4ed8; }

  @media (max-width: 768px) {
    .layout { flex-direction: column; }
    .sidebar { width: 100%; position: static; }
  }
</style>
</head>
<body>

<div class="toolbar">
  <div class="brand">📊 4대 카테고리 글감 뷰어</div>
  <label for="dateSelect">수집 일자:</label>
  <select id="dateSelect" onchange="switchDate(this.value)"></select>
  <div class="count" id="itemCount">0개 항목</div>
</div>

<div class="layout">
  <div class="sidebar">
    <h3>카테고리 선택</h3>
    <div id="filterList"></div>
  </div>

  <div class="content">
    <div class="header-card">
      <h2 id="currentDateTitle">수집 데이터</h2>
      <div class="date" id="currentGeneratedAt"></div>
    </div>
    <div class="cards-grid" id="cardsGrid"></div>
  </div>
</div>

<script>
const ANALYSES = __ANALYSES_DATA__;
let currentDateKey = Object.keys(ANALYSES)[0] || "";
let currentCategory = "전체";

function init() {
  const dateSelect = document.getElementById("dateSelect");
  dateSelect.innerHTML = "";
  
  const dates = Object.keys(ANALYSES);
  if (dates.length === 0) {
    document.getElementById("cardsGrid").innerHTML = "<p style='padding:2rem;text-align:center;'>수집된 데이터가 없습니다.</p>";
    return;
  }

  dates.forEach(dateKey => {
    const opt = document.createElement("option");
    opt.value = dateKey;
    opt.textContent = `${ANALYSES[dateKey].generated_at || dateKey} (${ANALYSES[dateKey].items.length}건)`;
    dateSelect.appendChild(opt);
  });

  if (!currentDateKey && dates.length > 0) {
    currentDateKey = dates[0];
  }
  dateSelect.value = currentDateKey;

  render();
}

function switchDate(dateKey) {
  currentDateKey = dateKey;
  currentCategory = "전체";
  render();
}

function selectCategory(cat) {
  currentCategory = cat;
  renderCards();
  renderFilters();
}

function render() {
  const data = ANALYSES[currentDateKey];
  if (!data) return;

  document.getElementById("currentDateTitle").textContent = `수집 리포트 (${data.timestamp || currentDateKey})`;
  document.getElementById("currentGeneratedAt").textContent = `생성일시: ${data.generated_at}`;

  renderFilters();
  renderCards();
}

function renderFilters() {
  const data = ANALYSES[currentDateKey];
  if (!data) return;

  const counts = { "전체": data.items.length };
  data.items.forEach(it => {
    const cat = it.main_category || "기타";
    counts[cat] = (counts[cat] || 0) + 1;
  });

  const filterList = document.getElementById("filterList");
  filterList.innerHTML = "";

  Object.keys(counts).forEach(cat => {
    const item = document.createElement("div");
    item.className = "filter-item" + (currentCategory === cat ? " active" : "");
    item.onclick = () => selectCategory(cat);
    item.innerHTML = `<span>${cat}</span><span class="badge-count">${counts[cat]}</span>`;
    filterList.appendChild(item);
  });
}

function renderCards() {
  const data = ANALYSES[currentDateKey];
  if (!data) return;

  const filtered = currentCategory === "전체" 
    ? data.items 
    : data.items.filter(it => (it.main_category || "기타") === currentCategory);

  document.getElementById("itemCount").textContent = `총 ${filtered.length}개 표시 중`;

  const grid = document.getElementById("cardsGrid");
  grid.innerHTML = "";

  if (filtered.length === 0) {
    grid.innerHTML = "<p style='padding:2rem;text-align:center;color:#64748b;'>해당 카테고리의 항목이 없습니다.</p>";
    return;
  }

  filtered.forEach(it => {
    const card = document.createElement("div");
    card.className = "card";

    const features = (it.core_features || []).map(f => `<li>${f}</li>`).join("");
    const steps = (it.step_by_step || []).map(s => `<li>${s}</li>`).join("");
    const tags = (it.keywords || []).map(k => `<span class="tag">#${k}</span>`).join("");

    card.innerHTML = `
      <div class="card-top">
        <span class="cat-pill">${it.main_category} &gt; ${it.sub_category || '일반'}</span>
        <span class="card-source">${it.source_name || ''}</span>
      </div>
      <div class="card-title">${it.blog_title_candidate || it.title}</div>
      <div class="card-summary">${it.summary || ''}</div>
      
      <div class="sec-heading">🎯 대상 독자</div>
      <p style="font-size:0.9rem;color:#475569;">${it.target_audience || '독자'}</p>

      <div class="sec-heading">✨ 핵심 특징</div>
      <ul class="feat-list">${features}</ul>

      <div class="sec-heading">🚀 3단계 실천 가이드</div>
      <ol class="step-list">${steps}</ol>

      <div class="sec-heading">💡 실전 팁 / 프롬프트 / 설정</div>
      <div class="code-box">${it.practical_prompt_or_tips || ''}</div>

      <div class="tag-row">${tags}</div>

      <div class="card-bottom">
        ${it.url ? `<a href="${it.url}" target="_blank" class="link-btn">원문/공식 링크 →</a>` : ''}
      </div>
    `;
    grid.appendChild(card);
  });
}

window.onload = init;
</script>
</body>
</html>
"""


def build_viewer(output_dir: str = DEFAULT_OUTPUT_DIR, viewer_path: str | None = None) -> str:
    norm_output = os.path.normpath(os.path.join(CURRENT_DIR, output_dir))
    if viewer_path is None:
        viewer_path = os.path.join(norm_output, "viewer.html")

    json_files = glob.glob(os.path.join(norm_output, "analysis_*.json"))
    json_files.sort(reverse=True)

    analyses_map = {}
    for jf in json_files:
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
                base = os.path.splitext(os.path.basename(jf))[0]
                stamp = data.get("timestamp") or base.replace("analysis_", "")
                analyses_map[stamp] = data
        except Exception as e:
            print(f"[경고] {jf} 로드 실패: {e}", file=sys.stderr)

    json_str = json.dumps(analyses_map, ensure_ascii=False)
    html_content = VIEWER_TEMPLATE.replace("__ANALYSES_DATA__", json_str)

    with open(viewer_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return viewer_path


if __name__ == "__main__":
    out = build_viewer()
    print(f"뷰어 대시보드가 성공적으로 생성되었습니다: {out}")
