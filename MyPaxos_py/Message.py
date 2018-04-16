"""
    @author: chaors

    @file: Message.py

    @time: 2018/04/14 09:31

    @desc: 消息传递类
"""

class Message:
    #常量
    MSG_ACCEPTOR_AGREE = 0  #Acceptor对提议请求的承诺
    MSG_ACCEPTOR_ACCEPT = 1  #Acceptor对Accept请求的接受
    MSG_ACCEPTOR_REJECT = 2  #Acceptor对提议请求的拒绝
    MSG_ACCEPTOR_UNACCEPT = 3  #Acceptor对Accept请求的不接受
    MSG_ACCEPT = 4  #Proposer发出的Accept请求 或
    MSG_PROPOSE = 5  #Proposer发出的提议请求
    MSG_EXT_PROPOSE = 6  #外部(Client)发给Proposer的提议
    MSG_HEARTBEAT = 7  #定时的心跳信息，用来同步提议

    def __init__(self, cmd=None):  #消息初始化有个命令
        self.cmd = cmd

    #对某个消息的回复消息
    def copyAsReply(self, msg):
        self.proposalID = msg.proposalID  #提议id
        self.instanceID = msg.instanceID  #当前id
        self.to = msg.source  #提议发给谁
        self.source = msg.to  #提议源自谁
        self.value = msg.value  #提议信息









