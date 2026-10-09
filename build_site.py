#!/usr/bin/env python3
"""Generate situs dashboard cyber meneliti.github.io
Halaman: index (dashboard) + 4 sub-pages saling terhubung.
Tailwind CDN, animasi CSS murni, data repo live dari GitHub API,
tabel harga/trending ditarik realtime dari raw README saat dibuka.
"""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
WIB = timezone(timedelta(hours=7))
BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]

REPOS = [
    ("Harga-Emas-Terbaru-Hari-Ini", "harga-emas/", "💰", "Emas",
     "Harga emas batangan 1 gr dari 18 penyedia resmi, urut termurah→termahal + buyback."),
    ("Harga-Sembako-Terbaru", "harga-sembako/", "🛒", "Sembako",
     "26 komoditas Bapok lintas 38 provinsi, tabel per kategori + perubahan harian."),
    ("Trending-di-Indonesia", "trending/", "🔥", "Trending",
     "25 tren Google Trends ID: volume, % kenaikan, kueri terkait. Update 2 jam."),
    ("Ping-Hash", "ping-hash/", "📡", "Ping-Hash",
     "Uptime monitor berbasis git — commit ber-hash tiap 1–8 menit."),
]

# ambil deskripsi 500 kata dari generate lama (dipakai di sub-page "tentang")
OLD = os.path.join(ROOT, "generate_long_desc.py")


def md_inline(s):
    """Konversi markdown inline sederhana -> HTML."""
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong class='text-white'>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
               r"<a href='\2' target='_blank' rel='noopener' class='text-cyan-400 hover:underline'>\1</a>", s)
    return s


def md_table_html(md):
    """Konversi tabel markdown sederhana -> HTML rows (tanpa lib)."""
    rows = [r for r in md.strip().splitlines() if r.startswith("|")]
    if len(rows) < 3:
        return ""
    def cells(r):
        return [md_inline(c.strip()) for c in r.strip("|").split("|")]
    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    th = "".join(f"<th>{c}</th>" for c in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body)
    return f"<thead><tr>{th}</tr></thead><tbody>{tr}</tbody>"


def readme_table(path, table_index=0):
    p = os.path.expanduser(path)
    if not os.path.exists(p):
        return ""
    h = open(p, encoding="utf-8").read()
    tables = re.findall(r"(?:^\|.*\n\|[-| :]+\|.*\n(?:\|.*\n)+)", h, re.M)
    return md_table_html(tables[table_index]) if len(tables) > table_index else ""


BASE_CSS = """
  body { background:#030712; }
  .grid-bg {
    background-image:
      linear-gradient(rgba(34,211,238,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(34,211,238,0.04) 1px, transparent 1px);
    background-size: 44px 44px;
  }
  .glow-text { text-shadow: 0 0 16px rgba(34,211,238,.5); }
  .scanline::after {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:50;
    background:repeating-linear-gradient(0deg, rgba(0,0,0,.10) 0 1px, transparent 1px 3px);
  }
  .flicker { animation: flicker 5s infinite; }
  @keyframes flicker { 0%,93%,97%,100%{opacity:1} 95%{opacity:.7} }
  /* card hover lift */
  .card { transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease; }
  .card:hover { transform: translateY(-3px); }
  /* typing cursor */
  .cursor::after { content:'▌'; animation: blink 1s steps(1) infinite; color:#22d3ee; }
  @keyframes blink { 50% { opacity:0 } }
  /* pulse dot */
  .pulse { animation: pulse 2s ease-in-out infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
  /* fade-slide in */
  .reveal { opacity:0; transform: translateY(14px); animation: reveal .6s ease forwards; }
  @keyframes reveal { to { opacity:1; transform:none; } }
  .reveal-1{animation-delay:.05s} .reveal-2{animation-delay:.15s} .reveal-3{animation-delay:.25s}
  .reveal-4{animation-delay:.35s} .reveal-5{animation-delay:.45s} .reveal-6{animation-delay:.55s}
  /* bar chart grow */
  .bar { transform-origin: bottom; animation: grow 1s cubic-bezier(.2,.8,.2,1) forwards; transform: scaleY(0); }
  @keyframes grow { to { transform: scaleY(1); } }
  /* marquee ticker */
  .ticker-track { display:flex; gap:3rem; width:max-content; animation: ticker 40s linear infinite; }
  .ticker:hover .ticker-track { animation-play-state: paused; }
  @keyframes ticker { from { transform: translateX(0); } to { transform: translateX(-50%); } }
  /* progress shimmer */
  .shimmer { position:relative; overflow:hidden; }
  .shimmer::after {
    content:''; position:absolute; inset:0;
    background:linear-gradient(90deg, transparent, rgba(34,211,238,.15), transparent);
    animation: shimmer 2.5s infinite;
  }
  @keyframes shimmer { from { transform:translateX(-100%);} to { transform:translateX(100%);} }
  /* table */
  .dtable th { text-align:left; font-size:.72rem; letter-spacing:.08em; text-transform:uppercase;
    color:#67e8f9; border-bottom:1px solid rgba(34,211,238,.25); padding:.55rem .75rem; white-space:nowrap; }
  .dtable td { padding:.5rem .75rem; border-bottom:1px solid rgba(148,163,184,.08); font-size:.82rem; }
  .dtable tbody tr { transition: background .15s; }
  .dtable tbody tr:hover { background:rgba(34,211,238,.05); }
  .dtable tbody tr { animation: rowin .4s ease both; }
  @keyframes rowin { from { opacity:0; transform:translateX(-8px);} to { opacity:1; transform:none;} }
  /* nav active */
  .navlink.active { color:#22d3ee; text-shadow:0 0 12px rgba(34,211,238,.6); }
  .navlink.active::before { content:'▸ '; }
  /* scroll bar */
  ::-webkit-scrollbar { width:10px; height:10px; }
  ::-webkit-scrollbar-track { background:#030712; }
  ::-webkit-scrollbar-thumb { background:#164e63; border-radius:6px; }
  ::-webkit-scrollbar-thumb:hover { background:#0e7490; }
  /* clock digits */
  .clock { font-variant-numeric: tabular-nums; }
  /* sub-page hero underline sweep */
  .sweep { position:relative; }
  .sweep::after { content:''; position:absolute; left:0; bottom:-6px; height:2px; width:100%;
    background:linear-gradient(90deg,#22d3ee,#a855f7); transform:scaleX(0); transform-origin:left;
    transition:transform .4s ease; }
  .sweep:hover::after { transform:scaleX(1); }
"""

