# coding=utf-8
# ======================================
# File:     hp_visual_plotly.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-03-15
# Desc:
#   HistoryPanel 交互式渲染层（Plotly）：根据规格片段输出 Plotly Figure，
#   风格与静态图表一致，支持顶部数据展示区与时间轴同步。
# ======================================

from __future__ import annotations

import html
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from qteasy.hp_visual_bar_display import (
    build_bar_display_data,
    mpl_ohlc_header_segments,
    primary_kline_group_index,
    specs_contain_kline,
)
from qteasy.hp_visual_layout import compute_hp_visual_layout_spec, plotly_trace_row_1based
from qteasy.hp_visual_theme_adapt import (
    HeaderFontRole,
    header_font_span_style,
    merge_header_font_theme,
    plotly_font_dict,
    resolve_candle_style_plotly,
    resolve_font_size,
    resolve_header_font_plotly,
)

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False


def _annotations_for_plotly_html_export(layout: Any, meta: Optional[Mapping[str, Any]]) -> List[Any]:
    """
    供嵌入 Notebook HTML 的 Figure 使用的 ``layout.annotations`` 列表。

    顶栏 OHLC 由独立 ``div`` 展示时，不再整表清空 annotations，仅保留
    ``make_subplots(..., subplot_titles=...)`` 产生的前缀条数（与 FigureWidget
    路径 ``subplot_annotation_count`` 语义一致），避免多组时分组标题丢失。

    Parameters
    ----------
    layout : Any
        Plotly ``layout`` 对象（含 ``annotations``）。
    meta : mapping, optional
        ``_hp_plotly_meta``；无 ``show_ohlc_header`` / ``initial_header_html`` 时不裁剪。

    Returns
    -------
    list
        写入 ``update_layout(annotations=...)`` 的 annotation 序列。
    """
    ann = list(layout.annotations) if getattr(layout, 'annotations', None) else []
    if not meta or not meta.get('show_ohlc_header') or not meta.get('initial_header_html'):
        return ann
    n_meta = meta.get('subplot_annotation_count')
    if n_meta is None:
        return ann
    n_sub = max(0, min(int(n_meta), len(ann)))
    return ann[:n_sub]


class _PlotlyFigureWrapper:
    """
    包装 Plotly Figure，在 Jupyter Notebook 中通过嵌入完整 HTML（含 Plotly.js CDN）
    保证交互图能显示，不依赖前端的 renderer 配置。
    未定义的属性（如 data、layout）委托给底层 Figure。
    """

    def __init__(self, figure: Any) -> None:
        self._figure = figure

    @property
    def figure(self) -> Any:
        """底层 Plotly Figure，用于 write_html、保存等。"""
        return self._figure

    def __getattr__(self, name: str) -> Any:
        """委托 data、layout 等属性到底层 Figure，便于测试与写文件。"""
        return getattr(self._figure, name)

    def _repr_html_(self) -> str:
        """Jupyter 输出单元格时调用，直接返回完整 HTML 以在 Notebook 中显示。"""
        config = dict(
            displayModeBar=True,
            responsive=True,
            modeBarButtonsToRemove=[
                'toImage', 'sendDataToCloud', 'lasso2d', 'select2d',
                'toggleSpikeLines', 'hoverClosestCartesian', 'hoverCompareCartesian',
            ],
            displaylogo=False,
        )
        import json
        div_id = 'hp-plotly-' + str(id(self._figure))
        meta = getattr(self._figure, '_hp_plotly_meta', None)
        # 使用包装器时用独立 header div，不再在 figure 内显示 title 避免重复
        fig_for_html = self._figure
        if meta and meta.get('show_ohlc_header') and meta.get('initial_header_html'):
            fig_for_html = go.Figure(self._figure)
            kept = _annotations_for_plotly_html_export(fig_for_html.layout, meta)
            fig_for_html.update_layout(title=None, annotations=kept)
        html = fig_for_html.to_html(
            include_plotlyjs='cdn',
            config=config,
            full_html=False,
            div_id=div_id,
        )
        # 表头置于画布最上方（独立 div）；无 K 线时不预留
        if meta and meta.get('show_ohlc_header') and meta.get('initial_header_html'):
            fs = 12
            if meta.get('theme'):
                fs = int(merge_header_font_theme(meta['theme'])['header_normal']['size'])
            header_style = (
                f'min-height:52px;line-height:1.4;padding:6px 10px;font-size:{fs}px;'
                'background:#f8f8f8;border-bottom:1px solid #ddd;'
            )
            header_div = '<div id="hp-header-' + div_id + '" style="' + header_style + '"></div>\n'
            html = header_div + html
        if meta is not None:
            meta_js = {k: v for k, v in meta.items() if k != 'theme'}
            html += '\n<script>window["HP_PLOTLY_META_' + div_id + '"] = ' + json.dumps(meta_js) + ';</script>\n'
        script = _click_update_header_script(div_id)
        if script:
            html = html.rstrip(' \n') + '\n' + script
        return html

    def show(self) -> None:
        """在当前前端（如 Notebook）中显示图表；在 Jupyter 中不依赖 renderer。"""
        try:
            from IPython.display import display, HTML
            display(HTML(self._repr_html_()))
        except ImportError:
            self._figure.show()


