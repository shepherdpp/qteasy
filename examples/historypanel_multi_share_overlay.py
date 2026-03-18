import qteasy as qt


def main() -> None:
    """HistoryPanel 多标的 overlay/stack 可视化示例。

    本示例展示：
    1. 为多个指数获取收盘价数据，构建 HistoryPanel；
    2. 使用 overlay 布局在同一组图中叠加多条净值曲线；
    3. 使用 stack 布局将不同标的拆分为多组图表。
    """

    # 获取多个标的的收盘价数据
    hp = qt.get_history_data(
        htypes='close',
        shares='000300.SH,000905.SH,000852.SH',
        start='20230101',
        end='20231231',
    )
    print(hp)

    # 在同一组图中叠加多标的收盘价
    hp.plot(
        htypes=['close'],
        layout='overlay',
        interactive=False,
    )

    # 将多标的拆分为多组图表进行对比
    hp.plot(
        htypes=['close'],
        layout='stack',
        interactive=False,
    )


if __name__ == '__main__':
    main()