FOOTER = """
<footer class="border-t border-cyan-500/10 py-10 text-center mt-16">
  <p class="text-gray-500 text-sm font-mono">© {year} <a href="https://github.com/meneliti" class="text-cyan-400 hover:underline" target="_blank" rel="noopener">meneliti</a> · PT. Pastiin Siber Indonesia</p>
  <p class="text-gray-600 text-xs mt-2 font-mono">GitHub Pages · Tailwind CSS · Python · <a href="/" class="text-cyan-500 hover:underline">beranda</a></p>
  {counter_html}
</footer>
"""

COUNTER_HTML = ('<p class="mt-3"><img src="https://s01.flagcounter.com/countxl/qaoY/bg_FFFFFF/txt_000000/'
                'border_CCCCCC/columns_2/maxflags_10/viewers_0/labels_0/pageviews_1/flags_0/percent_0/" '
                'alt="pengunjung" class="inline-block rounded"></p>')

NAV_ITEMS = [("Beranda", "/", "index.html"), ("Emas", "/harga-emas/", "harga-emas/index.html"),
             ("Sembako", "/harga-sembako/", "harga-sembako/index.html"),
             ("Trending", "/trending/", "trending/index.html"),
             ("Ping-Hash", "/ping-hash/", "ping-hash/index.html")]


def nav(active):
    items = []
    for label, url, file in NAV_ITEMS:
        cls = "navlink active" if file == active else "navlink"
        href = url if file != active else "#"
        items.append(f'<a href="{href}" class="{cls} text-gray-400 hover:text-cyan-300 transition font-mono text-sm">{label}</a>')
    return "\n      ".join(items)


def page_shell(title, desc, active, body, extra_head=""):
    now = datetime.now(WIB)
    return f"""<!DOCTYPE html>
<html lang="id" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="meneliti">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="meneliti.github.io">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta name="theme-color" content="#030712">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔬</text></svg>">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"meneliti","url":"https://meneliti.github.io/"}}</script>
<style>{BASE_CSS}</style>
{extra_head}
</head>
<body class="scanline font-mono text-gray-200 antialiased">
<nav class="sticky top-0 z-40 backdrop-blur bg-gray-950/85 border-b border-cyan-500/20">
  <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
    <a href="/" class="font-bold text-cyan-400 glow-text flicker whitespace-nowrap">🔬 meneliti<span class="text-fuchsia-400">.io</span></a>
    <div class="hidden md:flex gap-5 items-center">
      {nav(active)}
    </div>
    <div class="clock text-cyan-400 text-sm hidden sm:block" id="clock"></div>
  </div>
</nav>
{body}
{FOOTER.format(year=now.year, counter_html=COUNTER_HTML if active == "index.html" else "")}
<script>
// jam WIB live
(function tick(){{
  const el = document.getElementById('clock');
  if (el) {{
    const now = new Date(Date.now() + (new Date().getTimezoneOffset() + 420) * 60000);
    el.textContent = now.toTimeString().slice(0, 8) + ' WIB';
  }}
  requestAnimationFrame(() => setTimeout(tick, 1000));
}})();
// animasi reveal saat scroll
const io = new IntersectionObserver(es => es.forEach(e => {{
  if (e.isIntersecting) {{ e.target.classList.add(...('reveal reveal-'+(2+Math.floor(Math.random()*4))).split(' ')); io.unobserve(e.target); }}
}}), {{threshold:.1}});
document.querySelectorAll('.card, .dtable').forEach(el => io.observe(el));
</script>
</body>
</html>"""


