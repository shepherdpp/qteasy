# Tutorial 09 - qteasy AI shell 快速上手

本教程展示 S1.4 阶段A的最小闭环：plan 生成、确认执行、结构化结果查看。

## 1. 准备环境

```bash
pip install -e .[dev]
```

可选 Provider 配置：

```bash
export QTEASY_AI_MODEL="gpt-4o-mini"
export QTEASY_AI_API_KEY="your_api_key"
export QTEASY_AI_BASE_URL="https://api.openai.com/v1"
```

也可以直接查看 qteasy 全局 AI 配置：

```python
import qteasy as qt
print(qt.configuration(["ai_model", "ai_base_url", "ai_timeout", "ai_home"]))
```

## 2. CLI 方式

### 2.1 Ask 模式

```bash
qteasy-ai ask "list built-in strategies"
```

### 2.2 Plan 模式

```bash
qteasy-ai plan "show kline summary of 000300.SH from 20240101"
qteasy-ai plan "show kline summary of 000300.SH from 20240101" --pretty
qteasy-ai plan "show kline summary of 000300.SH from 20240101" --raw
```

### 2.3 Run 模式

```bash
qteasy-ai run "export kline 000300.SH to png"
```

执行后可在返回结果中查看 `run_file`，并追溯每个 step 的输入输出。

### 2.4 Provider 配置诊断

```bash
qteasy-ai provider-check
```

输出会包含 `mode/model/base_url/timeout/api_key_present/config_sources`，用于快速确认当前是规则模式、云端模型还是本地模型。

## 3. Notebook 方式

```python
import qteasy as qt
from qteasy.ai.app import QteasyAssistant

assistant = QteasyAssistant()
plan_output = assistant.plan("list built-in strategies")  # 默认 user_friendly
run_output = assistant.run("export kline of 000300.SH", keep=True)
raw_plan = assistant.plan("list built-in strategies", response_style="raw", persist="none")
debug_payload = assistant.debug_config()
```

其中 `debug_payload` 可用于核对当前配置来源与模式，不包含明文 API key。
`plan_output` / `run_output` 默认包含 `narrative/python_code/result_preview/raw` 四段信息。
如需完全兼容旧版结构化输出，使用 `response_style="raw"`。

### 3.1 Classic Notebook 魔法命令（无需 ipywidgets）

在 Classic Notebook 中可直接加载扩展，用“只写 prompt”的方式交互：

```python
%load_ext qteasy.ai.notebook_magic
```

Plan（默认）：

```python
%%qtai --mode plan
列出所有内置策略，并告诉我 macd 策略参数
```

Ask（纯只读）：

```python
%%qtai --mode ask
解释一下 PT/PS/VS 信号语义差异
```

Run（先 plan，后 confirm）：

```python
%%qtai --mode run
列出所有内置策略
```

输出会给出确认指令，再在下一个 cell 执行：

```python
%%qtai --confirm <plan_id>
Execute.
```

可选参数：

- `--raw`：返回原始结构化输出
- `--persist {bounded,audit,none}`：覆盖本次留存策略
- `--keep`：将本次 run 标记为保留

对于尚未实现的能力（例如下载/回测/优化/策略生成等），当前阶段会返回结构化回退结果，
`payload.fallback_action` 可能为：

- `plan_only`
- `not_supported_yet`
- `clarify_required`

## 4. 本地记忆文件

默认在项目目录创建：

- `.qteasy/ai/profile.json`
- `.qteasy/ai/env_facts.json`
- `.qteasy/ai/runs/*.json`
- `.qteasy/ai/pinned/*.json`

其中 runs 文件用于复盘每次 plan 的执行轨迹与产物路径，默认采用有界留存（bounded）并自动清理；
用户显式保留的记录会写入 `pinned/`，不参与自动清理。

## 5. 语料回归入口（可选）

- 语料文件：`tests/ai_corpus/*.json`
- 人工记录模板：`tests/ai_corpus/manual_record_template.md`
- 执行脚本：`python tests/run_ai_manual_corpus.py`
