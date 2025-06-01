from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
from utils import logger

import time


@AgentServer.custom_action("GoDownstairsTrick_Test")
class GoDownstairsTrick_Test(CustomAction):
    # 这里检查永恒套装
    def CheckEternalSuit(self, context: Context, image, tartget_equipment_path):
        checkEternalDetail = context.run_recognition(
            "CheckEternalSuit",
            image,
            pipeline_override={
                "CheckEternalSuit": {
                    "recognition": "TemplateMatch",
                    "template": [tartget_equipment_path],
                    "roi": [30, 68, 665, 590],
                    "threshold": 0.7,
                }
            },
        )
        return checkEternalDetail

    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        # 这里检查永恒套装
        logger.info("黑永恒 检查是否有目标装备")
        context.run_task("OpenEquipmentPackage")
        img = context.tasker.controller.post_screencap().wait().get()
        before_gloves = self.CheckEternalSuit(
            context, img, "equipments/5level/永恒腕轮.png"
        )
        before_cloak = self.CheckEternalSuit(
            context, img, "equipments/5level/永恒披风.png"
        )
        before_helmet = self.CheckEternalSuit(
            context, img, "equipments/5level/永恒王冠.png"
        )
        before_weapon = self.CheckEternalSuit(
            context, img, "equipments/5level/永恒之球.png"
        )
        context.run_task("BackText")

        for i in range(30):
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)

            logger.info(f"黑永恒第{i}次尝试")
            context.run_task("Save_Status")
            context.run_task("StartAppV2")
            context.run_task("CheckDoor")
            context.run_task("CheckClosedDoor")
            context.run_task("Use_Earthquake")
            context.run_task("KillChestMonster")

            logger.info("黑永恒 检查是否黑到目标装备")
            context.run_task("OpenEquipmentPackage")
            time.sleep(1)
            img_2 = context.tasker.controller.post_screencap().wait().get()
            temp = 0
            if not before_gloves:
                after_gloves = self.CheckEternalSuit(
                    context, img_2, "equipments/5level/永恒腕轮.png"
                )
                if after_gloves:
                    temp += 1
            else:
                after_gloves = before_gloves
            if not before_cloak:
                after_cloak = self.CheckEternalSuit(
                    context, img_2, "equipments/5level/永恒披风.png"
                )
                if after_cloak:
                    temp += 1
            else:
                after_cloak = before_cloak
            if not before_helmet:
                after_helmet = self.CheckEternalSuit(
                    context, img_2, "equipments/5level/永恒王冠.png"
                )
                if after_helmet:
                    temp += 1
            else:
                after_helmet = before_helmet
            if not before_weapon:
                after_weapon = self.CheckEternalSuit(
                    context, img_2, "equipments/5level/永恒之球.png"
                )
                if after_weapon:
                    temp += 1
            else:
                after_weapon = before_weapon

            context.run_task("BackText")

            if temp >= 1:
                logger.info("黑永恒成功，恢复网络，可以暂离保存")
                context.run_task("StopAppV2")
                time.sleep(1)
                context.run_task("Save_Status")
                return CustomAction.RunResult(success=True)

            else:
                logger.info("黑永恒失败, 小SL然后联网进行下一次尝试")
                context.run_task("LogoutGame")
                time.sleep(3)
                context.run_task("StopAppV2")
                context.run_task("ReturnMaze")

        logger.warning("黑永恒失败")
        return CustomAction.RunResult(success=False)
