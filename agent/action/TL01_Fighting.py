from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
import time
import re

@AgentServer.custom_action("TL01_Fighting_Test")
class TL01_Fighting(CustomAction):
    # 从一个字符串里面识仅识别一串数字, 并返回
    def extract_numbers(self, input_string):
        # 使用正则表达式匹配所有的数字
        numbers = re.findall(r'\d+', input_string)
        # 如果找到数字，返回第一个数字，否则返回 None, 返回类型为 int
        if numbers:
            return int(numbers[0])
        else:
            return None

    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    )-> CustomAction.RunResult:
        # 检查当前层数
        layers = 1
        RunResult = context.run_task("TL01_CheckLayer")
        if RunResult.nodes:
            layers = self.extract_numbers(RunResult.nodes[0].recognition.best_result.text)
            print(f"current layer {layers}")

        # 检查当前层数是否小于5层
        while layers < 5:
            # 小怪层开始探索
            print(f"Start Explore {layers} 层")
            context.run_task("TL01_clearMonsterLayer")
            time.sleep(3)
            
            # 检查当前层数
            RunResult = context.run_task("TL01_CheckLayer")
            if RunResult.nodes:
                layers = self.extract_numbers(RunResult.nodes[0].recognition.best_result.text)
                print(f"current layer :{layers}")
                
        
        # print("小怪层探索完成,检测是否存在boos")
        time.sleep(3)
        # 检查是否有Boss
        print("check Boss and fight.")
        context.run_task("TL01_checkBossMons")
        print("Boss fight complete.")
        context.run_task("BackButton")
        context.run_task("AlchemyReward")

        return CustomAction.RunResult(success=True)