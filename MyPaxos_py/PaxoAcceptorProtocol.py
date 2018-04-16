"""
    @author: chaors

    @file: PaxoAcceptorProtocol.py

    @time: 2018/04/14 10:50

    @desc: 决策者协议
"""

from Message import Message  #协议依赖消息

class PaxoAcceptorProtocol:
    #常量
    STATE_UNDEFIND = -1  #协议未定义
    STATE_PROPOSAL_RECEIVED = 0  #收到消息
    STATE_PROPOSAL_REJECTED = 1  #拒绝链接，网络不通可能
    STATE_PROPOSAL_AGREED = 2  #承诺将接受该提议  针对Proposer的PROPOSED请求
    STATE_PROPOSAL_ACCEPTED = 3  #接受该协议  针对Proposer的Accept请求
    STATE_PROPOSAL_UNACCEPTED = 4  #拒绝请求

    def __init__(self, client):
        self.client = client
        self.state = PaxoAcceptorProtocol.STATE_UNDEFIND  #默认初始未定义

    #收到提议
    def recvProposal(self, msg):
        if msg.cmd == Message.MSG_PROPOSE:  #处理提议
            self.proposalID = msg.proposalID  #协议编号
            self.instanceID = msg.instanceID  #记录编号
            (port, count) = self.client.getHighestProposal(msg.instanceID)  #获取端口，协议最高编号

            #[start---1.3] AcceptorProtocol收到一个提议，判断提议版本回复承诺接受消息或拒绝消息
            #判断协议是否是最高版本，版本相同时优先接收端口号高的提议消息
            if count < self.proposalID[0] \
                    or (count == self.proposalID[0] and port < self.proposalID[1]):
                self.state = PaxoAcceptorProtocol.STATE_PROPOSAL_AGREED  #Acceptor当前已经承诺给某Proposer会接受请求
                print("承诺会接受该提议:%s, %s " % (msg.instanceID, msg.value))
                value = self.client.getInstanceValue(msg.instanceID)  #抓取记录的数据值

                msg_agree = Message(Message.MSG_ACCEPTOR_AGREE)  #创建一个消息作为对Proposer的承诺
                msg_agree.copyAsReply(msg)  #拷贝并回复
                msg_agree.value = value  #保存值
                msg_agree.sequence = (port, count)  #保存端口数据
                self.client.sendMsg(msg_agree)  #给Proposer回复承诺消息

            else:
                #提议版本过低，我已经承诺给别的Proposer  所以拒绝
                self.state = PaxoAcceptorProtocol.STATE_PROPOSAL_REJECTED

            return self.proposalID

        else:
            pass


    #过渡
    def doTranition(self, msg):
        # [start---2.2_1] AcceptorPropotal收到Proposer发出的Accept请求。按Paxos算法思想，这里需要判断请求版本号，当且仅当Acceptor之前承诺过的提议版本号最大值小于Accept请求版本号才会接受该Proposer提议。这里我们借助“先入为主”的思想简化问题，只要这时候协议状态为STATE_PROPOSAL_AGREED，就给所有Proposer广播消息表示自己确认接受该Proposer提议
        if self.state == PaxoAcceptorProtocol.STATE_PROPOSAL_AGREED \
                and msg.cmd == Message.MSG_ACCEPT:  #同意链接 并消息被接受
            self.state = PaxoAcceptorProtocol.STATE_PROPOSAL_ACCEPTED  #接受协议
            msg_accept = Message(Message.MSG_ACCEPTOR_ACCEPT)  #创造消息，用来表示该Acceptor最终接受了某个Proposer的提议
            msg_accept.copyAsReply(msg)

            #广播消息给所有提议者，告知自己最终接受了拿个Proposer的提议
            for proposer in self.client.proposers:
                msg_accept.to = proposer
                self.client.sendMsg(msg_accept)

            #[start - --2.2_1]AcceptorPropotal通知Acceptor更新InstanceRecord的值，到此时已有一个提议被一个Acceptor最终接受。
            self.notifyClient(msg)

            return True

        raise Exception(u"并非预期状态与命令")

    #通知客户端
    def notifyClient(self, msg):
        self.client.notifyClient(self, msg)










