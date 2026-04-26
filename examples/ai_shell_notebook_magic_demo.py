# coding=utf-8
# ======================================
# File: ai_shell_notebook_magic_demo.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-26
# Desc:
# 可复制到 Classic Notebook 的 qteasy AI
# 魔法命令示例片段。
# ======================================

"""Classic Notebook 魔法命令示例。

使用方式：
1. 打开 Jupyter Notebook；
2. 将下面代码块粘贴到单元格运行；
3. 按示例继续在后续单元格输入 prompt。
"""

print(
    """
# Cell 1: load extension
%load_ext qteasy.ai.notebook_magic

# Cell 2: plan mode
%%qtai --mode plan
列出所有内置策略，并告诉我 macd 策略参数

# Cell 3: ask mode
%%qtai --mode ask
解释一下 PT/PS/VS 的区别

# Cell 4: run mode (first returns plan + confirm hint)
%%qtai --mode run
列出所有内置策略

# Cell 5: confirm execution (replace <plan_id>)
%%qtai --confirm <plan_id>
Execute.
""".strip()
)

