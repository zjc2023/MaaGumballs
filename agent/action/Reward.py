from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
import time  

@AgentServer.custom_action("UnionReward")
class UnionReward(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        
        roi_list = [[96,814,112,110],
                   [242,812,94,102],
                   [383,816,92,94],
                   [523,816,92,94]]
        
        for roi in roi_list:
            try:
                # Click Roi区域中间
                x_center, y_center = roi[0] + roi[2] // 2, roi[1] + roi[3] // 2
                context.tasker.controller.post_click(x_center, y_center)
                context.run_task("ObtainUnionReward")

            except Exception as e:
                print(f"Recognition error: {e}")
                continue

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("UnionReward_Execute")
class UnionReward_Execute(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        
        context.run_task("EntryUnionReward")
        context.run_task("EntryUnionTask")
        
        return CustomAction.RunResult(success=True)