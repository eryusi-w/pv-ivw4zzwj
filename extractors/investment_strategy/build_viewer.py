"""output/analysis_*.json을 모아 단일 viewer.html을 생성합니다.

사용법: python build_viewer.py [output_dir] [viewer_path]
새 분석 후 뷰어를 갱신하려면 다시 실행하세요.
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CHANNELS, DEFAULT_OUTPUT_DIR

TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>투자 전략 분석 뷰어</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Malgun Gothic', sans-serif;
    background: #f1f5f9;
    color: #1a1a2e;
    line-height: 1.6;
  }

  .toolbar {
    position: sticky; top: 0; z-index: 10;
    background: #1e293b;
    color: #fff;
    padding: 0.9rem 1.5rem;
    display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;
  }
  .toolbar .brand { font-weight: 700; font-size: 1.05rem; margin-right: 0.5rem; }
  .toolbar label { font-size: 0.85rem; color: #94a3b8; }
  .toolbar select {
    background: #0f172a; color: #e2e8f0; border: 1px solid #475569;
    border-radius: 6px; padding: 0.4rem 0.6rem; font-size: 0.9rem;
  }
  .toolbar .count { margin-left: auto; font-size: 0.85rem; color: #94a3b8; }

  .layout { display: flex; max-width: 1200px; margin: 1.5rem auto; gap: 1.5rem; padding: 0 1rem; }

  .sidebar {
    width: 220px; flex-shrink: 0;
    background: #fff; border-radius: 12px; padding: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    align-self: flex-start; position: sticky; top: 70px;
  }
  .sidebar h3 { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.6rem; }
  .channel-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0.7rem; border-radius: 8px; cursor: pointer;
    font-size: 0.9rem; margin-bottom: 2px;
  }
  .channel-item:hover { background: #f1f5f9; }
  .channel-item.active { background: #eff6ff; color: #2563eb; font-weight: 600; }
  .channel-item .badge {
    font-size: 0.7rem; background: #e2e8f0; color: #475569;
    border-radius: 10px; padding: 0.1rem 0.5rem;
  }
  .channel-item.active .badge { background: #2563eb; color: #fff; }

  .wrap { flex: 1; min-width: 0; }

  .report-header {
    background: #fff; border-radius: 12px; padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 1rem;
  }
  .report-header h1 { font-size: 1.3rem; margin-bottom: 0.25rem; }
  .report-header .meta { font-size: 0.82rem; color: #64748b; }

  details.strategy {
    background: #fff; border-radius: 12px; margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); overflow: hidden;
  }
  details.strategy summary {
    padding: 1rem 1.5rem; font-weight: 600; cursor: pointer; font-size: 0.95rem;
  }
  details.strategy .strategy-body {
    padding: 0 1.5rem 1.5rem; border-top: 1px solid #f1f5f9; font-size: 0.92rem;
  }
  details.strategy .strategy-body h2 { font-size: 1.1rem; margin: 1.25rem 0 0.5rem; color: #1e3a5f; }
  details.strategy .strategy-body h3 { font-size: 1rem; margin: 1rem 0 0.4rem; color: #2d4a6b; }
  details.strategy .strategy-body ul { padding-left: 1.4rem; margin-bottom: 0.6rem; }
  details.strategy .strategy-body li { margin-bottom: 0.3rem; }
  details.strategy .strategy-body table { width: 100%; border-collapse: collapse; margin: 0.75rem 0; font-size: 0.85rem; }
  details.strategy .strategy-body th, details.strategy .strategy-body td {
    border: 1px solid #e2e8f0; padding: 0.5rem 0.7rem; text-align: left; vertical-align: top;
  }
  details.strategy .strategy-body th { background: #f1f5f9; }
  details.strategy .strategy-body p { margin-bottom: 0.6rem; }

  .video-card {
    background: #fff; border-radius: 12px; padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 1rem;
  }
  .video-card h2 { font-size: 1.1rem; margin-bottom: 0.3rem; }
  .video-card .vmeta { font-size: 0.8rem; color: #64748b; margin-bottom: 1rem; display: flex; gap: 0.8rem; flex-wrap: wrap; align-items: center; }
  .sentiment {
    display: inline-block; font-size: 0.75rem; font-weight: 600;
    padding: 0.15rem 0.6rem; border-radius: 12px;
  }
  .sentiment.bullish { background: #dcfce7; color: #166534; }
  .sentiment.bearish { background: #fee2e2; color: #991b1b; }
  .sentiment.neutral { background: #fef3c7; color: #92400e; }
  .sentiment.other { background: #e2e8f0; color: #475569; }

  .field { margin-bottom: 0.9rem; font-size: 0.92rem; }
  .field .label { font-size: 0.78rem; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 0.2rem; }
  .field ul { padding-left: 1.3rem; }
  .field li { margin-bottom: 0.2rem; }
  .field a { color: #2563eb; }
  .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .tag { background: #eff6ff; color: #1e40af; border-radius: 6px; padding: 0.15rem 0.55rem; font-size: 0.8rem; font-weight: 500; }
  .tag.stock { background: #f0fdf4; color: #166534; }

  .empty {
    background: #fff; border-radius: 12px; padding: 3rem; text-align: center;
    color: #94a3b8; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }

  @media (max-width: 800px) {
    .layout { flex-direction: column; }
    .sidebar { width: 100%; position: static; display: flex; flex-wrap: wrap; gap: 0.3rem; }
    .channel-item { margin-bottom: 0; }
  }

  .channel-head {
    background: #fff; border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;
  }
  .channel-head .name { font-weight: 700; font-size: 1.05rem; }
  .channel-head .ch-url a { font-size: 0.8rem; color: #2563eb; }
</style>
</head>
<body>

<div class="toolbar">
  <span class="brand">📈 투자 전략 분석 뷰어</span>
  <label>분석 일시
    <select id="dateSelect"></select>
  </label>
  <span class="count" id="resultCount"></span>
</div>

<div class="layout">
  <aside class="sidebar">
    <h3>채널</h3>
    <div id="channelList"></div>
  </aside>
  <main class="wrap" id="main"></main>
</div>

<script>
const ANALYSES = __DATA__;
const ALL_CHANNELS = __CHANNELS__;

const SENTIMENT_KO = { bullish: "강세", bearish: "약세", neutral: "중립" };
const SENTIMENT_CLASS = { bullish: "bullish", bearish: "bearish", neutral: "neutral" };

let analysisIdx = 0;
let channel = "__home__";

const dateSelect = document.getElementById('dateSelect');
const channelList = document.getElementById('channelList');
const main = document.getElementById('main');
const resultCount = document.getElementById('resultCount');

function current() { return ANALYSES[analysisIdx]; }

function populateDates() {
  dateSelect.innerHTML = ANALYSES.map((a, i) =>
    `<option value="${i}">${a.generated_at}</option>`).join('');
  dateSelect.value = analysisIdx;
}

function videosFor(name) {
  const a = current();
  return a.channels.filter(c => c.name === name)
    .flatMap(c => c.videos || []);
}

function channelUrl(name) {
  const found = ALL_CHANNELS.find(c => c.name === name);
  return found ? found.url : "";
}

function populateChannels() {
  const items = [{ key: "__home__", label: "🏠 종합 전략" }]
    .concat(ALL_CHANNELS.map(c => ({
      key: c.name,
      label: c.name,
      count: videosFor(c.name).length,
    })));

  if (channel !== "__home__" && !ALL_CHANNELS.some(c => c.name === channel)) {
    channel = "__home__";
  }

  channelList.innerHTML = items.map(it => `
    <div class="channel-item ${it.key === channel ? 'active' : ''}" data-ch="${esc(it.key)}">
      <span>${esc(it.label)}</span>
      ${it.count != null ? `<span class="badge">${it.count}</span>` : ''}
    </div>`).join('');
  channelList.querySelectorAll('.channel-item').forEach(el => {
    el.onclick = () => { channel = el.dataset.ch; refreshChannelsOnly(); };
  });
}

function refreshChannelsOnly() {
  populateChannels();
  render();
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, m =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

function asList(v) {
  if (Array.isArray(v)) return v;
  if (v == null || v === '') return [];
  return [String(v)];
}

function renderVideo(v) {
  const sent = (v.sentiment || '').toLowerCase();
  const sentClass = SENTIMENT_CLASS[sent] || 'other';
  const sentLabel = SENTIMENT_KO[sent] || v.sentiment || '-';
  const sectors = asList(v.sectors).map(s => `<span class="tag">${esc(s)}</span>`).join('');
  const stocks = asList(v.stocks).map(s => `<span class="tag stock">${esc(s)}</span>`).join('');
  const points = asList(v.key_points);
  const risks = asList(v.risks);
  return `
  <article class="video-card">
    <h2>${esc(v.title || 'Untitled')}</h2>
    <div class="vmeta">
      <span>게시일: ${esc(v.published_at || '-')}</span>
      <span class="sentiment ${sentClass}">${esc(sentLabel)}</span>
      ${v.confidence ? `<span>신뢰도: ${esc(v.confidence)}</span>` : ''}
      ${v.url ? `<a href="${esc(v.url)}" target="_blank">영상 링크 ↗</a>` : ''}
    </div>
    ${v.thesis ? `<div class="field"><div class="label">핵심 주장</div><p>${esc(v.thesis)}</p></div>` : ''}
    ${points.length ? `<div class="field"><div class="label">주요 포인트</div>
      <ul>${points.map(p => `<li>${esc(p)}</li>`).join('')}</ul></div>` : ''}
    ${sectors ? `<div class="field"><div class="label">섹터</div><div class="tags">${sectors}</div></div>` : ''}
    ${stocks ? `<div class="field"><div class="label">종목</div><div class="tags">${stocks}</div></div>` : ''}
    ${v.strategy_short ? `<div class="field"><div class="label">단기 전략</div><p>${esc(v.strategy_short)}</p></div>` : ''}
    ${v.strategy_long ? `<div class="field"><div class="label">중장기 전략</div><p>${esc(v.strategy_long)}</p></div>` : ''}
    ${risks.length ? `<div class="field"><div class="label">리스크</div>
      <ul>${risks.map(r => `<li>${esc(r)}</li>`).join('')}</ul></div>` : ''}
  </article>`;
}

function render() {
  const a = current();

  let html = `
    <div class="report-header">
      <h1>투자 전략 리포트 — ${esc(a.generated_at)}</h1>
      <div class="meta">${a.channels.length}개 채널 분석 결과</div>
    </div>`;

  if (channel === "__home__") {
    if (a.strategy_html) {
      html += `<details class="strategy" open>
        <summary>📊 종합 투자 전략</summary>
        <div class="strategy-body">${a.strategy_html}</div>
      </details>`;
    } else {
      html += `<div class="empty">이 회차에는 종합 전략이 없습니다.</div>`;
    }
    html += `<div class="channel-head" style="margin-top:1rem">
      <span class="name">채널별 분석 영상</span></div>`;
    for (const c of ALL_CHANNELS) {
      const n = videosFor(c.name).length;
      const url = channelUrl(c.name);
      html += `<div class="channel-head">
        <span class="name" style="font-size:0.95rem">${esc(c.name)}</span>
        <span style="font-size:0.85rem;color:#64748b">영상 ${n}건
          ${url ? ` · <a href="${esc(url)}" target="_blank" style="color:#2563eb">채널 ↗</a>` : ''}</span>
      </div>`;
    }
    main.innerHTML = html;
    resultCount.textContent = `영상 ${a.channels.reduce((s, c) => s + (c.videos || []).length, 0)}건`;
    return;
  }

  const names = [channel];
  let total = 0;
  for (const name of names) {
    const videos = videosFor(name);
    total += videos.length;
    const url = channelUrl(name);
    html += `
      <div class="channel-head">
        <span class="name">${esc(name)}</span>
        <span class="ch-url">${url ? `<a href="${esc(url)}" target="_blank">채널 페이지 ↗</a>` : ''}</span>
      </div>`;
    if (!videos.length) {
      html += `<div class="empty" style="margin-bottom:1rem">분석된 영상이 없습니다.</div>`;
    } else {
      html += videos.map(renderVideo).join('');
    }
  }

  main.innerHTML = html;
  resultCount.textContent = `영상 ${total}건`;
}

function refresh() {
  populateDates();
  populateChannels();
  render();
}

dateSelect.onchange = () => { analysisIdx = +dateSelect.value; refresh(); };

refresh();
</script>
</body>
</html>
"""


def build(output_dir: str = DEFAULT_OUTPUT_DIR, viewer_path: str = "viewer.html") -> str | None:
    """output/analysis_*.json을 모아 viewer.html을 생성. 분석 없으면 None."""
    files = sorted(glob.glob(os.path.join(output_dir, "analysis_*.json")))
    analyses = []
    for path in files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data.pop("date", None)
        data.pop("stamp", None)
        analyses.append(data)
    analyses.sort(key=lambda a: a.get("generated_at", ""), reverse=True)

    if not analyses:
        print("analysis_*.json 파일이 없습니다. 먼저 분석을 실행하거나 backfill_analyses.py를 실행하세요.")
        return None

    channels_meta = [{"name": c["name"], "url": c["url"]} for c in CHANNELS]
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(analyses, ensure_ascii=False))
            .replace("__CHANNELS__", json.dumps(channels_meta, ensure_ascii=False)))
    with open(viewer_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{viewer_path} 생성 완료 ({len(analyses)}개 분석, {os.path.getsize(viewer_path)//1024}KB)")
    return viewer_path


def main() -> None:
    output_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR
    viewer_path = sys.argv[2] if len(sys.argv) > 2 else "viewer.html"
    if build(output_dir, viewer_path) is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
