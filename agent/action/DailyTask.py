from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils import logger

import json
import time  

@AgentServer.custom_action("DailyTaskSelect")
class DailyTask(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        taskList: dict = json.loads(argv.custom_action_param)
        logger.info(taskList)
        
        for key in taskList:
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)
            
            if taskList.get(key) == 1:
                # 生成任务执行逻辑框架
                logger.info(f"执行任务: {key}")
                context.run_task(key)

                logger.info(f"完成任务: {key}")
                context.run_task("ReturnHall")
                
                time.sleep(2)

        return CustomAction.RunResult(success=True)
