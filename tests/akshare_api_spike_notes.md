# AKShare API Spike 备忘（S3.2b）

日期：2026-06-01

## fund_etf_hist_em

- 签名含 `period: str = 'daily'`，与 `stock_zh_a_hist` 一致，代码层按 `daily/weekly/monthly` 实现 `fund_weekly` / `fund_monthly`。
- 联网验证受环境代理影响可能失败；离线以签名为准。

## index_zh_a_hist

- 支持 `period` 为 `daily/weekly/monthly`；`index_weekly` / `index_monthly` 已挂接 `AKSHARE_API_MAP`。

## 指数分钟频

- 存在 `index_zh_a_hist_min_em`；与股票 `stock_zh_a_hist_min_em` 分离，**未纳入本批**，需单独 spike 后再做 `index_1min` 等表。
