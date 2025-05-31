from asyncio import tasks
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from loguru import logger
from numpy import true_divide
from action import Utils

import time


@AgentServer.custom_action("JJC101")
class JJC101(CustomAction):
    # 从一个字符串里面识仅识别一串数字, 并返回

    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        # 检查当前层数
        layers = 1
        RunResult = context.run_task("Fight_CheckLayer")
        if RunResult.nodes:
            layers = Utils.extract_numbers(
                RunResult.nodes[0].recognition.best_result.text
            )
            logger.info(f"current layer {layers}")

        # 检查当前层数是否小于29层
        while layers < 29:
            # 小怪层开始探索
            print(f"Start Explore {layers} layer.")
            context.run_task("JJC_Fight_ClearCurrentLayer")
            time.sleep(3)

            # 检查当前层数
            RunResult = context.run_task("Fight_CheckLayer")
            if RunResult.nodes:
                layers = Utils.extract_numbers(
                    RunResult.nodes[0].recognition.best_result.text
                )
        print(f"current layer :{layers}")

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("JJC101_Select")
class JJC101_Select(CustomAction):
    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        logger.info("选择药剂中")
        context.run_task("JJC_SelectDrug")

        logger.info("选择神器中")
        context.run_task("JJC_SelectArtifact")

        # 选择帝释天
        img = context.tasker.controller.post_screencap().wait().get()
        recodetail = context.run_recognition(
            "JJC_Select_Gumball_Check",
            img,
            pipeline_override={
                "JJC_Select_Gumball_Check": {
                    "recognition": "TemplateMatch",
                    "template": ["fight/JJC/帝释天冈布奥_小.png"],
                    "roi": [348, 604, 294, 231],
                },
            },
        )

        if recodetail:
            logger.info("帝释天已检测到")
        else:
            logger.info("帝释天未检测到，自动选择中")
            context.run_task(
                "JJC_Select_Gumball_1",
                pipeline_override={
                    "JJC_Select_Gumball_Next": {
                        "template": "fight/JJC/帝释天冈布奥.png",
                    }
                },
            )

        # 选择夜叉
        img = context.tasker.controller.post_screencap().wait().get()
        recodetail = context.run_recognition(
            "JJC_Select_Gumball_Check",
            img,
            pipeline_override={
                "JJC_Select_Gumball_Check": {
                    "recognition": "TemplateMatch",
                    "template": ["fight/JJC/夜叉冈布奥_小.png"],
                    "roi": [348, 604, 294, 231],
                },
            },
        )
        if recodetail:
            logger.info("夜叉已检测到")
        else:
            logger.info("夜叉未检测到, 自动选择中")
            context.run_task(
                "JJC_Select_Gumball_2",
                pipeline_override={
                    "JJC_Select_Gumball_Next": {
                        "template": "fight/JJC/夜叉冈布奥.png",
                    }
                },
            )

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("JJC101_Title")
class JJC101_Title(CustomAction):

    def Fight_CheckLayer(self, context: Context):
        RunResult = context.run_task("Fight_CheckLayer")
        if RunResult.nodes:
            layers = Utils.extract_numbers(
                RunResult.nodes[0].recognition.best_result.text
            )
            logger.info(f"current layer {layers}")
            return layers
        else:
            return 0

    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        layers = self.Fight_CheckLayer(context)
        if layers > 0:
            # 打开称号面板
            recodetail = context.run_task("Fight_TitlePanel_Open")
            if not recodetail.nodes:
                logger.warning("打开称号面板失败, 识别错误")
                return CustomAction.RunResult(success=False)
            else:
                logger.info("打开称号面板")

            # 进入冒险系称号
            recodetail = context.run_task(
                "Fight_TitlePanel_Series",
                pipeline_override={"Fight_TitlePanel_Series": {"expected": "冒险"}},
            )

            if not recodetail.nodes:
                logger.warning("进入冒险系称号失败, 请检查是否携带冒险系冈布奥")
                return CustomAction.RunResult(success=False)
            else:
                logger.info("进入冒险系称号")

            # 选择称号
            logger.info("开始学习称号")
            recodetail = context.run_recognition("Fight_TitlePanel_Learnable", img)
            if not recodetail:
                logger.warning("当前冒险系没有可学习的称号")
                return CustomAction.RunResult(success=False)

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("JJC_Fight_ClearCurrentLayer")
class JJC_Fight_ClearCurrentLayer(CustomAction):
    def CheckMonster(self, context: Context, image):
        # 检测是否有怪物并攻击
        checkMonsterDetail = context.run_recognition(
            "GridCheckMonster",
            image,
            pipeline_override={
                "GridCheckMonster": {
                    "recognition": "TemplateMatch",
                    "template": [
                        "fight/JJC/m1.png",
                        "fight/JJC/m2.png",
                        "fight/JJC/m3.png",
                        "fight/JJC/m4.png",
                    ],
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

    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        # 进入战斗
        context.run_task("JJC_Fight_Enter")
        FailCheckMonsterCnt = 0
        checkGridCnt = 0
        cols, rows = 5, 6
        roi_list = Utils.calRoiList()
        roi_matrix = [roi_list[i * cols : (i + 1) * cols] for i in range(rows)]

        cnt = 15
        while cnt > 0:
            if context.tasker.stopping:
                logger.info("JJC_Fight_ClearCurrentLayer 被停止")
                return CustomAction.RunResult(success=False)

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
                        context.tasker.controller.post_click(
                            x + w // 2, y + h // 2
                        ).wait()
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
