from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from loguru import logger
import time  


@AgentServer.custom_action("SaveLoad_little")
class SaveLoad_little(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        img = context.tasker.controller.post_screencap().wait().get()
        reco_inMaze = context.run_recognition("ConfirmEquipmentPack", img)
        if reco_inMaze:
            # 登出游戏
            logger.info("登出游戏")
            context.run_task("LogoutGame")

            # 返回迷宫
            logger.info("返回迷宫") 
            context.run_task("ReturnMaze")
        else :
            logger.warning("不在迷宫中，无需保存")
        
        return CustomAction.RunResult(success=True)