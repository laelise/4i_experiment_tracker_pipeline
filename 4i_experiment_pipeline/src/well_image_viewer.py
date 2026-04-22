"""
well_image_viewer.py
--------------------
Interactive multi-layer 4i image viewer. No plotly or ipympl required.
Uses ipywidgets + PIL/Pillow (included in Anaconda).

Features
--------
- Round and channel selection per layer
- Colormap picker with true additive blending across layers
- Opacity and manual contrast controls (with Auto button)
- Zoom slider (1×–8×) + pan X/Y sliders when zoomed in

Usage
-----
from well_image_viewer import WellImageViewer
viewer = WellImageViewer(well='D02', base_dir=r'Z:\\...\\LPS_863_Abema_July_2025')
viewer.show()
"""

import io
import os
import re

import ipywidgets as widgets
import numpy as np
from IPython.display import display
from PIL import Image as PILImage
from tifffile import imread

# ── Color definitions: black → target color ───────────────────────────────────

_COLORS = {
    'Gray':    (255, 255, 255),
    'Cyan':    (0,   255, 255),
    'Magenta': (255,   0, 255),
    'Yellow':  (255, 255,   0),
    'Green':   (0,   255,   0),
    'Red':     (255,   0,   0),
    'Blue':    (0,   136, 255),
    'Orange':  (255, 136,   0),
}
_MPL_CMAPS   = ('Hot', 'Viridis', 'Plasma')
_ALL_COLORS  = list(_COLORS.keys()) + list(_MPL_CMAPS)

# ── File discovery ─────────────────────────────────────────────────────────────

_FNAME_RE = re.compile(r'Round_R(\d+)_well([A-H]\d{2})_(.+)\.tif$', re.IGNORECASE)


def _discover_rounds(tiff_dir):
    """Returns {'R0': {'CDK2': path, ...}, 'R1': {...}, ...} sorted by round."""
    rounds = {}
    try:
        for fname in sorted(os.listdir(tiff_dir)):
            m = _FNAME_RE.match(fname)
            if m:
                rlabel = f'R{m.group(1)}'
                rounds.setdefault(rlabel, {})[m.group(3)] = os.path.join(tiff_dir, fname)
    except FileNotFoundError:
        pass
    return dict(sorted(rounds.items(), key=lambda kv: int(kv[0][1:])))


# ── Image helpers ─────────────────────────────────────────────────────────────

def _load_image(path, max_pixels=1_048_576):
    """Load TIFF → 2D float32, downsampled so total pixels ≤ max_pixels."""
    im = imread(path)
    while im.ndim > 2:
        im = im[0]
    im = im.astype(np.float32)
    h, w = im.shape
    factor = max(1, int(np.ceil(np.sqrt(h * w / max_pixels))))
    if factor > 1:
        im = im[::factor, ::factor]
    return im


def _colorize(im, color_name, vmin, vmax):
    """2D float32 → RGBA uint8 using the chosen color."""
    normed = np.clip((im - vmin) / max(vmax - vmin, 1), 0, 1)
    if color_name in _COLORS:
        r, g, b = _COLORS[color_name]
        R = (normed * r).astype(np.uint8)
        G = (normed * g).astype(np.uint8)
        B = (normed * b).astype(np.uint8)
        A = np.full_like(R, 255)
        return np.stack([R, G, B, A], axis=-1)
    import matplotlib.cm as mcm
    return (mcm.get_cmap(color_name.lower())(normed) * 255).astype(np.uint8)


def _composite(rgbas, opacities):
    """Additively blend RGBA uint8 arrays with per-layer opacity."""
    if not rgbas:
        blank = np.zeros((64, 64, 4), dtype=np.uint8)
        blank[:, :, 3] = 255
        return blank
    acc = np.zeros((*rgbas[0].shape[:2], 3), dtype=np.float32)
    for rgba, alpha in zip(rgbas, opacities):
        acc += rgba[:, :, :3].astype(np.float32) / 255.0 * alpha
    rgb = (np.clip(acc, 0, 1) * 255).astype(np.uint8)
    a   = np.full((*rgb.shape[:2], 1), 255, dtype=np.uint8)
    return np.concatenate([rgb, a], axis=-1)


