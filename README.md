# PaxosDemo_py
# 基于Python的区块链共识算法Paxos实战

# 0.前言

本文记录笔者学习和理解区块链共识算法Paxos的点滴，文章比较长，需要耐心来细细琢磨，笔者也是苦战了一个周末才对此有那么一点初步了解，有问题的地方请不吝斧正！

1.初始是阅读本文后续内容的基础，概念性的东西叙述不多，干货干货干货在后面的代码实战。但有提供我认为优秀的帖子以供参考理解。前面这些Paxos基本的理解是2.代码设计和3.实战流程的基础！

# 1.初识

### 相关概念

  Paxos 问题是指分布式的系统中存在故障（fault），但不存在恶意（corrupt）节点场景（即 可能消息丢失或重复，但无错误消息）下的共识达成（Consensus）问题。
  
   Paxos最早是 Leslie Lamport 用 Paxon 岛的故事模型来进行描述而命名。故事背景是古希腊 Paxon 岛上的多个法官在一个大厅内对一个议案进行表决，如何达成统一 的结果。他们之间通过服务人员来传递纸条，但法官可能离开或进入大厅，服务人员可能偷 懒去睡觉。

Paxos 是第一个被证明的共识算法，其原理基于两阶段提交并进行扩展。 作为现在共识算法设计的鼻祖，以最初论文的难懂（算法本身并不复杂）出名。算法中将节点分为三种类型：

 - proposer：提出一个提案，等待大家批准为结案。往往是客户端担任该角色；

- acceptor：负责对提案进行投票。往往是服务端担任该角色；一般需要至少3个且节点个数为奇数，因为Paxos算法最终要产生一个大多数决策者都同意的提议。

- learner：被告知结案结果，并与之统一，不参与投票过程。可能为客户端或服务端。

### paxos算法的两阶段 
- prepare 阶段： 
  1. Proposer 选择一个提案编号 n，然后向acceptor的某个超过半数的子成员发送编号为n的 prepare 请求； 
  2. Acceptor 收到 prepare 消息后，如果提案的编号n大于该acceptor已经回复的所有 prepare 请求的编号，则 Acceptor 将自己上次已经批准的最大编号提案回复给 Proposer，并承诺不再回复小于 n 的提案；

- commit阶段： 
  1. 当一个 Proposer 收到了半数以上的 Acceptors 对 prepare 的回复后，就进入批准阶段。它要向回复 prepare 请求的 Acceptors 发送 accept 请求，包括编号 n 和根据 prepare阶段 决定的 value。这里的value是所有响应中编号最大的提案的value（如果根据 prepare 没有已经接受的 value，那么它可以自由决定 value）。 
  2. 在不违背自己向其他 Proposer 的承诺的前提下，Acceptor 收到 accept 请求后即接受这个请求。即如果acceptor收到这个针对n提案的accept请求，只要该acceptor尚未对编号大于n的prepare请求做出过响应，它就可以通过这个提案。

### 他山之石

Paxos算法初次接触听上去确实有点晦涩难懂，这里有一篇贴子我觉得不错。贴出来可以参考:

