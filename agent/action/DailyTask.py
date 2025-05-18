from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
import json
import time  

@AgentServer.custom_action("DailyTaskSelect")
class DailyTask(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        taskList: dict = json.loads(argv.custom_action_param)
        print(taskList)
        
        for key in taskList:
            if taskList.get(key) == 1:
                # 生成任务执行逻辑框架
                print(f"执行任务: {key}")
                context.run_task(key)
                context.run_task("ReturnHall")
                time.sleep(3)  # 
                # 用户可在此处添加具体实现

        return CustomAction.RunResult(success=True)
