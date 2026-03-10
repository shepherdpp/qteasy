# qteasy 开发共同背景（项目记忆）

本文档作为**项目记忆/共同背景上下文**，供规划与开发时引用，便于在不同 Chat Session 中保持一致性。

---

## 规划与执行的分工

- **高层次规划**（阶段、优先级、范围、新想法与建议）在**规划专用 Chat** 中讨论，结论更新到：
  - [.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md](../.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md)
  - [ROADMAP.md](../ROADMAP.md)
- **具体开发任务**在**独立 Chat Session** 中进行；新 Session 时通过 @ROADMAP.md 与 @展望文件 恢复上下文，再说明本步目标即可。

---

## 参考

- 执行清单与「当前聚焦」：见项目根目录 [ROADMAP.md](../ROADMAP.md)。
- 完整展望与时间表：见 [.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md](../.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md)。

---

## get_history_data 类型解析与 freq/asset_type 选择（开发者摘要）

- **职责分工**：
  - `DataType`：描述数据在数据源中的原生形态（`name`, `freq`, `asset_type`, `table_name`, `column` 等），不等于用户希望看到的输出频率。
  - `get_history_panel`：根据一组 `DataType` 从 `DataSource` 取原始数据，再按用户传入的 `freq` 调用 `_adjust_freq` 升/降频，对齐时间网格，并返回 `HistoryPanel` 或 dict。
  - `get_history_data`：面向用户的入口，负责把 `htype_names/htypes + freq + asset_type + shares` 推断为一组“原生 DataType 列表”，再交给 `get_history_panel`。

- **freq/asset_type 的语义**：
  - 用户传入的 `freq` 被视为**目标输出网格频率**，不会直接限制 `DataType` 的原生 `freq`；例如 `total_mv` 只有日频定义时，`freq='m'` 会通过 `_adjust_freq` 把日频数据升采样到月频。
  - 用户传入的 `asset_type` 只作为“过滤/偏好”信号：开发层面会在 core 里基于它过滤候选 DataType，而不是在 `infer_data_types` 阶段用 `allow_ignore_asset_type=True` 黑盒回退。

- **两阶段解析策略（简述）**：
  - 阶段 1：从 `DATA_TYPE_MAP` 收集每个 `name` 的所有原生 DataType 候选：
    - 调用 `infer_data_types(names=[n], freqs=[target_freq] 或宽频率集合, asset_types=..., allow_ignore_freq=False, allow_ignore_asset_type=False)`；
    - 只接受 MAP 中真实存在的 `(name, freq, asset_type)` 组合，不再退化为 `DataType(name=n_)`。
  - 阶段 2：在 core 层对候选结果做精细筛选：
    - **名称覆盖**：每个输入的 `name` 必须至少保留一个 DataType，否则统一 `warn + ValueError`；
    - **频率唯一化**：使用 `TIME_FREQ_LEVELS`/`parse_freq_string` 为每个 `name` 选定一个“最合适”的原生 `freq`（完全一致 > 更高频中最近 > 更低频中最近），丢弃其它频率；
    - **资产类型过滤**：
      - 显式 `asset_type` 时严格过滤只保留匹配资产类型，否则视为未覆盖；
      - `asset_type=None/'any'` 时，在当前不改 history 层的前提下采用保守优先级（`E > IDX > 其他`）为每个 `name` 选取一个 asset_type 版本，避免 `combine_asset_types=True` 下出现同一 `(name,freq)` 多 asset_type 冲突。

- **典型场景**：
  - `htype_names='total_mv', freq='m', shares=股票`：
    - 原生只存在 `total_mv_d_E/IDX`，阶段 2 会基于 `TIME_FREQ_LEVELS` 选 `d` 作为原生 `freq`，优先选择股票 `E` 版本，再由 `_adjust_freq` 把日频升采样到月频。
  - `htype_names='total_share', freq='d', shares=股票`：
    - 原生存在 `total_share_d_E` 与 `total_share_d_IDX`，阶段 2 会在 asset_type='any' + 股票 shares 的语境下只保留 `total_share_d_E`，避免 history 层看到 E+IDX 两套定义。

开发时如需修改或扩展 DataType 解析逻辑，请同时更新：

- `.cursor/rules/get-history-data-type-resolution.mdc`：记录完整规则与约定；
- `tests/test_core_sub_funcs.py` 中的 `TestGetHistoryDataAPI` 与 `TestGetHistoryDataRealData`，保持高风险类型（如 `total_mv`、`total_share`）的行为回归。