- [通过现实世界描述Paxos算法](http://www.cnblogs.com/endsock/p/3480093.html)
- [通过实例来理解paxos算法](https://blog.csdn.net/xiaqunfeng123/article/details/51712983)
- [Paxos算法原理与推导](http://www.cnblogs.com/linbingdong/p/6253479.html)

另外，wiki对[Paxos](https://en.wikipedia.org/wiki/Paxos_(computer_science))的描述也是比较不错和权威的参考资料。

有了以上对Paxos算法的理解，我们才能进行下一步：自己编程实现Paxos算法。

# 2.代码实战

### 流程理解

Paxos算法核心的两个角色便是Proposer(提议者)和Acceptor(决策者)，因此也必须围绕这两个对象进行算法架构的设计。

![Paxos算法流程](https://upload-images.jianshu.io/upload_images/830585-531976b2e68c1b2d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

###### Proposer行为分析
- 1.0  向所有Acceptor发出一个提议(proposal)；

- 2.0  如果收到一个拒绝信息(reject),尝试重新发送被拒绝的提议；

- 2.1 如果收到一个Acceptor的承诺回应(agree),用一个标志(agreeCount)来计数给了自己承诺的Acceptor个数。当agreeCount超过Acceptor总数的一半时，表示有大多数Acceptor承诺将接受这个提议，需要将自己的提议状态置为承诺接受状态(agreed)。同时，还要通知其他Proposer我这个提议已经得到大多数Acceptor承诺会接受。

- 3.0 提议为承诺接受状态(agreed)时，Proposer需要再向Acceptor集合发送一个接受提议的确认请求，我们称该请求为Accept请求。

- 3.1 发出Accept请求后会收到Acceptor的回复，如果收到接受信息(Accept),用一个标志(acceptCount)来计数接受自己提议的Acceptor个数。同样当acceptCount超过半数时，表示大多数Acceptor接受了这个提议，需要将提议状态由承诺接受状态(agreed)置为接受状态(acceptd)。
同时，还要通知其他Proposer我这个提议已经得到大多数Acceptor接受。

- 以上1，2属于Paxos算法的Prepare阶段，3属于Accept阶段。

###### Acceptor行为分析

- 1.0 当Acceptor收到一个提议后，判断提议版本号是否大于自身保存的提议版本。

- 1.0 如果小于自身表示曾经已经给过别的Proposer承诺，发送一个拒绝消息(reject),表示自己拒绝给当前Proposer任何承诺。

- 1.1 反之，则替换自身保存的提议版本号并给当前Proposer发送一个承诺回应(agree),表示将承诺接受他的提议。同时，将自身状态置为已经给了某个Proposer承诺(agree)。

- 2.0 Acceptor收到一个Proposer的编号为N的Accept请求，只要该Acceptor之前不曾承诺编号M(M>N)的其他Proposer提议，那么他就接受该提案。同时，将自身状态置为已接受某个Proposer提议，并通知所有Proposer这个消息。

- 以上1属于Paxos算法的Prepare阶段，2属于Accept阶段。

___以上行为分析针对本次Paxos算法编程实战！！！___

### 类的设计

Paxos算法解决的是分布式系统一致性的问题，我们通过端口号在一台计算机上模拟多个节点。

毋庸置疑，我们分别需要一个Proposer类和Acceptor类。

###### PaxoProposer 提议者类

- Proposer的作用是提出一个提议并发送给Acceptor，所以他本身必须知道所有的Acceptor，同时有些时候要跟其他Proposer通讯，所以也需要知道所有的Proposer(见init方法)。

- 基本的开始结束接口(start, stop)

 - 在判断提议是否被大多数Acceptor承诺接受或最终接受，我们需要设定一个判定条件(getQuorumCount)

 - 当提议被承诺接受或最终接受时需要通知其他Proposer(notifyProposer)

- 发送消息(提议或Accept请求)给Acceptor(sendMsg);接收来自Acceptor的消息(recvMsg)

- 为了方便调试，我们可能需要知道整个过程请求提议的历史记录(getHistory)

- 自己的提议最终被Acceptor接受的个数(getNumAccepted)

- 清楚Paxos算法流程后，我们发现假设有两个Proposer依次提出编号递增的提议，最终会陷入死循环使得Paxos算法无法保证活性。所以，一般的做法是选取一个主Proposer作为领导，只有领导才能提出提议(setPrimary)。

- Proposer类的一个难点在于提议发出后的各种状态转变与对应数据的处理。从提议发出到提议被接受整个过程，提议的状态是在不断地变化，但最终总会到达一个终止态。对于这种情况的处理，__状态机__注定是一个不错的选择。由于这里有点复杂我们将提议功能单独拿出来抽象为一个Proposer的协议类__PaxoProposerProtocol__。

-由于各个节点收发消息是并行的，这里对消息的检测需要用到线程。这里HeartbeatListener来监听消息，HeartbeatSender用来发送消息。


```
"""
    @author: chaors

    @file: PaxoProposer.py

    @time: 2018/04/14 10:50

    @desc: 提议者
"""

class PaxoProposer:

    #心跳监听类
    class HeartbeatListener(threading.Thread):
        pass
    #定时发送类
    class HeartbeatSender(threading.Thread):
        pass
        

    #初始化
    def __init__(self, port, proposers=None, acceptors=None):
        pass
    #开始
    def start(self):
        pass

    #停止
    def stop(self):
        pass

    #设置是否为领导者
    def setPrimary(self, isPrimary):
        pass

    #获取支持所有提议者的决策者
    def getGroup(self):
        pass

    #获取所有提议者
    def getProposers(self):
        pass

    #获取所有决策者
    def getAcceptors(self):
        pass

    #提议被承诺接受或最终接受的条件必须满足:获得1/2以上的Acceptor支持
    def getQuorumCount(self):
        pass

    #获取本地记录数据
    def getInstanceValue(self, instanceID):
        pass

    #获取历史记录
    def getHistory(self):
        pass

    #获取提议同意的数量
    def getNumAccepted(self):
        pass


    #通知其他提议者
    def notifyProposer(self, protocol, msg):
        pass


    #新的提议
    def newProposal(self, value, instance=None):
        pass

    # 发送消息
    def sendMsg(self, msg):
        pass

    # 接收消息
    def recvMsg(self, msg):
        pass
```

##### PaxoProposerProtocol类

用来提交一个提议，并用于提交提议后各种状态的处理。

- 定义一些状态来表示当前Proposoer提议的各种状态

- 发起提议(propose)

- 状态机处理(doTranition)

```
"""
    @author: chaors

    @file: PaxoProposerProtocol.py

    @time: 2018/04/14 10:50

    @desc: 提议者协议
"""

class PaxoProposerProtocol:
    #常量
    STATE_UNDEFIND = -1  #提议协议未定义
    STATE_PROPOSED = 0  #提议类型
    STATE_REJECTED = 1  #拒绝状态  提议被拒绝
    STATE_AGREED = 2    #提议被承诺接受 Prepare阶段获取大多数Acceptor承诺后的协议状态
    STATE_ACCEPTED = 3  #提议被接受
    STATE_UNACCEPTED = 4  #提议未被拒绝

    def __init__(self, proposer):
        pass

    #发起提议
    def propose(self, value, pID, instanceID):
        pass

    #状态过渡 根据状态机运行
    def doTranition(self, msg):
        pass
``` 

##### PaxoAcceptor类

决策者，对Proposer提出的提议和Accept请求做出回应。

- 和Proposer类似的接口不再赘述。

- 需要对比Proposer发来的提议版本(getHighestProposal)

```
"""
    @author: chaors

    @file: PaxoAcceptor.py

    @time: 2018/04/14 10:50

    @desc: 决策者
"""

class PaxoAcceptor:
    def __init__(self, port, proposers):
        pass

    #开始
    def start(self):
        pass

    #停止
    def stop(self):
        pass

    #失败
    def fail(self):
        pass

    #恢复
    def recover(self):
        pass

    #发送消息
    def sendMsg(self, msg):
        pass

    #接收消息
    def recvMsg(self, msg):
        pass


    #通知客户端
    def notifyClient(self, protocol, msg):
        pass


    #获取本地记录数据
    def getInstanceValue(self, instanceID):
        pass

    #获取最高同意建议
    def getHighestProposal(self, instanceID):
        pass
```

##### PaxoAcceptorProtocol类

决策者协议，用来处理Proposer提出的提议，并同样使用状态机来处理自身各种状态。

```
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
        pass

    #收到提议
    def recvProposal(self, msg):
        pass


    #过渡
    def doTranition(self, msg):
        pass

    #通知客户端
    def notifyClient(self, msg):
        pass
```

##### Message类

Proposer和Acceptor的角色都有了，还差一个他们之间传递的消息类。这个消息有以下几种：

- Proposer发出的提议请求
- Proposer发出的Accept请求
- Acceptor对提议请求的拒绝
- Acceptor对提议请求的承诺
- Acceptor对Accept请求的接受
- Acceptor对Accept请求的不接受
- 外部(Client)发给Proposer的提议
- 作为对消息的回复消息
- 定时的心跳信息，用来同步提议

```
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
    MSG_ACCEPT = 4  #Proposer发出的Accept请求
    MSG_PROPOSE = 5  #Proposer发出的提议请求
    MSG_EXT_PROPOSE = 6  #外部(Client)发给Proposer的提议
    MSG_HEARTBEAT = 7  #定时的心跳信息，用来同步提议

    def __init__(self, cmd=None):  #消息初始化有个状态
        pass
    
    #对某个消息的回复消息
    def copyAsReply(self, msg):
        pass
```

##### InstanceRecord类

提议被抽象在协议里，在系统达到一致性之前，Proposer可能尝试提交多次协议信息(包含提议)。在Proposer和Acceptor之间都需要保存所有的提议记录，所以两者都有一个InstanceRecord实例数组。

对于Proposer，InstanceRecord实例数组保存的是提交过的所有提议记录，并且会随着提议状态的改变更新记录状态(包括协议和记录的值)的值。

对于Acceptor，InstanceRecord实例数组保存的是Acceptor接收的Proposer提议请求，并随着提议版本的改变而更新。Acceptor给出承诺(agree)的条件是提议版本大于当前InstanceRecord里的协议版本；Acceptor接受提议(accept)的条件是当前Accept请求版本号比之前给出承诺的的提议版本号大。

- 协议，包含了每次请求的协议信息(protocols)
- 最高版本，当前所有提交的请求的最高版本(highestID)
- 记录值，该次请求的值

```
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
```

##### MessagePump类

消息的结构是有了，但是它是怎么在节点(Proposer和Acceptor)之间传递的呢。这里我们封装一个基于Socket传递消息的网络类。这里接收消息需要借助一个线程，我们在构造一个接收消息的辅助类。

这里的只是不属于Paxos算法重点，就不赘述了。直接上代码。

```
"""
    @author: chaors

    @file: MessagePump.py

    @time: 2018/04/14 09:46

    @desc: 基于Socket传递消息，封装网络类传递消息
"""

import threading  #线程
import pickle  #对象序列化
import socket  #网络信息传输
import queue  #队列

class MessagePump(threading.Thread):
    # 传递消息的辅助类
    class MPHelper(threading.Thread):
        def __init__(self, owner):
            self.owner = owner  #传递消息的对象的所有者

            threading.Thread.__init__(self)  # 父类初始化

        def run(self):  #运行
            while not self.owner.abort:  #只要所有者线程未结束
                try:
                    #返回二进制数据，地址
                    (bytes, addr) = self.owner.socket.recvfrom(2048)  #收取消息
                    msg = pickle.loads(bytes)  #读取二进制转化为消息
                    msg.source = addr[1]  #取出返回的地址
                    self.owner.queue.put(msg)  #消息存入队列

                except Exception as e:  #异常
                    print(e)

    def __init__(self, owner, port, timeout=2):
        #基本参数初始化
        self.owner = owner  #所有者
        self.timeout = 2  #超时时间
        self.port = port  #网络接口

        #网络通信初始化
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #UDP通信
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 200000)  #通信参数
        self.socket.bind(("localhost", port))  #socket绑定
        self.socket.settimeout(timeout)  #设置超时

        self.queue = queue.Queue()  #队列
        self.helper = MessagePump.MPHelper(self)  #接收消息的工具类

        threading.Thread.__init__(self)  #父类初始化
        self.abort = False  #默认不终止状态

    #运行主线程
    def run(self):
        self.helper.start()  #开启收消息的线程
        while not self.abort:  #只要不是终止状态
            msg = self.waitForMsg()  #阻塞等待消息
            self.owner.recvMsg(msg)  #收取消息

    #等待消息
    def waitForMsg(self):
        try:
            msg = self.queue.get(True, 3)  #从队列中取消息，最多等3s

            return msg
        except Exception as e:
            print(e)

            return None

    #发送消息
    def sendMsg(self, msg):
        bytes = pickle.dumps(msg)  #把消息转成二进制
        addr = ("localhost", msg.to)
        self.socket.sendto(bytes, addr)  #发送消息到地址

        return True

    #设置状态为放弃
    def doAbort(self):
        self.abort = True
```

##### Paxos_MainTest Paxos算法测试

```
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
```

# 3.通过代码进一步了解Paox算法处理逻辑

上面已经完成了基本代码的架构，详细源码稍后我会上传到github。
接下来，我们通过一个简单的测试用例来再一次更深入地从代码层面理解Paxos算法的处理逻辑。

我们运行paxo_testMain代码，事先我在关键步骤处都打了断点。这样就可以完整地从代码角度看一次Paxos算法两个阶段的运行，也能直观地观察到各个步骤的代码处理逻辑。

## __!!!阅读说明:__

  ##### 1.x 对应Paxos算法Prepare阶段
  ##### 2.x 对应Paxos算法Commit阶段

### 废话少说上代码

- ##### 1.0 [start---1.0]Proposer收到一个消息，消息类型为一个提议。首先判断自身是否为领导者，如果是创建协议

![start---1.0](https://upload-images.jianshu.io/upload_images/830585-fbae9b0c3d42392e.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 1.1 [start---1.1]Proposer借助自身的PaxoProposerProtocol实例发起一个提议请求

![start---1.1_1](https://upload-images.jianshu.io/upload_images/830585-62473a5898e9963c.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

![start---1.1_2有于消息是并发执行的，这里协议的状态改变需要等到提议请求发送发送给所有的Acceptor后才会执行到这，所以start---1.1_1断点之后可能不会是这个断点](https://upload-images.jianshu.io/upload_images/830585-3034359883a64c86.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 1.2 [start---1.2]Acceptor收到一个消息，消息类型为提议。然后借助AcceptorProtocol实例处理提议。

![start---1.2](https://upload-images.jianshu.io/upload_images/830585-497771c473781c3c.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 1.3[start---1.3] AcceptorProtocol收到一个提议，判断提议版本回复Proposer承诺接受消息或拒绝消息

![start---1.3](https://upload-images.jianshu.io/upload_images/830585-8c1e7862a03bedfd.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 1.4[start---1.4]Proposer收到一个消息，类型为Acceptor的承诺(MSG_ACCEPTOR_AGREE)。既然不是Proposer最终要的接受提议的结果，转给ProposerPropotocal(当前消息的记录ID(instanceID)对应的协议)状态机处理。

![start---1.4](https://upload-images.jianshu.io/upload_images/830585-86d312bac72a269b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### [start---1.5]  and [start---2.0]
###### --[start---1.5] ProposerPropotocal状态机函数收到一个MSG_ACCEPTOR_AGREE消息，此时表示新增加一个Acceptor承诺会接受我的请求。

  ###### -- [start---2.0_1]该条件下的代码会不断执行，直到许诺Proposer的数量超过半数，表示Prepare阶段基本结束。此时协议状态更新为协议被承诺接受(STATE_AGREED)。此时的Proposer向Acceptor集合发送Accept请求，请求Acceptor确认他们的许诺。

 ###### -- [start---2.0_2]同时，向其他Proposer广播该消息，使得其他Proposer知道Prepare阶段哪个提议获得的承诺最多。这样，在Commit阶段，他们可能通过改变提议来使系统尽快达到一致性。

![start---1.5 & 2.0](https://upload-images.jianshu.io/upload_images/830585-2d19b7f6b930887b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 2.1[start---2.1]Acceptor收到一个消息，类型为来自Proposer的Accept请求。借助AcceptorPropotal处理该消息。

![start---2.1](https://upload-images.jianshu.io/upload_images/830585-7fd1a4627c2516fc.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 2.2[start---2.2] 
  ###### -- [start---2.2_1] AcceptorPropotal收到Proposer发出的Accept请求。按Paxos算法思想，这里需要判断请求版本号，当且仅当Acceptor之前承诺过的提议版本号最大值小于Accept请求版本号才会接受该Proposer提议。这里我们借助“先入为主”的思想简化问题，只要这时候协议状态为STATE_PROPOSAL_AGREED，就给所有Proposer广播消息表示自己确认接受该Proposer提议。

  ###### -- [start---2.2_2] AcceptorPropotal通知Acceptor更新InstanceRecord的值，到此时已有一个提议被一个Acceptor最终接受。

![start---2.2](https://upload-images.jianshu.io/upload_images/830585-6e6a38ed68e93c5a.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 2.3[start---2.3]Proposer收到一个消息，类型为Acceptor确认接受提议(MSG_ACCEPTOR_ACCEPT),根据该消息更新Proposer的InstanceRecord(新建record，追加协议等)。并将消息交给ProposerProtocol状态机处理。

![start---2.3](https://upload-images.jianshu.io/upload_images/830585-73c867f7445a7224.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 2.4[start---2.4] 
  ###### [start---2.4_1] -- ProposerProtocol收到一个Acceptor的最终确认消息(MSG_ACCEPTOR_ACCEPT),此时表示新增一个Acceptor最终接受了我的提议。但此时的协议状态仍然是STATE_AGREED状态，因为一个提议最终被系统接受必须先被超半数的Acceptor节点确认接受。

  ###### [start---2.4_2] STATE_AGREED条件下的代码会不断执行，直到最终接受提议的Acceptor超过半数。这时，协议状态由STATE_AGREED状态更新为最终被系统确认状态(STATE_ACCEPTED)。最后，当前Proposer更新自己的InstanceRecord记录。当然，这里也有一种可能是被超过半数节点不接受，那么同样其他Proposer节点必有一个节点提议被接受。

![start---2.4](https://upload-images.jianshu.io/upload_images/830585-f65732b2969d2c66.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

- ##### 2.5[start---2.5] Proposer更新InstanceRecord记录，如果协议最终被大多数Acceptor拒绝则尝试重新提议(步骤回到1.1)。

![start---2.5](https://upload-images.jianshu.io/upload_images/830585-3479d538cf584eff.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

# 总结
以上，我们就从代码层面对PAxos算法有一个更深入的了解，我想根据代码再反过来理解PAxos算法，势必会有一个更深刻的印象。

刚开始听说Paxos也是好几脸懵逼，也是鏖战一个周末才有这么点体悟。还在学习区块链的小小白起步中，写这篇帖子也是记录下自己学习的过程。勉之。



