# 内置 DataType 完整清单

本目录提供 **qteasy 内置数据类型（DataType）** 的可浏览完整清单。清单由脚本从 `get_dtype_map()` 生成并提交进仓，与当前代码中的内置映射表一致。

> **请先读概念**：若您还不熟悉「信息 ≠ 数据」、三种形状或四条工作路径，请先阅读 [用稳定的信息 ID 取数（DataType）](../../manage_data/02.%20datatypes.md)。

## 如何读表

每一行对应一种内置 DataType，由 `name` + `freq` + `asset_type` 唯一确定。分册按**业务类别**组织，而不是按内部提取算法。

| 列 | 含义 |
| --- | --- |
| `name` | 数据类型名称（宽匹配名，如 `close`、`pe`） |
| `freq` | 原生频率（如 `d` / `w` / `m` / `q` / `1min`；`None` 表示与频率无关） |
| `asset_type` | 资产类型（`E` 股票、`IDX` 指数、`FD` 基金、`FT` 期货、`OPT` 期权、`None` / `Any` 等） |
| `description` | 中文用途简述 |
| `kind` | 消费形状：`history`（时间×标的）/ `reference`（仅时间）/ `static`（仅标的） |
| `usable_in` | 推荐入口标记（可多选）：`history_panel`、`reference_api`、`static_api`、`strategy`、`universe`；`none` 表示暂无一等用法 |
| `acquisition_type` | 内部获取方式（直读、复权、事件等），**仅供对照 refill，不是用户主分类** |
| `table_name` | 底层数据表（来自映射 kwargs；部分类型可能为空或多表逻辑） |

日常多数场景只需给出 `name`；需要消歧时改用完整 id（如 `close_E_d`）。请按 `kind` / `usable_in` 选择入口：History 用 `get_history_data` / `get_kline`；不要假定清单里的每一条都能编进 HistoryPanel。需要精确匹配或排查时，请对照本清单中的三元组。

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

按业务打开分册：

- [行情与复权](_generated/quotes.md)
- [估值与财务](_generated/valuation.md)
- [宏观、利率与资金](_generated/macro.md)
- [交易行为与事件](_generated/events.md)
- [指数成分与权重](_generated/composition.md)
- [静态证券信息](_generated/static.md)

## 相关链接

- 概念与精选表：[manage_data · DataType](../../manage_data/02.%20datatypes.md)
- 取数 API：[get_history_data](../../api/history_data.rst)
- 数据表（存储层，≠ DataType）：[数据表章节](../../manage_data/04.%20data_tables_10.md)
