"""
    @author: chaors

    @file: PaxoAcceptor.py

    @time: 2018/04/14 10:50

    @desc: 决策者
"""

from Message import Message
from MessagePump import MessagePump
from InstanceRecord import InstanceRecord
from PaxoAcceptorProtocol import  PaxoAcceptorProtocol

class PaxoAcceptor:
    def __init__(self, port, proposers):
        self.port = port  #端口
        self.proposers = proposers  #提议者
        self.instances = {}  # 接口列表
        self.msgPump = MessagePump(self, self.port)  #消息传送器
        self.failed = False  #没有失败

    #开始
    def start(self):
        self.msgPump.start()

    #停止
    def stop(self):
        self.msgPump.doAbort()

    #失败
    def fail(self):
        self.failed = True

    #恢复
    def recover(self):
        self.failed = False

    #发送消息
    def sendMsg(self, msg):
        self.msgPump.sendMsg(msg)

    #接收消息
    def recvMsg(self, msg):
        if msg == None:  #消息为空
            return

        if self.failed:  #失败状态不接收消息
            return

        if msg.cmd == Message.MSG_PROPOSE:  #消息为提议
            if msg.instanceID not in self.instances:  #消息未加入
                record = InstanceRecord()  #记录器
                # record.value = msg.value
                self.instances[msg.instanceID] = record  #将消息记录下来

            protocol = PaxoAcceptorProtocol(self)  #创建决策者协议

            #[start---1.2]Acceptor收到一个消息，消息类型为提议。然后借助AcceptorProtocol实例处理提议
            protocol.recvProposal(msg)  #借助决策者处理协议
            self.instances[msg.instanceID].addProtocol(protocol)  #记录协议

        else:
            #[start---2.1]Acceptor收到一个消息，类型为来自Proposer的Accept请求。借助AcceptorPropotal处理该消息
            self.instances[msg.instanceID].getProtocol(msg.proposalID).doTranition(msg)  #抓取协议记录


    #通知客户端
    def notifyClient(self, protocol, msg):
        if protocol.state == PaxoAcceptorProtocol.STATE_PROPOSAL_ACCEPTED:  #接受协议
            self.instances[protocol.instanceID].value = msg.value  #存储信息
            print("协议被客户端接受", msg.value)


    #获取本地记录数据
    def getInstanceValue(self, instanceID):
        return self.instances[instanceID].value

    #获取最高同意建议
    def getHighestProposal(self, instanceID):
        return self.instances[instanceID].highestID