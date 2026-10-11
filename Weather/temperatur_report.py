"""Erzeugt eine interaktive HTML-Auswertung der Lufttemperatur (temp_2m_mean) aus der SQLite-Datenbank weather.db.

Die Seite (daten/temperatur_auswertung.html) zeigt für eine wählbare Station, wie viel wärmer es über die Jahre wurde:
  1. Jahresmittel als Abweichung von einer Referenzperiode (frei wählbar in 30-Jahres-Schritten, z. B. 1961-1990), mit 10-Jahres-Mittel und Trend
  2. Warming Stripes: ein Streifen pro Jahr, blau = kälter, rot = wärmer als die Referenz
  3. Monatsmittel im Vergleich (1961-1990, 1991-2020, letzte 10 Jahre)
  4. Erwärmung pro Kalendermonat (Trend in °C pro Jahrzehnt)
  5. Alle Stationen im Vergleich (Trend in °C pro Jahrzehnt)
Kennzahlen und Trend gelten für den gewählten Zeitraum (gesamte Reihe, seit 1961 oder seit 1991).

Ein Jahr zählt nur, wenn alle zwölf Monate einen Messwert haben; das laufende, unvollständige Jahr fehlt deshalb.
Die Datenbank wird nur gelesen (zuerst GetWeatherData.py ausführen). Die Seite lädt die Diagramm-Bibliothek Plotly aus
dem Internet, es sind keine Python-Zusatzpakete nötig.

Aufruf:  py temperatur_report.py [--out DATEI] [--open]
"""
import argparse
import json
import os
import sqlite3
import webbrowser

from SqlLiteWD import DB_PATH

PARAMETER = 'temp_2m_mean'
DEFAULT_OUT = os.path.join(os.path.dirname(DB_PATH), 'temperatur_auswertung.html')


def build_data(db_path):
    """Liest die Monatsmittel aller Stationen und gibt sie für die Seite aufbereitet zurück.

    Je Station: Beginn der Reihe (Jahr, Monat) und eine lückenlose Liste der Monatswerte ab dann (null = kein Messwert).
    """
    if not os.path.exists(db_path):
        raise SystemExit("Datenbank fehlt: " + db_path + " (zuerst GetWeatherData.py ausführen)")
    # Nur lesen: mode=ro verhindert, dass eine fehlende Datenbank leer neu angelegt wird
    conn = sqlite3.connect('file:' + db_path.replace('\\', '/') + '?mode=ro', uri=True)
    try:
        info = {row[0]: row[1:] for row in conn.execute("SELECT station_abbr, station_name, canton, height_masl FROM stations")}
        values = {}
        for abbr, month, value in conn.execute(
                "SELECT station_abbr, month_start, value FROM homogeneous_monthly WHERE parameter = ? ORDER BY 1, 2",
                (PARAMETER,)):
            values.setdefault(abbr, {})[(int(month[:4]), int(month[5:7]))] = value
        retrieved_at = conn.execute("SELECT max(retrieved_at) FROM homogeneous_monthly").fetchone()[0]
    finally:
        conn.close()

    stations = []
    for abbr, months in values.items():
        first, last = min(months), max(months)
        count = (last[0] - first[0]) * 12 + last[1] - first[1] + 1
        series = [None] * count
        for (year, month), value in months.items():
            series[(year - first[0]) * 12 + month - first[1]] = round(value, 1)
        name, canton, height = info.get(abbr, (abbr, '', None))
        stations.append({'abbr': abbr, 'name': name, 'canton': canton, 'height': height,
                         'startYear': first[0], 'startMonth': first[1], 'values': series})
    stations.sort(key=lambda s: s['name'])
    return {'stations': stations, 'retrievedAt': retrieved_at}


