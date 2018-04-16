"""
    @author: chaors

    @file: paxo_testMain.py

    @time: 2018/04/14 17:50

    @desc: Paxos算法测试用例
"""

import threading, socket, pickle, queue,random
import time

from MessagePump import MessagePump
from Message import Message
from InstanceRecord import InstanceRecord
from PaxoProposer import PaxoProposer
from PaxoProposerProtocol import PaxoProposerProtocol
from PaxoAcceptorProtocol import PaxoAcceptorProtocol
from PaxoAcceptor import PaxoAcceptor

if __name__ == '__main__':
    #Acceptor数量
    numclients = 5
    #实例化决策者数组，决策者节点端口号为65520-65525
    acceptors = [PaxoAcceptor(port, [56321, 56322]) for port in range(65520, 65520 + numclients)]

    #实例化提议者，端口号分别56321，56322  对应的决策者为acceptors
    proposer1 = PaxoProposer(56321, [56321, 56322], [acceptor.port for acceptor in acceptors])
    proposer2 = PaxoProposer(56322, [56321, 56322], [acceptor.port for acceptor in acceptors])

    #启动提议者提议程序
    proposer1.start()
    proposer1.setPrimary(True)
    proposer2.setPrimary(True)
    proposer2.start()

    #启动决策者决策程序
    for acceptor in acceptors:
        acceptor.start()

    #模拟网络中两个节点宕机
    acceptors[0].fail()
    acceptors[1].fail()

    #利用Socket机制发送提议给决策者
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start = time.time()

    #将1-1000作为每次提议的值
    for i in range(1000):
        m = Message(Message.MSG_EXT_PROPOSE)
        m.value = 0 + i
        m.to = 56322
        bytes = pickle.dumps(m)
        s.sendto(bytes, ("localhost", m.to))

        # if i == 2 or i == 30:
        #     print(leader2.getInstanceValue(1))

    #当提议被999个决策者接受时结束整个提议程序
    while proposer1.getNumAccepted() < 999:
        print(u"休眠1秒--被接受: %d" % proposer1.getNumAccepted())
        time.sleep(1)
    end = time.time()

    print(u"休眠10秒")
    time.sleep(10)
    print(u"结束领导者")
    proposer1.stop()
    proposer2.stop()
    print(u"结束客户端")
    for acceptor in acceptors:
        acceptor.stop()

    print(u"领导者1 历史记录:  %s" % proposer1.getHistory())
    print(u"领导者 2 历史记录: %s " % proposer2.getHistory())
    print(u"一共用了%d 秒" % (end - start))
