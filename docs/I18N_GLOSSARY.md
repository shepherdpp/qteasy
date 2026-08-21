# qteasy 文档翻译术语表（v1.0 冻结）

本文档为 Sphinx 国际化（i18n）翻译的**术语约束**。**Phase 1（英文 100%）已于 2026-05-23 冻结**；de/fr/es/zh_TW/ja 翻译须遵循本表。  
源语言：`zh_CN`（[`docs/source/`](source/)）；翻译文件：[`docs/source/locale/`](source/locale/)。

---

## 1. 品牌与产品名（不翻译）

| 术语 | 规则 |
|------|------|
| `qteasy` / `QTEASY` | 保持原样；句首描述可用 ``QTEASY`` |
| `Python`、`pip`、`NumPy`、`Numba`、`pandas` | 保持原样 |
| `GitHub`、`Read the Docs` | 保持原样 |

---

## 2. 核心类与模块名（英文保留，正文可加解释）

翻译时**保留英文类名/函数名**，首次出现可加括号说明，后续不重复解释。

| 英文 | 中文源文档常用说法 | 英文翻译说明 |
|------|-------------------|--------------|
| `Operator` | 交易员 | trader / operator object |
| `HistoryPanel` | 历史数据面板 | keep `HistoryPanel` |
| `DataType` | 数据类型 | keep `DataType` |
| `DataSource` | 数据源 | keep `DataSource` |
| `BaseStrategy` | 基础策略类 | keep `BaseStrategy` |
| `Backtester` | 回测器 | keep `Backtester` |
| `Trader` | 交易员（实盘） | keep `Trader`; disambiguate from `Operator` in live-trading chapters |
| `Broker` / `BrokerFacade` | 券商 / 适配层 | keep English names in API docs |
| `RiskManager` | 风控管理器 | keep `RiskManager` |

---

## 3. 交易信号类型（PT / PS / VS）

| 缩写 | 中文 | 英文推荐译法 |
|------|------|--------------|
| PT | 目标仓位 / Position Target | Position Target (PT) |
| PS | 比例信号 / Proportional Signal | Proportional Signal (PS) |
| VS | 数值信号 / Value Signal | Value Signal (VS) |

规则：缩写与英文全称在首次出现时可并列；技术章节以英文缩写为准，与代码一致。

---

## 4. 通用金融与量化术语

| 中文 | English | Deutsch | Français | Español |
|------|---------|---------|----------|---------|
| 回测 | backtest | Backtest | backtest | backtest |
| 实盘 / 模拟实盘 | live trading / simulated live trading | Live-Handel | trading en direct | trading en vivo |
| 策略 | strategy | Strategie | stratégie | estrategia |
| 持仓 | position | Position | position | posición |
| 资产池 | asset pool | Asset-Pool | pool d'actifs | pool de activos |
| 复权 | adjustment (price adjustment) | Anpassung | ajustement | ajuste |
| 未来函数 | look-ahead bias / future function | Look-ahead-Bias | biais de look-ahead | sesgo de look-ahead |
| 交割 | delivery / settlement | Lieferung | livraison | entrega |
| 滑点 | slippage | Slippage | slippage | deslizamiento |
| 优化 | optimization | Optimierung | optimisation | optimización |

繁中（zh_TW）与日语（ja）在 Phase 3 单独补充列。

**台湾用语（zh_TW）**：OpenCC `s2t` 只解决字形；语义词见知识库  
[`knowledge/domain/i18n-zh-tw-taiwan-terms.md`](../knowledge/domain/i18n-zh-tw-taiwan-terms.md)  
与机读表 [`docs/scripts/zh_tw_taiwan_terms.py`](scripts/zh_tw_taiwan_terms.py)（例：軟件→軟體、內存→記憶體、數據庫→資料庫、默認→預設）。

---

## 5. `manage_data` 数据表字段

[`manage_data/04`–`09. data_tables_*.md`](source/manage_data/) 含大量 **英文字段名**（如 `ocf_to_shortdebt`、`total_mv`）。

**规则：**

- `msgid` 中的字段名：**不翻译**，`msgstr` 中同样保留英文字段名。
- 只翻译字段周围的**中文描述、表头说明、章节引导语**。
- 同一字段在多表重复出现时，保持译法一致；可在 Poedit 翻译记忆中复用。

---

## 6. 文档内链（Read the Docs URL）

`msgstr` 中的文档链接应指向**目标语言**路径，避免读者被导向简体中文版。

| 语言 | RTD 路径前缀 | 示例 |
|------|--------------|------|
| zh_CN（源） | `/zh-cn/latest/` | `https://qteasy.readthedocs.io/zh-cn/latest/faq.html` |
| en | `/en/latest/` | `https://qteasy.readthedocs.io/en/latest/faq.html` |
| de | `/de/latest/` | … |
| fr | `/fr/latest/` | … |
| es | `/es/latest/` | … |
| zh_TW | `/zh-tw/latest/` | … |
| ja | `/ja/latest/` | … |

替换时保留 URL 路径中 `.md` 转换后的 HTML 路径及锚点。

---

## 7. 代码与格式约束

- **不翻译**：代码块、CLI 命令、配置键名（如 `sys_log_file_path`）、JSON/YAML 示例。
- **保留**：Markdown 围栏、RST 指令、Mermaid 语法结构；只翻译其中的自然语言标签。
- **API autodoc**：参数名、类型名保持英文；docstring 已随源码语言处理，翻译 po 时勿改动 `:param:` 等指令结构。

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-23 | Phase 0 草稿，供 en 补译与后续语言 pivot 使用 |
| v1.0 | 2026-05-23 | Phase 1 完成：en 113 个 `.po`、10,790 条 msg 全部已译；术语与 RTD 内链规则冻结 |
| v1.0-de | 2026-05-23 | Phase 2 de 首轮：en→de 机翻 pivot + 手工补译；德文内链 `/de/latest/` |
