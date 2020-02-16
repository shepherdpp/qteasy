from core import *

if __name__ == '__main__':

    op = Operator(['DMA'])
    for item in op.timing:
        item.info()


    def six_str(n):
        s = str(n)
        l = len(s)
        if l < 6:
            s = '0' * (6 - l) + s
        return s


    h = History()
    h.work_days()
    op = Operator(timing_types=['DMA', 'MACD'], selecting_types=['simple'], ricon_types=['urgent'])
    worker = Qteasy(operator=op, history=h)
    op.info()