HTML = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Temperatur Auswertung</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root { --bg:#fff; --fg:#1c2733; --muted:#5b6b7a; --line:#d9e0e7; --accent:#0b6bcb; --card:#f5f8fb;
          --warm:#d6453d; --cold:#3b7dd8; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14191f; --fg:#e6ecf2; --muted:#9fb0c0; --line:#2b3641; --accent:#5aa9ff; --card:#1b232c;
            --warm:#ef6b62; --cold:#5b9bf0; }
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
  .warm { color:var(--warm); } .cold { color:var(--cold); }
  #summary { background:var(--card); border-left:4px solid var(--accent); padding:10px 14px; border-radius:4px; margin-bottom:12px; }
  .chart { width:100%; }
</style>
</head>
<body>
<h1>Wie viel wärmer wurde es?</h1>
<div class="sub">Lufttemperatur 2 m über Boden, homogene Messreihen von MeteoSchweiz · Quelle: <span id="retrieved"></span></div>

<div class="controls">
  <label>Station <select id="station"></select></label>
  <label>Referenzperiode <select id="baseline"></select></label>
  <label>Trendzeitraum <select id="range">
    <option value="all">gesamte Reihe</option>
    <option value="1961">seit 1961</option>
    <option value="1991">seit 1991</option>
  </select></label>
</div>

<div id="summary"></div>
<div class="cards" id="cards"></div>

<h2>Jahresmittel im Vergleich zur Referenzperiode</h2>
<p class="note">Balken: Abweichung des Jahresmittels vom Mittel der Referenzperiode. Linie: 10-Jahres-Mittel. Gestrichelt: linearer Trend im gewählten Zeitraum.</p>
<div id="c_annual" class="chart"></div>

<h2>Warming Stripes</h2>
<p class="note">Jeder Streifen ist ein Jahr: blau kälter, rot wärmer als die Referenzperiode.</p>
<div id="c_stripes" class="chart"></div>

<h2>Monatsmittel im Vergleich</h2>
<p class="note">Durchschnittstemperatur je Kalendermonat in drei Zeiträumen.</p>
<div id="c_months" class="chart"></div>

<h2>Erwärmung je Kalendermonat</h2>
<p class="note">Trend in °C pro Jahrzehnt im gewählten Zeitraum, für jeden Monat einzeln.</p>
<div id="c_trend_month" class="chart"></div>

<h2>Alle Stationen im Vergleich</h2>
<p class="note">Trend der Jahresmitteltemperatur in °C pro Jahrzehnt im gewählten Zeitraum. Die gewählte Station ist hervorgehoben. Stationen mit weniger als 20 Jahren im Zeitraum fehlen.</p>
<div id="c_stations" class="chart"></div>

<script>
const DATA = __DATA__;
const MONTHS = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt = (x, d=1) => x === null || x === undefined || isNaN(x) ? '–' : (x > 0 ? '+' : x < 0 ? '−' : '') + Math.abs(x).toFixed(d).replace('.', ',');
const num = (x, d=1) => x === null || x === undefined || isNaN(x) ? '–' : x.toFixed(d).replace('.', ',');
const mean = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;

// Monatswert (Jahr, Monat 1-12) oder null
function monthValue(st, year, month) {
  const i = (year - st.startYear) * 12 + (month - st.startMonth);
  return i >= 0 && i < st.values.length ? st.values[i] : null;
}

// Jahresmittel aller Jahre mit zwölf Monatswerten
function annual(st) {
  const years = [], means = [];
  const lastYear = st.startYear + Math.floor((st.values.length + st.startMonth - 2) / 12);
  for (let y = st.startYear; y <= lastYear; y++) {
    const v = MONTHS.map((_, m) => monthValue(st, y, m + 1));
    if (v.every(x => x !== null)) { years.push(y); means.push(mean(v)); }
  }
  return {years, means};
}

// Lineare Regression: Steigung in °C pro Jahr
function trend(xs, ys) {
  const n = xs.length;
  if (n < 2) return null;
  const mx = mean(xs), my = mean(ys);
  let sxy = 0, sxx = 0;
  for (let i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; }
  return {slope: sxy / sxx, mx, my};
}

function rangeStart() {
  const r = document.getElementById('range').value;
  return r === 'all' ? -Infinity : parseInt(r);
}

function periodMean(a, from, to) {
  const v = a.years.map((y, i) => (y >= from && y <= to) ? a.means[i] : null).filter(x => x !== null);
  return v.length >= 20 ? mean(v) : null;
}

// Trend der Jahresmittel ab Startjahr; null, wenn weniger als 20 Jahre
function annualTrend(a, from) {
  const xs = [], ys = [];
  a.years.forEach((y, i) => { if (y >= from) { xs.push(y); ys.push(a.means[i]); } });
  if (xs.length < 20) return null;
  const t = trend(xs, ys);
  return {slope: t.slope, from: xs[0], to: xs[xs.length - 1], mx: t.mx, my: t.my, n: xs.length};
}

function render() {
  const st = DATA.stations.find(s => s.abbr === document.getElementById('station').value);
  const [b0, b1] = document.getElementById('baseline').value.split('-').map(Number);
  const from = rangeStart();
  const a = annual(st);
  const fg = css('--fg'), muted = css('--muted'), line = css('--line'), warm = css('--warm'), cold = css('--cold');

  let base = periodMean(a, b0, b1), baseNote = '';
  if (base === null) {
    base = mean(a.means);
    baseNote = ' Für diese Station liegen zu wenige Jahre in der Referenzperiode vor, deshalb dient das Mittel der gesamten Reihe als Referenz.';
  }
  const anom = a.means.map(x => x - base);
  const t = annualTrend(a, from);

  // Kennzahlen
  const pOld = periodMean(a, 1961, 1990), pNew = periodMean(a, 1991, 2020);
  let warmest = 0; a.means.forEach((x, i) => { if (x > a.means[warmest]) warmest = i; });
  const cards = [
    ['Trend pro Jahrzehnt', t ? fmt(t.slope * 10, 2) + ' °C' : '–', t ? t.from + '–' + t.to : 'zu wenige Jahre', t && t.slope > 0 ? 'warm' : 'cold'],
    ['Erwärmung im Zeitraum', t ? fmt(t.slope * (t.to - t.from), 1) + ' °C' : '–', t ? 'Trend × ' + (t.to - t.from) + ' Jahre' : '', t && t.slope > 0 ? 'warm' : 'cold'],
    ['1991–2020 gegenüber 1961–1990', pOld !== null && pNew !== null ? fmt(pNew - pOld, 1) + ' °C' : '–', pOld !== null && pNew !== null ? num(pOld) + ' → ' + num(pNew) + ' °C' : 'Zeiträume nicht vollständig', pNew - pOld > 0 ? 'warm' : 'cold'],
    ['Wärmstes Jahr', a.years[warmest] + '', num(a.means[warmest]) + ' °C Jahresmittel', ''],
    ['Letztes volles Jahr', a.years[a.years.length - 1] + '', fmt(anom[anom.length - 1], 1) + ' °C zur Referenz', anom[anom.length - 1] > 0 ? 'warm' : 'cold'],
  ];
  document.getElementById('cards').innerHTML = cards.map(c =>
    `<div class="card"><div class="l">${c[0]}</div><div class="v ${c[3]}">${c[1]}</div><div class="l">${c[2]}</div></div>`).join('');

  const hot = a.means.slice(-10), cnt = hot.filter(x => x > base).length;
  document.getElementById('summary').innerHTML =
    `<b>${st.name}</b> (${st.canton}, ${st.height !== null ? Math.round(st.height) + ' m ü. M.' : ''}), Messreihe ${a.years[0]}–${a.years[a.years.length - 1]}. ` +
    (t ? `Im Zeitraum ${t.from}–${t.to} stieg die Jahresmitteltemperatur um rund <b>${num(t.slope * (t.to - t.from))} °C</b> (${num(t.slope * 10, 2)} °C pro Jahrzehnt). ` : '') +
    `${cnt} der letzten 10 vollen Jahre waren wärmer als das Mittel ${baseNote ? 'der Reihe' : b0 + '–' + b1} (${num(base)} °C).` + baseNote;

  const cfg = {responsive: true, displaylogo: false};
  const layout = (extra) => Object.assign({
    margin: {l: 55, r: 15, t: 10, b: 40}, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {color: fg}, xaxis: {gridcolor: line}, yaxis: {gridcolor: line, zerolinecolor: muted}, legend: {orientation: 'h', y: -0.18},
  }, extra);

  // 1. Jahresmittel
  const roll = a.means.map((_, i) => i >= 9 ? mean(a.means.slice(i - 9, i + 1)) - base : null);
  const traces = [
    {type: 'bar', x: a.years, y: anom, name: 'Abweichung vom Referenzmittel', marker: {color: anom.map(x => x >= 0 ? warm : cold)},
     customdata: a.means.map(x => num(x)), hovertemplate: '%{x}: %{y:+.2f} °C (Jahresmittel %{customdata} °C)<extra></extra>'},
    {type: 'scatter', mode: 'lines', x: a.years, y: roll, name: '10-Jahres-Mittel', line: {color: fg, width: 2.5}, connectgaps: false,
     hovertemplate: '%{x}: %{y:+.2f} °C<extra>10-Jahres-Mittel</extra>'},
  ];
  if (t) {
    const y0 = t.from, y1 = t.to;
    traces.push({type: 'scatter', mode: 'lines', x: [y0, y1], y: [t.my + t.slope * (y0 - t.mx) - base, t.my + t.slope * (y1 - t.mx) - base],
      name: 'Trend', line: {color: fg, dash: 'dash', width: 2}, hoverinfo: 'skip'});
  }
  Plotly.react('c_annual', traces, layout({height: 380, yaxis: {title: '°C zur Referenz', gridcolor: line, zerolinecolor: muted}}), cfg);

  // 2. Warming Stripes
  const m = Math.max(...anom.map(Math.abs));
  Plotly.react('c_stripes', [{type: 'heatmap', x: a.years, y: [''], z: [anom], zmin: -m, zmax: m, showscale: false,
    colorscale: [[0, '#08306b'], [0.2, '#4292c6'], [0.4, '#c6dbef'], [0.5, '#f7f7f7'], [0.6, '#fcbba1'], [0.8, '#ef3b2c'], [1, '#67000d']],
    customdata: [a.means.map(x => num(x))], hovertemplate: '%{x}: %{z:+.2f} °C (Jahresmittel %{customdata} °C)<extra></extra>'}],
    layout({height: 150, margin: {l: 10, r: 10, t: 5, b: 30}, yaxis: {visible: false}}), cfg);

  // 3. Monatsmittel in drei Zeiträumen
  const lastY = a.years[a.years.length - 1];
  const periods = [[1961, 1990, '1961–1990', cold], [1991, 2020, '1991–2020', '#e0a030'], [lastY - 9, lastY, 'letzte 10 Jahre (' + (lastY - 9) + '–' + lastY + ')', warm]];
  const mtraces = periods.map(p => {
    const y = MONTHS.map((_, k) => {
      const v = []; for (let yr = p[0]; yr <= p[1]; yr++) { const x = monthValue(st, yr, k + 1); if (x !== null) v.push(x); }
      return v.length >= Math.min(20, (p[1] - p[0] + 1) * 0.66) ? mean(v) : null;
    });
    return {type: 'scatter', mode: 'lines+markers', x: MONTHS, y, name: p[2], line: {color: p[3], width: 2.5}, hovertemplate: '%{x}: %{y:.1f} °C<extra>' + p[2] + '</extra>'};
  });
  Plotly.react('c_months', mtraces, layout({height: 360, yaxis: {title: '°C', gridcolor: line, zerolinecolor: muted}}), cfg);

  // 4. Trend je Kalendermonat
  const slopes = MONTHS.map((_, k) => {
    const xs = [], ys = [];
    for (let yr = Math.max(st.startYear, isFinite(from) ? from : -Infinity); yr <= lastY; yr++) {
      const x = monthValue(st, yr, k + 1); if (x !== null) { xs.push(yr); ys.push(x); }
    }
    const r = xs.length >= 20 ? trend(xs, ys) : null;
    return r ? r.slope * 10 : null;
  });
  Plotly.react('c_trend_month', [{type: 'bar', x: MONTHS, y: slopes, marker: {color: slopes.map(x => x >= 0 ? warm : cold)},
    hovertemplate: '%{x}: %{y:+.2f} °C pro Jahrzehnt<extra></extra>'}],
    layout({height: 320, yaxis: {title: '°C pro Jahrzehnt', gridcolor: line, zerolinecolor: muted}}), cfg);

  // 5. Alle Stationen
  const rows = DATA.stations.map(s => { const r = annualTrend(annual(s), from); return r ? {s, v: r.slope * 10} : null; })
    .filter(Boolean).sort((p, q) => q.v - p.v);
  Plotly.react('c_stations', [{type: 'bar', x: rows.map(r => r.s.abbr), y: rows.map(r => r.v),
    text: rows.map(r => r.s.name), marker: {color: rows.map(r => r.s.abbr === st.abbr ? warm : cold), opacity: rows.map(r => r.s.abbr === st.abbr ? 1 : 0.55)},
    hovertemplate: '%{text}: %{y:+.2f} °C pro Jahrzehnt<extra></extra>'}],
    layout({height: 340, yaxis: {title: '°C pro Jahrzehnt', gridcolor: line, zerolinecolor: muted}}), cfg);
}

document.getElementById('retrieved').textContent = 'Abruf ' + (DATA.retrievedAt || '').replace('T', ' ');
// Referenzperioden in 30-Jahres-Schritten (…, 1931–1960, 1961–1990, 1991–2020); angeboten werden nur Perioden,
// in denen mindestens eine Station 20 volle Jahre hat
const allAnnual = DATA.stations.map(annual);
const baseSel = document.getElementById('baseline');
for (let start = 1991; start >= 1700; start -= 30) {
  if (allAnnual.some(a => periodMean(a, start, start + 29) !== null)) {
    baseSel.add(new Option(start + '–' + (start + 29), start + '-' + (start + 29)));
  }
}
baseSel.value = '1961-1990';
const sel = document.getElementById('station');
sel.innerHTML = DATA.stations.map(s => `<option value="${s.abbr}">${s.name} (${s.abbr})</option>`).join('');
sel.value = (DATA.stations.find(s => s.abbr === 'SMA') || DATA.stations[0]).abbr;
['station', 'baseline', 'range'].forEach(id => document.getElementById(id).addEventListener('change', render));
render();
</script>
</body>
</html>
"""


def main():
    """Liest die Datenbank und schreibt die HTML-Seite."""
    parser = argparse.ArgumentParser(description="Erzeugt die interaktive Temperatur-Auswertung als HTML-Seite.")
    parser.add_argument('--out', default=DEFAULT_OUT, help=f"Ausgabedatei (Standard: {DEFAULT_OUT})")
    parser.add_argument('--open', action='store_true', help="Seite danach im Browser öffnen")
    args = parser.parse_args()

    data = build_data(DB_PATH)
    page = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f"Fertig: {args.out} ({os.path.getsize(args.out) // 1024} KB, {len(data['stations'])} Stationen)")
    if args.open:
        webbrowser.open('file:///' + os.path.abspath(args.out).replace('\\', '/'))


if __name__ == "__main__":
    main()