def _zoom_crop(rgba, zoom, pan_x, pan_y):
    """
    Crop rgba to show 1/zoom of the image, centred at (pan_x, pan_y) in [0,1].
    Returns the cropped region scaled back to the original size.
    """
    if zoom <= 1:
        return rgba
    h, w = rgba.shape[:2]
    ch, cw = max(1, h // zoom), max(1, w // zoom)
    cx = int(pan_x * (w - cw))
    cy = int(pan_y * (h - ch))
    cx = max(0, min(cx, w - cw))
    cy = max(0, min(cy, h - ch))
    crop = rgba[cy:cy + ch, cx:cx + cw]
    img  = PILImage.fromarray(crop, 'RGBA').resize((w, h), PILImage.NEAREST)
    return np.array(img)


def _to_png(rgba):
    buf = io.BytesIO()
    PILImage.fromarray(rgba, 'RGBA').save(buf, format='PNG')
    return buf.getvalue()


# ── Viewer class ──────────────────────────────────────────────────────────────

class WellImageViewer:
    """
    Parameters
    ----------
    well : str        Well name, e.g. 'D02'.
    base_dir : str    Root experiment directory (contains aligned_tiffs/).
    tiff_subdir : str Subfolder inside base_dir (default 'aligned_tiffs').
    """

    def __init__(self, well, base_dir, tiff_subdir='aligned_tiffs'):
        self.well    = well
        self.base_dir = base_dir
        self.tiff_dir = os.path.join(base_dir, tiff_subdir, well)
        self._rounds  = _discover_rounds(self.tiff_dir)

        self._layer_states = []
        self._layers_vbox  = widgets.VBox([])
        self._img_widget   = widgets.Image(
            value=b'', format='png',
            layout=widgets.Layout(
                max_width='100%', height='600px',
                object_fit='contain', border='1px solid #1e3a4a',
            ),
        )
        self._status   = widgets.HTML(value='')
        self._zoom_w   = None  # set in build()
        self._pan_x_w  = None
        self._pan_y_w  = None
        self._pan_box  = None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _rounds_list(self):
        return list(self._rounds.keys())

    def _channels_for(self, r):
        return list(self._rounds.get(r, {}).keys())

    def _render(self, *_):
        rgbas, opacities = [], []
        for state in self._layer_states:
            path = self._rounds.get(state['round_dd'].value, {}).get(state['chan_dd'].value)
            if path is None:
                continue
            try:
                im = _load_image(path)
            except Exception as e:
                self._status.value = f'<span style="color:#ff6b6b;">Load error: {e}</span>'
                continue
            try:
                vmin = float(state['cmin_w'].value)
                vmax = float(state['cmax_w'].value)
            except (ValueError, TypeError):
                vmin, vmax = 0.0, float(im.max())
            rgbas.append(_colorize(im, state['color_dd'].value, vmin, vmax))
            opacities.append(state['opacity_s'].value)

        if not rgbas:
            self._img_widget.value = b''
            return

        composite = _composite(rgbas, opacities)

        # Apply zoom / pan
        zoom  = int(self._zoom_w.value)  if self._zoom_w  else 1
        pan_x = self._pan_x_w.value      if self._pan_x_w else 0.5
        pan_y = self._pan_y_w.value      if self._pan_y_w else 0.5
        if zoom > 1:
            composite = _zoom_crop(composite, zoom, pan_x, pan_y)

        self._img_widget.value = _to_png(composite)
        self._status.value = (
            f'<span style="color:#6a9ab0;font-size:11px;">'
            f'{len(rgbas)} layer(s) &nbsp;|&nbsp; {self.well}'
            + (f' &nbsp;|&nbsp; {zoom}× zoom' if zoom > 1 else '')
            + '</span>'
        )

    def _auto_contrast(self, state):
        path = self._rounds.get(state['round_dd'].value, {}).get(state['chan_dd'].value)
        if path is None:
            return
        try:
            im = _load_image(path)
            state['cmin_w'].value = str(int(np.percentile(im, 1)))
            state['cmax_w'].value = str(int(np.percentile(im, 99)))
            self._render()
        except Exception:
            pass

    # ── layer row factory ─────────────────────────────────────────────────────

    def _make_layer_row(self, round_default=None, chan_default=None,
                        color_default='Gray', opacity_default=1.0,
                        cmin_default='0', cmax_default='4095'):
        rounds = self._rounds_list()
        if not rounds:
            return None, None

        round_default = round_default or rounds[0]
        chans         = self._channels_for(round_default)
        chan_default  = chan_default or (chans[0] if chans else '')

        def _lbl(t):
            s = 'color:#6a9ab0;font-size:11px;margin:auto 3px auto 0;white-space:nowrap;'
            return widgets.HTML(value=f'<span style="{s}">{t}</span>')

        round_dd  = widgets.Dropdown(options=rounds, value=round_default,
                                     style={'description_width': '0px'},
                                     layout=widgets.Layout(width='90px'))
        chan_dd   = widgets.Dropdown(options=chans, value=chan_default,
                                     style={'description_width': '0px'},
                                     layout=widgets.Layout(width='90px'))
        color_dd  = widgets.Dropdown(options=_ALL_COLORS, value=color_default,
                                     style={'description_width': '0px'},
                                     layout=widgets.Layout(width='88px'))
        opacity_s = widgets.FloatSlider(
            value=opacity_default, min=0.0, max=1.0, step=0.05,
            readout_format='.2f',
            style={'description_width': '0px'},
            layout=widgets.Layout(width='110px'),
        )
        cmin_w = widgets.Text(value=cmin_default, layout=widgets.Layout(width='62px'))
        cmax_w = widgets.Text(value=cmax_default, layout=widgets.Layout(width='62px'))
        auto_btn = widgets.Button(
            description='Auto',
            layout=widgets.Layout(width='50px', height='28px'),
            style=widgets.ButtonStyle(button_color='#1e3a4a', font_color='#a8d8f0'),
        )
        remove_btn = widgets.Button(
            description='✕', button_style='danger',
            layout=widgets.Layout(width='30px', height='28px'),
        )

        state = dict(round_dd=round_dd, chan_dd=chan_dd, color_dd=color_dd,
                     opacity_s=opacity_s, cmin_w=cmin_w, cmax_w=cmax_w)

        def _on_round(change):
            new_chans = self._channels_for(change['new'])
            chan_dd.options = new_chans
            if new_chans:
                chan_dd.value = new_chans[0]
            self._render()

        round_dd.observe(_on_round, names='value')
        for w in (chan_dd, color_dd, opacity_s, cmin_w, cmax_w):
            w.observe(self._render, names='value')
        auto_btn.on_click(lambda _: self._auto_contrast(state))

        row = widgets.HBox(
            [_lbl('Round'), round_dd, _lbl('Ch'), chan_dd,
             _lbl('Color'), color_dd, _lbl('Opacity'), opacity_s,
             _lbl('Min'), cmin_w, _lbl('Max'), cmax_w, auto_btn, remove_btn],
            layout=widgets.Layout(
                align_items='center', margin='2px 0', padding='3px 8px',
                border='1px solid #1e3a4a', border_radius='5px',
            ),
        )

        def _on_remove(_):
            if state in self._layer_states:
                idx = self._layer_states.index(state)
                self._layer_states.pop(idx)
                rows = list(self._layers_vbox.children)
                rows.pop(idx)
                self._layers_vbox.children = rows
            self._render()

        remove_btn.on_click(_on_remove)
        return row, state

    # ── public API ────────────────────────────────────────────────────────────

    def add_layer(self, round_label=None, channel=None, color='Gray',
                  opacity=1.0, cmin='0', cmax='4095'):
        row, state = self._make_layer_row(round_label, channel, color, opacity, cmin, cmax)
        if row is None:
            self._status.value = (
                f'<span style="color:#ff6b6b;">No TIFFs found in: {self.tiff_dir}</span>'
            )
            return
        self._layer_states.append(state)
        self._layers_vbox.children = list(self._layers_vbox.children) + [row]
        self._render()

    def build(self):
        """
        Build and return the viewer as a single widget (without displaying it).
        Call .show() to display, or put the return value in an Output widget.
        """
        if not self._rounds:
            return widgets.HTML(
                value=(
                    f'<div style="color:#ff6b6b;font-size:13px;padding:10px;">'
                    f'No TIFF files found for well <b>{self.well}</b> in:<br>'
                    f'<code>{self.tiff_dir}</code></div>'
                )
            )

        rounds_str = ', '.join(self._rounds_list())
        title = widgets.HTML(value=(
            f'<div style="font-size:13px;font-weight:bold;color:#cdd6f4;margin-bottom:3px;">'
            f'Well {self.well} — 4i Image Viewer</div>'
            f'<div style="font-size:10px;color:#6a9ab0;margin-bottom:5px;">'
            f'Rounds: {rounds_str} &nbsp;|&nbsp; '
            f'Add layers to overlay &nbsp;|&nbsp; Auto = auto-contrast</div>'
        ))

        add_btn = widgets.Button(
            description='+ Add Layer',
            layout=widgets.Layout(width='110px', height='28px', margin='3px 0 5px 0'),
            style=widgets.ButtonStyle(button_color='#1a7abf', font_color='#ffffff'),
        )
        add_btn.on_click(lambda _: self.add_layer())

        # ── Zoom / Pan controls ───────────────────────────────────────────────
        def _lbl(t):
            s = 'color:#6a9ab0;font-size:11px;margin:auto 4px auto 0;white-space:nowrap;'
            return widgets.HTML(value=f'<span style="{s}">{t}</span>')

        self._zoom_w = widgets.SelectionSlider(
            options=[1, 2, 4, 8],
            value=1,
            description='',
            style={'description_width': '0px'},
            layout=widgets.Layout(width='120px'),
        )
        self._pan_x_w = widgets.FloatSlider(
            value=0.5, min=0.0, max=1.0, step=0.02,
            description='', style={'description_width': '0px'},
            layout=widgets.Layout(width='130px'),
        )
        self._pan_y_w = widgets.FloatSlider(
            value=0.5, min=0.0, max=1.0, step=0.02,
            description='', style={'description_width': '0px'},
            layout=widgets.Layout(width='130px'),
        )

        pan_x_row = widgets.HBox(
            [_lbl('Pan X'), self._pan_x_w], layout=widgets.Layout(align_items='center'),
        )
        pan_y_row = widgets.HBox(
            [_lbl('Pan Y'), self._pan_y_w], layout=widgets.Layout(align_items='center'),
        )
        self._pan_box = widgets.VBox(
            [pan_x_row, pan_y_row],
            layout=widgets.Layout(display='none'),  # hidden at 1×
        )

        def _on_zoom(change):
            self._pan_box.layout.display = 'none' if change['new'] <= 1 else ''
            self._render()

        self._zoom_w.observe(_on_zoom, names='value')
        self._pan_x_w.observe(self._render, names='value')
        self._pan_y_w.observe(self._render, names='value')

        zoom_row = widgets.HBox(
            [_lbl('Zoom'), self._zoom_w],
            layout=widgets.Layout(align_items='center', margin='2px 0'),
        )

        container = widgets.VBox(
            [title, self._layers_vbox, add_btn, zoom_row,
             self._pan_box, self._status, self._img_widget],
            layout=widgets.Layout(padding='12px 16px'),
        )

        # Add the first default layer (no display call here — caller manages display)
        self.add_layer()
        return container

    def show(self):
        """Build and display the viewer widget in the current cell output."""
        display(self.build())
