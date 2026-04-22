"""
project_config.py
-----------------
Step 1: run show_well_plate_selector() (from well_plate_selector.py) to pick wells,
        then click Generate Code and copy the  well_list = [...]  line into the next cell.
Step 2: run show_save_form(well_list) to fill in experiment details and save.

In any downstream notebook:

    from project_config import load_config
    config    = load_config()
    base_dir  = config['base_dir']
    well_list = config['well_list']
    meta      = config['well_metadata']   # dict: well -> {dose, treatment, sample_ID}

    full_dir  = os.path.join(base_dir, 'cell_data')
    img_dir   = os.path.join(base_dir, 'output_images')
"""

import json
import os
import uuid
import ipywidgets as widgets
from IPython.display import display, Javascript

_ROOT                  = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CONFIG_FILE            = os.path.join(_ROOT, 'project_config.json')
EXPERIMENT_CONFIGS_DIR = os.path.join(_ROOT, '00_experiment_setup', 'experiment_configs')


def load_config(config_path=None):
    """Load and return the active project config dict."""
    path = config_path or CONFIG_FILE
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_experiment_config(experiment_key):
    """Load a named experiment config from 00_experiment_setup/experiment_configs/{key}.json."""
    path = os.path.join(EXPERIMENT_CONFIGS_DIR, f'{experiment_key}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(config, config_path=None):
    path = config_path or CONFIG_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def show_save_form(well_list, experiment_key=None):
    """
    Fill in experiment details and per-well metadata, then click Save Config.
    Pass the well_list you got from the well plate selector Generate Code button.

    Parameters
    ----------
    well_list : list
        Well names selected on the plate, e.g. ['D02', 'D03', ...].
    experiment_key : str, optional
        Short slug for this experiment (e.g. 'LPS863_Abema_July2025').
        Pre-populates the Experiment Key field and is used to save a named
        config to 00_experiment_setup/experiment_configs/{key}.json in addition
        to the shared project_config.json.

    Keyboard shortcuts in the per-well table:
      Enter / Arrow Down  — move to the same field in the next well
      Arrow Up            — move to the same field in the previous well

    Click  ↓ Fill  in a column header to copy the first non-empty value
    in that column down to all empty wells below it.
    """
    if not well_list:
        display(widgets.HTML(
            '<div style="color:#ff6b6b;font-size:13px;">'
            'well_list is empty — select wells in the plate above first, '
            'click Generate Code, and paste the well_list line into the cell above this one.</div>'
        ))
        return

    # Try to load existing config for this key (or fall back to the shared config)
    _existing = {}
    try:
        if experiment_key:
            _existing = load_experiment_config(experiment_key)
        else:
            _existing = load_config()
    except Exception:
        try:
            _existing = load_config()
        except Exception:
            pass

    # ── CSS ───────────────────────────────────────────────────────────────────
    css = widgets.HTML(value="""<style>
.wpc-section {
    background: #111827 !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    margin-bottom: 10px !important;
}
</style>""")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _lbl(text, width='140px'):
        return widgets.HTML(
            f'<div style="color:#6a9ab0;font-size:12px;width:{width};'
            f'display:flex;align-items:center;">{text}</div>'
        )

    def _row(label, widget, lbl_width='140px'):
        return widgets.HBox(
            [_lbl(label, lbl_width), widget],
            layout=widgets.Layout(margin='4px 0'),
        )

    def _section_title(text):
        return widgets.HTML(
            f'<div style="font-size:14px;font-weight:bold;color:#cdd6f4;'
            f'margin-bottom:10px;">{text}</div>'
        )

    # ── Section 1: experiment info ─────────────────────────────────────────────
    exp_key_val = experiment_key or _existing.get('experiment_key', '')
    exp_key_w = widgets.Text(
        value=exp_key_val,
        placeholder='e.g. LPS863_Abema_July2025  (no spaces, used as file name)',
        layout=widgets.Layout(width='400px'),
    )
    exp_name  = widgets.Text(value=_existing.get('experiment_name', ''),  placeholder='e.g. LPS863 Abema July 2025',       layout=widgets.Layout(width='400px'))
    base_dir  = widgets.Text(value=_existing.get('base_dir', ''),         placeholder=r'e.g. Z:\Lauryn\Liposarcoma\...',   layout=widgets.Layout(width='600px'))
    date_done = widgets.Text(value=_existing.get('date_completed', ''),   placeholder='e.g. 2025-07-15',                   layout=widgets.Layout(width='200px'))
    cell_type = widgets.Text(value=_existing.get('cell_type', ''),        placeholder='e.g. LPS863 liposarcoma',           layout=widgets.Layout(width='340px'))
    passage   = widgets.Text(value=_existing.get('passage', ''),          placeholder='e.g. P5',                           layout=widgets.Layout(width='150px'))
    notes     = widgets.Textarea(value=_existing.get('notes', ''),        placeholder='Any additional experiment notes...', layout=widgets.Layout(width='600px', height='70px'))

    info_sec = widgets.VBox([
        _section_title('Experiment Info'),
        _row('Experiment key:',   exp_key_w),
        widgets.HTML(
            '<div style="color:#5a8aa0;font-size:10px;margin:-2px 0 8px 140px;">'
            'Short slug used as the config file name — no spaces (use underscores).</div>'
        ),
        _row('Experiment name:',  exp_name),
        _row('Base directory:',   base_dir),
        _row('Date completed:',   date_done),
        _row('Cell type:',        cell_type),
        _row('Passage:',          passage),
        _row('Notes:',            notes),
    ], layout=widgets.Layout(padding='16px 20px', margin='0 0 10px 0'))
    info_sec.add_class('wpc-section')

    # ── Section 2: per-well metadata ───────────────────────────────────────────
    _prev        = _existing.get('well_metadata', {})
    meta_fields  = {}
    sorted_wells = sorted(well_list)
    dose_ws, trt_ws, sid_ws = [], [], []

    for w in sorted_wells:
        prev   = _prev.get(w, {})
        dose_w = widgets.Text(value=prev.get('dose', ''),      placeholder='e.g. 100nM',         layout=widgets.Layout(width='158px'))
        trt_w  = widgets.Text(value=prev.get('treatment', ''), placeholder='e.g. Abemaciclib',    layout=widgets.Layout(width='158px'))
        sid_w  = widgets.Text(value=prev.get('sample_ID', ''), placeholder=f'e.g. LPS863_{w}',   layout=widgets.Layout(width='205px'))
        meta_fields[w] = {'dose': dose_w, 'treatment': trt_w, 'sample_ID': sid_w}
        dose_ws.append(dose_w)
        trt_ws.append(trt_w)
        sid_ws.append(sid_w)

    # Fill-down buttons — copies first non-empty value to all empty cells below
    def _fill_btn(col_ws, width):
        btn = widgets.Button(
            description='↓ Fill',
            tooltip='Copy first non-empty value down to all empty wells',
            style=widgets.ButtonStyle(button_color='#1a5c8c', font_color='#ffffff'),
            layout=widgets.Layout(width=width, height='22px'),
        )
        def _on_click(_):
            first = next((w.value for w in col_ws if w.value.strip()), None)
            if first:
                for w in col_ws:
                    if not w.value.strip():
                        w.value = first
        btn.on_click(_on_click)
        return btn

    _ch = 'color:#6a9ab0;font-size:11px;font-weight:bold;'
    hdr = widgets.HBox([
        widgets.HTML(f'<div style="width:58px;{_ch}">Well</div>'),
        widgets.VBox([
            widgets.HTML(f'<div style="width:158px;{_ch}">Dose</div>'),
            _fill_btn(dose_ws, '158px'),
        ], layout=widgets.Layout(width='162px', margin='0 4px 0 0')),
        widgets.VBox([
            widgets.HTML(f'<div style="width:158px;{_ch}">Treatment</div>'),
            _fill_btn(trt_ws, '158px'),
        ], layout=widgets.Layout(width='162px', margin='0 4px 0 0')),
        widgets.VBox([
            widgets.HTML(f'<div style="width:205px;{_ch}">Sample ID</div>'),
            _fill_btn(sid_ws, '205px'),
        ], layout=widgets.Layout(width='209px')),
    ], layout=widgets.Layout(margin='0 0 8px 0'))

    well_rows = [hdr]
    for w in sorted_wells:
        lbl = widgets.HTML(
            f'<div style="width:58px;color:#cdd6f4;font-size:12px;'
            f'display:flex;align-items:center;">{w}</div>'
        )
        well_rows.append(widgets.HBox(
            [lbl, meta_fields[w]['dose'], meta_fields[w]['treatment'], meta_fields[w]['sample_ID']],
            layout=widgets.Layout(margin='2px 0'),
        ))

    meta_cls = f'wpc-meta-{uuid.uuid4().hex[:8]}'
    hint = widgets.HTML(
        '<div style="color:#5a8aa0;font-size:11px;margin:-4px 0 10px;">'
        '&#8595; Fill copies the first value down to empty wells.&nbsp;&nbsp;'
        'Enter&nbsp;/&nbsp;&#8595;&nbsp;/&nbsp;&#8593; navigate rows within a column.</div>'
    )
    # Inline script runs when the HTML widget is inserted into the DOM.
    # document.currentScript lets us locate the container without waiting for
    # the CSS class to propagate — more reliable in VS Code's webview.
    _nav_html = widgets.HTML(f'''<script>
(function(){{
  var COLS=3, sc=document.currentScript, tries=0;
  function find(){{
    var el=sc?sc.parentElement:null;
    while(el){{
      var ins=el.querySelectorAll('input[type="text"]');
      if(ins.length>=COLS)return el;
      el=el.parentElement;
    }}
    return document.querySelector('.{meta_cls}');
  }}
  function go(){{
    var s=find();
    if(!s&&++tries<40){{setTimeout(go,250);return;}}
    if(!s||s.dataset.wpcNav)return;
    s.dataset.wpcNav='1';
    s.addEventListener('keydown',function(e){{
      if(e.key!=='Enter'&&e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;
      var a=Array.from(s.querySelectorAll('input[type="text"]'));
      var i=a.indexOf(document.activeElement);
      if(i<0)return;
      e.preventDefault();
      var t=(e.key==='ArrowUp')?a[i-COLS]:a[i+COLS];
      if(t){{t.focus();t.select();}}
    }});
  }}
  go();
}})();
</script>''')
    meta_sec = widgets.VBox([
        _section_title('Per-Well Metadata'),
        hint,
        _nav_html,
        widgets.VBox(well_rows),
    ], layout=widgets.Layout(padding='16px 20px', margin='0 0 10px 0'))
    meta_sec.add_class('wpc-section')
    meta_sec.add_class(meta_cls)

    # ── Section 3: save ────────────────────────────────────────────────────────
    save_status = widgets.HTML(value='')

    def _save_config(_):
        if not base_dir.value.strip():
            save_status.value = '<div style="color:#ff6b6b;">Base directory is required.</div>'
            return
        key = exp_key_w.value.strip()
        config = {
            'experiment_key':  key,
            'experiment_name': exp_name.value.strip(),
            'base_dir':        base_dir.value.strip(),
            'date_completed':  date_done.value.strip(),
            'cell_type':       cell_type.value.strip(),
            'passage':         passage.value.strip(),
            'notes':           notes.value.strip(),
            'well_list':       sorted(well_list),
            'well_metadata': {
                w: {k: v.value for k, v in fields.items()}
                for w, fields in meta_fields.items()
            },
        }
        # Always write to the shared active config
        _save(config)
        # Also write to the named experiment config if a key is provided
        saved_named = False
        if key:
            named_path = os.path.join(EXPERIMENT_CONFIGS_DIR, f'{key}.json')
            _save(config, named_path)
            saved_named = True

        named_note = (f'&nbsp;|&nbsp; also saved to experiment_configs/{key}.json'
                      if saved_named else '')
        save_status.value = (
            f'<div style="color:#a8d8f0;font-size:12px;">'
            f'Saved — {len(well_list)} wells &nbsp;|&nbsp; {base_dir.value.strip()}'
            f'{named_note}</div>'
        )

    save_btn = widgets.Button(
        description='Save Config',
        style=widgets.ButtonStyle(button_color='#1a7abf', font_color='#ffffff'),
        layout=widgets.Layout(margin='0 8px 0 0'),
    )
    save_btn.on_click(_save_config)

    save_sec = widgets.VBox(
        [_section_title('Save'), save_btn, save_status],
        layout=widgets.Layout(padding='16px 20px'),
    )
    save_sec.add_class('wpc-section')

    display(widgets.VBox([css, info_sec, meta_sec, save_sec]))

    # Fallback: display(Javascript) for environments where the inline <script>
    # tag above is stripped by the renderer's content-security policy.
    display(Javascript(f"""
(function(){{
  var COLS=3,cls='{meta_cls}',tries=0;
  function go(){{
    var s=document.querySelector('.'+cls);
    if(!s&&++tries<40){{setTimeout(go,250);return;}}
    if(!s||s.dataset.wpcNav)return;
    s.dataset.wpcNav='1';
    s.addEventListener('keydown',function(e){{
      if(e.key!=='Enter'&&e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;
      var a=Array.from(s.querySelectorAll('input[type="text"]'));
      var i=a.indexOf(document.activeElement);
      if(i<0)return;
      e.preventDefault();
      var t=(e.key==='ArrowUp')?a[i-COLS]:a[i+COLS];
      if(t){{t.focus();t.select();}}
    }});
  }}
  go();
}})();
"""))
