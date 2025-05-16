from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

@AgentServer.custom_action("CircusReward")
class CircusReward(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        
        context.run_task("getCircusReward_01")
        context.run_task("getCircusReward_01")
        context.run_task("getCircusReward_02")
        context.run_task("getCircusReward_03")

        return CustomAction.RunResult(success=True)