# ---------- helpers live data ----------

LIVE_JS = """
async function fetchReadmeTable(url, targetId, opts = {}) {
  const el = document.getElementById(targetId);
  if (!el) return;
  try {
    const res = await fetch(url, {cache: 'no-store'});
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const md = await res.text();
    const lines = md.split('\\n');
    // ambil tabel markdown terbesar
    let best = [], cur = [];
    for (const l of lines) {
      if (l.trim().startsWith('|')) cur.push(l);
      else { if (cur.length > best.length) best = cur; cur = []; }
    }
    if (cur.length > best.length) best = cur;
    if (best.length < 3) throw new Error('no table');
    const cells = r => r.trim().replace(/^\\||\\|$/g, '').split('|').map(c => c.trim());
    const mdInline = s => s
      .replace(/\\*\\*(.+?)\\*\\*/g, '<strong class="text-white">$1</strong>')
      .replace(/\\[([^\\]]+)\\]\\((https?:\\/\\/[^)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener" class="text-cyan-400 hover:underline">$1</a>');
    const head = cells(best[0]);
    const body = best.slice(2).map(cells);
    let html = '<thead><tr>' + head.map(h => '<th>' + mdInline(h) + '</th>').join('') + '</tr></thead><tbody>';
    body.forEach((row, i) => {
      html += '<tr style="animation-delay:' + Math.min(i*0.04, 1.2) + 's">' +
        row.map(c => '<td>' + mdInline(c) + '</td>').join('') + '</tr>';
    });
    html += '</tbody>';
    el.innerHTML = html;
    el.closest('.shimmer')?.classList.remove('shimmer');
    if (opts.after) opts.after(body);
  } catch (e) {
    el.innerHTML = '<tr><td colspan="8" class="text-gray-500">⚠ gagal memuat data live (' + e.message + ') — buka repo untuk snapshot</td></tr>';
    el.closest('.shimmer')?.classList.remove('shimmer');
  }
}
"""


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {path} ({len(content):,} bytes)")


# ---------- INDEX (dashboard) ----------