def _y_autorange_script(div_id: str) -> str:
    """时间范围（X 轴）变化后，每张图表 Y 轴范围调整为该图可见数据的 MIN/MAX。"""
    return (
        '<script type="text/javascript">\n'
        '(function() {\n'
        '  var divId = ' + repr(div_id) + ';\n'
        '  function getXRangeFromLayout(layout) {\n'
        '    var k, r;\n'
        '    for (var i = 1; i <= 20; i++) {\n'
        '      k = i === 1 ? "xaxis" : "xaxis" + i;\n'
        '      r = layout[k] && layout[k].range;\n'
        '      if (r && Array.isArray(r) && r.length >= 2) return r;\n'
        '    }\n'
        '    return null;\n'
        '  }\n'
        '  function getXRangeFromFullLayout(gd) {\n'
        '    var fl = gd._fullLayout;\n'
        '    if (!fl) return null;\n'
        '    var r = fl.xaxis && fl.xaxis.range;\n'
        '    if (r && Array.isArray(r) && r.length >= 2) return r.slice();\n'
        '    for (var i = 2; i <= 20; i++) {\n'
        '      var ax = fl["xaxis" + i];\n'
        '      if (ax && ax.range && ax.range.length >= 2) return ax.range.slice();\n'
        '    }\n'
        '    return null;\n'
        '  }\n'
        '  function getXRangeFromEvent(ev) {\n'
        '    if (!ev) return null;\n'
        '    var key, m, prefix, r0, r1;\n'
        '    for (key in ev) {\n'
        '      if (ev.hasOwnProperty(key) && (m = key.match(/^xaxis(\\d*)\\.range\\[0\\]$/))) {\n'
        '        prefix = "xaxis" + (m[1] || "") + ".range";\n'
        '        r0 = ev[prefix + "[0]"]; r1 = ev[prefix + "[1]"];\n'
        '        if (typeof r0 === "number" && typeof r1 === "number") return [r0, r1];\n'
        '      }\n'
        '    }\n'
        '    var r = ev["xaxis.range"];\n'
        '    if (r && Array.isArray(r) && r.length >= 2) return r.slice();\n'
        '    if (ev.xaxis && ev.xaxis.range) return ev.xaxis.range.slice();\n'
        '    return null;\n'
        '  }\n'
        '  function getDataXExtent(data) {\n'
        '    var xMin = Infinity, xMax = -Infinity;\n'
        '    for (var i = 0; i < data.length; i++) {\n'
        '      var xs = data[i].x || [];\n'
        '      for (var j = 0; j < xs.length; j++) {\n'
        '        if (typeof xs[j] === "number" && !isNaN(xs[j])) {\n'
        '          if (xs[j] < xMin) xMin = xs[j]; if (xs[j] > xMax) xMax = xs[j];\n'
        '        }\n'
        '      }\n'
        '    }\n'
        '    if (xMin === Infinity) return null;\n'
        '    return [xMin, xMax];\n'
        '  }\n'
        '  function applyYAutorangeWithXRange(gd, xrange) {\n'
        '    var data = gd.data;\n'
        '    if (!data || !data.length || !xrange || xrange.length < 2) return;\n'
        '    var full = gd._fullData;\n'
        '    var x0 = Math.min(xrange[0], xrange[1]), x1 = Math.max(xrange[0], xrange[1]);\n'
        '    var n = 0;\n'
        '    for (var i = 0; i < data.length; i++) {\n'
        '      var d = data[i], f = full && full[i];\n'
        '      var L = (d.x || []).length;\n'
        '      var low = (f && f.low) || d.low, high = (f && f.high) || d.high;\n'
        '      if (low && high) L = Math.max(L, low.length, high.length);\n'
        '      if ((d.y && d.y.length) || (f && f.y && f.y.length)) L = Math.max(L, (f && f.y && f.y.length) || 0, (d.y && d.y.length) || 0);\n'
        '      if (L > n) n = L;\n'
        '    }\n'
        '    if (n > 0) {\n'
        '      x0 = Math.max(0, Math.min(x0, n - 1)); x1 = Math.min(n - 1, Math.max(x1, 0));\n'
        '      if (x0 > x1) { var t = x0; x0 = x1; x1 = t; }\n'
        '    }\n'
        '    var j0 = Math.max(0, Math.floor(x0)), j1 = Math.ceil(x1);\n'
        '    var yaxes = {};\n'
        '    for (var i = 0; i < data.length; i++) {\n'
        '      var t = data[i], f = full && full[i], yax = t.yaxis || "y";\n'
        '      if (!yaxes[yax]) yaxes[yax] = { min: Infinity, max: -Infinity };\n'
        '      var yMin = Infinity, yMax = -Infinity;\n'
        '      var typeStr = (t.type || "").toLowerCase();\n'
        '      var low = (f && f.low) || t.low, high = (f && f.high) || t.high;\n'
        '      if ((typeStr === "candlestick" || typeStr === "ohlc") && low && high && low.length > 0 && high.length > 0) {\n'
        '        var len = Math.min(low.length, high.length);\n'
        '        for (var j = j0; j <= j1 && j < len; j++) {\n'
        '          var lj = low[j], hj = high[j];\n'
        '          if (typeof lj === "number" && !isNaN(lj) && lj < yMin) yMin = lj;\n'
        '          if (typeof hj === "number" && !isNaN(hj) && hj > yMax) yMax = hj;\n'
        '        }\n'
        '      }\n'
        '      if (yMin === Infinity) {\n'
        '        var yArr = (f && f.y) || t.y;\n'
        '        if (yArr && Array.isArray(yArr)) {\n'
        '          for (var j = j0; j <= j1 && j < yArr.length; j++) {\n'
        '            var v = yArr[j];\n'
        '            if (typeof v === "number" && !isNaN(v)) { if (v < yMin) yMin = v; if (v > yMax) yMax = v; }\n'
        '          }\n'
        '        }\n'
        '      }\n'
        '      if (yMin !== Infinity) {\n'
        '        if (yMin < yaxes[yax].min) yaxes[yax].min = yMin;\n'
        '        if (yMax > yaxes[yax].max) yaxes[yax].max = yMax;\n'
        '      }\n'
        '    }\n'
        '    var update = {};\n'
        '    for (var k in yaxes) {\n'
        '      var r = yaxes[k];\n'
        '      if (r.min !== Infinity && isFinite(r.min) && isFinite(r.max)) {\n'
        '        var pad = Math.max((r.max - r.min) * 0.05, 1e-6);\n'
        '        var layoutKey = (k === "y") ? "yaxis" : ("yaxis" + String(k).replace(/^y/, ""));\n'
        '        update[layoutKey + ".range"] = [r.min - pad, r.max + pad];\n'
        '      }\n'
        '    }\n'
        '    try {\n'
        '      var hook = window.__HP_ON_Y_AUTORANGE || (window.parent && window.parent !== window && window.parent.__HP_ON_Y_AUTORANGE);\n'
        '      if (typeof hook === "function") hook(Object.keys(update).length ? update : { _empty: true, _n: n, _x0: x0, _x1: x1, _yaxesKeys: Object.keys(yaxes) });\n'
        '    } catch (e) {}\n'
        '    if (Object.keys(update).length) {\n'
        '      for (var key in update) {\n'
        '        var one = {}; one[key] = update[key];\n'
        '        try { Plotly.relayout(gd, one); } catch (e) {}\n'
        '      }\n'
        '    }\n'
        '  }\n'
        '  function applyYAutorange(gd, evOrRange) {\n'
        '    var data = gd.data;\n'
        '    if (!data || !data.length) return;\n'
        '    var xrange = null;\n'
        '    if (Array.isArray(evOrRange) && evOrRange.length >= 2) xrange = evOrRange;\n'
        '    else if (evOrRange && typeof evOrRange === "object") xrange = getXRangeFromEvent(evOrRange) || getXRangeFromFullLayout(gd) || getXRangeFromLayout(gd.layout) || getDataXExtent(data);\n'
        '    else xrange = getXRangeFromFullLayout(gd) || getXRangeFromLayout(gd.layout) || getDataXExtent(data);\n'
        '    if (!xrange || xrange.length < 2) return;\n'
        '    applyYAutorangeWithXRange(gd, xrange);\n'
        '  }\n'
        '  function attachOne(gd) {\n'
        '    if (!gd || !gd.data || gd.getAttribute("data-hp-y-autorange") === "1") return;\n'
        '    try { gd.setAttribute("data-hp-y-autorange", "1"); } catch (e) {}\n'
        '    gd.on("plotly_afterplot", function() {\n'
        '      setTimeout(function() { applyYAutorange(gd, null); }, 250);\n'
        '    });\n'
        '    gd.on("plotly_relayout", function(ev) {\n'
        '      try {\n'
        '        var xrange = ev ? getXRangeFromEvent(ev) : null;\n'
        '        try { if (typeof window.__HP_ON_Y_AUTORANGE === "function") window.__HP_ON_Y_AUTORANGE({_ev: !!ev, _xrange: xrange ? xrange.length : 0}); else if (window.parent && window.parent !== window && typeof window.parent.__HP_ON_Y_AUTORANGE === "function") window.parent.__HP_ON_Y_AUTORANGE({_ev: !!ev, _xrange: xrange ? xrange.length : 0}); } catch (e) {}\n'
        '        if (xrange && xrange.length >= 2) {\n'
        '          setTimeout(function() { try { applyYAutorangeWithXRange(gd, xrange); } catch (e) { try { if (typeof window.__HP_ON_Y_AUTORANGE === "function") window.__HP_ON_Y_AUTORANGE({_error: String(e)}); } catch(e2) {} } }, 20);\n'
        '        }\n'
        '      } catch (e) {\n'
        '        try { if (typeof window.__HP_ON_Y_AUTORANGE === "function") window.__HP_ON_Y_AUTORANGE({_error: String(e)}); } catch(e2) {}\n'
        '      }\n'
        '    });\n'
        '  }\n'
        '  function attach() {\n'
        '    var doc = document;\n'
        '    try { if (document.currentScript && document.currentScript.ownerDocument) doc = document.currentScript.ownerDocument; } catch (e) {}\n'
        '    var gd = doc.getElementById(divId);\n'
        '    if (gd && gd.data) { attachOne(gd); return; }\n'
        '    if (doc.querySelectorAll) {\n'
        '      var list = doc.querySelectorAll("[id^=\'hp-plotly-\']");\n'
        '      for (var i = 0; i < list.length; i++) { if (list[i].data) attachOne(list[i]); }\n'
        '      if (list.length > 0) return;\n'
        '    }\n'
        '    gd = doc.querySelector("[id^=\'hp-plotly-\']");\n'
        '    if (gd && gd.data) { attachOne(gd); return; }\n'
        '    setTimeout(attach, 150);\n'
        '  }\n'
        '  if (document.readyState === "complete") attach(); else window.addEventListener("load", attach);\n'
        '  var retryCount = 0;\n'
        '  var retryId = setInterval(function() {\n'
        '    retryCount++; if (retryCount > 5) { clearInterval(retryId); return; }\n'
        '    var doc = document;\n'
        '    try { if (document.currentScript && document.currentScript.ownerDocument) doc = document.currentScript.ownerDocument; } catch (e) {}\n'
        '    var list = doc.querySelectorAll ? doc.querySelectorAll("[id^=\'hp-plotly-\']") : [];\n'
        '    for (var i = 0; i < list.length; i++) { if (list[i].data && list[i].getAttribute("data-hp-y-autorange") !== "1") attachOne(list[i]); }\n'
        '  }, 2000);\n'
        '})();\n'
        '</script>'
    )


