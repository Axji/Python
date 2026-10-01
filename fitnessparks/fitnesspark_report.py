"""Erzeugt eine interaktive HTML-Auswertung der Fitnesspark-Belegung aus den CSV-Dateien im Ordner `data`.

Die Seite (data/fitnesspark_auswertung.html) lässt sich nach Park filtern und zeigt:
  1. Beste Zeit: Wochentag x Uhrzeit als Heatmap, dazu die beste und die stärkste Stunde je Wochentag
  2. Tagesverlauf: durchschnittliche Belegung über den Tag, eine Linie je Wochentag
  3. Saison: Monatsmittel (Jahre im Vergleich), Wochenverlauf und Monat x Uhrzeit

Warum die CSV-Dateien und nicht die Datenbank: Der Scraper schreibt nur Zeilen mit einem Wert grösser als 0. Ein
geschlossener oder leerer Park fehlt in den Daten also einfach. Ob eine fehlende Zeile "Belegung 0" oder "unverändert"
bedeutet, lässt sich nur mit den ursprünglichen CSV-Dateien erkennen. Die durch fitnesspark_clean.py bereinigte Datenbank
enthält diese Information nicht mehr.

Auswertung:
  - Gemessen wurde in einem 5-Minuten-Fenster, wenn mindestens ein Park eine Zeile geliefert hat (Messzeiten des Scrapers).
  - In einem gemessenen Fenster zählt ein Park ohne Zeile als leer (Belegung 0). Fenster ohne jede Messung (nachts, Ausfälle
    des Scrapers) und Tage ohne CSV-Datei werden nicht ausgewertet.
  - Öffnungszeiten: Ein Zeitfenster gilt für einen Park und Wochentag als geöffnet, wenn die Belegung an mindestens 80 % der
    gemessenen Tage grösser als 0 war. Nur diese Zeiten fliessen in "beste Zeit" und die Saisonwerte ein.
  - Monate mit weniger als 10 und Wochen mit weniger als 5 Tagen Daten werden in der Saison-Ansicht weggelassen.

Die Dateien werden nur gelesen. Die Seite lädt die Diagramm-Bibliothek Plotly aus dem Internet, es sind keine
Python-Zusatzpakete nötig.

Aufruf:  py fitnesspark_report.py [--out DATEI] [--open]
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import sys
import webbrowser

# Das gemeinsame Datenbankmodul liegt eine Ebene höher (liefert hier nur den Pfad des Ordners `data`)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitnesspark_db  # noqa: E402

SLOT_SECONDS = 300  # Raster: 5 Minuten
SLOTS = 24 * 3600 // SLOT_SECONDS  # 288 Zeitfenster pro Tag
OPEN_SHARE = 0.8  # Anteil der Tage mit Belegung > 0, ab dem ein Zeitfenster als geöffnet gilt
MIN_DAYS_FOR_OPEN = 3  # Mindestanzahl gemessener Tage, bevor ein Zeitfenster bewertet wird
MIN_DAYS_MONTH = 10
MIN_DAYS_WEEK = 5
DEFAULT_OUT = os.path.join(fitnesspark_db.DATA_DIR, 'fitnesspark_auswertung.html')


def load_csv(data_dir):
    """
    Liest alle CSV-Dateien (Park, Belegung, Zeitstempel).
    Gibt (values, coverage) zurück:
      values:   {Park: {Datum: {Fenster: Belegung}}}
      coverage: {Datum: Menge der Fenster, in denen mindestens ein Park gemessen wurde}
    """
    files = sorted(glob.glob(os.path.join(data_dir, '*.csv')))
    if not files:
        sys.exit(f"Keine CSV-Dateien im Ordner '{data_dir}' gefunden.")
    values = collections.defaultdict(lambda: collections.defaultdict(dict))
    coverage = collections.defaultdict(set)
    skipped = 0
    for file in files:
        with open(file, encoding='utf-8-sig') as f:
            next(f, None)  # Kopfzeile überspringen
            for line in f:
                parts = line.strip().rsplit(',', 2)
                if len(parts) != 3:
                    continue  # Leerzeilen
                park, value, stamp = parts
                try:
                    day = dt.date(int(stamp[0:4]), int(stamp[5:7]), int(stamp[8:10]))
                    slot = (int(stamp[11:13]) * 3600 + int(stamp[14:16]) * 60) // SLOT_SECONDS
                    number = int(float(value))
                except ValueError:
                    skipped += 1  # Unlesbare Zeilen ignorieren
                    continue
                values[park][day][slot] = number
                coverage[day].add(slot)
    if skipped:
        print(f"Hinweis: {skipped} unlesbare Zeilen wurden ignoriert.")
    return values, coverage


def find_gaps(days):
    """Gibt die Datenlücken (Tage ohne CSV-Datei zwischen dem ersten und letzten Tag) als Liste von (von, bis) zurück."""
    present = set(days)
    gaps, run = [], []
    day = min(days)
    while day <= max(days):
        if day in present:
            if run:
                gaps.append((run[0], run[-1]))
            run = []
        else:
            run.append(day)
        day += dt.timedelta(days=1)
    return gaps


def day_vectors(park_days, coverage, days):
    """
    Erstellt für jeden Tag einen Vektor mit der Belegung je 5-Minuten-Fenster.
    Fenster ohne Messung des Scrapers sind None, gemessene Fenster ohne Zeile des Parks zählen als 0 (leer).
    """
    result = []
    for day in days:
        measured, rows = coverage[day], park_days.get(day, {})
        result.append((day, [rows.get(slot, 0) if slot in measured else None for slot in range(SLOTS)]))
    return result


def mean(numbers):
    """Mittelwert einer Liste, None bei leerer Liste."""
    return sum(numbers) / len(numbers) if numbers else None


def r1(x):
    """Rundet auf eine Nachkommastelle, None bleibt None."""
    return None if x is None else round(x, 1)


def analyse_park(park_days, coverage, days):
    """Berechnet alle Kennzahlen eines Parks, die die Seite darstellt."""
    vectors = day_vectors(park_days, coverage, days)

    # Öffnungszeiten je Wochentag und Zeitfenster bestimmen
    count = [[0] * SLOTS for _ in range(7)]
    positive = [[0] * SLOTS for _ in range(7)]
    for day, vector in vectors:
        weekday = day.weekday()
        for slot, value in enumerate(vector):
            if value is not None:
                count[weekday][slot] += 1
                if value > 0:
                    positive[weekday][slot] += 1
    is_open = [
        [count[w][s] >= MIN_DAYS_FOR_OPEN and positive[w][s] / count[w][s] >= OPEN_SHARE for s in range(SLOTS)]
        for w in range(7)
    ]

    # Mittelwerte nur über die Öffnungszeiten
    heat_sum = [[0.0] * SLOTS for _ in range(7)]
    heat_cnt = [[0] * SLOTS for _ in range(7)]
    month_sum, month_cnt = collections.defaultdict(lambda: [0.0] * SLOTS), collections.defaultdict(lambda: [0] * SLOTS)
    month_daily = collections.defaultdict(list)
    week_daily = collections.defaultdict(list)
    levels = collections.Counter()
    for day, vector in vectors:
        weekday = day.weekday()
        month = day.strftime('%Y-%m')
        week = (day - dt.timedelta(days=weekday)).isoformat()  # Montag der Woche
        open_values = []
        for slot, value in enumerate(vector):
            if value is None or not is_open[weekday][slot]:
                continue
            heat_sum[weekday][slot] += value
            heat_cnt[weekday][slot] += 1
            month_sum[month][slot] += value
            month_cnt[month][slot] += 1
            open_values.append(value)
            levels[value] += 1
        daily = mean(open_values)
        if daily is not None:
            month_daily[month].append(daily)
            week_daily[week].append(daily)

    # 95. Perzentil als Bezugswert für die relative Darstellung (Parks unterschiedlicher Grösse vergleichbar machen)
    total = sum(levels.values())
    p95, cumulative = 0, 0
    for level in sorted(levels):
        cumulative += levels[level]
        p95 = level
        if cumulative >= 0.95 * total:
            break

    return {
        'heat': [[r1(heat_sum[w][s] / heat_cnt[w][s]) if heat_cnt[w][s] else None for s in range(SLOTS)] for w in range(7)],
        'month': {m: r1(mean(v)) for m, v in sorted(month_daily.items()) if len(v) >= MIN_DAYS_MONTH},
        'week': {w: r1(mean(v)) for w, v in sorted(week_daily.items()) if len(v) >= MIN_DAYS_WEEK},
        'monthslot': {
            m: [r1(month_sum[m][s] / month_cnt[m][s]) if month_cnt[m][s] else None for s in range(SLOTS)]
            for m in sorted(month_daily) if len(month_daily[m]) >= MIN_DAYS_MONTH
        },
        'p95': max(p95, 1),
        'days': len(vectors),
    }


def build_data(data_dir):
    """Liest die CSV-Dateien und berechnet die Daten für die HTML-Seite."""
    values, coverage = load_csv(data_dir)
    days = sorted(coverage)
    return {
        'parks': {name: analyse_park(park_days, coverage, days) for name, park_days in sorted(values.items())},
        'range': [days[0].isoformat(), days[-1].isoformat()],
        'gaps': [[a.isoformat(), b.isoformat()] for a, b in find_gaps(days)],
        'days': len(days),
        'created': dt.datetime.now().strftime('%d.%m.%Y %H:%M'),
    }


HTML = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fitnesspark Auswertung</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root { --bg:#fff; --fg:#1c2733; --muted:#5b6b7a; --line:#d9e0e7; --accent:#0b6bcb; --card:#f5f8fb; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14191f; --fg:#e6ecf2; --muted:#9fb0c0; --line:#2b3641; --accent:#5aa9ff; --card:#1b232c; }
  }
  body { margin:0; padding:16px; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, Segoe UI, sans-serif; }
  h1 { font-size:22px; margin:0 0 4px; }
  .sub { color:var(--muted); margin-bottom:14px; }
  .bar { display:flex; flex-wrap:wrap; gap:12px 18px; align-items:end; margin-bottom:12px; }
  label { display:flex; flex-direction:column; font-size:12px; color:var(--muted); gap:3px; }
  select { font:inherit; padding:6px 8px; background:var(--card); color:var(--fg); border:1px solid var(--line); border-radius:6px; }
  .tabs { display:flex; gap:6px; border-bottom:1px solid var(--line); margin-bottom:12px; }
  .tab { padding:8px 14px; cursor:pointer; border:1px solid transparent; border-bottom:none; border-radius:6px 6px 0 0; color:var(--muted); }
  .tab.active { color:var(--fg); background:var(--card); border-color:var(--line); font-weight:600; }
  .view { display:none; } .view.active { display:block; }
  table { border-collapse:collapse; width:100%; max-width:760px; margin:10px 0 16px; }
  th, td { text-align:left; padding:6px 10px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-weight:600; font-size:12px; }
  .good { color:#1a9a4a; font-weight:600; } .busy { color:#d4572a; font-weight:600; }
  .note { color:var(--muted); font-size:13px; margin-top:6px; }
  .chart { width:100%; }
</style>
</head>
<body>
<h1>Fitnesspark Auswertung</h1>
<div class="sub" id="sub"></div>

<div class="bar">
  <label>Park <select id="park"></select></label>
  <label>Darstellung <select id="metric">
    <option value="abs">Personen (absolut)</option>
    <option value="rel">% vom Spitzenwert (vergleichbar)</option>
  </select></label>
  <label>Zeitfenster für „beste Zeit“ <select id="win">
    <option value="30">30 Minuten</option><option value="60" selected>1 Stunde</option>
    <option value="90">90 Minuten</option><option value="120">2 Stunden</option>
  </select></label>
</div>

<div class="tabs" id="tabs">
  <div class="tab active" data-view="best">Beste Zeit</div>
  <div class="tab" data-view="day">Tagesverlauf</div>
  <div class="tab" data-view="season">Saison</div>
</div>

<div class="view active" id="view-best">
  <table id="besttable"></table>
  <div id="heat" class="chart" style="height:380px"></div>
  <div class="note">Je niedriger der Wert, desto leerer das Studio. Berücksichtigt werden nur Zeiten, in denen der Park üblicherweise geöffnet ist (an mindestens 80 % der Tage Besucher). Bei „Alle Parks“ nur Zeiten, in denen mindestens die Hälfte der Parks geöffnet ist.</div>
</div>
<div class="view" id="view-day">
  <div id="lines" class="chart" style="height:460px"></div>
  <div class="note">Legende anklicken blendet einen Wochentag aus oder ein.</div>
</div>
<div class="view" id="view-season">
  <div id="months" class="chart" style="height:340px"></div>
  <div id="weeks" class="chart" style="height:340px"></div>
  <div id="monthslot" class="chart" style="height:420px"></div>
  <div class="note" id="seasonnote"></div>
</div>

<script>
const DATA = __DATA__;
const WD = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag'];
const MONTHS = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
const SLOTS = 288;
const labels = Array.from({length:SLOTS}, (_, i) => String(Math.floor(i/12)).padStart(2,'0') + ':' + String((i%12)*5).padStart(2,'0'));
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

// Skaliert alle Zahlen einer verschachtelten Struktur (Listen, Objekte) mit einem Faktor; null bleibt null.
function scale(x, f) {
  if (x === null || x === undefined) return null;
  if (Array.isArray(x)) return x.map(v => scale(v, f));
  if (typeof x === 'object') { const o = {}; for (const k in x) o[k] = scale(x[k], f); return o; }
  return x * f;
}
// Mittelt mehrere gleich aufgebaute Strukturen; null-Werte werden ignoriert. Mit minShare (0 bis 1) wird ein Wert nur
// gebildet, wenn mindestens dieser Anteil der Strukturen einen Wert hat.
function mean(list, minShare = 0) {
  const ref = list.find(v => v !== null && v !== undefined);
  if (ref === undefined) return null;
  if (Array.isArray(ref)) return ref.map((_, i) => mean(list.map(l => (l ? l[i] : null)), minShare));
  if (typeof ref === 'object') {
    const keys = new Set(list.flatMap(l => (l ? Object.keys(l) : []))), o = {};
    for (const k of [...keys].sort()) o[k] = mean(list.map(l => (l ? l[k] : null)), minShare);
    return o;
  }
  const n = list.filter(v => v !== null && v !== undefined);
  return n.length && n.length >= minShare * list.length ? n.reduce((a, b) => a + b, 0) / n.length : null;
}
function current() {
  const park = document.getElementById('park').value, rel = document.getElementById('metric').value === 'rel';
  const pick = n => {
    const p = DATA.parks[n], f = rel ? 100 / p.p95 : 1;
    return {heat: scale(p.heat, f), month: scale(p.month, f), week: scale(p.week, f), monthslot: scale(p.monthslot, f)};
  };
  const names = park === '__all__' ? Object.keys(DATA.parks) : [park];
  const parts = names.map(pick);
  const d = parts.length === 1 ? parts[0] : {
    heat: mean(parts.map(p => p.heat), 0.5), month: mean(parts.map(p => p.month)),
    week: mean(parts.map(p => p.week)), monthslot: mean(parts.map(p => p.monthslot), 0.5)};
  return {d, unit: rel ? '% vom Spitzenwert' : 'Personen', rel};
}
// Farbverlauf: grün = wenig los (gut), gelb = mittel, rot = voll
const SCALE = [[0, '#1a9850'], [0.5, '#fee08b'], [1, '#d73027']];
const hhmm = slot => labels[slot % SLOTS] || '24:00';
const fmt = (v, rel) => rel ? v.toFixed(0) + ' %' : v.toFixed(1) + ' Pers.';

function layout(title, extra) {
  return Object.assign({
    title: {text: title, font: {size: 15}}, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {color: css('--fg')}, margin: {l: 60, r: 20, t: 46, b: 50}, legend: {orientation: 'h', y: -0.2}
  }, extra || {});
}
// Funktion statt Objekt: Plotly schreibt erkannte Achsenarten in das übergebene Layout, ein gemeinsames Objekt würde andere Achsen verfälschen
const grid = () => ({gridcolor: css('--line'), zerolinecolor: css('--line')});

// Sichtbarer Zeitbereich: von der ersten bis zur letzten Zeit, in der irgendein Wochentag Daten hat
function timeRange(heat) {
  let lo = SLOTS, hi = -1;
  heat.forEach(row => row.forEach((v, s) => { if (v !== null) { lo = Math.min(lo, s); hi = Math.max(hi, s); } }));
  return hi < 0 ? [0, SLOTS - 1] : [lo, hi];
}

function bestTable(c) {
  const L = +document.getElementById('win').value / 5;
  let html = '<tr><th>Wochentag</th><th>Beste Zeit (am leersten)</th><th>Stärkste Zeit (am vollsten)</th></tr>';
  c.d.heat.forEach((row, w) => {
    let best = null, busy = null;
    for (let s = 0; s + L <= SLOTS; s++) {
      const win = row.slice(s, s + L);
      if (win.some(v => v === null)) continue;
      const m = win.reduce((a, b) => a + b, 0) / L;
      if (!best || m < best.m) best = {s, m};
      if (!busy || m > busy.m) busy = {s, m};
    }
    const cell = (x, cls) => x ? `<span class="${cls}">${hhmm(x.s)}–${hhmm(x.s + L)}</span> (Ø ${fmt(x.m, c.rel)})` : '–';
    html += `<tr><td>${WD[w]}</td><td>${cell(best, 'good')}</td><td>${cell(busy, 'busy')}</td></tr>`;
  });
  document.getElementById('besttable').innerHTML = html;
}

function render() {
  const c = current(), [lo, hi] = timeRange(c.d.heat), xs = labels.slice(lo, hi + 1);
  const tick = {type: 'category', tickmode: 'array', tickvals: xs.filter((_, i) => (lo + i) % 12 === 0), ...grid()};
  const z = unit => ({colorbar: {title: unit}});

  bestTable(c);
  Plotly.react('heat', [{type: 'heatmap', x: xs, y: WD, z: c.d.heat.map(r => r.slice(lo, hi + 1)),
    colorscale: SCALE, hoverongaps: false, ...z(c.unit),
    hovertemplate: '%{y} %{x}<br>Ø %{z:.1f}<extra></extra>'}],
    layout('Durchschnittliche Belegung nach Wochentag und Uhrzeit', {xaxis: tick, yaxis: {autorange: 'reversed'}}), {responsive: true});

  Plotly.react('lines', c.d.heat.map((row, w) => ({type: 'scatter', mode: 'lines', name: WD[w], x: xs,
    y: row.slice(lo, hi + 1), connectgaps: false, line: {width: 2, shape: 'hv'}})),
    layout('Tagesverlauf nach Wochentag (' + c.unit + ')', {xaxis: tick, yaxis: {title: c.unit, rangemode: 'tozero', ...grid()}}), {responsive: true});

  // Monatsmittel: je Jahr eine Linie
  const years = {};
  Object.entries(c.d.month).forEach(([ym, v]) => { const [y, m] = ym.split('-'); (years[y] = years[y] || Array(12).fill(null))[+m - 1] = v; });
  Plotly.react('months', Object.entries(years).map(([y, arr]) => ({type: 'scatter', mode: 'lines+markers', name: y, x: MONTHS, y: arr, connectgaps: false})),
    layout('Saison: Durchschnittliche Belegung je Monat (' + c.unit + ')', {xaxis: grid(), yaxis: {title: c.unit, rangemode: 'tozero', ...grid()}}), {responsive: true});

  const wk = Object.entries(c.d.week);
  Plotly.react('weeks', [{type: 'scatter', mode: 'lines', x: wk.map(e => e[0]), y: wk.map(e => e[1]), name: 'Woche', line: {width: 2}}],
    layout('Verlauf je Kalenderwoche (' + c.unit + ')', {xaxis: grid(), yaxis: {title: c.unit, rangemode: 'tozero', ...grid()}, showlegend: false}), {responsive: true});

  const ms = Object.entries(c.d.monthslot);
  Plotly.react('monthslot', [{type: 'heatmap', x: xs, y: ms.map(e => e[0]), z: ms.map(e => e[1].slice(lo, hi + 1)),
    colorscale: SCALE, hoverongaps: false, ...z(c.unit),
    hovertemplate: '%{y} %{x}<br>Ø %{z:.1f}<extra></extra>'}],
    layout('Monat x Uhrzeit: wann ist es in welcher Jahreszeit voll?', {xaxis: tick, yaxis: {type: 'category', autorange: 'reversed'}}), {responsive: true});
}

// Seitenkopf, Auswahlfelder und Bedienung
document.getElementById('sub').textContent =
  `Daten vom ${DATA.range[0]} bis ${DATA.range[1]} (${DATA.days} ausgewertete Tage), erstellt am ${DATA.created}.`
  + (DATA.gaps.length ? ' Lücken ohne Daten: ' + DATA.gaps.map(g => g[0] + ' bis ' + g[1]).join(', ') + '.' : '');
document.getElementById('seasonnote').textContent =
  'Monate mit weniger als 10 und Wochen mit weniger als 5 ausgewerteten Tagen werden weggelassen. '
  + 'Der Vergleich der Jahre zeigt sich nur dort, wo Daten aus beiden Jahren vorliegen.';
const sel = document.getElementById('park');
sel.innerHTML = '<option value="__all__">Alle Parks (Durchschnitt)</option>'
  + Object.keys(DATA.parks).sort().map(p => `<option>${p}</option>`).join('');
['park', 'metric', 'win'].forEach(id => document.getElementById(id).addEventListener('change', render));
document.getElementById('tabs').addEventListener('click', e => {
  const t = e.target.closest('.tab'); if (!t) return;
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x === t));
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + t.dataset.view));
  window.dispatchEvent(new Event('resize'));  // Plotly passt die Grösse der nun sichtbaren Diagramme an
});
render();
</script>
</body>
</html>
"""


def main():
    """
    Hauptfunktion zur Steuerung des Skripts.
    """
    parser = argparse.ArgumentParser(description="Erzeugt die interaktive Fitnesspark-Auswertung als HTML-Seite.")
    parser.add_argument('--out', default=DEFAULT_OUT, help=f"Ausgabedatei (Standard: {DEFAULT_OUT})")
    parser.add_argument('--open', action='store_true', help="Seite danach im Browser öffnen")
    args = parser.parse_args()

    print("Lese die CSV-Dateien und berechne die Auswertung...")
    data = build_data(fitnesspark_db.DATA_DIR)
    page = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f"Fertig: {args.out} ({os.path.getsize(args.out) // 1024} KB, {len(data['parks'])} Parks, {data['days']} Tage)")
    if data['gaps']:
        print("Datenlücken (nicht ausgewertet):", ", ".join(f"{a} bis {b}" for a, b in data['gaps']))
    if args.open:
        webbrowser.open('file:///' + os.path.abspath(args.out).replace('\\', '/'))


if __name__ == "__main__":
    main()