def build_index():
    now = datetime.now(WIB)
    updated = now.strftime(f"%d {BULAN[now.month]} %Y %H:%M WIB")

    stat_cards = ""
    for i, (repo, sub, icon, label, blurb) in enumerate(REPOS):
        stat_cards += f"""
    <a href="{sub}" class="card reveal reveal-{i+1} group relative bg-gray-900/60 border border-cyan-500/20 rounded-2xl p-5 hover:border-cyan-400/60 hover:shadow-[0_0_30px_-8px_rgba(34,211,238,0.35)] block">
      <div class="flex items-center justify-between mb-3">
        <span class="text-2xl">{icon}</span>
        <span class="text-[10px] font-mono px-2 py-0.5 rounded-full border border-cyan-500/40 text-cyan-400">STATS</span>
      </div>
      <h3 class="text-cyan-300 font-bold mb-1">{label}</h3>
      <p class="text-xs text-gray-500 leading-relaxed mb-3">{blurb}</p>
      <div class="flex items-center justify-between text-xs">
        <span class="text-gray-600" id="stat-{i}">memuat…</span>
        <span class="text-cyan-500 group-hover:text-cyan-300 group-hover:translate-x-1 transition inline-block">buka →</span>
      </div>
    </a>"""

    body = f"""
<!-- TICKER -->
<div class="ticker overflow-hidden border-b border-cyan-500/10 bg-gray-950/60 py-2" id="ticker">
  <div class="ticker-track text-xs text-cyan-500/80" id="ticker-track">
    <span>⟳ menghubungkan ke GitHub…</span><span>⟳ menghubungkan ke GitHub…</span>
  </div>
</div>

<!-- HERO -->
<header class="grid-bg">
  <div class="max-w-6xl mx-auto px-4 pt-14 pb-10">
    <p class="text-cyan-500/70 text-[10px] md:text-xs tracking-[0.35em] mb-3">[ DASHBOARD · REALTIME DATA · INDONESIA ]</p>
    <h1 class="text-3xl md:text-5xl font-extrabold text-white glow-text mb-4">meneliti<span class="text-cyan-400">.io</span><span class="cursor"></span></h1>
    <p class="max-w-2xl text-gray-400 text-sm md:text-base leading-relaxed">
      Konsol pemantauan data Indonesia — harga emas, sembako, tren pencarian, dan uptime server.
      Semua modul diperbarui otomatis; halaman ini hanya jendelanya.
    </p>
    <p class="mt-4 text-[11px] text-gray-600">build: {updated} · kartu &amp; ticker ditarik live dari api.github.com</p>
  </div>
</header>

<main class="max-w-6xl mx-auto px-4 -mt-2 pb-8">
  <!-- STATUS BAR -->
  <div class="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-mono bg-gray-900/50 border border-gray-800 rounded-xl px-4 py-3 mb-8">
    <span id="live-status" class="text-gray-500"><span class="text-cyan-400 pulse">●</span> menghubungi api.github.com…</span>
    <span class="text-gray-700">|</span>
    <span class="text-gray-500">uptime probe: <span class="text-green-400 pulse">AKTIF</span></span>
    <span class="text-gray-700 hidden sm:inline">|</span>
    <span class="text-gray-500 hidden sm:inline">zona waktu: <span class="text-cyan-400">WIB (UTC+7)</span></span>
  </div>

  <!-- MODUL GRID -->
  <h2 class="text-lg font-bold text-white mb-4 glow-text">📁 Modul Pemantauan</h2>
  <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{stat_cards}
  </div>

  <!-- PETA SITUS -->
  <h2 class="text-lg font-bold text-white mt-12 mb-4 glow-text">🧭 Peta Situs</h2>
  <div class="grid sm:grid-cols-2 gap-4">
    <div class="card bg-gray-900/40 border border-gray-800 rounded-xl p-5">
      <h3 class="text-cyan-300 font-semibold mb-2 text-sm">Halaman Data</h3>
      <ul class="space-y-2 text-sm text-gray-400">
        <li>💰 <a href="/harga-emas/" class="sweep text-cyan-400 hover:text-cyan-200">/harga-emas/</a> — tabel 18 penyedia, termurah→termahal</li>
        <li>🛒 <a href="/harga-sembako/" class="sweep text-cyan-400 hover:text-cyan-200">/harga-sembako/</a> — 26 komoditas per kategori</li>
        <li>🔥 <a href="/trending/" class="sweep text-cyan-400 hover:text-cyan-200">/trending/</a> — 25 tren Google Trends ID</li>
        <li>📡 <a href="/ping-hash/" class="sweep text-cyan-400 hover:text-cyan-200">/ping-hash/</a> — log probe &amp; verifikasi hash</li>
      </ul>
    </div>
    <div class="card bg-gray-900/40 border border-gray-800 rounded-xl p-5">
      <h3 class="text-cyan-300 font-semibold mb-2 text-sm">Navigasi Cepat</h3>
      <ul class="space-y-2 text-sm text-gray-400">
        <li>⌨️ Gunakan navbar atas atau peta di samping</li>
        <li>🔄 Semua tabel di sub-halaman memuat <span class="text-cyan-400">data live</span> dari repo GitHub</li>
        <li>📱 Responsif — rapi di ponsel &amp; desktop</li>
        <li>🐙 <a href="https://github.com/meneliti" target="_blank" rel="noopener" class="text-cyan-400 hover:underline">github.com/meneliti</a> — semua kode terbuka</li>
      </ul>
    </div>
  </div>
</main>

<script>
{LIVE_JS}
// repo stats utk kartu
(async () => {{
  const el = document.getElementById('live-status');
  try {{
    const res = await fetch('https://api.github.com/users/meneliti/repos?per_page=100&sort=updated');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const repos = await res.json();
    const list = repos.filter(r => r.name !== 'meneliti.github.io');
    const last = new Date(list[0].updated_at).toLocaleString('id-ID', {{dateStyle:'long', timeStyle:'short'}});
    el.innerHTML = '<span class="text-green-400 pulse">● LIVE</span> ' + list.length + ' repositori aktif · push terakhir: ' + last;
    const map = {{}};
    list.forEach(r => map[r.name] = r);
    const mods = ['Harga-Emas-Terbaru-Hari-Ini','Harga-Sembako-Terbaru','Trending-di-Indonesia','Ping-Hash'];
    mods.forEach((n, i) => {{
      const s = document.getElementById('stat-' + i);
      const r = map[n];
      if (s && r) {{
        const d = new Date(r.updated_at);
        s.textContent = 'update: ' + d.toLocaleDateString('id-ID', {{day:'numeric', month:'short'}}) +
          ' · ' + (r.stargazers_count || 0) + '★';
      }}
    }});
    // ticker: daftar repo + update
    const items = list.map(r => {{
      const t = new Date(r.updated_at).toLocaleDateString('id-ID', {{day:'numeric', month:'short'}});
      return '📦 ' + r.name + ' · update ' + t;
    }}).join(' &nbsp;&nbsp;✦&nbsp;&nbsp; ');
    document.getElementById('ticker-track').innerHTML =
      '<span>' + items + '</span><span>' + items + '</span>';
  }} catch (e) {{
    el.innerHTML = '<span class="text-yellow-500">○ OFFLINE</span> API tidak terjangkau (' + e.message + ')';
  }}
}})();
</script>"""
    write("index.html", page_shell(
        "meneliti.io — Dashboard Data Realtime Indonesia",
        "Dashboard cyber pemantauan data Indonesia: harga emas, sembako, trending Google Trends, uptime monitor. Live & open-source.",
        "index.html", body))