def _click_update_header_script(div_id: str) -> str:
    """点击某 bar 时，表头（独立 HTML div）更新为该 bar 的数据；加载时用 initial_header_html 填充。"""
    return (
        '<script type="text/javascript">\n'
        '(function() {\n'
        '  var divId = ' + repr(div_id) + ';\n'
        '  function span(t, c, fs) { fs = fs || 11; return "<span style=\'color:"+c+";font-size:"+fs+"px\'>"+t+"</span>"; }\n'
        '  function buildHeaderHTML(rec, fsBody, fsEm) {\n'
        '    fsBody = fsBody || 11; fsEm = fsEm || 16;\n'
        '    var c = rec.change, colorMain = (c != null) ? (c > 0 ? "red" : (c < 0 ? "green" : "black")) : "black";\n'
        '    var lowColor = (c != null && c < 0) ? "green" : "black";\n'
        '    var p1 = [];\n'
        '    p1.push(span("O/C: ", "black", fsBody));\n'
        '    if (rec.open != null && rec.close != null) p1.push(span(rec.open.toFixed(2)+" / "+rec.close.toFixed(2), colorMain, fsEm));\n'
        '    p1.push(" &nbsp; "); p1.push(span("H: ", "black", fsBody));\n'
        '    if (rec.high != null) p1.push(span(rec.high.toFixed(3), colorMain, fsBody));\n'
        '    p1.push(" &nbsp; "); p1.push(span("Vol(10k): ", "black", fsBody));\n'
        '    if (rec.volume != null) p1.push(span((rec.volume/1e4).toFixed(3), "black", fsBody));\n'
        '    p1.push(" &nbsp; "); p1.push(span("Up limit: ", "black", fsBody));\n'
        '    if (rec.upper_lim != null) p1.push(span(rec.upper_lim.toFixed(3), "red", fsBody));\n'
        '    p1.push(" &nbsp; "); p1.push(span("Avg: ", "black", fsBody));\n'
        '    if (rec.ma && Object.keys(rec.ma).length) p1.push(span(parseFloat(rec.ma[Object.keys(rec.ma)[0]]).toFixed(3), "black", fsBody));\n'
        '    var p2 = [];\n'
        '    p2.push(span(rec.date_str || "", "black", fsBody));\n'
        '    if (rec.change != null) { p2.push(" &nbsp; "); p2.push(span(rec.change.toFixed(3), colorMain, fsBody)); }\n'
        '    if (rec.pct_change != null) p2.push(span(" ["+rec.pct_change.toFixed(3)+"%]", colorMain, fsBody));\n'
        '    p2.push(" &nbsp; "); p2.push(span("L: ", "black", fsBody));\n'
        '    if (rec.low != null) p2.push(span(rec.low.toFixed(3), lowColor, fsBody));\n'
        '    p2.push(" &nbsp; "); p2.push(span("Turn(100M): ", "black", fsBody));\n'
        '    if (rec.value != null) p2.push(span((rec.value/1e8).toFixed(3), "black", fsBody));\n'
        '    p2.push(" &nbsp; "); p2.push(span("Dn limit: ", "black", fsBody));\n'
        '    if (rec.lower_lim != null) p2.push(span(rec.lower_lim.toFixed(3), "green", fsBody));\n'
        '    p2.push(" &nbsp; "); p2.push(span("Prev: ", "black", fsBody));\n'
        '    if (rec.last_close != null) p2.push(span(rec.last_close.toFixed(3), "black", fsBody));\n'
        '    return "<div style=\'line-height:1.4;padding:6px 10px;font-size:"+fsBody+"px;background:#f8f8f8;border-bottom:1px solid #ddd\'><div>"+p1.join("")+"</div><div>"+p2.join("")+"</div></div>";\n'
        '  }\n'
        '  function attach() {\n'
        '    var gd = document.getElementById(divId);\n'
        '    if (!gd || !gd.data) { setTimeout(attach, 80); return; }\n'
        '    var meta = window["HP_PLOTLY_META_" + divId]; if (!meta || !meta.show_ohlc_header) return;\n'
        '    var nt = meta.n_types, ng = meta.n_groups || 1;\n'
        '    var hdr = document.getElementById("hp-header-" + divId);\n'
        '    var fsB = meta.header_font_body || 11, fsE = meta.header_font_emphasis || 16;\n'
        '    if (hdr && meta.initial_header_html) hdr.innerHTML = meta.initial_header_html;\n'
        '    gd.on("plotly_click", function(ev) {\n'
        '      if (!ev || !ev.points || !ev.points.length) return;\n'
        '      var pt = ev.points[0], pointIndex = pt.pointNumber != null ? pt.pointNumber : Math.round(pt.x);\n'
        '      var trace = gd.data[pt.curveNumber]; var yax = (trace && trace.yaxis) ? trace.yaxis : "y";\n'
        '      var row = (yax === "y") ? 1 : (parseInt(String(yax).replace(/^y/,""), 10) || 1);\n'
        '      var groupIdx = (ng > 1) ? Math.floor((row - 1) / (nt + 1)) : 0;\n'
        '      if (groupIdx < 0 || groupIdx >= ng) return;\n'
        '      var barData = meta.bar_data[groupIdx]; if (!barData || pointIndex >= barData.length) return;\n'
        '      var rec = barData[pointIndex];\n'
        '      if (hdr) hdr.innerHTML = buildHeaderHTML(rec, fsB, fsE);\n'
        '    });\n'
        '  }\n'
        '  if (document.readyState === "complete") attach(); else window.addEventListener("load", attach);\n'
        '})();\n'
        '</script>'
    )


