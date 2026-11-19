"""Baut die Pünktlichkeits-Heatmap der Züge in der Schweiz als eigenständige HTML-Seite (daten/puenktlichkeit_auswertung.html).

Liest alle CSV-Dateien daten/ist_daten_*.csv (siehe get_sbb_data.py) und verdichtet sie:
  - Verspätung = prognostizierte (REAL = gemessene) minus fahrplanmässige Ankunftszeit
  - pünktlich = weniger als 3 Minuten Verspätung (SBB-Definition), Ankunftszeit = geplante Ankunft
  - gezählt werden nur gemessene Ankünfte (an_prognose_status = REAL) ohne Ausfälle und Durchfahrten
"""
import csv
import datetime as dt
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "daten" / "puenktlichkeit_auswertung.html"
PUNCTUAL_S = 180   # unter 3 Minuten = pünktlich
LATE_S = 360       # ab 6 Minuten = deutlich verspätet
TOP_STATIONS = 40  # Bahnhöfe mit den meisten Ankünften für die Bahnhof-Heatmap


def load():
    """Gibt (Aggregat nach Zugart/Wochentag/Stunde, Aggregat nach Zugart/Bahnhof/Stunde, Kennzahlen) zurück."""
    by_wd = defaultdict(lambda: [0, 0, 0, 0])   # [Ankünfte, pünktlich, Summe Verspätung s, ab 6 min]
    by_st = defaultdict(lambda: [0, 0, 0, 0])
    days, stops, cancelled = set(), 0, 0
    for path in sorted((HERE / "daten").glob("ist_daten_*.csv")):
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter=";"):
                days.add(r["betriebstag"])
                if r["faellt_aus_tf"] == "True":
                    cancelled += 1
                    continue
                if r["durchfahrt_tf"] == "True" or r["an_prognose_status"] != "REAL" or not (r["ankunftszeit"] and r["an_prognose"]):
                    continue
                plan, real = dt.datetime.fromisoformat(r["ankunftszeit"]), dt.datetime.fromisoformat(r["an_prognose"])
                delay = max((real - plan).total_seconds(), 0)  # zu früh zählt als pünktlich
                vm = r["verkehrsmittel_text"] or "?"
                wd = dt.date.fromisoformat(r["betriebstag"]).weekday()
                for agg, key in ((by_wd, (vm, wd, plan.hour)), (by_st, (vm, r["haltestellen_name"], plan.hour))):
                    c = agg[key]
                    c[0] += 1
                    c[1] += delay < PUNCTUAL_S
                    c[2] += delay
                    c[3] += delay >= LATE_S
                stops += 1
    return by_wd, by_st, {"days": sorted(days), "arrivals": stops, "cancelled": cancelled}


def compact(by_wd, by_st):
    """Bahnhöfe auf die mit den meisten Ankünften beschränken und alles als Listen ablegen (kleine HTML-Seite)."""
    vms = sorted({k[0] for k in by_wd} | {k[0] for k in by_st})
    vi = {v: i for i, v in enumerate(vms)}
    total = defaultdict(int)
    for (_vm, st, _h), c in by_st.items():
        total[st] += c[0]
    top = sorted(total, key=lambda s: -total[s])[:TOP_STATIONS]  # die Bahnhöfe mit den meisten Ankünften ...
    stations = sorted(top, key=lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().casefold())  # ... alphabetisch (ä = a)
    si = {s: i for i, s in enumerate(stations)}
    wd = [[vi[k[0]], k[1], k[2], *map(int, c)] for k, c in sorted(by_wd.items())]
    st = [[vi[k[0]], si[k[1]], k[2], *map(int, c)] for k, c in sorted(by_st.items()) if k[1] in si]
    return vms, stations, wd, st