# ---------- SUB-PAGE GENERATOR ----------

def build_sub(repo_name, subdir, icon, label, blurb, readme_path, table_idx,
              seo_title, seo_desc, extra_body, extra_js="", summary_html=""):
    now = datetime.now(WIB)
    updated = now.strftime(f"%d {BULAN[now.month]} %Y")
    sub = REPOS
    prev_next = []
    idx = [r[0] for r in REPOS].index(repo_name)
    for off, tag in [(-1, "◀ sebelumnya"), (1, "berikutnya ▶")]:
        j = (idx + off) % len(REPOS)
        prev_next.append(f'<a href="/{REPOS[j][1]}" class="card text-xs px-4 py-2 rounded-lg border border-gray-700 text-gray-400 hover:border-cyan-400/60 hover:text-cyan-300 transition">{tag} {REPOS[j][3]}</a>')
    cross = "".join(
        f'<a href="/{r[1]}" class="card flex items-center gap-2 bg-gray-900/40 border border-gray-800 rounded-lg px-3 py-2 hover:border-cyan-400/50 transition">'
        f'<span>{r[2]}</span><span class="text-xs text-gray-400">{r[3]}</span></a>'
        for r in REPOS if r[0] != repo_name)

    body = f"""
<header class="grid-bg border-b border-cyan-500/10">
  <div class="max-w-6xl mx-auto px-4 pt-12 pb-8">
    <p class="text-[10px] tracking-[0.3em] text-cyan-500/70 mb-2">[ MODUL · {label.upper()} ]</p>
    <h1 class="text-2xl md:text-4xl font-extrabold text-white glow-text mb-3">{icon} {label}</h1>
    <p class="max-w-2xl text-gray-400 text-sm leading-relaxed">{blurb}</p>
    <div class="mt-4 flex flex-wrap gap-3 text-xs">
      <a href="https://github.com/meneliti/{repo_name}" target="_blank" rel="noopener" class="px-3 py-1.5 rounded-lg border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 transition">📦 repo GitHub</a>
      <a href="https://github.com/meneliti/{repo_name}#readme" target="_blank" rel="noopener" class="px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:border-gray-500 transition">📄 README</a>
      <span class="px-3 py-1.5 rounded-lg border border-gray-800 text-gray-600">snapshot build: {updated}</span>
    </div>
  </div>
</header>

<main class="max-w-6xl mx-auto px-4 py-8">
{summary_html}
{extra_body}
</main>

<!-- NAVIGASI ANTAR MODUL -->
<div class="max-w-6xl mx-auto px-4 pb-4">
  <div class="flex flex-wrap items-center justify-between gap-3 border-t border-gray-800/60 pt-6">
    <div class="flex gap-2">{prev_next[0]}{prev_next[1]}</div>
    <div class="flex flex-wrap gap-2 items-center">
      <span class="text-[10px] text-gray-600 mr-1">MODUL LAIN:</span>{cross}
    </div>
  </div>
</div>

<script>
{LIVE_JS}
{extra_js}
</script>"""
    write(f"{subdir}index.html", page_shell(seo_title, seo_desc, "harga-emas/index.html" if False else f"{subdir}index.html", body))


