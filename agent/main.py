from queue import SimpleQueue
import sys
from threading import Thread
import time
import random

from maa.controller import AdbController
from maa.custom_recognition import CustomRecognition
from maa.define import TaskDetail
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit


resource = Resource()
resource.set_cpu()
resource.post_bundle("./assets/resource").wait()




class MaaWorker:
    def __init__(self, queue: SimpleQueue, api_key):
        user_path = "./"
        Toolkit.init_option(user_path)

        self.queue = queue
        self.tasker = Tasker()
        self.connected = False
        # self.ai_resolver = AIResolver(api_key=api_key)
        self.stop_flag = False
        self.pause_flag = False
        self.send_log("MAA初始化成功")

        # 启动日志消费者线程
        self.log_file = "logs.txt"
        self.log_thread = Thread(target=lambda: self.log_consumer_to_screen_and_file(self.log_file))
        self.log_thread.start()

    def send_log(self, msg):
        self.queue.put(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} {msg}")
        time.sleep(0.05)

    def pause(self):
        self.send_log("任务暂停")
        self.pause_flag = True
        while self.pause_flag:
            time.sleep(0.05)

    def log_consumer_to_screen_and_file(self, log_file):
        with open(log_file, "a", encoding="utf-8") as f:
            while True:
                log_message = self.queue.get()  # 从队列中取出消息
                if log_message == "STOP":  # 停止标志
                    break
                print(log_message)  # 打印到屏幕
                f.write(log_message + "\n")  # 写入日志到文件

    @staticmethod
    def get_device():
        adb_devices = []
        for device in Toolkit.find_adb_devices():
            # 这两个字段的数字在JS里会整数溢出，转为字符串处理
            # device.input_methods = str(device.input_methods)
            # device.screencap_methods = str(device.screencap_methods)
            if device not in adb_devices:
                adb_devices.append(device)
        return adb_devices

    def connect_device(self, device):
        controller = AdbController(
            adb_path=device.adb_path,
            address=device.address,
            screencap_methods=device.screencap_methods,
            input_methods=device.input_methods,
            config=device.config,
        )
        status = controller.post_connection().wait().succeeded
        if not status:
            self.send_log("设备连接失败，请检查终端日志")
            return self.connected
        if self.tasker.bind(resource, controller):
            self.connected = True
            self.send_log("设备连接成功")
        else:
            self.send_log("设备连接失败，请检查终端日志")
        return self.connected
    
    def task(self, tasks):
        self.stop_flag = False
        if not self.connected:
            self.send_log("设备未连接，请检查终端日志")
            return False
        if not tasks:
            self.send_log("没有任务，请检查终端日志")
            return False
        
        for task in tasks:
            if self.stop_flag:
                self.send_log("任务已停止")
                return

            if task == "启动游戏":
                self.send_log("开始执行启动游戏任务")
            elif task == "伊甸收菜":
                self.send_log("开始执行伊甸收菜任务")
                self.dailyTask()
                # self.tasker.post_task(TaskDetail.Eden).wait()
            elif task == "商店":
                self.send_log("开始执行商店任务")
                # self.tasker.post_task(TaskDetail.Store).wait()
            else:
                self.send_log(f"未知任务类型：{task}")
        self.send_log("所有任务完成")
        time.sleep(0.5)
    
    def startUpGame(self):
        self.send_log("开始执行启动游戏任务")
        if not self.connected:
            self.send_log("设备未连接，请检查终端日志")
            return False

        # 启动游戏
        self.send_log("开始启动敲砖大冒险")
        self.tasker.post_task("Sub_StartUp").wait()
        time.sleep(random.randint(2, 3))
        self.send_log("启动敲砖大冒险成功")

    def dailyTask(self):
        self.send_log("开始执行每日任务")
        self.stop_flag = False
        finish_task = []
        finish_time = 0

        # 进入伊甸大厅
        self.send_log("开始进入伊甸大厅")
        self.tasker.post_task("EntryEden").wait()
        time.sleep(random.randint(2, 3))
        self.send_log("进入战术大厅成功，开始进入每日收菜")
        taskList_ = ["DailySweep","WildernessExplore", "SendLizards", "AlchemySignboard",
                     "DailySignIn","SkyExplore","RuinsExplore"]
        for task in taskList_:
            if self.stop_flag:
                self.send_log("任务已停止")
                return
            if task in finish_task:
                continue
            self.send_log(f"开始执行{task}任务")
            self.tasker.post_task(task).wait()
            time.sleep(random.randint(3, 4))
            self.send_log(f"执行完成{task}任务")

        self.send_log("每日任务完成")
        time.sleep(0.5)

if __name__ == "__main__":
    
    worker = MaaWorker(SimpleQueue(), "123456")
    adb_devices = worker.get_device()

    if not adb_devices:
        print("没有找到可用设备，请检查终端日志")
        worker.send_log("没有找到可用设备，请检查终端日志")
    else:
        print("找到可用设备：")
        for device in adb_devices:
            if worker.connect_device(device):
                break
    
    # 启动游戏
    worker.startUpGame()

    # 启动任务
    tasks = ["伊甸收菜"]
    worker.task(tasks)

    # 停止日志消费者线程
    worker.queue.put("STOP")  # 向队列发送停止信号
    worker.log_thread.join()  # 等待线程结束
    # worker.send_log("日志线程已退出")