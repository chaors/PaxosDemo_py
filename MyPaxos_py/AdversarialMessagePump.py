"""
    @author: chaors

    @file: AdversarialMessagePump.py

    @time: 2018/04/14 10:21

    @desc:#对抗消息传输，延迟并任意顺序传输，模拟网络延迟
"""

import random  #随机数

from MessagePump import MessagePump  #导入MessagePump类

class AdversarialMessagePump(MessagePump):
    def __init__(self, owner, port, timeout=3):
        MessagePump.__init__(owner, port, timeout)  #初始化父类
        self.msg = set()  #避免消息重复

    #等待消息
    def waitForMsg(self):
        try:
            msg = self.queue.get(True, 0.1)  # 从队列中取消息，最多等0.1s
            self.msg.add(msg)
        except Exception as e:
            print(e)

        #随机处理消息,为的是模拟网络延时
        if len(self.msg) > 0 and random.random() < 0.95:
            msg = random.choice(list(self.msg))  #随机取出一个消息
            self.msg.remove(msg)  #删除取出的消息

        else:
           msg = None

        return msg