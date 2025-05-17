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
        argv: dict = json.loads(argv.custom_action_param)
        
        # 检查注释中的键值是否为1
        task_keys = [
            "DailySweep", "WildernessExplore", "SendLizards",
            "AlchemySignboard", "DailySignIn", "SkyExplore", "RuinsExplore"
        ]
        
        for key in task_keys:
            if argv.get(key) == 1:
                # 生成任务执行逻辑框架
                print(f"执行任务: {key}")
                context.run_task(key)
                context.run_task("ReturnHall")
                time.sleep(3)  # 
                # 用户可在此处添加具体实现

        return CustomAction.RunResult(success=True)
