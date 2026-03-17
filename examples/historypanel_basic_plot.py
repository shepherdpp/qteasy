import qteasy as qt


def main() -> None:
    """HistoryPanel 基础可视化示例。

    本示例展示：
    1. 使用 get_history_data 获取单标的 OHLCV 数据（返回 HistoryPanel）；
    2. 在 HistoryPanel 上绘制静态 K 线 + 成交量；
    3. 在支持的环境下绘制交互式 K 线；
    4. 演示简单的 highlight 配置。
    """

    # 获取近一年的日线 OHLCV 数据，直接返回 HistoryPanel
    hp = qt.get_history_data(
        htypes='open, high, low, close, vol',
        shares='000300.SH',
        start='20230101',
        end='20231231',
    )
    print(hp)

    # 绘制静态 K 线 + 成交量
    hp.plot(interactive=False)

    # 在支持 Plotly FigureWidget 的环境中绘制交互式 K 线
    hp.plot(interactive=True)

    # 对收盘价做简单高亮：标记最大值
    hp.plot(
        interactive=True,
        highlight={'condition': 'max'},
    )


if __name__ == '__main__':
    main()

