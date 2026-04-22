import random
import ipywidgets as widgets
from IPython.display import display, HTML

WELL_SZ = 42
MARGIN  = 2
BORDER  = 2
SLOT    = WELL_SZ + MARGIN * 2 + BORDER * 2  # 50 px — wells consume width + border + margin
ROW_LBL = 32                                  # px for the row-letter label on the left


def show_well_plate_selector():
    """
    Interactive 96-well plate. Click wells to select/deselect, then click
    Generate Code for a ready-to-fill data loading template.
    """
    pid = 'p{}'.format(random.randint(10000, 99999))

    # ── column headers ────────────────────────────────────────────────────────
    col_headers = (
        '<div style="display:flex;margin-left:{lbl}px;margin-bottom:4px;">'.format(lbl=ROW_LBL)
        + ''.join(
            '<div style="width:{slot}px;flex:0 0 {slot}px;text-align:center;color:#6a9ab0;'
            'font-size:11px;font-weight:bold;box-sizing:border-box;">{c}</div>'.format(slot=SLOT, c=c)
            for c in range(1, 13)
        )
        + '</div>'
    )

    # ── plate rows ────────────────────────────────────────────────────────────
    rows_html = ''
    for r in 'ABCDEFGH':
        rows_html += (
            '<div style="display:flex;align-items:center;">'
            '<div style="width:{lbl}px;flex:0 0 {lbl}px;text-align:center;color:#6a9ab0;'
            'font-weight:bold;font-size:13px;">{r}</div>'.format(lbl=ROW_LBL, r=r)
        )
        for c in range(1, 13):
            well = '{}{:02d}'.format(r, c)
            rows_html += (
                '<div class="w-{pid}" data-well="{well}" '
                'style="width:{ws}px;height:{ws}px;border-radius:50%;'
                'background:#1e3a4a;border:2px solid #2a5a74;margin:{m}px;'
                'cursor:pointer;display:flex;align-items:center;flex:0 0 {ws}px;'
                'justify-content:center;font-size:8px;color:#5a8aa0;'
                'user-select:none;transition:background 0.1s,border-color 0.1s,'
                'box-shadow 0.1s;box-sizing:content-box;">{well}</div>'
            ).format(pid=pid, well=well, ws=WELL_SZ, m=MARGIN)
        rows_html += '</div>'

    # ── JavaScript — placed after HTML so DOM is already present ──────────────
    js = '''
<script>
(function() {
  var sel = new Set();
  var plate = document.getElementById("plate_PID");
  if (!plate) return;

  plate.addEventListener("click", function(e) {
    var el = e.target;
    while (el && el !== plate && !el.classList.contains("w-PID")) {
      el = el.parentElement;
    }
    if (!el || el === plate) return;
    var w = el.dataset.well;
    if (sel.has(w)) {
      sel.delete(w);
      el.style.background  = "#1e3a4a";
      el.style.borderColor = "#2a5a74";
      el.style.color       = "#5a8aa0";
      el.style.boxShadow   = "none";
    } else {
      sel.add(w);
      el.style.background  = "#1a7abf";
      el.style.borderColor = "#4ab0ef";
      el.style.color       = "#ffffff";
      el.style.boxShadow   = "0 0 10px #1a7abf";
    }
  });

  document.getElementById("gen_PID").addEventListener("click", function() {
    var wells = Array.from(sel).sort();
    var out   = document.getElementById("out_PID");
    if (!wells.length) { out.value = "# No wells selected."; return; }
    var L = [];
    L.push("well_list = " + JSON.stringify(wells));
    L.push("");
    L.push("fullest_df = pd.DataFrame()");
    L.push("for well in well_list:");
    L.push("    print(f'starting Well {well}')");
    L.push("    full_df = pd.read_csv(os.path.join(full_dir, f'cell_data_{well}_df.csv'), sep=',')");
    L.push("");
    wells.forEach(function(w) {
      var r = w[0], c = w.slice(1);
      L.push("    if '" + r + "' in well and ('" + c + "' in well):");
      L.push("        full_df['dose'] = ''");
      L.push("        full_df['treatment'] = ''");
      L.push("        full_df['sample_ID'] = ");
      L.push("");
    });
    L.push("    exec(f'well{well}_df = full_df.copy()')");
    L.push("    fullest_df = pd.concat([fullest_df, full_df], ignore_index=True)");
    L.push("    print(len(full_df))");
    L.push("    print(len(fullest_df))");
    L.push("");
    L.push("fullest_df['sample_ID'] = fullest_df['sample_ID'].astype('category')");
    L.push("fullest_df['dose']      = fullest_df['dose'].astype(str)");
    L.push("fullest_df['treatment'] = fullest_df['treatment'].astype(str)");
    out.value = L.join("\\n");
  });

  document.getElementById("clr_PID").addEventListener("click", function() {
    sel.clear();
    document.querySelectorAll(".w-PID").forEach(function(el) {
      el.style.background  = "#1e3a4a";
      el.style.borderColor = "#2a5a74";
      el.style.color       = "#5a8aa0";
      el.style.boxShadow   = "none";
    });
    document.getElementById("out_PID").value =
      "Select wells above, then click Generate Code...";
  });
})();
</script>
'''.replace('PID', pid)

    out_width = ROW_LBL + 12 * SLOT

    html = (
        '<div id="plate_{pid}" style="background:#111827;padding:18px 22px 20px;'
        'border-radius:14px;display:inline-block;">'

        '<div style="font-size:15px;font-weight:bold;color:#cdd6f4;margin-bottom:10px;">'
        '96-Well Plate Selector</div>'

        '{col_headers}'
        '{rows_html}'

        '<div style="margin-top:14px;display:flex;gap:8px;">'
        '<button id="gen_{pid}" style="background:#1a7abf;color:#fff;border:none;'
        'padding:7px 18px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:bold;">'
        'Generate Code</button>'
        '<button id="clr_{pid}" style="background:#7a4010;color:#fff;border:none;'
        'padding:7px 14px;border-radius:6px;cursor:pointer;font-size:13px;">'
        'Clear All</button>'
        '</div>'

        '<div style="margin-top:6px;color:#3a5a6a;font-size:11px;">'
        'Copy the generated code into your data loading cell below &#8595;</div>'

        '<textarea id="out_{pid}" readonly '
        'style="width:{ow}px;height:280px;margin-top:6px;'
        'background:#0a0f1a;color:#a8d8f0;border:1px solid #1a3a4a;border-radius:8px;'
        'padding:10px;font-family:monospace;font-size:11px;resize:vertical;'
        'display:block;outline:none;">'
        'Select wells above, then click Generate Code...</textarea>'

        '</div>'
    ).format(pid=pid, col_headers=col_headers, rows_html=rows_html, ow=out_width)

    display(HTML(html + js))