def sub_emas():
    summary = """
<div class="grid sm:grid-cols-3 gap-4 mb-8" id="emas-summary">
  <div class="card bg-gray-900/60 border border-green-500/25 rounded-xl p-4">
    <p class="text-[10px] text-gray-500 mb-1">🟢 TERMURAH</p>
    <p class="text-xl font-bold text-green-300" id="lo">—</p>
    <p class="text-xs text-gray-500" id="lo-p">memuat…</p>
  </div>
  <div class="card bg-gray-900/60 border border-red-500/25 rounded-xl p-4">
    <p class="text-[10px] text-gray-500 mb-1">🔴 TERMAHAL</p>
    <p class="text-xl font-bold text-red-300" id="hi">—</p>
    <p class="text-xs text-gray-500" id="hi-p">memuat…</p>
  </div>
  <div class="card bg-gray-900/60 border border-cyan-500/25 rounded-xl p-4">
    <p class="text-[10px] text-gray-500 mb-1">⚖️ RATA-RATA</p>
    <p class="text-xl font-bold text-cyan-300" id="avg">—</p>
    <p class="text-xs text-gray-500">15+ penyedia · per gram</p>
  </div>
</div>"""
    extra_body = """
<section class="shimmer bg-gray-900/40 border border-cyan-500/15 rounded-xl p-4 md:p-6">
  <h2 class="text-white font-bold mb-1">📋 Tabel Harga Emas per Gram</h2>
  <p class="text-xs text-gray-500 mb-4">Live dari README repo — data terbaru sesuai cron 6 jam. Termurah di atas.</p>
  <div class="overflow-x-auto">
    <table class="dtable w-full" id="t"><tbody><tr><td class="text-gray-500">memuat data live…</td></tr></tbody></table>
  </div>
</section>"""
    js = """
fetchReadmeTable('https://raw.githubusercontent.com/meneliti/Harga-Emas-Terbaru-Hari-Ini/main/README.md', 't', {
  after: (rows) => {
    // ringkasan dari baris data (kolom: rank, penyedia, jenis, jual, buyback, selisih)
    const parse = s => parseInt((s||'').replace(/[^0-9]/g,'')) || null;
    const data = rows.map(r => ({p: r[1], jual: parse(r[3])})).filter(x => x.jual > 100000);
    if (!data.length) return;
    data.sort((a,b) => a.jual - b.jual);
    const fmt = n => 'Rp' + n.toLocaleString('id-ID');
    document.getElementById('lo').textContent = fmt(data[0].jual);
    document.getElementById('lo-p').textContent = data[0].p;
    const hi = data[data.length-1];
    document.getElementById('hi').textContent = fmt(hi.jual);
    document.getElementById('hi-p').textContent = hi.p;
    document.getElementById('avg').textContent = fmt(Math.round(data.reduce((s,x)=>s+x.jual,0)/data.length));
  }
});"""
    build_sub("Harga-Emas-Terbaru-Hari-Ini", "harga-emas/", "💰", "Harga Emas",
              "Perbandingan harga emas batangan 1 gram dari 18 penyedia resmi — Antam, Pegadaian, Bank BSI, Indogold, Treasury, dan lainnya. Diurutkan termurah → termahal lengkap dengan harga buyback.",
              "~/harga-emas/README.md", 1,
              "Harga Emas Hari Ini — 18 Penyedia, Termurah ke Termahal | meneliti.io",
              "Tabel harga emas batangan per gram hari ini dari Antam, Pegadaian, BSI, Indogold & 14 penyedia lain. Lengkap harga buyback & selisih. Update otomatis 6 jam.",
              extra_body, js, summary)


def sub_sembako():
    summary = """
<div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
  <div class="card bg-gray-900/60 border border-cyan-500/25 rounded-xl p-4 text-center">
    <p class="text-2xl font-bold text-cyan-300" id="n-kom">26</p>
    <p class="text-[10px] text-gray-500">KOMODITAS</p>
  </div>
  <div class="card bg-gray-900/60 border border-cyan-500/25 rounded-xl p-4 text-center">
    <p class="text-2xl font-bold text-cyan-300">38</p>
    <p class="text-[10px] text-gray-500">PROVINSI</p>
  </div>
  <div class="card bg-gray-900/60 border border-green-500/25 rounded-xl p-4 text-center">
    <p class="text-2xl font-bold text-green-300" id="n-up">–</p>
    <p class="text-[10px] text-gray-500">KENAIKAN ▲</p>
  </div>
  <div class="card bg-gray-900/60 border border-red-500/25 rounded-xl p-4 text-center">
    <p class="text-2xl font-bold text-red-300" id="n-down">–</p>
    <p class="text-[10px] text-gray-500">PENURUNAN ▼</p>
  </div>
</div>"""
    extra_body = """
<section class="shimmer bg-gray-900/40 border border-cyan-500/15 rounded-xl p-4 md:p-6">
  <h2 class="text-white font-bold mb-1">📋 Tabel Harga Sembako</h2>
  <p class="text-xs text-gray-500 mb-4">Rata-rata nasional · terendah · tertinggi · perubahan vs kemarin. Live dari repo (cron 6 jam).</p>
  <div class="overflow-x-auto">
    <table class="dtable w-full" id="t"><tbody><tr><td class="text-gray-500">memuat data live…</td></tr></tbody></table>
  </div>
</section>"""
    js = """
fetchReadmeTable('https://raw.githubusercontent.com/meneliti/Harga-Sembako-Terbaru/main/README.md', 't', {
  after: (rows) => {
    let up = 0, down = 0, kom = 0;
    rows.forEach(r => {
      const ch = r[5] || '';
      if (ch.includes('▲')) up++;
      else if (ch.includes('▼')) down++;
      if (r[1] && r[1] !== 'kg' && r[1] !== 'liter' && r[1] !== 'pcs') {} else kom++;
    });
    document.getElementById('n-up').textContent = up;
    document.getElementById('n-down').textContent = down;
  }
});"""
    build_sub("Harga-Sembako-Terbaru", "harga-sembako/", "🛒", "Harga Sembako",
              "Harga rata-rata 26 komoditas barang kebutuhan pokok dari 38 provinsi — beras, minyak, telur, gula, cabai, dan sayuran. Dikelompokkan per kategori dengan indikator perubahan harian.",
              "~/harga-sembako/README.md", 0,
              "Harga Sembako Terbaru Hari Ini — 26 Komoditas 38 Provinsi | meneliti.io",
              "Harga beras, minyak goreng, telur, gula, cabai & sayuran hari ini. Rata-rata nasional + terendah/tertinggi antar provinsi. Update otomatis 6 jam.",
              extra_body, js, summary)