def _can_use_figure_widget() -> bool:
    """当前环境是否支持 FigureWidget（Jupyter + ipywidgets），用于方案 B 双模。"""
    try:
        from IPython import get_ipython
        from plotly.graph_objs import FigureWidget
        return get_ipython() is not None
    except Exception:
        return False


def _in_ipython_kernel() -> bool:
    """是否在 Jupyter / IPython 内核中（不要求 ipywidgets）。"""
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except Exception:
        return False


def _normalize_plotly_backend_app(value: str) -> str:
    """
    校验 ``HistoryPanel.plot(..., plotly_backend_app=...)`` 取值。

    Returns
    -------
    str
        ``'auto'``、``'figurewidget'`` 或 ``'html'``（小写规范形式）。
    """
    k = (value or 'auto').strip().lower()
    if k in ('auto', ''):
        return 'auto'
    if k == 'figurewidget':
        return 'figurewidget'
    if k == 'html':
        return 'html'
    raise ValueError(
        "plotly_backend_app must be one of 'auto', 'FigureWidget', 'html'."
    )


def _is_plotly_figure_widget(obj: Any) -> bool:
    """判断是否为 plotly FigureWidget 实例。"""
    try:
        from plotly.graph_objs import FigureWidget
        return isinstance(obj, FigureWidget)
    except Exception:
        return False


def _select_plotly_notebook_output(fig: Any, plotly_backend_app: str = 'auto') -> Any:
    """
    在 Notebook 环境下为交互图选择返回类型：FigureWidget、HTML 包装器或原始 Figure。

    Parameters
    ----------
    fig : Any
        ``build_interactive_figure_from_specs`` 产出的 Figure（含 ``_hp_plotly_meta``）。
    plotly_backend_app : str, default 'auto'
        ``'auto'``：优先 FigureWidget，失败则回退 HTML 包装；``'figurewidget'``：强制 Widget，失败抛错；
        ``'html'``：强制 HTML 包装，失败抛错。

    Returns
    -------
    Any
        FigureWidget、``_PlotlyFigureWrapper`` 或无法包装时的原始 Figure（仅 ``auto`` 且非内核）。
    """
    mode = _normalize_plotly_backend_app(plotly_backend_app)
    if mode == 'auto':
        if _can_use_figure_widget():
            out = _create_figure_widget_with_callbacks(fig)
            if _is_plotly_figure_widget(out):
                return out
        return _wrap_figure_for_notebook(fig)
    if mode == 'figurewidget':
        if not _can_use_figure_widget():
            raise RuntimeError(
                "plotly_backend_app='FigureWidget' requires an active Jupyter/IPython environment "
                "with plotly FigureWidget support (e.g. ipywidgets)."
            )
        out = _create_figure_widget_with_callbacks(fig)
        if not _is_plotly_figure_widget(out):
            raise RuntimeError(
                "Failed to create plotly FigureWidget (plotly_backend_app='FigureWidget'). "
                "Check bar data, ipywidgets, and plotly installation."
            )
        return out
    if not _in_ipython_kernel():
        raise RuntimeError(
            "plotly_backend_app='html' requires an active Jupyter/IPython environment."
        )
    wrapped = _wrap_figure_for_notebook(fig)
    if isinstance(wrapped, _PlotlyFigureWrapper):
        return wrapped
    raise RuntimeError(
        "Failed to wrap plotly figure as HTML for notebook (plotly_backend_app='html')."
    )


def _wrap_figure_for_notebook(fig: Any) -> Any:
    """非 FigureWidget 时：若在 Jupyter 则返回包装器；否则返回原 Figure。"""
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            return _PlotlyFigureWrapper(fig)
    except Exception:
        pass
    return fig


def _compute_y_ranges_for_x_range(
    fw: Any,
    x0: float,
    x1: float,
    n: int,
) -> Dict[str, List[float]]:
    """
    根据当前可见 X 范围 [x0, x1] 与数据长度 n，从 fw.data 中计算每个 y 轴应设的 range [min, max]。
    返回形如 {'yaxis': [min, max], 'yaxis2': [...], ...}。
    """
    j0 = max(0, min(n - 1, int(np.floor(x0))))
    j1 = max(0, min(n - 1, int(np.ceil(x1))))
    if j0 > j1:
        j0, j1 = j1, j0
    y_ranges: Dict[str, List[float]] = {}

    for trace in fw.data:
        yax = getattr(trace, 'yaxis', None) or getattr(trace, 'yAxis', None)
        if yax is None:
            yax = 'y'
        layout_key = 'yaxis' if str(yax) == 'y' else ('yaxis' + str(yax).replace('y', '').replace('Y', ''))

        low = getattr(trace, 'low', None)
        high = getattr(trace, 'high', None)
        y_arr = getattr(trace, 'y', None)

        if low is not None and high is not None:
            low = np.asarray(low)
            high = np.asarray(high)
            seg_low = low[j0 : j1 + 1]
            seg_high = high[j0 : j1 + 1]
            valid = np.isfinite(seg_low) | np.isfinite(seg_high)
            if np.any(valid):
                y_min = float(np.nanmin(seg_low))
                y_max = float(np.nanmax(seg_high))
            else:
                continue
        elif y_arr is not None:
            y_arr = np.asarray(y_arr)
            seg = y_arr[j0 : j1 + 1]
            valid = np.isfinite(seg)
            if np.any(valid):
                y_min = float(np.nanmin(seg))
                y_max = float(np.nanmax(seg))
            else:
                continue
        else:
            continue

        if layout_key not in y_ranges:
            y_ranges[layout_key] = [y_min, y_max]
        else:
            y_ranges[layout_key][0] = min(y_ranges[layout_key][0], y_min)
            y_ranges[layout_key][1] = max(y_ranges[layout_key][1], y_max)

    return y_ranges


def _mm_to_css_px(mm: float, theme: Mapping[str, Any]) -> float:
    """
    将毫米转为 CSS 像素（默认 96px/inch，与常见浏览器一致）。

    Parameters
    ----------
    mm : float
        长度（毫米）。
    theme : mapping
        可含 ``plotly_css_px_per_inch``。

    Returns
    -------
    float
        像素值。
    """
    px_per_inch = float(theme.get('plotly_css_px_per_inch', 96.0))
    return float(mm) * px_per_inch / 25.4


