from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
import time
import cv2
import numpy as np

from maa.job import TaskDetail

@AgentServer.custom_action("CheckGrid")
class CheckGrid(CustomAction):
    def calRoiList(self):
        start_x, start_y = 15, 222
        width, height = 138, 126
        cols, rows = 5, 6

        roi_list = []

        for r in range(rows):
            for c in range(cols):
                x = start_x + c * width
                y = start_y + r * height
                roi = [x, y, width, height]
                roi_list.append(roi)
        return roi_list

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        cols, rows = 5, 6

        roi_list = self.calRoiList()
        roi_matrix = [roi_list[i * cols:(i + 1) * cols] for i in range(rows)]


        FailCheckMonsterCnt = 0
        checkGridCnt = 0
        cnt = 15
        while cnt > 0:
            img = context.tasker.controller.post_screencap().wait().get()
            cnt -= 1
            checkGridCnt = 0
            for r in range(rows):
                for c in range(cols):  # 重试次数
                    x, y, w, h = roi_matrix[r][c]
                    roi_image = img[y:y + h, x:x + w]
                    left_bottom_roi = roi_image[h-15:h, 0: 20]  # 提取左下角 20x20 区域
                    right_bottom_roi = roi_image[h-15:h, w - 20: w]  # 提取右下角 20x20 区域
                    
                    # 修正文件名格式
                    file_name = f"./grid/roi_image_{r + 1}_{c + 1}.png"
                    cv2.imwrite(file_name, roi_image)  # 保存当前格子图像用于调试
                    leftButtonName = f"./grid/leftGrid{r + 1}_{c + 1}.png"
                    rightButtonName = f"./grid/rightGrid{r + 1}_{c + 1}.png"
                    cv2.imwrite(leftButtonName, left_bottom_roi)  # 保存当前格子图像用于调试
                    cv2.imwrite(rightButtonName, right_bottom_roi)  # 保存当前格子图像用于调试

                    # 由于 cv2.inRange 实际上可以接受列表作为参数，因此可以直接用列表替代 np.array
                    lower_bound = np.array([130,135,143])  # 偏白色的下界
                    upper_bound = np.array([170,175,183])  # 偏白色的上界
                    mask = cv2.inRange(left_bottom_roi, lower_bound, upper_bound)
                    mask2 = cv2.inRange(right_bottom_roi, lower_bound, upper_bound)  # 右下角区域
                    white_pixel_count = cv2.countNonZero(mask)
                    white_pixel_count2 = cv2.countNonZero(mask2)  # 右下角区域
                    
                    threshold = 10  # 根据实际情况调整阈值
                    if white_pixel_count > threshold or white_pixel_count2 > threshold:
                        # self.send_log(f"点开地板: ({r + 1}, {c + 1}), 白色像素数量: {white_pixel_count, white_pixel_count2}")
                        checkGridCnt += 1
                        context.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
                        time.sleep(0.05)

                    # left_reco_detail = context.run_recognition(
                    #     "GridCheckTemplate",
                    #     left_bottom_roi,
                    #     pipeline_override={
                    #         "GridCheckTemplate": {
                    #             "recognition": "ColorMatch",
                    #             "method": 4,
                    #             "lower": [130, 135, 143],
                    #             "upper": [170, 175, 183],
                    #             "count": 10
                    #         }
                    #     },
                    # )
                    # right_context = context.clone()
                    # right_reco_detail = right_context.run_recognition("GridCheckTemplate", right_bottom_roi)

                    # if left_reco_detail or right_reco_detail:
                    #     count = left_reco_detail.best_result.count if left_reco_detail else right_reco_detail.best_result.count
                    #     print(f"点开地板: ({r + 1}, {c + 1}) , count = {count}")
                    #     click_job = context.tasker.controller.post_click(x + w // 2, y + h // 2)
                    #     click_job.wait()
                    #     checkGridCnt += 1


            # 检测怪物并进行攻击
            check: TaskDetail = context.run_task("TL01_checkMonster")
            # check: TaskDetail= context.tasker.post_task("TL01_checkMonster").wait().get()
            if check.nodes:
                for result in check.nodes[0].recognition.all_results:
                    x, y, w, h = result.box
                    print(f"快速點擊三次 {x}, {y}, {w}, {h}") 
                    context.tasker.controller.post_click( x + w // 2, y + h // 2).wait()
                    time.sleep(0.05)
                    context.tasker.controller.post_click( x + w // 2, y + h // 2).wait()
                    time.sleep(0.05)
                    context.tasker.controller.post_click( x + w // 2, y + h // 2).wait()
                    time.sleep(0.05)
            else :
                FailCheckMonsterCnt += 1
                print(f"FailCheckMonsterCnt: {FailCheckMonsterCnt}")
            
            # 如果提前清理完该层，那么不需要继续等待，可以提前退出
            if FailCheckMonsterCnt >= 5 and checkGridCnt == 0:
                print("FailCheckMonsterCnt 5 次, 提前退出")
                return CustomAction.RunResult(success=True)
        
        print("CheckGrid is running!")
        return CustomAction.RunResult(success=True)
