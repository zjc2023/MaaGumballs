from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
from utils import logger
import time


@AgentServer.custom_action("PoolTrick_Test")
class PoolTrick_Test(CustomAction):

    # 这里检查攻击力数值
    def getArmorATK(self, context: Context) -> int:
        armorATK = 0

        context.run_task("OpenArmorPage")
        recoDetail = context.run_task("OCRArmorATK")
        if recoDetail.nodes:
            armorATK = recoDetail.nodes[0].recognition.best_result.text
            logger.info(f"检测当前攻击力数值: {armorATK}")

        context.run_task("BackText")
        return int(armorATK)

    # 这里检查火神
    def checkFiregod(self, context: Context):
        time.sleep(0.5)
        img = context.tasker.controller.post_screencap().wait().get()
        checkfiregodDetail = context.run_recognition(
            "CheckEternalSuit",
            img,
            pipeline_override={
                "CheckEternalSuit": {
                    "recognition": "TemplateMatch",
                    "template": [
                        "divineForgeLand/Firegod.png",
                        "divineForgeLand/RedHatBody.png",
                        "divineForgeLand/Weapon.png",
                    ],
                    "roi": [8, 131, 710, 997],
                    "timeout": 3000,
                }
            },
        )
        return checkfiregodDetail

    # 这里是核心函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        # 这里检查攻击力数值
        before_ArmorATK = self.getArmorATK(context)

        # 这里保存状态
        context.run_task("Save_Status")

        # 先找到泉水位置
        checkCount = 10
        searchpoolpos = None
        searchDetail = context.run_task("SearchPool")
        while not (searchDetail or checkCount <= 0):
            checkCount -= 1
            searchDetail = context.run_task("SearchPool")
        if searchDetail:
            logger.info("找到泉水位置")
            searchpoolpos = searchDetail.nodes[0].recognition.best_result.box
        else:
            logger.info("没有找到泉水位置")
            return CustomAction.RunResult(success=False)

        # 检查是否有火神，如果有可以不用释放技能推序
        firegod = self.checkFiregod(context)

        # 这里进行小退，恢复现场
        context.run_task("LogoutGame")
        context.run_task("ReturnMaze")

        # 这里进行小退，恢复尸体
        for i in range(31):
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)
            logger.info(f"黑泉水第{i}次尝试")

            if not firegod:
                context.run_task("PushOne")
            context.run_task("Save_Status")

            # 每次暂离之后，执行点击泉水的操作
            click_job = context.tasker.controller.post_click(
                searchpoolpos[0] + searchpoolpos[2] // 2,
                searchpoolpos[1] + searchpoolpos[3] // 2,
            )
            click_job.wait()
            time.sleep(0.1)

            # 翻找泉水
            context.run_task("SearchPool_Next")

            # 检查是否泉水加成在攻击
            after_ArmorATK = self.getArmorATK(context)
            if after_ArmorATK != before_ArmorATK:
                logger.info(
                    f"黑泉水成功，检测到攻击力数值提升: {after_ArmorATK - before_ArmorATK}"
                )
                context.run_task("Save_Status")
                return CustomAction.RunResult(success=True)

            # 不满足条件则小退恢复尸体
            context.run_task("LogoutGame")
            context.run_task("ReturnMaze")

        logger.warning("黑泉水失败")
        return CustomAction.RunResult(success=False)