def _plotly_header_paper_y_from_layout(
    height_px: float,
    margin_t_px: float,
    margin_b_px: float,
    theme: Mapping[str, Any],
) -> Tuple[float, float]:
    """
    根据 layout 高度与上下边距反解两行表头的 paper y，使文字上沿距整图顶边为固定毫米。

    近似模型：绘图区高度 H_plot = height - margin_t - margin_b；paper 子图区 y∈[0,1]，
    y>1 位于上边距；距整图顶 d_px 处 y = 1 + (margin_t - d_px) / H_plot（yanchor='top'）。
    仅用于 FigureWidget；纯 HTML 顶栏不使用。

    Parameters
    ----------
    height_px : float
        ``layout.height``（像素）。
    margin_t_px, margin_b_px : float
        ``layout.margin.t`` / ``b``（像素）。
    theme : mapping
        含 ``plotly_header_line1_top_mm``、``plotly_header_line2_top_mm`` 等。

    Returns
    -------
    tuple[float, float]
        第一行、第二行的 paper ``y``（第一行更靠上，值更大）。
    """
    h_plot_min = float(theme.get('plotly_header_h_plot_px_min', 80.0))
    h_plot = max(float(height_px) - float(margin_t_px) - float(margin_b_px), h_plot_min)
    mm1 = float(theme.get('plotly_header_line1_top_mm', 6.0))
    mm2 = float(theme.get('plotly_header_line2_top_mm', 14.5))
    d1 = _mm_to_css_px(mm1, theme)
    d2 = _mm_to_css_px(mm2, theme)
    y1 = 1.0 + (float(margin_t_px) - d1) / h_plot
    y2 = 1.0 + (float(margin_t_px) - d2) / h_plot
    y_max = float(theme.get('plotly_header_paper_y_max', 1.42))
    y_min = float(theme.get('plotly_header_paper_y_min', 1.02))
    y1 = min(max(y1, y_min), y_max)
    y2 = min(max(y2, y_min), y_max)
    if y2 >= y1:
        y2 = max(y_min, min(y1 - 0.03, y_max))
    return y1, y2


def _layout_height_margin_tb(
    layout: Any,
    theme: Mapping[str, Any],
    *,
    has_ohlc_header: bool,
) -> Tuple[float, float, float]:
    """
    读取 Plotly layout 的 height 与 margin.t/b（缺省回退 theme）。

    Parameters
    ----------
    layout : Any
        Plotly ``layout`` 对象。
    theme : mapping
        用于缺省 ``margin.t``。
    has_ohlc_header : bool
        是否按「有 OHLC 顶栏」选用 ``plotly_margin_top_with_header``。

    Returns
    -------
    tuple[float, float, float]
        ``(height_px, margin_t, margin_b)``。
    """
    h = getattr(layout, 'height', None)
    height_px = float(h) if h is not None else 600.0
    default_t = float(
        theme.get(
            'plotly_margin_top_with_header' if has_ohlc_header else 'plotly_margin_top_no_header',
            120 if has_ohlc_header else 80,
        ),
    )
    default_b = 40.0
    m = getattr(layout, 'margin', None)
    if m is None:
        return height_px, default_t, default_b
    mt = getattr(m, 't', None)
    mb = getattr(m, 'b', None)
    margin_t = float(mt) if mt is not None else default_t
    margin_b = float(mb) if mb is not None else default_b
    return height_px, margin_t, margin_b


