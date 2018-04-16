"""
    @author: chaors

    @file: PaxoProposer.py

    @time: 2018/04/14 10:50

    @desc: 提议者
"""

import threading
import queue
import time

from Message import Message
from MessagePump import MessagePump
from InstanceRecord import InstanceRecord
from PaxoProposerProtocol import  PaxoProposerProtocol

class PaxoProposer:

    #心跳监听类
    class HeartbeatListener(threading.Thread):
        def __init__(self, proposer):
            self.proposer = proposer  #提议者
            self.queue = queue.Queue()  #消息队列
            self.abort = False

            threading.Thread.__init__(self)  #父类初始化

        #从队列取出消息
        def newHB(self, msg):
            self.queue.put(msg)

        #开始执行，读取消息
        def run(self):
            # elapsed = 0  #时间计数器
            while not self.abort:  #非取消状态
                # stime = time.time()
                try:
                    hb = self.queue.get(True, 2)  #抓取消息， 最多抓取2s
                    #假设谁的端口号比较高谁是领导
                    if hb.source > self.proposer.port:
                        self.proposer.setPrimary(False)
                except:
                    self.proposer.setPrimary(True)

        #取消
        def doAbort(self):
            self.abort = True

    #定时发送类
    class HeartbeatSender(threading.Thread):
        def __init__(self, proposer):
            self.proposer = proposer
            self.abort = False

            threading.Thread.__init__(self)

        #
        def run(self):
            while not self.abort:
                time.sleep(1)  #每1s一次
                if self.proposer.isPrimary:  #提议者为领导
                    msg = Message(Message.MSG_HEARTBEAT)  #心跳信息
                    msg.source = self.proposer.port  #设置消息源端口
                    for proposer in self.proposer.proposers:  #遍历提议者
                        msg.to = proposer
                        self.proposer.sendMsg(msg)  #发送消息

        #
        def doAbort(self):
            self.abort = True

    #初始化
    def __init__(self, port, proposers=None, acceptors=None):
        self.port = port

        #初始化提议者
        if proposers == None:
            self.proposers = []
        else:
            self.proposers = proposers

        if acceptors == None:
            self.acceptors = []
        else:
            self.acceptors = acceptors

        self.group = self.proposers+self.acceptors  #组
        self.isPrimary = False  #是否是领导,被大多说决策者选出来的提议者是领导
        self.proposalCount = 0  #提议数量
        self.msgPump = MessagePump(self, port)  #消息传送器
        self.instances = {}  #记录数据
        self.hbListener = PaxoProposer.HeartbeatListener(self)  #监听工具实例
        self.hbSender = PaxoProposer.HeartbeatSender(self)  #发送工具实例
        self.highestInstance = -1  #最高协议版本
        self.stopped = True  #是否在运行
        self.lastTime = time.time()  #最后一次时间

    #开始
    def start(self):
        self.hbSender.start()  # 发送器
        self.hbListener.start()  #监听器
        self.msgPump.start()  #消息发送
        self.stopped = False

    #停止
    def stop(self):
        self.hbSender.doAbort()  # 发送器
        self.hbListener.doAbort()  # 监听器
        self.msgPump.doAbort()  # 消息发送
        self.stopped = True

    #设置是否为领导者
    def setPrimary(self, isPrimary):
        if self.isPrimary != isPrimary:
            if isPrimary:
                print(u"%s is leader" % self.port)
            else:
                print(u"%s is not leader" % self.port)

        self.isPrimary = isPrimary

    #获取支持所有提议者的决策者
    def getGroup(self):
        return self.group

    #获取所有提议者
    def getProposers(self):
        return self.proposers

    #获取所有决策者
    def getAcceptors(self):
        return self.acceptors

    #提议被承诺接受或最终接受的条件必须满足:获得1/2以上的Acceptor支持
    def getQuorumCount(self):
        return len(self.getAcceptors())/2

    #获取本地记录数据
    def getInstanceValue(self, instanceID):
        if instanceID in self.instances.keys():
            return self.instances[instanceID].value

        return None

    #获取历史记录
    def getHistory(self):
        return [self.getInstanceValue(i) for i in range(0, self.highestInstance+1)]
        # mylist = []
        # for i in range(0, self.highestInstance + 1):
        #     last = self.getInstanceValue(i)
        #     mylist.append(last)
        #
        # return mylist

    #获取提议同意的数量
    def getNumAccepted(self):
        return len([v for v in self.getHistory() if v != None])
        # mylist = []
        # list = self.getHistory()
        # for i in list:
        #     if i != None:
        #         mylist.append(i)
        #
        # return len(mylist)


    #通知其他提议者
    def notifyProposer(self, protocol, msg):
        #提议被同意
        #[start---2.5] Proposer更新InstanceRecord记录，如果协议最终被大多数Acceptor拒绝则尝试重新提议
        if protocol.state == PaxoProposerProtocol.STATE_ACCEPTED:
            print(u"协议%s被%s同意"  % (msg.instanceID, msg.value))
            self.instances[msg.instanceID].accepted = True
            self.instances[msg.instanceID].value = msg.value
            self.highestInstance = max(msg.instanceID, self.highestInstance)

            return True

        #如果协议最终被大多数Acceptor拒绝则尝试重新提议
        if protocol.state == PaxoProposerProtocol.STATE_REJECTED:
            self.proposalCount = max(self.proposalCount, msg.highestPID[1])
            self.newProposal(msg.value)  #重试提议

            return True


    #新的提议
    def newProposal(self, value, instance=None):
        protocol = PaxoProposerProtocol(self)  #创建提议者协议实例

        #创建协议标号
        if instance == None:
            self.highestInstance += 1
            instanceID = self.highestInstance
        else:
            instanceID = instance

        self.proposalCount += 1  #提议数
        id = (self.port, self.proposalCount)  #保存端口，协议数

        #协议记录
        if instanceID in self.instances:
            record = self.instances[instanceID]
        else:
            record = InstanceRecord()
            self.instances[instanceID] = record

        #[start - --1.1]Proposer借助自身的PaxoProposerProtocol实例发起一个提议请求
        protocol.propose(value, id, instanceID)  #发起提议
        record.addProtocol(protocol)  #追加协议

    # 发送消息
    def sendMsg(self, msg):
        self.msgPump.sendMsg(msg)

    # 接收消息
    def recvMsg(self, msg):
        if self.stopped:
            return

        if msg == None:
            if self.isPrimary and time.time() - self.lastTime > 15.0:
                self.findAndFillGaps()
                self.garbageCollect()  #处理

            return

        if msg.cmd == Message.MSG_HEARTBEAT:  #心跳消息
            self.hbListener.newHB(msg)

            return True

        #[start---1.0]Proposer收到一个消息，消息类型为一个提议。首先判断自身是否为领导者，如果是创建协议
        if msg.cmd == Message.MSG_EXT_PROPOSE:  #额外协议
            print("u外部传来的提议 %s %s" % (self.port, self.highestInstance))
            if self.isPrimary:
                self.newProposal(msg.value)  #新的协议

            return True

        #[start---1.4]Proposer收到一个消息，类型为Acceptor的承诺(MSG_ACCEPTOR_AGREE)。既然不是Proposer最终要的接受提议的结果，转给ProposerPropotocal状态机处理
        if self.isPrimary and msg.cmd != Message.MSG_ACCEPTOR_ACCEPT:  #如果消息不是最终同意消息
            self.instances[msg.instanceID].getProtocol(msg.proposalID).doTranition(msg)

        if msg.cmd == Message.MSG_ACCEPTOR_ACCEPT:
            #[start---2.3]Proposer收到一个消息，类型为Acceptor确认接受提议(MSG_ACCEPTOR_ACCEPT),根据该消息更新Proposer的InstanceRecord(新建record，追加协议等)。并将消息交给ProposerProtocol状态机处理
            if msg.instanceID not in self.instances:
                record = InstanceRecord()
                # record.value = msg.value
                self.instances[msg.instanceID] = record

            record = self.instances[msg.instanceID]  #记录
            if msg.proposalID not in record.protocols:
                #创建协议
                protocol = PaxoProposerProtocol(self)  #提议者协议
                protocol.state = PaxoProposerProtocol.STATE_AGREED  #同意链接
                protocol.proposalID = msg.proposalID
                protocol.instanceID = msg.instanceID
                protocol.value = msg.value
                record.addProtocol(protocol)  #追加协议
            else:
                protocol = record.getProtocol(msg.proposalID)

            protocol.doTranition(msg)  #过渡处理
            # print(self.getInstanceValue(0))

        return True

    #无用信息处理
    def garbageCollect(self):
        for i in self.instances:
            self.instances[i].cleanProtocols()

    #获取空白时间处理下事务
    def findAndFillGaps(self):
        for i in range(1, self.highestInstance):
            if self.getInstanceValue(i) == None:
                print(u"填充空白", i)
                self.newProposal(0, i)

        self.lastTime = time.time()