HTML = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pünktlichkeit Auswertung</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root { --bg:#fff; --fg:#1c2733; --muted:#5b6b7a; --line:#d9e0e7; --accent:#0b6bcb; --card:#f5f8fb; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14191f; --fg:#e6ecf2; --muted:#9fb0c0; --line:#2b3641; --accent:#5aa9ff; --card:#1b232c; }
  }
  body { margin:0; padding:16px; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, Segoe UI, sans-serif; }
  h1 { font-size:22px; margin:0 0 4px; }
  h2 { font-size:17px; margin:26px 0 2px; }
  .sub { color:var(--muted); margin-bottom:14px; }
  .note { color:var(--muted); font-size:13px; margin:0 0 6px; }
  .controls { display:flex; flex-wrap:wrap; gap:14px; align-items:end; margin-bottom:14px; }
  label { display:flex; flex-direction:column; gap:3px; font-size:13px; color:var(--muted); }
  select { font:inherit; color:var(--fg); background:var(--card); border:1px solid var(--line); border-radius:6px; padding:6px 8px; }
  .cards { display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:10px; margin-bottom:8px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 12px; }
  .card .v { font-size:24px; font-weight:600; }
  .card .l { color:var(--muted); font-size:13px; }
  .chart { width:100%; }
  .wip { background:#fff4d6; color:#5c4300; border:1px solid #e6c35c; border-radius:8px; padding:8px 12px; margin:0 0 14px; font-size:14px; }
  @media (prefers-color-scheme: dark) { .wip { background:#3a2f10; color:#f3dca0; border-color:#7a6320; } }
</style>
</head>
<body>
<h1>Wie pünktlich sind die Züge in der Schweiz?</h1>
<div class="sub">Soll/Ist-Vergleich der Ankunftszeiten, Quelle: opentransportdata.swiss (Ist-Daten, alle Bahnunternehmen) · <span id="period"></span> · Abruf <span id="retrieved"></span></div>

<div class="wip" id="wip" hidden></div>

<div class="controls">
  <label>Heatmap <select id="view">
    <option value="wd">Wochentag × Uhrzeit</option>
    <option value="st">Bahnhof × Uhrzeit</option>
  </select></label>
  <label>Zugart <select id="vm"></select></label>
  <label>Kennzahl <select id="metric">
    <option value="punct">Pünktlichkeit (% unter 3 Min.)</option>
    <option value="avg">Ø Verspätung (Minuten)</option>
    <option value="late">Anteil ab 6 Min. Verspätung (%)</option>
  </select></label>
  <label>Mindestens <select id="minn">
    <option value="1">1 Ankunft</option><option value="10" selected>10 Ankünfte</option>
    <option value="30">30 Ankünfte</option><option value="100">100 Ankünfte</option>
  </select></label>
</div>

<div class="cards" id="cards"></div>

<h2 id="title"></h2>
<p class="note" id="note"></p>
<div id="heat" class="chart"></div>

<script>
const DATA = __DATA__;
const WDAYS = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag'];
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const $ = id => document.getElementById(id);
const pct = (a, b) => b ? 100 * a / b : null;
const num = n => n.toLocaleString('de-CH');

$('retrieved').textContent = DATA.retrievedAt.replace('T', ' ');
const d0 = DATA.days[0], d1 = DATA.days[DATA.days.length - 1];
const dfmt = d => d.split('-').reverse().join('.');
$('period').textContent = DATA.days.length === 1 ? 'Betriebstag ' + dfmt(d0) : DATA.days.length + ' Betriebstage (' + dfmt(d0) + ' bis ' + dfmt(d1) + ')';
if (DATA.days.length < 7) {
  $('wip').hidden = false;
  $('wip').innerHTML = '<b>Noch im Aufbau:</b> Es liegen erst ' + DATA.days.length + ' von mindestens 7 Betriebstagen vor. Die Auswertung wird aussagekräftiger, je mehr Tage gesammelt sind.';
}
$('vm').innerHTML = '<option value="-1">Alle Zugarten</option>' + DATA.vms.map((v, i) => `<option value="${i}">${v}</option>`).join('');

// Kennzahl einer Zelle aus [Ankünfte, pünktlich, Summe Verspätung s, ab 6 Min.]
function value(c, m) {
  if (m === 'punct') return pct(c[1], c[0]);
  if (m === 'avg') return c[2] / c[0] / 60;
  return pct(c[3], c[0]);
}

function render() {
  const view = $('view').value, vm = +$('vm').value, m = $('metric').value, minn = +$('minn').value;
  const rows = (view === 'wd' ? DATA.wd : DATA.st).filter(r => vm < 0 || r[0] === vm);
  const ys = view === 'wd' ? WDAYS : DATA.stations;
  const cells = ys.map(() => Array.from({length: 24}, () => [0, 0, 0, 0]));
  rows.forEach(r => { const c = cells[r[1]][r[2]]; for (let i = 0; i < 4; i++) c[i] += r[3 + i]; });

  const tot = [0, 0, 0, 0];
  rows.forEach(r => { for (let i = 0; i < 4; i++) tot[i] += r[3 + i]; });
  const f = (x, d = 1) => x === null ? '–' : x.toFixed(d).replace('.', ',');
  $('cards').innerHTML = [
    ['Gemessene Ankünfte', num(tot[0]), vm < 0 ? 'alle Zugarten' : DATA.vms[vm]],
    ['Pünktlich (unter 3 Min.)', f(pct(tot[1], tot[0])) + ' %', ''],
    ['Ø Verspätung', tot[0] ? f(tot[2] / tot[0] / 60) + ' Min.' : '–', 'zu frühe Züge zählen als 0'],
    ['Ab 6 Min. verspätet', f(pct(tot[3], tot[0])) + ' %', num(DATA.cancelled) + ' ausgefallene Halte'],
  ].map(([l, v, s]) => `<div class="card"><div class="v">${v}</div><div class="l">${l}${s ? ' · ' + s : ''}</div></div>`).join('');

  const z = cells.map(row => row.map(c => c[0] >= minn ? value(c, m) : null));
  const text = cells.map(row => row.map(c => c[0] >= minn ? c[0] + ' Ankünfte' : ''));
  const good = m === 'punct';
  const unit = m === 'avg' ? ' Min.' : ' %';
  const xs = Array.from({length: 24}, (_, h) => String(h).padStart(2, '0') + ':00');
  const fg = css('--fg'), line = css('--line');
  $('title').textContent = view === 'wd' ? 'Wochentag nach Uhrzeit' : 'Die ' + DATA.stations.length + ' Bahnhöfe mit den meisten Ankünften (alphabetisch) nach Uhrzeit';
  $('note').textContent = 'Geplante Ankunftsstunde. Grün = pünktlich, rot = verspätet. Leere Felder: weniger als ' + minn + ' Ankünfte' +
    (view === 'wd' && DATA.days.length < 7 ? '. Es liegen erst ' + DATA.days.length + ' Betriebstag(e) vor, die Wochentage füllen sich mit jedem Tag.' : '.');
  const h = view === 'wd' ? 380 : Math.max(420, ys.length * 24 + 120);
  Plotly.react('heat', [{type: 'heatmap', x: xs, y: ys, z, text, xgap: 1, ygap: 1, hoverongaps: false,
    colorscale: good ? [[0, '#d6453d'], [0.5, '#f0c040'], [1, '#2e9e6a']] : [[0, '#2e9e6a'], [0.5, '#f0c040'], [1, '#d6453d']],
    zmin: good ? 70 : 0, zmax: good ? 100 : (m === 'avg' ? 5 : 25), colorbar: {title: {text: unit.trim(), font: {color: fg}}, tickfont: {color: fg}},
    hovertemplate: '%{y}, %{x}<br>%{z:.1f}' + unit + '<br>%{text}<extra></extra>'}],
    {height: h, margin: {l: view === 'wd' ? 90 : 150, r: 10, t: 10, b: 50}, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
     font: {color: fg}, xaxis: {tickangle: -45, gridcolor: line}, yaxis: {autorange: 'reversed', automargin: true}},
    {responsive: true, displaylogo: false});
}
['view', 'vm', 'metric', 'minn'].forEach(id => $(id).addEventListener('change', render));
render();
</script>
</body>
</html>
"""


def main() -> int:
    by_wd, by_st, info = load()
    if not info["days"]:
        print("FEHLER: keine CSV-Dateien in daten/ (erst get_sbb_data.py ausführen)")
        return 1
    vms, stations, wd, st = compact(by_wd, by_st)
    data = {"retrievedAt": dt.datetime.now().isoformat(timespec="seconds"), "days": info["days"], "cancelled": info["cancelled"],
            "vms": vms, "stations": stations, "wd": wd, "st": st}
    OUT.write_text(HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")
    print(f"Fertig: {OUT} ({OUT.stat().st_size // 1024} KB, {info['arrivals']} Ankünfte, {len(info['days'])} Betriebstag(e))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
