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