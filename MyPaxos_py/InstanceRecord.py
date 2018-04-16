"""
    @author: chaors

    @file: InstanceRecord.py

    @time: 2018/04/14 10:31

    @desc: 本地记录类,记录决策者，提议者之间协议
"""

import threading, socket, pickle, queue,random
#  InstanceRecord本地记录类，决策者，提议者之间协议
from PaxoProposerProtocol import PaxoProposerProtocol

class InstanceRecord():
    def __init__(self):
        self.protocols = {}  #协议字典
        self.highestID = (-1, -1)  #最高版本(提议版本，端口号)
        self.value = None  #提议值

    #增加协议
    def addProtocol(self, protocol):
        self.protocols[protocol.proposalID] = protocol
        #取得版本最高的协议  假设端口较大的Proposer为领导，优先承诺 端口相同时取版本号较大的
        if protocol.proposalID[1] > self.highestID[1] or \
                (protocol.proposalID[1] == self.highestID[1] \
                 and protocol.proposalID[0] > self.highestID[0]):
            self.highestID = protocol.proposalID

    #抓取协议
    def getProtocol(self, protocolID):

        return self.protocols[protocolID]

    #清理协议
    def cleanProtocols(self):
        keys = self.protocols.keys()  #取得所有可以
        #遍历删除协议
        for key in keys:
            protocol = self.protocols[key]
            if protocol.state == PaxoProposerProtocol.STATE_ACCEPTED:
                print("Deleting protocol")
                del self.protocols[key] #删除协议

