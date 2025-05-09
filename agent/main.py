from queue import SimpleQueue
from collections import deque
from threading import Thread
import numpy as np
import sys
import time
import random
import cv2

from maa.agent.agent_server import AgentServer
from maa.controller import AdbController
from maa.define import TaskDetail
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit
from maa.context import Context

from action import CheckGrid
from action import TL01_Fighting

import os
import utils

# 默认编码 utf-8
sys.stdout.reconfigure(encoding="utf-8")
# 获取当前main.py所在路径并设置上级目录为工作目录
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
parent_dir = os.path.dirname(current_dir)
os.chdir(parent_dir)
print(f"设置工作目录为: {parent_dir}")

# 将当前目录添加到路径
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 获取当前工作目录
'''
resource = Resource()
resource.set_cpu()
resource_path = f"{parent_dir}/resource"
assets_resource_path = f"{parent_dir}/assets/resource"

# 检查路径是否存在，如果存在再绑定
if os.path.exists(resource_path):
    resource.post_bundle(resource_path).wait()

if os.path.exists(assets_resource_path):
    resource.post_bundle(assets_resource_path).wait()
'''

class MaaWorker:
    def __init__(self, queue: SimpleQueue, api_key):
        user_path = "./"
        Toolkit.init_option(user_path)

        self.queue = queue
        self.tasker = Tasker()
        self.connected = False
        self.context = Context
        # self.ai_resolver = AIResolver(api_key=api_key)
        self.stop_flag = False
        self.pause_flag = False
        self.send_log("MAA初始化成功")

        # 启动日志消费者线程
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        self.log_file = os.path.join(log_dir, f"logs_{current_time}.txt")
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
                self.startUpGame()
            elif task == "伊甸收菜":
                self.send_log("开始执行伊甸收菜任务")
                self.dailyTask()
            elif task == "商店":
                self.send_log("开始执行商店任务")
                # self.tasker.post_task(TaskDetail.Store).wait()
            elif task == "活动副本":
                self.send_log("开始执行限时副本任务")
                for i in range(1, 3):
                    # 清除格子
                    self.clearGrid()
                    print(f"完成{i}次探索") 
                    time.sleep(3)
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

        self.tasker.post_task("BackButton_Third").wait()
        self.send_log("每日任务完成")

        time.sleep(0.5)

    def bfs_explore1(self, roi_matrix):
        rows, cols = len(roi_matrix), len(roi_matrix[0])
        FailCheckMonsterCnt = 0
        checkGridCnt = 0
        cnt = 15

        while cnt > 0:
            cnt -= 1
            checkGridCnt = 0
            # 初始化队列，将所有偏白色的格子加入队列
            image = self.tasker.controller.post_screencap().wait().get()
            for r in range(rows):
                for c in range(cols):
                    x, y, w, h = roi_matrix[r][c]
                    roi_image = image[y:y + h, x:x + w]


                    # 自定义颜色匹配逻辑，仅检测左下角 20x20 的区域
                    h, w = roi_image.shape[:2]
                    left_bottom_roi = roi_image[h-15:h, 0: 20]  # 提取左下角 20x20 区域
                    right_bottom_roi = roi_image[h-15:h, w - 20: w]  # 提取右下角 20x20 区域
                    
                    # 修正文件名格式
                    file_name = f"./grid/roi_image_{r + 1}_{c + 1}.png"
                    cv2.imwrite(file_name, roi_image)  # 保存当前格子图像用于调试
                    leftButtonName = f"./grid/leftGrid{r + 1}_{c + 1}.png"
                    rightButtonName = f"./grid/rightGrid{r + 1}_{c + 1}.png"
                    cv2.imwrite(leftButtonName, left_bottom_roi)  # 保存当前格子图像用于调试
                    cv2.imwrite(rightButtonName, right_bottom_roi)  # 保存当前格子图像用于调试

                    lower_bound = np.array([130,135,143])  # 偏白色的下界
                    upper_bound = np.array([170,175,183])  # 偏白色的上界
                    mask = cv2.inRange(left_bottom_roi, lower_bound, upper_bound)
                    mask2 = cv2.inRange(right_bottom_roi, lower_bound, upper_bound)  # 右下角区域
                    white_pixel_count = cv2.countNonZero(mask)
                    white_pixel_count2 = cv2.countNonZero(mask2)  # 右下角区域

                    # 如果白色像素数量超过阈值，则认为匹配到
                    threshold = 10  # 根据实际情况调整阈值
                    
                    if white_pixel_count > threshold or white_pixel_count2 > threshold:
                        self.send_log(f"点开地板: ({r + 1}, {c + 1}), 白色像素数量: {white_pixel_count, white_pixel_count2}")
                        checkGridCnt += 1
                        self.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
                        time.sleep(0.05)

            # 检测怪物并进行攻击
            check:TaskDetail = self.tasker.post_task("TL01_checkMonster").wait().get()
            if check.nodes:
                for result in check.nodes[0].recognition.all_results:
                    x, y, w, h = result.box
                    self.send_log(f"快速點擊三次 {x}, {y}, {w}, {h}") 
                    self.tasker.controller.post_click( x + w // 2, y + h // 2).wait()
                    time.sleep(0.05)
                    self.tasker.controller.post_click( x + w // 2, y + h // 2).wait()
                    time.sleep(0.05)
                    self.tasker.controller.post_click( x + w // 2, y + h // 2).wait()
                    time.sleep(0.05)
            else :
                FailCheckMonsterCnt += 1
                self.send_log(f"FailCheckMonsterCnt: {FailCheckMonsterCnt}")
            
            # 如果提前清理完该层，那么不需要继续等待，可以提前退出
            if FailCheckMonsterCnt >= 5 and checkGridCnt == 0:
                self.send_log("FailCheckMonsterCnt 5 次, 提前退出")
                break
        self.send_log("bfs explore finish")

    def clearGrid(self):
        # 计算ROI坐标
        roi_list = utils.calCoordinate()
        # 将 roi_list 转换为 6x5 的二维矩阵
        layers = 1
        rows, cols = 6, 5
        roi_matrix = [roi_list[i * cols:(i + 1) * cols] for i in range(rows)]
        self.send_log("开始探索地图")
        self.tasker.post_task("TL01_Start").wait()

        # 检查当前层数
        check:TaskDetail = self.tasker.post_task("TL01_CheckLayer").wait().get()
        if check.nodes:
            layers = utils.extract_numbers(check.nodes[0].recognition.best_result.text)
            self.send_log(f"当前层数是 {layers}")

        # 检查当前层数是否小于5层
        while layers < 5:
            # 小怪层开始探索
            self.send_log(f"开始探索第{layers}层")
            self.bfs_explore1(roi_matrix)

            # 检查是否有奖励
            self.tasker.post_task("TL01_OpenRewardBox").wait()
            self.send_log(f"第{layers}层探索完成")

            # 检查是否卡返回界面
            self.tasker.post_task("BackButton").wait()
            self.send_log("检查返回按钮, 点击返回")

            # check 门
            check:TaskDetail = self.tasker.post_task("CheckDoor").wait().get()
            if check.nodes:
                self.send_log("check door!!")
                # 场景切换等待
                time.sleep(3)

            # 检查当前层数
            check:TaskDetail = self.tasker.post_task("TL01_CheckLayer").wait().get()
            if check.nodes:    
                layers = utils.extract_numbers(check.nodes[0].recognition.best_result.text)
                self.send_log(f"当前层数是 {layers}")
            
        
        self.send_log("小怪层探索完成,检测是否存在boos")
        time.sleep(3)
        # 检查是否有Boss
        self.tasker.post_task("TL01_checkBossMons").wait()
        self.send_log("探索完成，开始领取奖励")
        self.tasker.post_task("BackButton").wait()
        self.tasker.post_task("AlchemyReward").wait()
        

def mainFunc(tasks):
    worker = MaaWorker(SimpleQueue(), "123456")
    adb_devices = worker.get_device()
    if not adb_devices.__sizeof__:
        print("没有找到可用设备，请检查终端日志")
        worker.send_log("没有找到可用设备，请检查终端日志")
        return
    else:
        for device in adb_devices:
            if worker.connect_device(device):
                print("设备连接成功")
                worker.send_log("设备连接成功")
                break
            else :
                print("设备连接失败，请检查终端日志")
                worker.send_log("设备连接失败，请检查终端日志")
                return 

    # 启动任务
    worker.task(tasks)

    # 停止日志消费者线程
    worker.queue.put("STOP")  # 向队列发送停止信号
    worker.log_thread.join()  # 等待线程结束
    worker.send_log("日志线程已退出")

if __name__ == "__main__":
    Toolkit.init_option("./")
    if len(sys.argv) > 1:
        print("use socket_id: " + sys.argv[-1])
        socket_id = sys.argv[-1]
    else:
        print("Use Default socket_id: MAA_AGENT_SOCKET")
        socket_id = "MAA_AGENT_SOCKET"
    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()

    # tasks.append("启动游戏")
    # tasks.append("伊甸收菜")
    # tasks.append("活动副本")
    # mainFunc(tasks)
    # testFunc()