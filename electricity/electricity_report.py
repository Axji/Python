"""Erzeugt eine interaktive HTML-Auswertung der Schweizer Strombilanz aus der SQLite-Datenbank electricity.db.

Die Seite (daten/strom_auswertung.html) zeigt, wie viel Strom die Schweiz erzeugt und verbraucht hat und ob sie über- oder
unterproduziert hat (Überschuss = Nettoerzeugung minus Landesverbrauch = Ausfuhr minus Einfuhr):
  1. Kennzahlen und Zusammenfassung (neuester Monat, letztes volles Jahr, letzter voller Winter, Photovoltaik, Kernkraft)
  2. Über- und Unterproduktion pro Monat, mit 12-Monats-Summe
  3. Jahresbilanz: Überschuss pro Jahr und Eigendeckung in Prozent des Verbrauchs
  4. Winter (Oktober bis März) gegen Sommer (April bis September)
  5. Erzeugung nach Herstellungsart pro Jahr, absolut oder als Anteil
Der Zeitraum der Diagramme ist wählbar (alle Jahre, seit 2010, seit 2020). Jahres- und Halbjahreswerte zählen nur, wenn alle
Monate vorhanden sind; das laufende Jahr fehlt deshalb. Provisorische Monate sind im Monatsdiagramm blasser gezeichnet.

Die Datenbank wird nur gelesen (zuerst swiss_electricity.py ausführen). Die Seite lädt die Diagramm-Bibliothek Plotly aus
dem Internet, es sind keine Python-Zusatzpakete nötig.

Aufruf:  py electricity/electricity_report.py [--daten ORDNER] [--out DATEI] [--open]
"""
import argparse
import json
import os
import sqlite3
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'daten')  # gleicher Ordner wie bei swiss_electricity.py
DB_NAME = 'electricity.db'
OUT_NAME = 'strom_auswertung.html'

# Spalten der Tabelle monthly, die in die Seite übernommen werden (Name in der Seite ohne "_gwh")
SERIES = ['laufwerk', 'speicherwerk', 'kernkraft', 'andere', 'thermisch', 'wind', 'photovoltaik', 'landeserzeugung', 'speicherpumpen',
          'erzeugung_netto', 'einfuhr', 'ausfuhr', 'landesverbrauch', 'verluste', 'endverbrauch']


def clean(value):
    """Ganze Zahlen ohne Nachkommastelle (kleineres JSON), fehlende Werte bleiben None (null)."""
    if value is not None and float(value).is_integer():
        return int(value)
    return value


def build_data(db_path):
    """Liest alle Monate aus der Datenbank und gibt sie spaltenweise für die Seite zurück."""
    if not os.path.exists(db_path):
        raise SystemExit('Datenbank fehlt: ' + db_path + ' (zuerst swiss_electricity.py ausführen)')
    # Nur lesen: mode=ro verhindert, dass eine fehlende Datenbank leer neu angelegt wird
    conn = sqlite3.connect('file:' + db_path.replace('\\', '/') + '?mode=ro', uri=True)
    try:
        columns = ', '.join(f'{name}_gwh' for name in SERIES)
        rows = conn.execute(f'SELECT periode, definitiv, abgerufen_am, {columns} FROM monthly ORDER BY jahr, monat').fetchall()
    finally:
        conn.close()
    if not rows:
        raise SystemExit('Die Datenbank enthält keine Monatsdaten (zuerst swiss_electricity.py ausführen)')
    return {
        'periods': [r[0] for r in rows],
        'definitiv': [r[1] for r in rows],
        'retrievedAt': max(r[2] for r in rows),
        'series': {name: [clean(r[3 + i]) for r in rows] for i, name in enumerate(SERIES)},
    }


