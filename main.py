from queue import SimpleQueue
import sys
import time

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

    def send_log(self, msg):
        self.queue.put(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} {msg}")
        time.sleep(0.05)

    def pause(self):
        self.send_log("任务暂停")
        self.pause_flag = True
        while self.pause_flag:
            time.sleep(0.05)

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
            self.send_log("正在启动 学习强国")
            controller.post_start_app("com.leiting.gumballs.leiting").wait()
            # self.tasker.post_task("Sub_StartUp").wait()
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
                # self.tasker.post_task(TaskDetail.Eden).wait()
            elif task == "商店":
                self.send_log("开始执行商店任务")
                # self.tasker.post_task(TaskDetail.Store).wait()
            else:
                self.send_log(f"未知任务类型：{task.task_type}")
        self.send_log("所有任务完成")
        time.sleep(0.5)
    def dailyTask(self):
        self.send_log("开始执行每日任务")
        self.tasker.post_task("每日任务").wait()
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
    
    # main()