def sub_trending():
    summary = """
<div class="grid sm:grid-cols-3 gap-4 mb-8">
  <div class="card bg-gray-900/60 border border-amber-500/25 rounded-xl p-4">
    <p class="text-[10px] text-gray-500 mb-1">🥇 TERPANAS</p>
    <p class="text-lg font-bold text-amber-300" id="top1">—</p>
    <p class="text-xs text-gray-500" id="top1-v">memuat…</p>
  </div>
  <div class="card bg-gray-900/60 border border-gray-500/25 rounded-xl p-4">
    <p class="text-[10px] text-gray-500 mb-1">🥈 KEDUA</p>
    <p class="text-lg font-bold text-gray-300" id="top2">—</p>
    <p class="text-xs text-gray-500" id="top2-v">memuat…</p>
  </div>
  <div class="card bg-gray-900/60 border border-orange-500/25 rounded-xl p-4">
    <p class="text-[10px] text-gray-500 mb-1">🥉 KETIGA</p>
    <p class="text-lg font-bold text-orange-300" id="top3">—</p>
    <p class="text-xs text-gray-500" id="top3-v">memuat…</p>
  </div>
</div>"""
    extra_body = """
<section class="shimmer bg-gray-900/40 border border-cyan-500/15 rounded-xl p-4 md:p-6">
  <h2 class="text-white font-bold mb-1">📋 25 Tren Google Trends Indonesia</h2>
  <p class="text-xs text-gray-500 mb-4">24 jam terakhir · volume, % kenaikan, aktif sejak, kueri terkait. Live (cron 2 jam).</p>
  <div class="overflow-x-auto">
    <table class="dtable w-full" id="t"><tbody><tr><td class="text-gray-500">memuat data live…</td></tr></tbody></table>
  </div>
</section>"""
    js = """
fetchReadmeTable('https://raw.githubusercontent.com/meneliti/Trending-di-Indonesia/main/README.md', 't', {
  after: (rows) => {
    // tabel podium: rows dgn kolom [medali, tren, volume, kenaikan]
    const podium = rows.filter(r => (r[0]||'').includes('🥇') || (r[0]||'').includes('🥈') || (r[0]||'').includes('🥉'));
    // tabel utk 25: kolom [#, tren, volume, kenaikan, aktif, terkait]
    const list = rows.filter(r => /^\\d+$/.test((r[0]||'').trim())).slice(0, 3);
    const src = podium.length ? podium : list;
    for (let i = 0; i < 3 && i < src.length; i++) {
      const r = src[i];
      const name = r[1] || r[0], vol = r[2] || r[1];
      const n = document.getElementById('top' + (i+1));
      const v = document.getElementById('top' + (i+1) + '-v');
      if (n) n.textContent = name;
      if (v) v.textContent = vol;
    }
  }
});"""
    build_sub("Trending-di-Indonesia", "trending/", "🔥", "Trending Indonesia",
              "25 kata kunci paling banyak dicari di Google Indonesia 24 jam terakhir — volume penelusuran, persentase lonjakan, sejak kapan aktif, dan kueri terkait. Paling sering diperbarui (2 jam).",
              "~/trending-id/README.md", 0,
              "Trending di Indonesia Hari Ini — 25 Tren Google | meneliti.io",
              "Apa yang sedang ramai dicari orang Indonesia? 25 tren Google Trends teratas dengan volume, persen kenaikan & kueri terkait. Update otomatis tiap 2 jam.",
              extra_body, js, summary)