HTML = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Strom Auswertung</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root { --bg:#fff; --fg:#1c2733; --muted:#5b6b7a; --line:#d9e0e7; --accent:#0b6bcb; --card:#f5f8fb;
          --pos:#2e9e6a; --neg:#d6453d; --winter:#3b7dd8; --summer:#e0a030; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14191f; --fg:#e6ecf2; --muted:#9fb0c0; --line:#2b3641; --accent:#5aa9ff; --card:#1b232c;
            --pos:#46c08a; --neg:#ef6b62; --winter:#5b9bf0; --summer:#f0b84a; }
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
  .pos { color:var(--pos); } .neg { color:var(--neg); }
  #summary { background:var(--card); border-left:4px solid var(--accent); padding:10px 14px; border-radius:4px; margin-bottom:12px; }
  .chart { width:100%; }
</style>
</head>
<body>
<h1>Hat die Schweiz mehr Strom erzeugt als verbraucht?</h1>
<div class="sub">Monatliche Elektrizitätsbilanz des Bundesamts für Energie (BFE), alle Werte in GWh · Quelle: <span id="retrieved"></span></div>

<div class="controls">
  <label>Zeitraum der Diagramme <select id="range">
    <option value="all">alle Jahre</option>
    <option value="2010">seit 2010</option>
    <option value="2020">seit 2020</option>
  </select></label>
</div>

</div>

<div id="summary"></div>
<div class="cards" id="cards"></div>

<h2>Über- und Unterproduktion pro Monat</h2>
<p class="note">Balken: Nettoerzeugung (nach Abzug des Pumpstroms) minus Landesverbrauch. Grün = mehr erzeugt als verbraucht (Ausfuhrüberschuss), rot = Strom netto importiert. Linie (rechte Achse): Summe der letzten zwölf Monate.</p>
<div id="c_surplus" class="chart"></div>

<h2>Jahresbilanz</h2>
<p class="note">Balken: Überschuss des Jahres. Linie (rechte Achse): Eigendeckung, also Nettoerzeugung in Prozent des Landesverbrauchs; über 100 % bedeutet Überproduktion.</p>
<div id="c_years" class="chart"></div>

<h2>Winter gegen Sommer</h2>
<p class="note">Überschuss je Halbjahr: Winter von Oktober bis März, Sommer von April bis September. Nur vollständige Halbjahre.</p>
<div id="c_half" class="chart"></div>

<h2>Erzeugung nach Herstellungsart pro Jahr</h2>
<p class="note">Landeserzeugung vor Abzug des Pumpstroms. Linie (nur absolut): Landesverbrauch. Wind, Photovoltaik und Thermische sind erst seit 2020 einzeln ausgewiesen, davor stehen sie unter «andere».</p>
<div class="controls"><label>Darstellung <select id="mix">
  <option value="">absolut in GWh</option><option value="percent">Anteil in %</option></select></label></div>
<div id="c_mix_year" class="chart"></div>


<script>
const DATA = __DATA__;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const N = DATA.periods.length;
const S = DATA.series;
const yearOf = DATA.periods.map(p => +p.slice(0, 4));
const monthOf = DATA.periods.map(p => +p.slice(5, 7));
const sub = (a, b) => a === null || b === null ? null : a - b;
const add = (a, b) => a === null || b === null ? null : a + b;
const ratio = (a, b) => a === null || b === null || b === 0 ? null : 100 * a / b;
const num = (x, d = 0) => x === null || x === undefined || isNaN(x) ? '–' : x.toLocaleString('de-CH', {minimumFractionDigits: d, maximumFractionDigits: d});
const signed = (x, d = 0) => x === null || x === undefined || isNaN(x) ? '–' : (x > 0 ? '+' : x < 0 ? '−' : '') + num(Math.abs(x), d);

// Abgeleitete Reihen pro Monat
S.wasserkraft = S.laufwerk.map((x, i) => add(x, S.speicherwerk[i]));
S.ueberschuss = S.erzeugung_netto.map((x, i) => sub(x, S.landesverbrauch[i]));
S.eigendeckung = S.erzeugung_netto.map((x, i) => ratio(x, S.landesverbrauch[i]));

// Summen von Gruppen: Jahre (nur mit zwölf Monaten) und Halbjahre (nur mit sechs Monaten)
const SUM_KEYS = ['wasserkraft', 'laufwerk', 'speicherwerk', 'kernkraft', 'andere', 'thermisch', 'wind', 'photovoltaik', 'landeserzeugung',
                  'speicherpumpen', 'erzeugung_netto', 'einfuhr', 'ausfuhr', 'landesverbrauch', 'ueberschuss'];
function groups(keyFn, size, labelFn) {
  const map = new Map();
  for (let i = 0; i < N; i++) { const k = keyFn(i); if (!map.has(k)) map.set(k, []); map.get(k).push(i); }
  return [...map].filter(([, idx]) => idx.length === size).map(([key, idx]) => {
    const g = {key, idx, label: labelFn(key)};
    SUM_KEYS.forEach(k => { const v = idx.map(i => S[k][i]).filter(x => x !== null); g[k] = v.length ? v.reduce((a, b) => a + b, 0) : null; });
    g.eigendeckung = ratio(g.erzeugung_netto, g.landesverbrauch);
    g.definitiv = idx.every(i => DATA.definitiv[i] === 1);
    return g;
  });
}
const YEARS = groups(i => yearOf[i], 12, k => '' + k);
const HALVES = groups(i => monthOf[i] >= 10 ? 'W' + yearOf[i] : monthOf[i] <= 3 ? 'W' + (yearOf[i] - 1) : 'S' + yearOf[i], 6,
  k => k[0] === 'W' ? 'Winter ' + k.slice(1) + '/' + ('' + (+k.slice(1) + 1)).slice(2) : 'Sommer ' + k.slice(1));
const halfStart = h => +h.key.slice(1);

function render() {
  const from = +(document.getElementById('range').value === 'all' ? 0 : document.getElementById('range').value);
  const fg = css('--fg'), muted = css('--muted'), line = css('--line'), pos = css('--pos'), neg = css('--neg');
  const winterC = css('--winter'), summerC = css('--summer');
  const years = YEARS.filter(y => +y.key >= from);
  const halves = HALVES.filter(h => halfStart(h) >= from);
  const months = [...Array(N).keys()].filter(i => yearOf[i] >= from);
  const dates = months.map(i => DATA.periods[i] + '-01');
  const sign = x => x === null ? muted : x >= 0 ? pos : neg;
  const statusText = x => x > 0 ? 'Überproduktion' : x < 0 ? 'Unterproduktion' : 'ausgeglichen';

  // ---- Kennzahlen und Zusammenfassung (immer über alle Daten, unabhängig vom gewählten Zeitraum)
  const last = N - 1, ly = YEARS[YEARS.length - 1], py = YEARS[YEARS.length - 2], lh = HALVES.filter(h => h.key[0] === 'W').pop();
  const share = (g, k) => ratio(g[k], g.landeserzeugung);
  const cards = [
    ['Neuester Monat ' + DATA.periods[last] + (DATA.definitiv[last] ? '' : ' (provisorisch)'), signed(S.ueberschuss[last]) + ' GWh',
      statusText(S.ueberschuss[last]) + ', Eigendeckung ' + num(S.eigendeckung[last], 1) + ' %', S.ueberschuss[last] >= 0 ? 'pos' : 'neg'],
    ['Letztes volles Jahr ' + ly.label, signed(ly.ueberschuss) + ' GWh', statusText(ly.ueberschuss) + ', Eigendeckung ' + num(ly.eigendeckung, 1) + ' %', ly.ueberschuss >= 0 ? 'pos' : 'neg'],
    ['Letzter voller Winter ' + (lh ? lh.label.slice(7) : ''), lh ? signed(lh.ueberschuss) + ' GWh' : '–', lh ? statusText(lh.ueberschuss) + ', Eigendeckung ' + num(lh.eigendeckung, 1) + ' %' : '', lh && lh.ueberschuss >= 0 ? 'pos' : 'neg'],
    ['Photovoltaik ' + ly.label, num(ly.photovoltaik) + ' GWh', num(share(ly, 'photovoltaik'), 1) + ' % der Erzeugung' + (py && py.photovoltaik ? ', ' + signed(ly.photovoltaik - py.photovoltaik) + ' GWh zum Vorjahr' : ''), ''],
    ['Kernkraft ' + ly.label, num(ly.kernkraft) + ' GWh', num(share(ly, 'kernkraft'), 1) + ' % der Erzeugung' + (py ? ', ' + signed(ly.kernkraft - py.kernkraft) + ' GWh zum Vorjahr' : ''), ''],
  ];
  document.getElementById('cards').innerHTML = cards.map(c =>
    `<div class="card"><div class="l">${c[0]}</div><div class="v ${c[3]}">${c[1]}</div><div class="l">${c[2]}</div></div>`).join('');
  const surplusYears = YEARS.filter(y => y.ueberschuss > 0).length;
  const winters = HALVES.filter(h => h.key[0] === 'W'), summers = HALVES.filter(h => h.key[0] === 'S');
  const winterDeficit = winters.filter(h => h.ueberschuss < 0).length, summerSurplus = summers.filter(h => h.ueberschuss > 0).length;
  document.getElementById('summary').innerHTML =
    `In <b>${surplusYears} von ${YEARS.length}</b> vollen Jahren (${YEARS[0].label}–${ly.label}) hat die Schweiz mehr Strom erzeugt als verbraucht. ` +
    `In <b>${winterDeficit} von ${winters.length}</b> vollständigen Winterhalbjahren wurde netto importiert, in <b>${summerSurplus} von ${summers.length}</b> Sommerhalbjahren netto exportiert. ` +
    `Das Jahr ${ly.label} endete mit ${signed(ly.ueberschuss)} GWh (${statusText(ly.ueberschuss)}).`;

  const cfg = {responsive: true, displaylogo: false};
  const layout = extra => Object.assign({
    margin: {l: 60, r: 60, t: 10, b: 40}, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {color: fg}, xaxis: {gridcolor: line}, yaxis: {gridcolor: line, zerolinecolor: muted}, legend: {orientation: 'h', y: -0.18},
  }, extra);
  const axis = (title, extra) => Object.assign({title, gridcolor: line, zerolinecolor: muted}, extra || {});
  const axis2 = title => ({title, overlaying: 'y', side: 'right', showgrid: false, zeroline: false});

  // ---- 1. Überschuss pro Monat mit 12-Monats-Summe
  const rolling = months.map(i => {
    if (i < 11) return null;
    let s = 0; for (let j = i - 11; j <= i; j++) { if (S.ueberschuss[j] === null) return null; s += S.ueberschuss[j]; }
    return s;
  });
  Plotly.react('c_surplus', [
    {type: 'bar', x: dates, y: months.map(i => S.ueberschuss[i]), name: 'Überschuss pro Monat', marker: {color: months.map(i => sign(S.ueberschuss[i])), opacity: months.map(i => DATA.definitiv[i] ? 1 : 0.5)},
     customdata: months.map(i => statusText(S.ueberschuss[i]) + ', Eigendeckung ' + num(S.eigendeckung[i], 1) + ' %' + (DATA.definitiv[i] ? '' : ' (provisorisch)')),
     hovertemplate: '%{x|%Y-%m}: %{y:+,.0f} GWh<br>%{customdata}<extra></extra>'},
    {type: 'scatter', mode: 'lines', x: dates, y: rolling, yaxis: 'y2', name: 'Summe der letzten 12 Monate (rechte Achse)', line: {color: fg, width: 2.5},
     hovertemplate: '%{x|%Y-%m}: %{y:+,.0f} GWh<extra>12 Monate</extra>'},
  ], layout({height: 380, yaxis: axis('GWh pro Monat'), yaxis2: axis2('GWh in 12 Monaten')}), cfg);

  // ---- 2. Jahresbilanz
  Plotly.react('c_years', [
    {type: 'bar', x: years.map(y => y.label), y: years.map(y => y.ueberschuss), name: 'Überschuss des Jahres', marker: {color: years.map(y => sign(y.ueberschuss)), opacity: years.map(y => y.definitiv ? 1 : 0.5)},
     hovertemplate: '%{x}: %{y:+,.0f} GWh<extra></extra>'},
    {type: 'scatter', mode: 'lines+markers', x: years.map(y => y.label), y: years.map(y => y.eigendeckung), yaxis: 'y2', name: 'Eigendeckung in % (rechte Achse)', line: {color: fg, width: 2.5},
     hovertemplate: '%{x}: %{y:.1f} %<extra>Eigendeckung</extra>'},
  ], layout({height: 360, xaxis: {gridcolor: line, type: 'category'}, yaxis: axis('GWh pro Jahr'), yaxis2: axis2('Eigendeckung in %')}), cfg);

  // ---- 3. Winter gegen Sommer
  const half = typ => ({x: halves.filter(h => h.key[0] === typ).map(h => h.label), y: halves.filter(h => h.key[0] === typ).map(h => h.ueberschuss),
    cd: halves.filter(h => h.key[0] === typ).map(h => statusText(h.ueberschuss) + ', Eigendeckung ' + num(h.eigendeckung, 1) + ' %')});
  const w = half('W'), s = half('S');
  Plotly.react('c_half', [
    {type: 'bar', x: s.x, y: s.y, customdata: s.cd, name: 'Sommer (April–September)', marker: {color: summerC}, hovertemplate: '%{x}: %{y:+,.0f} GWh<br>%{customdata}<extra></extra>'},
    {type: 'bar', x: w.x, y: w.y, customdata: w.cd, name: 'Winter (Oktober–März)', marker: {color: winterC}, hovertemplate: '%{x}: %{y:+,.0f} GWh<br>%{customdata}<extra></extra>'},
  ], layout({height: 360, margin: {l: 60, r: 15, t: 10, b: 70}, xaxis: {gridcolor: line, type: 'category', tickangle: -45}, yaxis: axis('GWh pro Halbjahr')}), cfg);

  // ---- 4. Mix pro Jahr (absolut oder Anteil)
  const MIX = [['laufwerk', 'Laufwerke', '#4f9be8'], ['speicherwerk', 'Speicherwerke', '#1f5fa8'], ['kernkraft', 'Kernkraft', '#8e5bd6'],
               ['photovoltaik', 'Photovoltaik', '#f0b429'], ['wind', 'Wind', '#3cb8a8'], ['thermisch', 'Thermische', '#8a8f98'], ['andere', 'andere (bis 2019)', '#c4c9d0']];
  const percent = document.getElementById('mix').value === 'percent';
  const mixTraces = MIX.map(m => ({type: 'bar', x: years.map(y => y.label), y: years.map(y => y[m[0]]), name: m[1], marker: {color: m[2]},
    hovertemplate: '%{x}: %{y:,.0f} GWh<extra>' + m[1] + '</extra>'}));
  if (!percent) mixTraces.push({type: 'scatter', mode: 'lines+markers', x: years.map(y => y.label), y: years.map(y => y.landesverbrauch), name: 'Landesverbrauch',
    line: {color: fg, width: 2.5}, hovertemplate: '%{x}: %{y:,.0f} GWh<extra>Landesverbrauch</extra>'});
  Plotly.react('c_mix_year', mixTraces, layout({height: 400, barmode: 'stack', barnorm: percent ? 'percent' : '', margin: {l: 60, r: 15, t: 10, b: 40},
    xaxis: {gridcolor: line, type: 'category'}, yaxis: axis(percent ? 'Anteil in %' : 'GWh pro Jahr')}), cfg);

}

document.getElementById('retrieved').textContent = 'Abruf ' + (DATA.retrievedAt || '').replace('T', ' ');
['range', 'mix'].forEach(id => document.getElementById(id).addEventListener('change', render));
render();
</script>
</body>
</html>
"""


def main(argv=None):
    """Liest die Datenbank und schreibt die HTML-Seite."""
    parser = argparse.ArgumentParser(description='Erzeugt die interaktive Strom-Auswertung als HTML-Seite.')
    parser.add_argument('--daten', default=DATA_DIR, help=f'Ordner mit der Datenbank {DB_NAME} (Standard: {DATA_DIR})')
    parser.add_argument('--out', help=f'Ausgabedatei (Standard: {OUT_NAME} im Datenordner)')
    parser.add_argument('--open', action='store_true', help='Seite danach im Browser öffnen')
    args = parser.parse_args(argv)
    out = args.out or os.path.join(args.daten, OUT_NAME)

    data = build_data(os.path.join(args.daten, DB_NAME))
    page = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'Fertig: {out} ({os.path.getsize(out) // 1024} KB, {len(data["periods"])} Monate bis {data["periods"][-1]})')
    if args.open:
        webbrowser.open('file:///' + os.path.abspath(out).replace('\\', '/'))


if __name__ == '__main__':
    main()