# ── Single-well selector (for masking workflows) ───────────────────────────────

class SingleWellSelector:
    """
    96-well plate where only ONE well can be active at a time.
    Designed for masking workflows where you process one well per run.

    Parameters
    ----------
    selectable_wells : list or None
        If provided, only wells in this list are clickable; others are dimmed.
        Pass None to make all 96 wells selectable.
    masked_wells : set or list or None
        Wells that already have masks — shown in a distinct "done" style with ✓.
    on_select : callable or None
        Optional callback ``f(well_name)`` called each time a well is selected.
        If a well is de-selected (clicked again) it is called with None.

    Usage
    -----
    # Basic (masking workflow):
    selector = SingleWellSelector(selectable_wells=well_list,
                                  masked_wells=get_masked_wells(base_dir))
    selector.show()

    # In the next cell (run after clicking a well):
    well = selector.well          # e.g. 'D02'

    # With auto-callback (image viewer):
    selector = SingleWellSelector(selectable_wells=well_list,
                                  on_select=lambda w: viewer.load(w))
    selector.show()
    """

    _BTN_W = '46px'
    _BTN_H = '46px'
    _BTN_M = '2px'
    _LBL_W = '34px'

    def __init__(self, selectable_wells=None, masked_wells=None, on_select=None):
        self._well            = None
        self._btns            = {}
        self._label           = None
        self._selectable      = set(selectable_wells) if selectable_wells is not None else None
        self._masked          = set(masked_wells) if masked_wells else set()
        self._on_select       = on_select

    @property
    def well(self):
        """The currently selected well name, e.g. 'B02'. None if none selected."""
        return self._well

    def _default_btn_style(self, well):
        """Return (button_color, font_color, description) for an unselected well."""
        if well in self._masked:
            return '#1a3020', '#3a8a50', f'✓{well}'
        if self._selectable is not None and well not in self._selectable:
            return '#141c28', '#2a3a4a', well   # dimmed, not clickable
        return '#1e3a4a', '#5a8aa0', well

    def show(self):
        rows_letters = 'ABCDEFGH'
        cols         = range(1, 13)

        css = widgets.HTML(value="""<style>
.sws-well button {
    border-radius: 50% !important;
    font-size: 8px !important;
    line-height: 1 !important;
    padding: 0 !important;
}
.sws-container {
    background: #111827 !important;
    border-radius: 14px !important;
    padding: 18px 22px 20px !important;
    display: inline-flex !important;
    flex-direction: column !important;
}
</style>""")

        spacer   = widgets.HTML(value='', layout=widgets.Layout(width=self._LBL_W))
        col_hdrs = [spacer] + [
            widgets.HTML(
                value=f'<div style="text-align:center;color:#6a9ab0;font-size:11px;font-weight:bold;">{c}</div>',
                layout=widgets.Layout(width=self._BTN_W, margin=self._BTN_M),
            )
            for c in cols
        ]
        header_row = widgets.HBox(col_hdrs, layout=widgets.Layout(margin='0 0 4px 0'))

        plate_rows = []
        for r in rows_letters:
            row_lbl = widgets.HTML(
                value=f'<div style="text-align:center;color:#6a9ab0;font-weight:bold;font-size:13px;'
                      f'display:flex;align-items:center;justify-content:center;height:{self._BTN_H};">{r}</div>',
                layout=widgets.Layout(width=self._LBL_W),
            )
            row_items = [row_lbl]
            for c in cols:
                well      = f'{r}{c:02d}'
                bg, fg, desc = self._default_btn_style(well)
                is_clickable = (
                    self._selectable is None or well in self._selectable
                )

                btn = widgets.Button(
                    description=desc,
                    disabled=not is_clickable,
                    layout=widgets.Layout(width=self._BTN_W, height=self._BTN_H, margin=self._BTN_M),
                    style=widgets.ButtonStyle(button_color=bg, font_color=fg),
                )
                btn.add_class('sws-well')
                self._btns[well] = btn

                def _make_cb(w, b):
                    def _cb(_):
                        # Deselect previous
                        if self._well and self._well in self._btns:
                            prev = self._btns[self._well]
                            pbg, pfg, pdesc = self._default_btn_style(self._well)
                            prev.style.button_color = pbg
                            prev.style.font_color   = pfg
                            prev.description        = pdesc
                        # Select new (toggle off if same)
                        if self._well == w:
                            self._well = None
                            self._label.value = (
                                '<div style="color:#5a8aa0;font-size:13px;margin-top:10px;">'
                                'No well selected</div>'
                            )
                            if self._on_select:
                                self._on_select(None)
                        else:
                            self._well = w
                            b.style.button_color = '#1a7abf'
                            b.style.font_color   = '#ffffff'
                            b.description        = w
                            self._label.value = (
                                f'<div style="color:#a8d8f0;font-size:14px;font-weight:bold;margin-top:10px;">'
                                f'Selected: <span style="color:#4ab0ef;">{w}</span> '
                                f'&nbsp;— run the next cell to process this well</div>'
                            )
                            if self._on_select:
                                self._on_select(w)
                    return _cb

                if is_clickable:
                    btn.on_click(_make_cb(well, btn))
                row_items.append(btn)
            plate_rows.append(widgets.HBox(row_items))

        self._label = widgets.HTML(
            value='<div style="color:#5a8aa0;font-size:13px;margin-top:10px;">No well selected</div>'
        )

        # Build legend if masked or restricted wells exist
        legend_parts = []
        if self._masked:
            legend_parts.append(
                '<span style="color:#3a8a50;">&#10003; = mask complete</span>'
            )
        if self._selectable is not None:
            n_other = 96 - len(self._selectable)
            if n_other > 0:
                legend_parts.append(
                    '<span style="color:#2a3a4a;">dim = not in experiment</span>'
                )
        legend_html = (
            '<div style="font-size:10px;margin-top:6px;">'
            + ' &nbsp;|&nbsp; '.join(legend_parts)
            + '</div>'
        ) if legend_parts else ''

        title = widgets.HTML(
            value='<div style="font-size:15px;font-weight:bold;color:#cdd6f4;margin-bottom:10px;">'
                  'Single-Well Selector — click a well, then run the next cell</div>'
                  + legend_html
        )

        container = widgets.VBox(
            [css, title, header_row] + plate_rows + [self._label]
        )
        container.add_class('sws-container')
        display(container)