def sub_pinghash():
    # ambil beberapa entri log utk ilustrasi verifikasi
    log = os.path.expanduser("~/ping-hash/repo/logs")
    sample = ""
    try:
        files = sorted(os.listdir(log))[-1:]
        if files:
            lines = open(os.path.join(log, files[0])).read().strip().splitlines()[-6:]
            sample = "".join(f"<tr><td class='text-gray-400'>{l.split(' | ')[0]}</td><td class='text-cyan-400 font-mono'>{(l.split(' | ')[1] if ' | ' in l else '')[:12]}…</td><td class='text-gray-500'>SHA-256 ✓</td></tr>" for l in lines)
    except Exception:
        pass
    if not sample:
        sample = "<tr><td class='text-gray-500'>log belum tersedia di build ini</td></tr>"
    extra_body = f"""
<div class="grid md:grid-cols-2 gap-6">
  <section class="card bg-gray-900/40 border border-cyan-500/15 rounded-xl p-5">
    <h2 class="text-white font-bold mb-3">🔓 Verifikasi Hash</h2>
    <p class="text-xs text-gray-500 mb-4">Setiap commit memuat fingerprint SHA-256 dari timestamp. Siapa pun bisa memverifikasi:</p>
    <div class="bg-black/60 border border-gray-800 rounded-lg p-4 text-xs text-green-400 font-mono overflow-x-auto">
      <div class="text-gray-500"># verifikasi entri log</div>
      <div>$ echo -n "TIMESTAMP" | sha256sum</div>
      <div class="text-gray-500"># cocokkan 12 digit pertama dgn kolom hash</div>
    </div>
    <h3 class="text-cyan-300 text-sm font-semibold mt-5 mb-2">Contoh entri terakhir (build-time):</h3>
    <table class="dtable w-full"><thead><tr><th>Timestamp UTC</th><th>Hash (12d)</th><th>Status</th></tr></thead><tbody>{sample}</tbody></table>
  </section>
  <section class="card bg-gray-900/40 border border-cyan-500/15 rounded-xl p-5">
    <h2 class="text-white font-bold mb-3">📊 Cara Kerja</h2>
    <ol class="space-y-3 text-sm text-gray-400">
      <li><span class="text-cyan-400 font-bold">1.</span> Daemon melakukan probe tiap <span class="text-cyan-300">1–8 menit</span> (delay acak)</li>
      <li><span class="text-cyan-400 font-bold">2.</span> Timestamp di-<span class="text-cyan-300">SHA-256</span> sebagai fingerprint unik</li>
      <li><span class="text-cyan-400 font-bold">3.</span> Hasil (status UP/WARN, RTT, emoji) ditulis ke log harian</li>
      <li><span class="text-cyan-400 font-bold">4.</span> Commit otomatis &amp; push ke <span class="text-cyan-300">main</span></li>
    </ol>
    <div class="mt-5 grid grid-cols-2 gap-3 text-center">
      <div class="bg-gray-950/60 border border-green-500/20 rounded-lg p-3">
        <p class="text-xl font-bold text-green-400 pulse">●</p>
        <p class="text-[10px] text-gray-500">STATUS PROBE</p>
      </div>
      <div class="bg-gray-950/60 border border-cyan-500/20 rounded-lg p-3">
        <p class="text-xl font-bold text-cyan-300">1–8<span class="text-xs"> mnt</span></p>
        <p class="text-[10px] text-gray-500">INTERVAL ACAK</p>
      </div>
    </div>
    <a href="https://github.com/meneliti/Ping-Hash" target="_blank" rel="noopener" class="mt-5 inline-block text-xs px-4 py-2 rounded-lg border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 transition">lihat grafik kontribusi →</a>
  </section>
</div>"""
    build_sub("Ping-Hash", "ping-hash/", "📡", "Ping-Hash",
              "Uptime monitor berbasis git: setiap probe menghasilkan commit dengan fingerprint SHA-256. Bukti server hidup yang transparan, gratis, dan sulit dipalsukan.",
              "~/ping-hash/repo/logs", 0,
              "Ping-Hash — Uptime Monitor Berbasis Git | meneliti.io",
              "Bukti server masih hidup lewat commit ber-hash SHA-256 tiap 1-8 menit. Transparan, gratis, terverifikasi publik di GitHub.",
              extra_body)


def main():
    print("Membangun situs dashboard cyber:")
    build_index()
    sub_emas()
    sub_sembako()
    sub_trending()
    sub_pinghash()
    print("selesai.")


if __name__ == "__main__":
    main()
