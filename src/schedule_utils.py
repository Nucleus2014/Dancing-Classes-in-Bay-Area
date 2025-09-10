from pathlib import Path
from dateutil import parser
import html

def df_to_date_then_studio_html_with_filters(df, filename="schedule_by_studio_filtered.html"):
    """
    Render a mobile-friendly HTML view grouped by DATE -> STUDIO,
    with dropdown filters for Date, Studio, and Instructor.
    Inside each studio, classes are shown as a compact table: Time | Instructor | Type | Location.

    Requires columns: ["date", "time", "studio", "instructor", "type", "location"].
    """
    from pathlib import Path
    import html
    from dateutil import parser

    # Defensive copy & validations
    df = df.copy()
    required = ["date", "time", "studio", "instructor", "type"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Need {required}")

    # Normalize/sort helpers
    def _norm_time(t):
        try: return parser.parse(str(t)).strftime("%I:%M %p")
        except: return str(t)
    def _date_key(x):
        try: return parser.parse(str(x)).date()
        except: return str(x)

    # Normalize & sort
    df["time"] = df["time"].map(_norm_time)
    df = df.sort_values(by=["date", "studio", "time"],
                        key=lambda s: s.map(_date_key) if s.name == "date" else s)

    # Unique values for filter dropdowns
    unique_dates = [str(x) for x in df["date"].astype(str).unique()]
    unique_studios = [str(x) for x in df["studio"].astype(str).unique()]
    unique_instructors = [str(x) for x in df["instructor"].astype(str).unique()]

    # Styles
    css = """
<style>
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  margin: 16px;
}
.controls {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.controls label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}
select, button {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e3e3e3;
  border-radius: 10px;
  background: #fff;
  font-size: 14px;
}
@media (max-width: 740px) {
  .controls { grid-template-columns: 1fr 1fr; }
}
select, button {
  width: 100%; padding: 10px 12px; border: 1px solid #e3e3e3; border-radius: 10px; background: #fff;
  font-size: 14px;
}
button { cursor: pointer; }
.section-date {
  font-weight: 800; font-size: 18px; margin: 20px 0 10px;
}
.section-studio {
  font-weight: 700; font-size: 16px; margin: 12px 0 8px; opacity: .9;
}
.box {
  border: 1px solid #eaeaea; border-radius: 12px; padding: 8px; margin: 8px 0 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,.04); background: #fff;
}
.hidden { display: none !important; }

table.mini {
  width: 100%; border-collapse: collapse; font-size: 14px;
}
.mini th, .mini td { padding: 8px 6px; border-bottom: 1px solid #f0f0f0; text-align: left; }
.mini thead { background: #fafafa; position: sticky; top: 0; }
.mini tr:last-child td { border-bottom: none; }

/* Mobile card-like rows */
@media (max-width: 640px) {
  .mini thead { display: none; }
  .mini, .mini tbody, .mini tr, .mini td { display: block; width: 100%; }
  .mini tr {
    border: 1px solid #eee; border-radius: 10px; padding: 8px; margin: 8px 0;
    box-shadow: 0 1px 2px rgba(0,0,0,.03); background: #fff;
  }
  .mini td { border: none; padding: 4px 0; }
  .mini td::before {
    display: inline-block; min-width: 110px; font-weight: 600; opacity: .7; margin-right: .5rem;
  }
  .mini td:nth-child(1)::before { content: "Time"; }
  .mini td:nth-child(2)::before { content: "Instructor"; }
  .mini td:nth-child(3)::before { content: "Type"; }
}
.badge { font-size: 12px; opacity: .65; margin-left: 6px; }
</style>
"""

        # Controls (filters with labels above each dropdown)
    def _options(values):
        return "\n".join(
            [f"<option value=''>{html.escape('All')}</option>"] +
            [f"<option value='{html.escape(v)}'>{html.escape(v)}</option>" for v in values]
        )

    controls = f"""
<div class="controls">
  <div class="filter-col">
    <label for="filter-date">Date</label>
    <select id="filter-date">{_options(unique_dates)}</select>
  </div>
  <div class="filter-col">
    <label for="filter-studio">Studio</label>
    <select id="filter-studio">{_options(unique_studios)}</select>
  </div>
  <div class="filter-col">
    <label for="filter-instructor">Instructor</label>
    <select id="filter-instructor">{_options(unique_instructors)}</select>
  </div>
  <div class="filter-col">
    <label>&nbsp;</label>
    <button id="clear-filters">Clear</button>
  </div>
</div>
"""


    # Build grouped HTML, tagging nodes with data-* so JS can filter efficiently
    parts = ["<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>",
             css, "</head><body>", controls]

    for date_val, date_chunk in df.groupby("date", sort=False):
        date_label = html.escape(str(date_val))
        parts.append(f"<section class='date-section' data-date='{date_label}'>")
        parts.append(f"<div class='section-date'>{date_label}</div>")

        for studio_val, studio_chunk in date_chunk.groupby("studio", sort=False):
            studio_label = html.escape(str(studio_val))
            parts.append(f"<div class='studio-section' data-date='{date_label}' data-studio='{studio_label}'>")
            parts.append(f"<div class='section-studio'>{studio_label}"
                         f"<span class='badge' data-count>({len(studio_chunk)})</span></div>")
            parts.append("<div class='box'>")
            parts.append("<table class='mini'><thead><tr><th>Time</th><th>Instructor</th><th>Type</th><th>Location</th></tr></thead><tbody>")

            for _, r in studio_chunk.iterrows():
                time = html.escape(str(r.get("time", "")))
                instr = html.escape(str(r.get("instructor", "")))
                lvl = html.escape(str(r.get("type", "")))
                loc = html.escape(str(r.get("location", "")))
                # Each row carries attributes for filtering
                parts.append(
                    f"<tr class='class-row' data-date='{date_label}' "
                    f"data-studio='{studio_label}' data-instructor='{html.escape(instr)}'>"
                    f"<td>{time}</td><td>{instr}</td><td>{lvl}</td><td>{loc}</td></tr>"
                )
            parts.append("</tbody></table></div></div>")  # close box + studio-section

        parts.append("</section>")  # close date-section

    # Filtering script: hides rows based on dropdowns, then hides empty studios/dates
    script = """
<script>
(function(){
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  const fDate = $("#filter-date");
  const fStudio = $("#filter-studio");
  const fInstr = $("#filter-instructor");
  const clearBtn = $("#clear-filters");

  function matches(val, filterVal) {
    return !filterVal || val === filterVal;
  }

  function applyFilters() {
    const d = fDate.value;
    const s = fStudio.value;
    const i = fInstr.value;

    // Filter class rows
    const rows = $$(".class-row");
    rows.forEach(row => {
      const ok = matches(row.dataset.date, d)
             && matches(row.dataset.studio, s)
             && matches(row.dataset.instructor, i);
      row.classList.toggle("hidden", !ok);
    });

    // Recompute studio visibility and counts
    const studios = $$(".studio-section");
    studios.forEach(st => {
      const visibleRows = $$(".class-row:not(.hidden)", st);
      st.classList.toggle("hidden", visibleRows.length === 0);
      const badge = $("[data-count]", st);
      if (badge) badge.textContent = `(${visibleRows.length})`;
    });

    // Recompute date visibility
    const dates = $$(".date-section");
    dates.forEach(ds => {
      const visibleStudios = $$(".studio-section:not(.hidden)", ds);
      ds.classList.toggle("hidden", visibleStudios.length === 0);
    });
  }

  // Wire up events
  [fDate, fStudio, fInstr].forEach(el => el.addEventListener("change", applyFilters));
  clearBtn.addEventListener("click", () => {
    fDate.value = ""; fStudio.value = ""; fInstr.value = "";
    applyFilters();
  });

  // Initial
  applyFilters();
})();
</script>
"""

    parts.append(script)
    parts.append("</body></html>")

    Path(filename).write_text("".join(parts), encoding="utf-8")
    return filename
