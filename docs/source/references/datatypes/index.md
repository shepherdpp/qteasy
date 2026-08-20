# 内置 DataType 完整清单

本目录提供 **qteasy 内置历史数据类型（DataType）** 的可浏览完整清单。清单由脚本从 `get_dtype_map()` 生成并提交进仓，与当前代码中的内置映射表一致。

> **请先读概念**：若您还不熟悉「信息 ≠ 数据」、三种形状或四条工作路径，请先阅读 [用稳定的信息 ID 取数（DataType）](../../manage_data/02.%20datatypes.md)。

## 如何读表

每一行对应一种内置 DataType，由 `name` + `freq` + `asset_type` 唯一确定：

| 列 | 含义 |
| --- | --- |
| `name` | 数据类型名称（宽匹配名，如 `close`、`pe`） |
| `freq` | 原生频率（如 `d` / `w` / `m` / `q` / `1min`；`None` 表示与频率无关） |
| `asset_type` | 资产类型（`E` 股票、`IDX` 指数、`FD` 基金、`FT` 期货、`OPT` 期权、`None` / `Any` 等） |
| `description` | 中文用途简述 |
| `table_name` | 底层数据表（来自映射 kwargs；部分类型可能为空或多表逻辑） |
| `kind` | 消费形状：`history`（时间×标的）/ `reference`（仅时间）/ `static`（仅标的） |
| `usable_in` | 推荐入口标记（可多选）：`history_panel`、`reference_api`、`static_api`、`strategy`、`universe`；`none` 表示暂无一等用法 |
| `acquisition_type` | 内部获取方式分册（直读、复权、事件等，不是用户主分类） |

日常多数场景只需给出 `name`。请按 `kind` / `usable_in` 选择入口：History 用 `get_history_data` / `get_kline`；不要假定清单里的每一条都能编进 HistoryPanel。需要精确匹配或排查时，请对照本清单中的三元组。

## 推荐检索方式

完整表很长（一千余条），浏览前建议先用 API 缩小范围：

```python
import qteasy as qt

# 按名称 / 中文描述 / 通配符查找
qt.find_history_data('pe')
qt.find_history_data('每股收益')
qt.find_history_data('ep*', fuzzy=True)

# 结构化结果
df = qt.find_history_data('close', as_data_frame=True)
print(df.head())
```

也可用 `qteasy.datatypes.get_dtype_map()` 在交互环境中自行筛选。API 签名见 [DataType API](../../api/data_types.rst)。

## 分册索引（生成物）

> **勿手改** [`_generated/`](_generated/) 下的文件。更新内置类型或发文档前请重跑：
>
> `/opt/anaconda3/envs/py39/bin/python docs/scripts/generate_datatype_catalog.py`

- [分册统计与链接（catalog_index）](_generated/catalog_index.md)

按获取方式打开分册：

- [直读（direct）](_generated/direct.md)
- [基本信息（basics）](_generated/basics.md)
- [复权 / 修正（adjustment）](_generated/adjustment.md)
- [引用型（reference）](_generated/reference.md)
- [筛选型（selection）](_generated/selection.md)
- [成份（composition）](_generated/composition.md)
- [分类（category）](_generated/category.md)
- [事件信号（event_signal）](_generated/event_signal.md)
- [事件状态（event_status）](_generated/event_status.md)
- [多事件状态（event_multi_stat）](_generated/event_multi_stat.md)
- [选定事件（selected_events）](_generated/selected_events.md)

## 相关链接

- 概念与精选表：[manage_data · DataType](../../manage_data/02.%20datatypes.md)
- 取数 API：[get_history_data](../../api/history_data.rst)
- 数据表（存储层，≠ DataType）：[数据表章节](../../manage_data/04.%20data_tables_10.md)
