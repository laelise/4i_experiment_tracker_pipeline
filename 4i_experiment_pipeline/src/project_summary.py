"""
project_summary.py
------------------
show_summary()              — static HTML plate (persists in notebook on reopen)
show_interactive_summary()  — unified clickable plate + 4i image viewer in one cell
                              clicking a well opens its images inline below the plate
"""

import html
import os
import sys
import ipywidgets as widgets
from IPython.display import display, HTML

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from project_config import load_config

_WELL_SZ = 88
_MARGIN  = 3
_BORDER  = 2
_SLOT    = _WELL_SZ + _MARGIN * 2 + _BORDER * 2   # 98 px
_ROW_LBL = 32


# ══════════════════════════════════════════════════════════════════════════════
# Static HTML summary (show_summary)
# ══════════════════════════════════════════════════════════════════════════════

def _make_html(cfg):
    wells_sel = set(cfg.get('well_list', []))
    meta      = cfg.get('well_metadata', {})

    col_hdrs = (
        f'<div style="display:flex;margin-left:{_ROW_LBL}px;margin-bottom:2px;">'
        + ''.join(
            f'<div style="width:{_SLOT}px;text-align:center;color:#6a9ab0;'
            f'font-size:10px;font-weight:bold;">{c}</div>'
            for c in range(1, 13)
        )
        + '</div>'
    )

    _txt_style = ('line-height:1.25;overflow:hidden;text-overflow:ellipsis;'
                  'white-space:nowrap;')
    plate_html = ''
    for r in 'ABCDEFGH':
        plate_html += (
            f'<div style="display:flex;align-items:center;">'
            f'<div style="width:{_ROW_LBL}px;text-align:center;color:#6a9ab0;'
            f'font-weight:bold;font-size:12px;">{r}</div>'
        )
        for c in range(1, 13):
            well = f'{r}{c:02d}'
            m    = meta.get(well, {})
            sel  = well in wells_sel

            if sel:
                bg, border_col = '#1a7abf', '#4ab0ef'
                shadow = '0 0 8px #1a7abf66'
                dose_e = html.escape(m.get('dose', ''))
                trt_e  = html.escape(m.get('treatment', ''))
                sid_e  = html.escape(m.get('sample_ID', ''))
                inner = (
                    f'<div style="font-size:10px;font-weight:bold;'
                    f'color:#fff;line-height:1.3;">{well}</div>'
                )
                if dose_e:
                    inner += (f'<div style="font-size:9px;color:#c8e6f5;'
                               f'max-width:76px;{_txt_style}">{dose_e}</div>')
                if trt_e:
                    inner += (f'<div style="font-size:9px;color:#c8e6f5;'
                               f'max-width:76px;{_txt_style}">{trt_e}</div>')
                if sid_e:
                    inner += (f'<div style="font-size:8px;color:#a0c8e0;'
                               f'max-width:70px;{_txt_style}">{sid_e}</div>')
                clip = (
                    f'<div style="position:absolute;inset:0;border-radius:50%;'
                    f'overflow:hidden;display:flex;flex-direction:column;'
                    f'align-items:center;justify-content:center;text-align:center;'
                    f'padding:5px;box-sizing:border-box;gap:1px;">'
                    f'{inner}</div>'
                )
                tt_lines = [x for x in [dose_e, trt_e, sid_e] if x]
                tooltip  = (
                    f'<div class="wp-tt">' + '<br>'.join(tt_lines) + '</div>'
                ) if tt_lines else ''
                plate_html += (
                    f'<div class="wp-sw" style="position:relative;'
                    f'width:{_WELL_SZ}px;height:{_WELL_SZ}px;border-radius:50%;'
                    f'background:{bg};border:{_BORDER}px solid {border_col};'
                    f'margin:{_MARGIN}px;box-shadow:{shadow};'
                    f'flex:0 0 {_WELL_SZ}px;box-sizing:content-box;">'
                    f'{clip}{tooltip}</div>'
                )
            else:
                bg, border_col = '#1e3a4a', '#2a5a74'
                plate_html += (
                    f'<div style="width:{_WELL_SZ}px;height:{_WELL_SZ}px;'
                    f'border-radius:50%;background:{bg};'
                    f'border:{_BORDER}px solid {border_col};margin:{_MARGIN}px;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'font-size:9px;color:#5a8aa0;'
                    f'flex:0 0 {_WELL_SZ}px;box-sizing:content-box;">'
                    f'{well}</div>'
                )
        plate_html += '</div>'

    def _row(label, value):
        if not value:
            return ''
        return (
            f'<tr><td style="color:#6a9ab0;width:130px;padding:2px 0;'
            f'vertical-align:top;">{label}</td>'
            f'<td style="color:#a8d8f0;padding:2px 0;">{html.escape(value)}</td></tr>'
        )

    info = f'''
    <div style="font-size:17px;font-weight:bold;color:#cdd6f4;margin-bottom:10px;">
        {html.escape(cfg.get("experiment_name", "(no name)"))}
    </div>
    <table style="border-collapse:collapse;font-size:12px;margin-bottom:16px;">
        {_row("Base directory",  cfg.get("base_dir", ""))}
        {_row("Date completed",  cfg.get("date_completed", ""))}
        {_row("Cell type",       cfg.get("cell_type", ""))}
        {_row("Passage",         cfg.get("passage", ""))}
        {_row("Notes",           cfg.get("notes", ""))}
    </table>'''

    wells_sorted = sorted(wells_sel)
    meta_rows = ''.join(
        f'<tr>'
        f'<td style="padding:3px 16px;color:#cdd6f4;">{w}</td>'
        f'<td style="padding:3px 16px;color:#a8d8f0;">'
        f'{html.escape(meta.get(w,{}).get("dose",""))}</td>'
        f'<td style="padding:3px 16px;color:#a8d8f0;">'
        f'{html.escape(meta.get(w,{}).get("treatment",""))}</td>'
        f'<td style="padding:3px 16px;color:#a8d8f0;">'
        f'{html.escape(meta.get(w,{}).get("sample_ID",""))}</td>'
        f'</tr>'
        for w in wells_sorted
    )
    th = 'padding:4px 16px;color:#6a9ab0;text-align:left;font-weight:normal;border-bottom:1px solid #2a3a4a;'
    meta_table = f'''
    <div style="color:#6a9ab0;font-size:11px;margin:14px 0 6px;">
        {len(wells_sorted)} wells selected
    </div>
    <table style="border-collapse:collapse;font-size:11px;">
        <tr>
            <th style="{th}">Well</th>
            <th style="{th}">Dose</th>
            <th style="{th}">Treatment</th>
            <th style="{th}">Sample ID</th>
        </tr>
        {meta_rows}
    </table>'''

    css = '''<style>
.wp-tt {
    display: none;
    position: absolute;
    bottom: 115%;
    left: 50%;
    transform: translateX(-50%);
    background: #0a1628;
    color: #a8d8f0;
    padding: 5px 9px;
    border-radius: 6px;
    font-size: 10px;
    white-space: nowrap;
    z-index: 99;
    border: 1px solid #2a5a74;
    line-height: 1.6;
    pointer-events: none;
}
.wp-sw:hover .wp-tt { display: block; }
</style>'''

    return f'''{css}
<div style="overflow-x:auto;">
<div style="background:#111827;padding:20px 24px 24px;border-radius:12px;
            display:inline-block;min-width:max-content;">
    {info}
    <div style="color:#6a9ab0;font-size:11px;font-weight:bold;margin-bottom:6px;">
        96-Well Plate
    </div>
    {col_hdrs}
    {plate_html}
    {meta_table}
</div>
</div>'''


