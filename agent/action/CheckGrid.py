from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
import time
from utils import logger
from action import Utils


@AgentServer.custom_action("CheckGrid")
class CheckGrid(CustomAction):
    def CheckMonster(self, context: Context, image):
        # 检测是否有怪物并攻击
        checkMonsterDetail = context.run_recognition(
            "GridCheckMonster",
            image,
            pipeline_override={
                "GridCheckMonster": {
                    "recognition": "TemplateMatch",
                    "template": ["fight/TL01/m1.png", "fight/TL01/m2.png"],
                    "roi": [21, 217, 682, 762],
                    "threshold": 0.7,
                }
            },
        )

        # 对检测到的每个怪物进行攻击
        if checkMonsterDetail:
            for result in checkMonsterDetail.all_results:
                x, y, w, h = result.box
                logger.info(
                    f"检测到第{checkMonsterDetail.all_results.index(result) + 1}个怪物: {x}, {y}, {w}, {h}"
                )
                context.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
                time.sleep(0.1)
                context.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
                time.sleep(0.1)
                context.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
                time.sleep(0.1)
            return True
        else:
            return False

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        FailCheckMonsterCnt = 0
        checkGridCnt = 0
        cols, rows = 5, 6
        roi_list = Utils.calRoiList()
        roi_matrix = [roi_list[i * cols : (i + 1) * cols] for i in range(rows)]

        cnt = 15
        while cnt > 0:
            img = context.tasker.controller.post_screencap().wait().get()
            cnt -= 1
            checkGridCnt = 0
            for r in range(rows):
                for c in range(cols):  # 重试次数
                    # 计算 ROI 区域
                    x, y, w, h = roi_matrix[r][c]
                    roi_image = img[y : y + h, x : x + w]
                    left_bottom_roi = roi_image[
                        h - 15 : h, 0:20
                    ].copy()  # 提取左下角 20x20 区域
                    right_bottom_roi = roi_image[
                        h - 15 : h, w - 20 : w
                    ].copy()  # 提取右下角 20x20 区域

                    left_reco_detail = context.run_recognition(
                        "GridCheckTemplate",
                        left_bottom_roi,
                        pipeline_override={
                            "GridCheckTemplate": {
                                "recognition": "ColorMatch",
                                "method": 4,
                                "lower": [130, 135, 143],
                                "upper": [170, 175, 183],
                                "count": 10,
                            }
                        },
                    )
                    right_context = context.clone()
                    right_reco_detail = right_context.run_recognition(
                        "GridCheckTemplate", right_bottom_roi
                    )

                    if left_reco_detail or right_reco_detail:
                        count = (
                            left_reco_detail.best_result.count
                            if left_reco_detail
                            else right_reco_detail.best_result.count
                        )
                        # print(f"点开地板: ({r + 1}, {c + 1}) , count = {count}")
                        click_job = context.tasker.controller.post_click(
                            x + w // 2, y + h // 2
                        )
                        click_job.wait()
                        checkGridCnt += 1
                        time.sleep(0.05)

            # 检测怪物并进行攻击
            if not self.CheckMonster(context, img):
                FailCheckMonsterCnt += 1
                logger.info(f"FailCheckMonsterCnt: {FailCheckMonsterCnt}")

            # 如果提前清理完该层，那么不需要继续等待，可以提前退出
            if FailCheckMonsterCnt >= 5 and checkGridCnt == 0:
                logger.info("FailCheckMonsterCnt 5 次, 提前退出")
                return CustomAction.RunResult(success=True)

        return CustomAction.RunResult(success=True)
