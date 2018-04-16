"""
    @author: chaors

    @file: PaxoProposerProtocol.py

    @time: 2018/04/14 10:50

    @desc: 提议者协议
"""

from Message import Message  #协议依赖消息

class PaxoProposerProtocol:
    #常量
    STATE_UNDEFIND = -1  #提议协议未定义
    STATE_PROPOSED = 0  #提议类型
    STATE_REJECTED = 1  #拒绝状态  提议被拒绝
    STATE_AGREED = 2    #提议被承诺接受 Prepare阶段获取大多数Acceptor承诺后的协议状态
    STATE_ACCEPTED = 3  #提议被接受
    STATE_UNACCEPTED = 4  #提议未被拒绝

    def __init__(self, proposer):
        self.proposer = proposer

        self.state = PaxoProposerProtocol.STATE_UNDEFIND
        self.proprsalID = (-1, -1)
        # self.agreeCount = (0, 0)
        # self.acceptCount = (0, 0)
        # self.rejectCount = (0, 0)
        # self.unacceptCount = (0, 0)

        self.agreeCount = 0
        self.acceptCount = 0
        self.rejectCount = 0
        self.unacceptCount = 0

        self.instanceID = -1
        self.highestseen = (0, 0)  #最高协议


    #提议
    def propose(self, value, pID, instanceID):
        self.proposalID = pID
        self.instanceID = instanceID
        self.value = value

        # 创建一个提议类型的消息
        msg = Message(Message.MSG_PROPOSE)
        msg.proposalID = pID
        msg.instanceID = instanceID
        msg.value = value

        #将提议请求发送给每一位决策者Acceptor
        for server in self.proposer.getAcceptors():
            msg.to = server
            self.proposer.sendMsg(msg)

        #当前协议状态为已提议状态
        self.state = PaxoProposerProtocol.STATE_PROPOSED  #提议类型

        return self.proprsalID

    #过渡 根据状态机运行
    def doTranition(self, msg):
        #[start---1.5]ProposerPropotocal状态机函数收到一个MSG_ACCEPTOR_AGREE消息，此时表示有一个Acceptor承诺会接受我的请求。
        if self.state == PaxoProposerProtocol.STATE_PROPOSED:  #当前协议为提议状态提议
            if msg.cmd == Message.MSG_ACCEPTOR_AGREE:
                #许诺接受提议的计数器
                self.agreeCount += 1
                #[start---2.0_1]该条件下的代码会不断执行，直到许诺Proposer的数量超过半数，表示Prepare阶段基本结束。此时的Proposer向Acceptor集合发送Accept请求，请求Acceptor确认他们的许诺。
                if self.agreeCount > self.proposer.getQuorumCount():  #选举
                    print(u"达成协议的法定人数%d，最后的价值回答是:%s" % (self.agreeCount, msg.value))
                    if msg.value != None:
                        #判断版本号，根据版本高德更新记录的值
                        if msg.sequence[0] > self.highestseen[0] \
                            or (msg.sequence[0] == self.highestseen[0] \
                                and msg.sequence[1] > self.highestseen[1]):
                            self.value = msg.value  #数据同步
                            self.highestseen = msg.sequence

                    self.state == PaxoProposerProtocol.STATE_AGREED  #提议取得超半数Acceptor承诺，对应协议状态变为协议被许诺将接受

                    #[start---2.0_1]向Acceptor发送Accept请求，请求Acceptor确认许诺
                    msg_accept = Message(Message.MSG_ACCEPT)
                    msg_accept.copyAsReply(msg)
                    msg_accept.value = self.value
                    msg_accept.proposerID = msg.to
                    for server in self.proposer.getAcceptors():  #广播Accept请求
                        msg_accept.to = server
                        self.proposer.sendMsg(msg_accept)

                    #[start---2.0_2]通知其他提议者我的提议已经被半数Accept许诺将会被接受，使得其他Proposer知道Prepare阶段哪个提议获得的承诺最多。这样，在Commit阶段，他们可能通过改变提议来使系统尽快达到一致性。
                    self.proposer.notifyProposer(self, msg)

                return True
            if msg.cmd == Message.MSG_ACCEPTOR_REJECT:  #被拒绝
                self.rejectCount += 1
                if self.rejectCount > self.proposer.getQuorumCount():  #决策者拒绝数超过半数
                self.state = PaxoProposerProtocol.STATE_REJECTED
                self.proposer.notifyProposer(self, msg)

            return True


        if self.state == PaxoProposerProtocol.STATE_AGREED:  #同意状态
            #[start---2.4_1]ProposerProtocol收到一个Acceptor的最终确认消息(MSG_ACCEPTOR_ACCEPT),此时表示新增一个Acceptor最终接受了我的提议。但此时的协议状态仍然是STATE_AGREED状态，因为一个提议最终被系统接受必须先被超半数的Acceptor节点确认接受。
            if msg.cmd == Message.MSG_ACCEPTOR_ACCEPT:  #确认接受协议
                #确认接受当前协议的Acceptor计数器
                self.acceptCount += 1
                if self.acceptCount > self.proposer.getQuorumCount():  #提议被超半数Acceptor最终确认接受

                    #[start---2.4_2] STATE_AGREED条件下的代码会不断执行，直到最终接受提议的Acceptor超过半数。这时，协议状态由STATE_AGREED状态更新为最终被系统确认状态(STATE_ACCEPTED)。
                    self.state = PaxoProposerProtocol.STATE_ACCEPTED  #接受
                    #最后，最后，当前Proposerg更新自己的InstanceRecord记录
                    self.proposer.notifyProposer(self, msg)

            #当然，这里也有一种可能是被超过半数节点不接受，那么同样其他Proposer节点必有一个节点提议被接受。
            #该Proposer的提议最终不被Acceptor确认接受
            if msg.cmd == Message.MSG_ACCEPTOR_UNACCEPT: #不同意协议
                self.unacceptCount += 1
                if self.unacceptCount > self.proposer.getQuorumCount():
                    self.state = PaxoProposerProtocol.STATE_UNACCEPTED
                    self.proposer.notifyProposer(self, msg)

        pass