def _create_figure_widget_with_callbacks(fig: Any) -> Any:
    """
    方案 B：在 Jupyter 中返回 FigureWidget，并绑定：
    - 表头 annotations（首条 bar）+ 点击 bar 更新表头；
    - 监听 x 轴范围变化，自动重算并更新各 y 轴 range（Y 轴自适应）。
    若无法创建 FigureWidget 则返回原 fig。
    """
    try:
        from plotly.graph_objs import FigureWidget
    except Exception:
        return fig
    meta = getattr(fig, '_hp_plotly_meta', None)
    if not meta or 'bar_data' not in meta:
        return fig
    bar_data = meta.get('bar_data', [])
    if not bar_data or not bar_data[0]:
        return fig
    theme = meta.get('theme') or _get_theme_internal()
    show_header = bool(meta.get('show_ohlc_header'))
    pk_fb = int(meta.get('ohlc_header_primary_group', 0))
    try:
        fw = FigureWidget(fig.data, fig.layout)
        fw._hp_plotly_meta = meta
        fw._hp_updating_y = False
    except Exception:
        return fig

    if show_header:
        bd0 = bar_data[pk_fb] if pk_fb < len(bar_data) else bar_data[0]
        init_rec = bd0[-1] if bd0 else {}
        if init_rec:
            n_sub = int(meta.get('subplot_annotation_count', 0))
            base: List[Any] = []
            if fw.layout.annotations:
                n_sub = min(n_sub, len(fw.layout.annotations))
                base = list(fw.layout.annotations[:n_sub])
            lay_h, mtb, mbb = _layout_height_margin_tb(fw.layout, theme, has_ohlc_header=True)
            py1, py2 = _plotly_header_paper_y_from_layout(lay_h, mtb, mbb, theme)
            fw.update_layout(
                annotations=base + _build_top_info_annotations(init_rec, theme, y1=py1, y2=py2),
            )

    # 数据长度 n（X 为 0..n-1）
    n = 0
    if fw.data:
        t0 = fw.data[0]
        x = getattr(t0, 'x', None)
        if x is not None:
            n = len(x)
        elif getattr(t0, 'y', None) is not None:
            n = len(t0.y)
    if n <= 0:
        n = 1

    # 可见索引的最小根数限制
    min_visible_bars = 15

    def _on_xaxis_change(layout_obj: Any, xrange: Any) -> None:
        if getattr(fw, '_hp_updating_y', False):
            return
        try:
            # xrange 为 xaxis.range 的新值；若拿不到则从当前 layout 读取
            if xrange and isinstance(xrange, (list, tuple)) and len(xrange) >= 2:
                x0, x1 = float(xrange[0]), float(xrange[1])
            else:
                xaxis = getattr(fw.layout, 'xaxis', None)
                x_range = getattr(xaxis, 'range', None) if xaxis is not None else None
                if not x_range or len(x_range) < 2:
                    x_range = [0, float(n - 1)]
                x0, x1 = float(x_range[0]), float(x_range[1])

            # 规范化与约束：保证 x0 <= x1，且在 [0, n-1] 范围内
            if x0 > x1:
                x0, x1 = x1, x0
            x0 = max(0.0, min(float(n - 1), x0))
            x1 = max(0.0, min(float(n - 1), x1))
            if x0 == x1:
                x1 = min(float(n - 1), x0 + 1.0)

            # 根据当前范围计算可见 K 线数量，并控制最小缩放级别
            j0 = max(0, min(n - 1, int(np.floor(x0))))
            j1 = max(0, min(n - 1, int(np.ceil(x1))))
            if j0 > j1:
                j0, j1 = j1, j0
            visible_count = j1 - j0 + 1

            if n > min_visible_bars and visible_count < min_visible_bars:
                # 放大过头时，强制回退到至少 min_visible_bars 根，以当前中心为基准
                center = 0.5 * (x0 + x1)
                half = 0.5 * float(min_visible_bars - 1)
                x0 = max(0.0, center - half)
                x1 = min(float(n - 1), center + half)
                if x0 == x1:
                    x1 = min(float(n - 1), x0 + 1.0)
                j0 = max(0, min(n - 1, int(np.floor(x0))))
                j1 = max(0, min(n - 1, int(np.ceil(x1))))
                if j0 > j1:
                    j0, j1 = j1, j0

            y_ranges = _compute_y_ranges_for_x_range(fw, x0, x1, n)
            if not y_ranges:
                return
            fw._hp_updating_y = True
            try:
                update = {}
                for key, (ymin, ymax) in y_ranges.items():
                    pad = max((ymax - ymin) * 0.05, 1e-6)
                    # Plotly 多 y 轴用 yaxis_range, yaxis2_range 等
                    update[f'{key}_range'] = [ymin - pad, ymax + pad]

                # 同步更新 X 轴范围，限制平移不超出 K 线两端
                update['xaxis_range'] = [x0, x1]

                fw.update_layout(**update)

                # 根据当前可见区间自适应更新时间轴刻度密度
                bar_data = getattr(fw, '_hp_plotly_meta', {}).get('bar_data', [])
                pk = int(getattr(fw, '_hp_plotly_meta', {}).get('ohlc_header_primary_group', 0))
                dates = (
                    bar_data[pk] if pk < len(bar_data) and bar_data[pk] else (bar_data[0] if bar_data else [])
                )
                if dates:
                    theme_local = getattr(fw, '_hp_plotly_meta', {}).get('theme') or _get_theme_internal()
                    max_x_ticks = int(theme_local.get('max_x_ticks', 12))
                    visible_count = j1 - j0 + 1
                    step = max(1, visible_count // max_x_ticks) if visible_count > 0 else 1
                    tickvals = list(range(j0, j1 + 1, step))
                    ticktext: List[str] = []
                    for idx in tickvals:
                        if 0 <= idx < len(dates):
                            ticktext.append(str(dates[idx].get('date_str', '')))
                    if tickvals and ticktext and len(tickvals) == len(ticktext):
                        fw.update_xaxes(
                            tickmode='array',
                            tickvals=tickvals,
                            ticktext=ticktext,
                        )
            finally:
                fw._hp_updating_y = False
        except Exception:
            fw._hp_updating_y = False

    def _on_click(trace: Any, points: Any, selector: Any) -> None:
        if not getattr(fw, '_hp_plotly_meta', {}).get('show_ohlc_header'):
            return
        if not points or not getattr(points, 'point_inds', None):
            return
        try:
            inds = points.point_inds
            if not inds:
                return
            point_index = int(inds[0])
            custom = getattr(trace, 'customdata', None)
            group = int(custom[point_index]) if custom is not None and point_index < len(custom) else 0
            bar_data = getattr(fw, '_hp_plotly_meta', {}).get('bar_data', [])
            if group >= len(bar_data) or point_index >= len(bar_data[group]):
                return
            rec = bar_data[group][point_index]
            theme = getattr(fw, '_hp_plotly_meta', {}).get('theme') or _get_theme_internal()
            n_sub = int(getattr(fw, '_hp_plotly_meta', {}).get('subplot_annotation_count', 0))
            base: List[Any] = []
            if fw.layout.annotations:
                n_sub = min(n_sub, len(fw.layout.annotations))
                base = list(fw.layout.annotations[:n_sub])
            lay_h, mtb, mbb = _layout_height_margin_tb(fw.layout, theme, has_ohlc_header=True)
            py1, py2 = _plotly_header_paper_y_from_layout(lay_h, mtb, mbb, theme)
            new_annotations = base + _build_top_info_annotations(rec, theme, y1=py1, y2=py2)
            fw.update_layout(annotations=new_annotations)
        except Exception:
            pass

    # 监听 X 轴 range 变化（缩放/平移）实现 Y 轴自适应
    try:
        if hasattr(fw.layout, 'xaxis') and hasattr(fw.layout.xaxis, 'on_change'):
            fw.layout.xaxis.on_change(_on_xaxis_change, 'range')
            # 初始化一次 Y 轴范围
            _on_xaxis_change(fw.layout.xaxis, getattr(fw.layout.xaxis, 'range', [0, float(n - 1)]))
    except Exception:
        pass
    try:
        for trace in fw.data:
            trace.on_click(_on_click)
    except Exception:
        pass
    return fw


def _get_theme_internal() -> Dict[str, Any]:
    """从静态渲染层获取主题，保证与静态图表一致。"""
    from qteasy.hp_visual_render import _get_theme
    return _get_theme()


def _theme_to_plotly_color(theme_val: Any) -> str:
    """将主题中的颜色（tuple 或 str）转为 Plotly 可用的 rgb/rgba 或颜色名。"""
    if isinstance(theme_val, str):
        return theme_val
    if isinstance(theme_val, (list, tuple)) and len(theme_val) >= 3:
        r, g, b = float(theme_val[0]), float(theme_val[1]), float(theme_val[2])
        a = float(theme_val[3]) if len(theme_val) > 3 else 1.0
        return f'rgba({int(r*255)},{int(g*255)},{int(b*255)},{a})'
    return 'gray'


def _format_display_text(rec: Dict[str, Any], theme: Dict[str, Any]) -> str:
    """将单 bar 的展示数据格式化为顶部区单行摘要（备用）。"""
    lines: List[str] = []
    if rec.get('close') is not None:
        lines.append(f"Close: {rec['close']:.2f}")
    lines.append(f"Date: {rec.get('date_str', '')}")
    if rec.get('open') is not None:
        lines.append(f"Open: {rec['open']:.2f}")
    if rec.get('high') is not None:
        lines.append(f"High: {rec['high']:.2f}")
    if rec.get('low') is not None:
        lines.append(f"Low: {rec['low']:.2f}")
    if rec.get('volume') is not None:
        lines.append(f"Vol: {rec['volume']/1e4:.2f} (10k)")
    if rec.get('value') is not None:
        lines.append(f"Value: {rec['value']/1e8:.2f} (100M)")
    if rec.get('last_close') is not None:
        lines.append(f"PrevClose: {rec['last_close']:.2f}")
    if rec.get('pct_change') is not None:
        lines.append(f"Chg: {rec['change']:.3f} [{rec['pct_change']:.2f}%]")
    if rec.get('upper_lim') is not None:
        lines.append(f"UpLim: {rec['upper_lim']:.2f}")
    if rec.get('lower_lim') is not None:
        lines.append(f"DnLim: {rec['lower_lim']:.2f}")
    if rec.get('ma'):
        lines.append("MA: " + ", ".join(f"{k}={v:.2f}" for k, v in rec['ma'].items()))
    return "  |  ".join(lines)


def _bar_data_to_json_serializable(
    bar_data_per_group: List[List[Dict[str, Any]]],
) -> List[List[Dict[str, Any]]]:
    """转为可 JSON 序列化的结构，供前端点击时更新表头。"""
    out: List[List[Dict[str, Any]]] = []
    for group in bar_data_per_group:
        row: List[Dict[str, Any]] = []
        for rec in group:
            r: Dict[str, Any] = {}
            for k, v in rec.items():
                if v is None:
                    r[k] = None
                elif isinstance(v, (np.floating, np.integer)):
                    r[k] = float(v)
                elif isinstance(v, (int, float, str, bool)):
                    r[k] = v
                elif isinstance(v, dict):
                    r[k] = {str(a): float(b) for a, b in v.items()}
                else:
                    r[k] = str(v)
            row.append(r)
        out.append(row)
    return out


def _build_header_html(rec: Dict[str, Any], theme: Dict[str, Any]) -> str:
    """表头价格信息：独立 HTML 片段（英文），七种 ``header_font_*`` 与静态图一致。"""

    def _render_line(segs: List[Tuple[str, HeaderFontRole]]) -> str:
        parts: List[str] = []
        for text, role in segs:
            if not text:
                continue
            st = header_font_span_style(theme, role)
            parts.append(f'<span style="{st}">{html.escape(text)}</span>')
        return ''.join(parts)

    line1_segs, line2_segs = mpl_ohlc_header_segments(rec)
    line1 = _render_line(line1_segs)
    line2 = _render_line(line2_segs)
    fs_base = int(merge_header_font_theme(theme)['header_normal']['size'])
    return (
        f'<div style="line-height:1.4;padding:8px 12px;min-height:78px;'
        f'font-size:{fs_base}px;background:#f8f8f8;border-bottom:1px solid #ddd;">'
        f'<div>{line1}</div><div>{line2}</div></div>'
    )


def _build_top_info_annotations(
    rec: Dict[str, Any],
    theme: Dict[str, Any],
    *,
    y1: Optional[float] = None,
    y2: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    表头：两行 Plotly annotations，与 ``mpl_ohlc_header_segments`` 分段及七种字体一致。

    Parameters
    ----------
    y1, y2 : float, optional
        paper 坐标行位置；FigureWidget 路径应传入 ``_plotly_header_paper_y_from_layout`` 结果。
        未传时使用 theme 中 ``plotly_header_annotation_y1/y2``（非 Widget 兜底）。
    """
    ann: List[Dict[str, Any]] = []
    line1_segs, line2_segs = mpl_ohlc_header_segments(rec)
    if y1 is None:
        y1 = float(theme.get('plotly_header_annotation_y1', 1.115))
    else:
        y1 = float(y1)
    if y2 is None:
        y2 = float(theme.get('plotly_header_annotation_y2', 1.085))
    else:
        y2 = float(y2)
    x0 = 0.02

    def _add_line(segs: List[Tuple[str, HeaderFontRole]], y: float) -> None:
        x = x0
        for text, role in segs:
            if not text:
                continue
            fd = resolve_header_font_plotly(theme, role)
            ann.append(dict(
                x=x, y=y, xref='paper', yref='paper',
                text=text, showarrow=False, xanchor='left', yanchor='top',
                font=fd,
            ))
            x += len(text) * 0.0082 * (float(fd['size']) / 12.0) + 0.002

    _add_line(line1_segs, y1)
    _add_line(line2_segs, y2)
    return ann


def build_interactive_figure_from_specs(
    specs_per_group: Sequence[Sequence[Optional[Dict[str, Any]]]],
    types_info: Sequence[Any],
    x_dates: Optional[Sequence[Any]] = None,
    group_titles: Optional[Sequence[str]] = None,
    theme: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    根据多组规格与类型信息绘制 Plotly 交互式 Figure。
    布局、配色与静态图表一致；顶部预留数据展示区；多组时时间轴同步。
    """
    if not _HAS_PLOTLY:
        raise RuntimeError('plotly is required for interactive rendering. Install with: pip install plotly')

    theme = theme or _get_theme_internal()
    n_groups = len(specs_per_group)
    n_types = len(types_info) if types_info else 0
    if n_types == 0:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=_theme_to_plotly_color(theme.get('figure_facecolor', (0.82, 0.83, 0.85))),
            margin=dict(t=100),
        )
        return fig

    x_dates = x_dates or []
    n = len(x_dates)
    if n == 0 and specs_per_group and specs_per_group[0]:
        for spec in specs_per_group[0]:
            if spec and spec.get('data'):
                d = next(iter(spec['data'].values()), None)
                if d is not None:
                    n = d.shape[-1] if hasattr(d, 'shape') else len(d)
                    break
    if n == 0:
        n = 1
    x_idx = list(range(n))

    from qteasy.hp_visual_render import _to_1d, _format_x_label

    bar_data_per_group = build_bar_display_data(
        specs_per_group, types_info, list(x_dates) if x_dates else x_idx, theme=theme,
    )
    show_ohlc_header = specs_contain_kline(specs_per_group, types_info)
    pk = primary_kline_group_index(specs_per_group, types_info)
    header_rec: Dict[str, Any] = {}
    if show_ohlc_header and pk is not None and bar_data_per_group and pk < len(bar_data_per_group):
        grp = bar_data_per_group[pk]
        if grp:
            header_rec = grp[-1]

    row_off = 1 if (show_ohlc_header and bool(header_rec)) else 0
    layout_spec = compute_hp_visual_layout_spec(
        n_groups,
        n_types,
        types_info,
        theme,
        row_off=row_off,
        show_ohlc_header=show_ohlc_header,
        group_titles=group_titles,
    )

    fig = make_subplots(
        rows=layout_spec['plotly_n_subplot_rows'],
        cols=1,
        shared_xaxes=True,
        vertical_spacing=layout_spec['plotly_vertical_spacing'],
        row_heights=layout_spec['plotly_row_heights'],
        subplot_titles=layout_spec['plotly_subplot_titles'],
    )

    # 主题色
    paper_bg = _theme_to_plotly_color(theme.get('figure_facecolor'))
    plot_bg = _theme_to_plotly_color(theme.get('axes_facecolor'))
    color_up = theme.get('line_color_up', 'red')
    color_dn = theme.get('line_color_down', 'green')

    cst_candle = resolve_candle_style_plotly(theme)
    font_tick = resolve_font_size('plotly', 'axis_tick', theme)
    font_ytitle = resolve_font_size('plotly', 'axis_ylabel', theme)

    row_idx = 0
    for g in range(n_groups):
        gt = (group_titles[g] if group_titles and g < len(group_titles) else '').strip()
        name_prefix = f'{gt} | ' if n_groups > 1 and gt else ''
        for t in range(n_types):
            plot_row = plotly_trace_row_1based(layout_spec, g, t)
            spec = specs_per_group[g][t] if g < len(specs_per_group) and t < len(specs_per_group[g]) else None
            if spec is None:
                continue

            ct = spec.get('chart_type', '')
            data = spec.get('data', {})

            group_custom = [g] * n  # 供点击回调区分 group
            if ct == 'kline' and all(k in data for k in ('open', 'high', 'low', 'close')):
                o = _to_1d(np.asarray(data['open']), 0)[:n]
                h = _to_1d(np.asarray(data['high']), 0)[:n]
                l = _to_1d(np.asarray(data['low']), 0)[:n]
                c = _to_1d(np.asarray(data['close']), 0)[:n]
                fig.add_trace(
                    go.Candlestick(
                        x=x_idx,
                        open=o,
                        high=h,
                        low=l,
                        close=c,
                        increasing_line_color=cst_candle['increasing_line_color'],
                        decreasing_line_color=cst_candle['decreasing_line_color'],
                        increasing_fillcolor=cst_candle['increasing_fillcolor'],
                        decreasing_fillcolor=cst_candle['decreasing_fillcolor'],
                        increasing_line_width=cst_candle['increasing_line_width'],
                        decreasing_line_width=cst_candle['decreasing_line_width'],
                        whiskerwidth=cst_candle['whiskerwidth'],
                        name=f'{name_prefix}Price' if name_prefix else 'Price',
                        legendgroup=f'g{g}',
                        customdata=group_custom,
                    ),
                    row=plot_row,
                    col=1,
                )
                # MA 线
                for key in data:
                    if key in ('open', 'high', 'low', 'close'):
                        continue
                    arr = _to_1d(np.asarray(data[key]), 0)[:n]
                    fig.add_trace(
                        go.Scatter(
                            x=x_idx, y=arr, mode='lines',
                            name=f'{name_prefix}{key}' if name_prefix else key,
                            legendgroup=f'g{g}',
                            line=dict(width=1),
                            customdata=group_custom,
                        ),
                        row=plot_row,
                        col=1,
                    )

            elif ct == 'volume':
                vol_name = next((k for k in ('vol', 'volume') if k in data), next(iter(data), None))
                if vol_name:
                    arr = _to_1d(np.asarray(data[vol_name]), 0)[:n]
                    open_1d = _to_1d(np.asarray(data['open']), 0)[:n] if data.get('open') is not None else None
                    close_1d = _to_1d(np.asarray(data['close']), 0)[:n] if data.get('close') is not None else None
                    if open_1d is not None and close_1d is not None:
                        colors = [color_up if close_1d[i] >= open_1d[i] else color_dn for i in range(n)]
                    else:
                        colors = [theme.get('volume_color', color_dn)] * n
                    fig.add_trace(
                        go.Bar(
                            x=x_idx, y=arr, marker_color=colors,
                            name=f'{name_prefix}Volume' if name_prefix else 'Volume',
                            legendgroup=f'g{g}',
                            showlegend=False,
                            customdata=group_custom,
                        ),
                        row=plot_row,
                        col=1,
                    )

            elif ct == 'macd':
                series_kind = spec.get('series_kind', {})
                for key, y in data.items():
                    y_flat = _to_1d(np.asarray(y), 0)[:n]
                    kind = series_kind.get(key, 'line')
                    if kind == 'bar':
                        colors = [color_up if v >= 0 else color_dn for v in y_flat]
                        fig.add_trace(
                            go.Bar(
                                x=x_idx, y=y_flat, marker_color=colors,
                                name=f'{name_prefix}{key}' if name_prefix else key,
                                legendgroup=f'g{g}',
                                showlegend=False,
                                customdata=group_custom,
                            ),
                            row=plot_row,
                            col=1,
                        )
                    else:
                        fig.add_trace(
                            go.Scatter(
                                x=x_idx, y=y_flat, mode='lines',
                                name=f'{name_prefix}{key}' if name_prefix else key,
                                legendgroup=f'g{g}',
                                line=dict(width=1),
                                customdata=group_custom,
                            ),
                            row=plot_row,
                            col=1,
                        )

            elif ct == 'line':
                for key, y in data.items():
                    y_flat = _to_1d(np.asarray(y), 0)[:n]
                    fig.add_trace(
                        go.Scatter(
                            x=x_idx, y=y_flat, mode='lines',
                            name=f'{name_prefix}{key}' if name_prefix else key,
                            legendgroup=f'g{g}',
                            line=dict(width=1),
                            customdata=group_custom,
                        ),
                        row=plot_row,
                        col=1,
                    )

    last_row = layout_spec['plotly_n_subplot_rows']
    fig_height = max(400, min(900, 200 * last_row))
    fig_width = 1000
    top_margin = layout_spec['plotly_margin_top']
    initial_header_html = _build_header_html(header_rec, theme) if show_ohlc_header else ''
    bar_data_serializable = _bar_data_to_json_serializable(bar_data_per_group)
    n_subplot_titles = last_row
    axis_line = dict(
        showline=True,
        linecolor='#000000',
        linewidth=1,
        mirror=True,
        ticks='outside',
    )
    tick_font_x = dict(size=font_tick, family='Arial')
    tick_font_y = plotly_font_dict(font_tick)
    legend_cfg: Dict[str, Any] = dict(
        orientation='v',
        yanchor='top',
        y=0.99,
        yref='paper',
        xanchor='left',
        x=0.01,
        xref='paper',
        bgcolor='rgba(255,255,255,0.75)',
        bordercolor='#cccccc',
        borderwidth=1,
    )
    if n_groups > 1:
        legend_cfg['tracegroupgap'] = 12
    layout_updates = dict(
        height=fig_height,
        width=fig_width,
        margin=dict(t=top_margin, b=40, l=60, r=16),
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font=dict(size=font_tick, family='Arial'),
        template='none',
        dragmode='pan',
        hovermode='x unified',
        legend=legend_cfg,
    )
    fig.update_layout(**layout_updates)
    # 每组子图左侧 y 轴标签（与静态 set_ylabel 一致）；仅最下方显示 x 轴标签（日期）；Y 轴固定不随拖动
    type_to_ylabel = {'kline': 'Price', 'volume': 'Volume', 'macd': 'macd', 'line': 'Line'}
    max_x_ticks = theme.get('max_x_ticks', 12)
    step = max(1, n // max_x_ticks)
    date_fmt = theme.get('datetime_format', '%y/%m/%d')
    x_tickvals = list(range(0, n, step))
    x_ticktext = (
        [_format_x_label(x_dates[j], date_fmt) for j in x_tickvals]
        if x_dates and len(x_dates) >= n else None
    )
    for i in range(1, last_row + 1):
        xax = 'xaxis' if i == 1 else f'xaxis{i}'
        yax = 'yaxis' if i == 1 else f'yaxis{i}'
        if n_groups > 1:
            type_idx = (i - 1) % (n_types + 1)
            ytitle = '' if type_idx == n_types else type_to_ylabel.get(types_info[type_idx].id, '')
        else:
            ytitle = type_to_ylabel.get(types_info[i - 1].id, '') if i - 1 < len(types_info) else ''
        xax_dict = dict(
            range=[0, max(0, n - 1)],
            showticklabels=(i == last_row),
            rangeslider=dict(visible=False),
            rangeselector=dict(visible=False),
            tickfont=tick_font_x,
            **axis_line,
        )
        if i == last_row and x_ticktext is not None:
            xax_dict['tickmode'] = 'array'
            xax_dict['tickvals'] = x_tickvals
            xax_dict['ticktext'] = x_ticktext
        else:
            xax_dict['dtick'] = step
        fig.update_layout({
            xax: xax_dict,
            yax: dict(
                title=dict(text=ytitle, font=plotly_font_dict(font_ytitle)),
                fixedrange=True,
                tickfont=tick_font_y,
                **axis_line,
            ),
        })

    if fig.layout.annotations:
        ft = resolve_header_font_plotly(theme, 'header_title')
        for ann in fig.layout.annotations:
            txt = getattr(ann, 'text', None)
            if not txt:
                continue
            ann.update(font=dict(ft))

    subplot_ann_count = len(fig.layout.annotations) if fig.layout.annotations else 0

    # 供前端点击更新表头 / FigureWidget 回调更新 annotations 的元数据
    fig._hp_plotly_meta = {
        'bar_data': bar_data_serializable,
        'n_types': n_types,
        'n_groups': n_groups,
        'n_subplot_titles': n_subplot_titles,
        'initial_header_html': initial_header_html,
        'show_ohlc_header': show_ohlc_header,
        'ohlc_header_primary_group': int(pk if pk is not None else 0),
        'header_font_body': resolve_font_size('plotly', 'header_body', theme),
        'header_font_emphasis': resolve_font_size('plotly', 'header_emphasis', theme),
        'header_font_specs': {k: dict(v) for k, v in merge_header_font_theme(theme).items()},
        'subplot_annotation_count': subplot_ann_count,
        'theme': theme,
    }
    return fig