def show_summary():
    """
    Render and display a persistent HTML visual summary of the saved config.
    Run this cell after saving config, then save the notebook (Ctrl+S) —
    the visual will appear automatically next time the notebook is opened.
    """
    try:
        cfg = load_config()
        display(HTML(_make_html(cfg)))
    except FileNotFoundError:
        display(HTML(
            '<div style="color:#ff6b6b;font-size:13px;padding:12px;">'
            'No config saved yet — fill in the form below and click Save Config, '
            'then run this cell again.</div>'
        ))


# ══════════════════════════════════════════════════════════════════════════════
# Unified interactive summary + image viewer (show_interactive_summary)
# ══════════════════════════════════════════════════════════════════════════════

_BTN_W = '88px'
_BTN_H = '88px'
_BTN_M = '2px'
_LBL_W = '34px'


def show_interactive_summary(config=None):
    """
    Show the experiment summary plate where each selected well is a clickable
    button. Clicking a well opens its 4i image viewer inline below the plate.

    This replaces running show_summary() + show_plate_viewer() separately.

    Parameters
    ----------
    config : dict, optional
        Loaded config dict. If None, loads the active project_config.json.

    Usage
    -----
    from project_summary import show_interactive_summary
    show_interactive_summary()
    """
    from well_image_viewer import WellImageViewer

    try:
        cfg = config or load_config()
    except FileNotFoundError:
        display(widgets.HTML(
            value='<div style="color:#ff6b6b;font-size:13px;padding:12px;">'
                  'No config found — run the experiment setup notebook first.</div>'
        ))
        return

    well_list = cfg.get('well_list', [])
    base_dir  = cfg.get('base_dir', '')
    meta      = cfg.get('well_metadata', {})
    wells_sel = set(well_list)

    # ── CSS ───────────────────────────────────────────────────────────────────
    css = widgets.HTML(value="""<style>
.ips-well button {
    border-radius: 50% !important;
    width: 100% !important;
    height: 100% !important;
    font-size: 8px !important;
    line-height: 1.3 !important;
    padding: 2px !important;
    white-space: pre-line !important;
    word-break: break-word !important;
}
.ips-container {
    background: #111827 !important;
    border-radius: 12px !important;
    padding: 20px 24px 24px !important;
    display: inline-flex !important;
    flex-direction: column !important;
}
</style>""")

    # ── Experiment info (static HTML) ─────────────────────────────────────────
    def _esc(v):
        return html.escape(str(v)) if v else ''

    info_parts = [
        f'<div style="font-size:17px;font-weight:bold;color:#cdd6f4;margin-bottom:8px;">'
        f'{_esc(cfg.get("experiment_name","(no name)"))}</div>',
    ]
    for label, key in [("Base dir", "base_dir"), ("Date", "date_completed"),
                       ("Cell type", "cell_type"), ("Passage", "passage")]:
        val = cfg.get(key, '')
        if val:
            info_parts.append(
                f'<div style="font-size:11px;color:#6a9ab0;margin-bottom:2px;">'
                f'<span style="color:#5a8aa0;">{label}:</span> '
                f'<span style="color:#a8d8f0;">{_esc(val)}</span></div>'
            )
    if cfg.get('notes'):
        info_parts.append(
            f'<div style="font-size:11px;color:#6a9ab0;margin-bottom:2px;">'
            f'<span style="color:#5a8aa0;">Notes:</span> '
            f'<span style="color:#a8d8f0;">{_esc(cfg.get("notes",""))}</span></div>'
        )

    click_hint = (
        '<div style="font-size:11px;color:#4ab0ef;margin:10px 0 4px;">'
        '&#9432; Click a selected well (blue) to open its 4i images below</div>'
    )
    info_html = widgets.HTML(value=''.join(info_parts) + click_hint)

    # ── Column headers ────────────────────────────────────────────────────────
    spacer   = widgets.HTML(value='', layout=widgets.Layout(width=_LBL_W))
    col_hdrs = [spacer] + [
        widgets.HTML(
            value=f'<div style="text-align:center;color:#6a9ab0;font-size:10px;'
                  f'font-weight:bold;">{c}</div>',
            layout=widgets.Layout(width=_BTN_W, margin=_BTN_M),
        )
        for c in range(1, 13)
    ]
    header_row = widgets.HBox(col_hdrs, layout=widgets.Layout(margin='0 0 2px 0'))

    # ── Plate rows ────────────────────────────────────────────────────────────
    selected_label = widgets.HTML(
        value='<div style="color:#5a8aa0;font-size:12px;margin-top:8px;">No well selected — click a blue well</div>'
    )
    viewer_output  = widgets.Output()
    current_well   = {'value': None}
    btns           = {}

    def _btn_desc(well):
        m = meta.get(well, {})
        parts = [well]
        dose = m.get('dose', '')
        trt  = m.get('treatment', '')
        if dose:
            parts.append(dose[:12])
        if trt:
            parts.append(trt[:12])
        return '\n'.join(parts)

    plate_rows = []
    for r in 'ABCDEFGH':
        row_lbl = widgets.HTML(
            value=f'<div style="text-align:center;color:#6a9ab0;font-weight:bold;'
                  f'font-size:12px;display:flex;align-items:center;'
                  f'justify-content:center;height:{_BTN_H};">{r}</div>',
            layout=widgets.Layout(width=_LBL_W),
        )
        row_items = [row_lbl]
        for c in range(1, 13):
            well = f'{r}{c:02d}'
            sel  = well in wells_sel

            if sel:
                btn = widgets.Button(
                    description=_btn_desc(well),
                    tooltip='\n'.join(
                        f'{k}: {v}' for k, v in meta.get(well, {}).items() if v
                    ),
                    layout=widgets.Layout(width=_BTN_W, height=_BTN_H, margin=_BTN_M),
                    style=widgets.ButtonStyle(button_color='#1a7abf', font_color='#ffffff'),
                )
                btn.add_class('ips-well')
            else:
                btn = widgets.Button(
                    description=well,
                    disabled=True,
                    layout=widgets.Layout(width=_BTN_W, height=_BTN_H, margin=_BTN_M),
                    style=widgets.ButtonStyle(button_color='#1e3a4a', font_color='#2a3a4a'),
                )
                btn.add_class('ips-well')

            btns[well] = btn

            if sel:
                def _make_cb(w, b):
                    def _cb(_):
                        prev = current_well['value']
                        # Deselect previous
                        if prev and prev in btns:
                            btns[prev].style.button_color = '#1a7abf'
                            btns[prev].style.font_color   = '#ffffff'
                        # Toggle off if same well
                        if current_well['value'] == w:
                            current_well['value'] = None
                            selected_label.value = (
                                '<div style="color:#5a8aa0;font-size:12px;margin-top:8px;">'
                                'No well selected — click a blue well</div>'
                            )
                            viewer_output.clear_output()
                            return
                        # Select new well
                        current_well['value'] = w
                        b.style.button_color = '#4ab0ef'
                        b.style.font_color   = '#000000'
                        m_info = meta.get(w, {})
                        dose_str = m_info.get('dose', '')
                        trt_str  = m_info.get('treatment', '')
                        extra = ' '.join(x for x in [dose_str, trt_str] if x)
                        selected_label.value = (
                            f'<div style="color:#a8d8f0;font-size:13px;font-weight:bold;'
                            f'margin-top:8px;">Viewing: '
                            f'<span style="color:#4ab0ef;">{w}</span>'
                            + (f' &nbsp;— {html.escape(extra)}' if extra else '')
                            + '</div>'
                        )
                        viewer_output.clear_output(wait=True)
                        with viewer_output:
                            WellImageViewer(well=w, base_dir=base_dir).show()
                    return _cb
                btn.on_click(_make_cb(well, btn))

            row_items.append(btn)
        plate_rows.append(widgets.HBox(row_items))

    # ── Well metadata table (static, below plate) ─────────────────────────────
    wells_sorted = sorted(wells_sel)
    th_s = 'padding:4px 14px;color:#6a9ab0;text-align:left;font-weight:normal;border-bottom:1px solid #2a3a4a;font-size:11px;'
    td_s = 'padding:3px 14px;font-size:11px;'
    meta_rows_html = ''.join(
        f'<tr>'
        f'<td style="{td_s}color:#cdd6f4;">{w}</td>'
        f'<td style="{td_s}color:#a8d8f0;">{html.escape(meta.get(w,{}).get("dose",""))}</td>'
        f'<td style="{td_s}color:#a8d8f0;">{html.escape(meta.get(w,{}).get("treatment",""))}</td>'
        f'<td style="{td_s}color:#a8d8f0;">{html.escape(meta.get(w,{}).get("sample_ID",""))}</td>'
        f'</tr>'
        for w in wells_sorted
    )
    meta_table_html = widgets.HTML(value=f'''
<div style="color:#6a9ab0;font-size:11px;margin:12px 0 4px;">{len(wells_sorted)} wells selected</div>
<table style="border-collapse:collapse;">
  <tr>
    <th style="{th_s}">Well</th>
    <th style="{th_s}">Dose</th>
    <th style="{th_s}">Treatment</th>
    <th style="{th_s}">Sample ID</th>
  </tr>
  {meta_rows_html}
</table>''')

    # ── Assemble ──────────────────────────────────────────────────────────────
    plate_title = widgets.HTML(
        value='<div style="color:#6a9ab0;font-size:11px;font-weight:bold;margin-bottom:4px;">'
              '96-Well Plate</div>'
    )
    plate_widget = widgets.VBox(
        [css, info_html, plate_title, header_row] + plate_rows + [meta_table_html],
        layout=widgets.Layout(padding='20px 24px 24px', border_radius='12px'),
    )
    plate_widget.add_class('ips-container')

    display(plate_widget)
    display(selected_label)
    display(viewer_output)
