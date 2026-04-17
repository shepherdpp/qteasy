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

## 2. CLI 方式

### 2.1 Ask 模式

```bash
qteasy-ai ask "list built-in strategies"
```

### 2.2 Plan 模式

```bash
qteasy-ai plan "show kline summary of 000300.SH from 20240101"
```

### 2.3 Run 模式

```bash
qteasy-ai run "export kline 000300.SH to png"
```

执行后可在返回结果中查看 `run_file`，并追溯每个 step 的输入输出。

## 3. Notebook 方式

```python
import qteasy as qt
from qteasy.ai.app import QteasyAssistant

assistant = QteasyAssistant()
plan_payload = assistant.plan("list built-in strategies")
run_payload = assistant.run("export kline of 000300.SH")
```

## 4. 本地记忆文件

默认在项目目录创建：

- `.qteasy/ai/profile.json`
- `.qteasy/ai/env_facts.json`
- `.qteasy/ai/runs/*.json`

其中 runs 文件用于复盘每次 plan 的执行轨迹与产物路径。
