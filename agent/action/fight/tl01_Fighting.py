from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
from action.fight import fightUtils
import time


@AgentServer.custom_action("TL01_Fighting_Test")
class TL01_Fighting(CustomAction):

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
            layers = fightUtils.extract_num_layer(
                RunResult.nodes[0].recognition.best_result.text
            )
            # print(f"current layer {layers}")

        # 检查当前层数是否小于5层
        while layers < 5:
            # 小怪层开始探索
            print(f"Start Explore {layers} layer.")
            context.run_task("TL01_clearfightLayer")
            time.sleep(3)

            # 检查当前层数
            RunResult = context.run_task("Fight_CheckLayer")
            if RunResult.nodes:
                layers = fightUtils.extract_num_layer(
                    RunResult.nodes[0].recognition.best_result.text
                )
                # print(f"current layer :{layers}")

        # print("小怪层探索完成,检测是否存在boos")
        time.sleep(3)
        # 检查是否有Boss
        print("Start BossBattle.")
        context.run_task("TL01_checkBossMons")
        print("Finish And Return")
        context.run_task("BackText")
        print("Click AlchemyReward")
        context.run_task("AlchemyReward")

        return CustomAction.RunResult(success=True)
