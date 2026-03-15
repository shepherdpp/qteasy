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

from typing import Any, Dict, List, Optional, Sequence

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False


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
        if meta and meta.get('initial_header_html'):
            fig_for_html = go.Figure(self._figure)
            fig_for_html.update_layout(title=None, annotations=[])
        html = fig_for_html.to_html(
            include_plotlyjs='cdn',
            config=config,
            full_html=False,
            div_id=div_id,
        )
        # 表头置于画布最上方（独立 div），避免与第一组图表重叠
        header_style = (
            'min-height:52px;line-height:1.4;padding:6px 10px;font-size:11px;'
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
        '  function buildHeaderHTML(rec) {\n'
        '    var c = rec.change, colorMain = (c != null) ? (c > 0 ? "red" : (c < 0 ? "green" : "black")) : "black";\n'
        '    var lowColor = (c != null && c < 0) ? "green" : "black";\n'
        '    var p1 = [];\n'
        '    p1.push(span("开/收: ", "black"));\n'
        '    if (rec.open != null && rec.close != null) p1.push(span(rec.open.toFixed(2)+" / "+rec.close.toFixed(2), colorMain, 16));\n'
        '    p1.push(" &nbsp; "); p1.push(span("高: ", "black"));\n'
        '    if (rec.high != null) p1.push(span(rec.high.toFixed(3), colorMain));\n'
        '    p1.push(" &nbsp; "); p1.push(span("量(万手): ", "black"));\n'
        '    if (rec.volume != null) p1.push(span((rec.volume/1e4).toFixed(3), "black"));\n'
        '    p1.push(" &nbsp; "); p1.push(span("涨停: ", "black"));\n'
        '    if (rec.upper_lim != null) p1.push(span(rec.upper_lim.toFixed(3), "red"));\n'
        '    p1.push(" &nbsp; "); p1.push(span("均价: ", "black"));\n'
        '    if (rec.ma && Object.keys(rec.ma).length) p1.push(span(parseFloat(rec.ma[Object.keys(rec.ma)[0]]).toFixed(3), "black"));\n'
        '    var p2 = [];\n'
        '    p2.push(span(rec.date_str || "", "black"));\n'
        '    if (rec.change != null) { p2.push(" &nbsp; "); p2.push(span(rec.change.toFixed(3), colorMain)); }\n'
        '    if (rec.pct_change != null) p2.push(span(" ["+rec.pct_change.toFixed(3)+"%]", colorMain));\n'
        '    p2.push(" &nbsp; "); p2.push(span("低: ", "black"));\n'
        '    if (rec.low != null) p2.push(span(rec.low.toFixed(3), lowColor));\n'
        '    p2.push(" &nbsp; "); p2.push(span("额(亿元): ", "black"));\n'
        '    if (rec.value != null) p2.push(span((rec.value/1e8).toFixed(3), "black"));\n'
        '    p2.push(" &nbsp; "); p2.push(span("跌停: ", "black"));\n'
        '    if (rec.lower_lim != null) p2.push(span(rec.lower_lim.toFixed(3), "green"));\n'
        '    p2.push(" &nbsp; "); p2.push(span("昨收: ", "black"));\n'
        '    if (rec.last_close != null) p2.push(span(rec.last_close.toFixed(3), "black"));\n'
        '    return "<div style=\'line-height:1.4;padding:6px 10px;font-size:11px;background:#f8f8f8;border-bottom:1px solid #ddd\'><div>"+p1.join("")+"</div><div>"+p2.join("")+"</div></div>";\n'
        '  }\n'
        '  function attach() {\n'
        '    var gd = document.getElementById(divId);\n'
        '    if (!gd || !gd.data) { setTimeout(attach, 80); return; }\n'
        '    var meta = window["HP_PLOTLY_META_" + divId]; if (!meta) return;\n'
        '    var nt = meta.n_types, ng = meta.n_groups || 1;\n'
        '    var hdr = document.getElementById("hp-header-" + divId);\n'
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
        '      if (hdr) hdr.innerHTML = buildHeaderHTML(rec);\n'
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
    first_bar_rec = bar_data[0][0]
    try:
        fw = FigureWidget(fig.data, fig.layout)
        fw._hp_plotly_meta = meta
        fw._hp_updating_y = False
    except Exception:
        return fig

    # 表头：用 annotations 显示首条 bar，与包装器两行风格一致
    fw.update_layout(annotations=_build_top_info_annotations(first_bar_rec, theme))

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
                dates = bar_data[0] if bar_data and bar_data[0] else []
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
            new_annotations = _build_top_info_annotations(rec, theme)
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


def _build_bar_display_data(
    specs_per_group: Sequence[Sequence[Optional[Dict[str, Any]]]],
    types_info: Sequence[Any],
    x_dates: Sequence[Any],
) -> List[List[Dict[str, Any]]]:
    """
    为每组、每个时间索引构建顶部展示区所需的数据。
    仅包含：close（突出）、date/time、open、high、low、volume、value、last_close、pct_change、upper_lim、lower_lim、MA。
    """
    from qteasy.hp_visual_render import _to_1d, _format_x_label

    theme = _get_theme_internal()
    fmt = theme.get('datetime_format', '%y/%m/%d')
    out: List[List[Dict[str, Any]]] = []
    n = len(x_dates) if x_dates else 0
    if n == 0:
        return out

    for g, row in enumerate(specs_per_group):
        group_data: List[Dict[str, Any]] = []
        kline_spec = next((row[i] for i, t in enumerate(types_info) if t.id == 'kline' and row[i] is not None), None)
        vol_spec = next((row[i] for i, t in enumerate(types_info) if t.id == 'volume' and row[i] is not None), None)

        o = h = l = c = None
        vol = None
        ma_dict: Dict[str, np.ndarray] = {}

        if kline_spec:
            data = kline_spec.get('data', {})
            for key in ('open', 'high', 'low', 'close'):
                if key in data:
                    arr = _to_1d(np.asarray(data[key]), 0)
                    if key == 'open':
                        o = arr[:n]
                    elif key == 'high':
                        h = arr[:n]
                    elif key == 'low':
                        l = arr[:n]
                    else:
                        c = arr[:n]
            for key in data:
                if key in ('open', 'high', 'low', 'close'):
                    continue
                if key.startswith('ma_') or key.startswith('sma_') or key.startswith('ema_'):
                    ma_dict[key] = _to_1d(np.asarray(data[key]), 0)[:n]

        if vol_spec:
            data = vol_spec.get('data', {})
            vol_name = next((k for k in ('vol', 'volume') if k in data), None)
            if vol_name:
                vol = _to_1d(np.asarray(data[vol_name]), 0)[:n]

        close_ary = c if c is not None else np.full(n, np.nan)
        last_close = np.roll(close_ary, 1)
        last_close[0] = np.nan

        for i in range(n):
            rec: Dict[str, Any] = {
                'date_str': _format_x_label(x_dates[i], fmt) if i < len(x_dates) else '',
                'close': float(close_ary[i]) if np.isfinite(close_ary[i]) else None,
                'open': float(o[i]) if o is not None and np.isfinite(o[i]) else None,
                'high': float(h[i]) if h is not None and np.isfinite(h[i]) else None,
                'low': float(l[i]) if l is not None and np.isfinite(l[i]) else None,
            }
            if vol is not None and np.isfinite(vol[i]):
                rec['volume'] = float(vol[i])
                rec['value'] = float(vol[i] * close_ary[i]) if np.isfinite(close_ary[i]) else None
            else:
                rec['volume'] = None
                rec['value'] = None

            lc = last_close[i]
            if np.isfinite(lc) and lc != 0:
                rec['last_close'] = float(lc)
                chg = close_ary[i] - lc
                rec['change'] = float(chg)
                rec['pct_change'] = float(chg / lc * 100)
                rec['upper_lim'] = float(lc * 1.1)
                rec['lower_lim'] = float(lc * 0.9)
            else:
                rec['last_close'] = None
                rec['change'] = None
                rec['pct_change'] = None
                rec['upper_lim'] = None
                rec['lower_lim'] = None

            rec['ma'] = {k: float(ma_dict[k][i]) for k in ma_dict if np.isfinite(ma_dict[k][i])}
            group_data.append(rec)
        out.append(group_data)
    return out


def _get_theme_internal() -> Dict[str, Any]:
    """从静态渲染层获取主题，保证与静态图表一致。"""
    from qteasy.hp_visual_render import _get_theme
    return _get_theme()


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
    """表头价格信息：生成独立 HTML 片段，置于画布最顶部（第一组图表上方），避免与绘图区重叠。"""
    change = rec.get('change')
    if change is not None:
        color_main = 'red' if change > 0 else ('green' if change < 0 else 'black')
    else:
        color_main = 'black'
    low_color = 'green' if (change or 0) < 0 else 'black'

    def span(t: str, c: str = 'black', fs: int = 11) -> str:
        return f'<span style="color:{c};font-size:{fs}px">{t}</span>'

    parts: List[str] = []
    # 第一行：开/收、高、量、涨停、均价
    parts.append(span('开/收: ', 'black'))
    o, c = rec.get('open'), rec.get('close')
    if o is not None and c is not None:
        parts.append(span(f'{o:.2f} / {c:.2f}', color_main, 16))
    parts.append(' &nbsp; ')
    parts.append(span('高: ', 'black'))
    if rec.get('high') is not None:
        parts.append(span(f'{rec["high"]:.3f}', color_main))
    parts.append(' &nbsp; ')
    parts.append(span('量(万手): ', 'black'))
    if rec.get('volume') is not None:
        parts.append(span(f'{rec["volume"]/1e4:.3f}', 'black'))
    parts.append(' &nbsp; ')
    parts.append(span('涨停: ', 'black'))
    if rec.get('upper_lim') is not None:
        parts.append(span(f'{rec["upper_lim"]:.3f}', 'red'))
    parts.append(' &nbsp; ')
    parts.append(span('均价: ', 'black'))
    if rec.get('ma'):
        vals = list(rec['ma'].values())
        parts.append(span(f'{vals[0]:.3f}', 'black') if vals else '')
    line1 = ''.join(parts)
    parts = []
    # 第二行：日期、涨跌、低、额、跌停、昨收
    parts.append(span(str(rec.get('date_str', '')), 'black'))
    if rec.get('change') is not None:
        parts.append(' &nbsp; ')
        parts.append(span(f'{rec["change"]:.3f}', color_main))
    if rec.get('pct_change') is not None:
        parts.append(span(f' [{rec["pct_change"]:.3f}%]', color_main))
    parts.append(' &nbsp; ')
    parts.append(span('低: ', 'black'))
    if rec.get('low') is not None:
        parts.append(span(f'{rec["low"]:.3f}', low_color))
    parts.append(' &nbsp; ')
    parts.append(span('额(亿元): ', 'black'))
    if rec.get('value') is not None:
        parts.append(span(f'{rec["value"]/1e8:.3f}', 'black'))
    parts.append(' &nbsp; ')
    parts.append(span('跌停: ', 'black'))
    if rec.get('lower_lim') is not None:
        parts.append(span(f'{rec["lower_lim"]:.3f}', 'green'))
    parts.append(' &nbsp; ')
    parts.append(span('昨收: ', 'black'))
    if rec.get('last_close') is not None:
        parts.append(span(f'{rec["last_close"]:.3f}', 'black'))
    line2 = ''.join(parts)
    return (
        '<div style="line-height:1.4;padding:6px 10px;font-size:11px;background:#f8f8f8;border-bottom:1px solid #ddd;">'
        f'<div>{line1}</div><div>{line2}</div></div>'
    )


def _build_top_info_annotations(rec: Dict[str, Any], theme: Dict[str, Any]) -> List[Dict[str, Any]]:
    """表头价格信息：两行 Plotly annotations，开/收大号 16px 且与 bar 同色，其余 11px；供官方 renderer 与点击更新。"""
    ann: List[Dict[str, Any]] = []
    # 与组名（title_font_size=12）近似或稍小：正文 11，开/收 突出 16
    font_norm = 11
    font_open_close = 16
    change = rec.get('change')
    if change is not None:
        color_main = 'red' if change > 0 else ('green' if change < 0 else 'black')
    else:
        color_main = 'black'

    def _ann(x: float, y: float, text: str, font_size: int = font_norm, color: str = 'black') -> None:
        ann.append(dict(
            x=x, y=y, xref='paper', yref='paper',
            text=text, showarrow=False, xanchor='left', yanchor='top',
            font=dict(size=font_size, color=color),
        ))

    # 整张画布最顶部，略高于第一组名称（paper y>1 可以利用上边距区域）
    y1, y2 = 1.06, 1.03
    _ann(0.02, y1, '开/收: ', font_norm, 'black')
    o, c = rec.get('open'), rec.get('close')
    if o is not None and c is not None:
        _ann(0.08, y1, f'{o:.2f} / {c:.2f}', font_open_close, color_main)
    if rec.get('change') is not None:
        _ann(0.08, y2, f'{rec["change"]:.3f}', font_norm, color_main)
    if rec.get('pct_change') is not None:
        _ann(0.16, y2, f'[{rec["pct_change"]:.3f}%]', font_norm, color_main)
    _ann(0.02, y2, str(rec.get('date_str', '')), font_norm, 'black')
    _ann(0.28, y1, '高: ', font_norm, 'black')
    if rec.get('high') is not None:
        _ann(0.32, y1, f'{rec["high"]:.3f}', font_norm, color_main)
    _ann(0.28, y2, '低: ', font_norm, 'black')
    if rec.get('low') is not None:
        _ann(0.32, y2, f'{rec["low"]:.3f}', font_norm, 'green' if (change or 0) < 0 else 'black')
    _ann(0.45, y1, '量(万手): ', font_norm, 'black')
    if rec.get('volume') is not None:
        _ann(0.55, y1, f'{rec["volume"]/1e4:.3f}', font_norm, 'black')
    _ann(0.45, y2, '额(亿元): ', font_norm, 'black')
    if rec.get('value') is not None:
        _ann(0.55, y2, f'{rec["value"]/1e8:.3f}', font_norm, 'black')
    _ann(0.62, y1, '涨停: ', font_norm, 'black')
    if rec.get('upper_lim') is not None:
        _ann(0.68, y1, f'{rec["upper_lim"]:.3f}', font_norm, 'red')
    _ann(0.62, y2, '跌停: ', font_norm, 'black')
    if rec.get('lower_lim') is not None:
        _ann(0.68, y2, f'{rec["lower_lim"]:.3f}', font_norm, 'green')
    _ann(0.78, y1, '均价: ', font_norm, 'black')
    if rec.get('ma'):
        vals = list(rec['ma'].values())
        _ann(0.84, y1, f'{vals[0]:.3f}' if vals else '', font_norm, 'black')
    _ann(0.78, y2, '昨收: ', font_norm, 'black')
    if rec.get('last_close') is not None:
        _ann(0.84, y2, f'{rec["last_close"]:.3f}', font_norm, 'black')
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
            margin=dict(t=80),
        )
        return fig

    # 高度比例与静态一致
    type_ratios = []
    for info in types_info:
        imp = getattr(info, 'importance', 'secondary')
        type_ratios.append(2.0 if imp == 'main' else 0.5)
    has_main = any(getattr(t, 'importance', '') == 'main' for t in types_info)
    has_secondary = any(getattr(t, 'importance', '') == 'secondary' for t in types_info)
    if not (has_main and has_secondary):
        type_ratios = [1.0] * n_types

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

    # 多组：垂直堆叠 + 组间 spacer
    if n_groups > 1:
        spacer = 0.4
        row_heights_list: List[float] = []
        for g in range(n_groups):
            row_heights_list.extend(type_ratios)
            if g < n_groups - 1:
                row_heights_list.append(spacer)
        n_rows_total = len(row_heights_list)
        subplot_titles_list: List[str] = []
        for g in range(n_groups):
            for t in range(n_types):
                subplot_titles_list.append(group_titles[g] if t == 0 and group_titles and g < len(group_titles) else '')
            if g < n_groups - 1:
                subplot_titles_list.append('')
        fig = make_subplots(
            rows=n_rows_total,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0,
            row_heights=row_heights_list,
            subplot_titles=subplot_titles_list,
        )
    else:
        subplot_titles_list = [
            (group_titles[0] if group_titles else '') if t == 0 else ''
            for t in range(n_types)
        ]
        fig = make_subplots(
            rows=n_types,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0,
            row_heights=type_ratios,
            subplot_titles=subplot_titles_list,
        )
        n_rows_total = n_types

    # 主题色
    paper_bg = _theme_to_plotly_color(theme.get('figure_facecolor'))
    plot_bg = _theme_to_plotly_color(theme.get('axes_facecolor'))
    color_up = theme.get('line_color_up', 'red')
    color_dn = theme.get('line_color_down', 'green')
    font_size = theme.get('font_size', 10)
    title_font_size = theme.get('title_font_size', 12)

    from qteasy.hp_visual_render import _to_1d, _format_x_label

    bar_data_per_group = _build_bar_display_data(specs_per_group, types_info, list(x_dates) if x_dates else x_idx)
    first_bar_rec = bar_data_per_group[0][0] if bar_data_per_group and bar_data_per_group[0] else {}

    row_idx = 0
    for g in range(n_groups):
        for t, info in enumerate(types_info):
            if n_groups > 1:
                r = g * (n_types + 1) + t
            else:
                r = t
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
                        increasing_line_color=color_up,
                        decreasing_line_color=color_dn,
                        name='Price',
                        customdata=group_custom,
                    ),
                    row=r + 1,
                    col=1,
                )
                # MA 线
                for key in data:
                    if key in ('open', 'high', 'low', 'close'):
                        continue
                    arr = _to_1d(np.asarray(data[key]), 0)[:n]
                    fig.add_trace(
                        go.Scatter(
                            x=x_idx, y=arr, mode='lines', name=key, line=dict(width=1),
                            customdata=group_custom,
                        ),
                        row=r + 1,
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
                            x=x_idx, y=arr, marker_color=colors, name='Volume', showlegend=False,
                            customdata=group_custom,
                        ),
                        row=r + 1,
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
                                x=x_idx, y=y_flat, marker_color=colors, name=key, showlegend=False,
                                customdata=group_custom,
                            ),
                            row=r + 1,
                            col=1,
                        )
                    else:
                        fig.add_trace(
                            go.Scatter(
                                x=x_idx, y=y_flat, mode='lines', name=key, line=dict(width=1),
                                customdata=group_custom,
                            ),
                            row=r + 1,
                            col=1,
                        )

            elif ct == 'line':
                for key, y in data.items():
                    y_flat = _to_1d(np.asarray(y), 0)[:n]
                    fig.add_trace(
                        go.Scatter(
                            x=x_idx, y=y_flat, mode='lines', name=key, line=dict(width=1),
                            customdata=group_custom,
                        ),
                        row=r + 1,
                        col=1,
                    )

            row_idx = r

    last_row = n_rows_total
    fig_height = max(400, min(900, 200 * last_row))
    fig_width = 1000
    # 表头仅由包装器顶部 div 显示，figure 内不画 annotations 避免与图表重叠
    top_margin = 80
    initial_header_html = _build_header_html(first_bar_rec, theme)
    bar_data_serializable = _bar_data_to_json_serializable(bar_data_per_group)
    n_subplot_titles = last_row
    axis_common = dict(
        showline=True,
        linecolor='#000000',
        linewidth=1,
        mirror=True,
        ticks='outside',
        tickfont=dict(size=font_size),
    )
    layout_updates = dict(
        height=fig_height,
        width=fig_width,
        margin=dict(t=top_margin, b=40, l=60, r=40),
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font=dict(size=font_size),
        template='none',
        dragmode='pan',
        hovermode='x unified',
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
            **axis_common,
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
                title=dict(text=ytitle, font=dict(size=font_size)),
                fixedrange=True,
                **axis_common,
            ),
        })

    # 供前端点击更新表头 / FigureWidget 回调更新 annotations 的元数据
    fig._hp_plotly_meta = {
        'bar_data': bar_data_serializable,
        'n_types': n_types,
        'n_groups': n_groups,
        'n_subplot_titles': n_subplot_titles,
        'initial_header_html': initial_header_html,
        'theme': theme,
    }
    return fig
