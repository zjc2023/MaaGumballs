from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
from loguru import logger
import time
import re

@AgentServer.custom_action("JJC101")
class JJC101(CustomAction):
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
        # layers = 1
        # RunResult = context.run_task("TL01_CheckLayer")
        # if RunResult.nodes:
        #     layers = self.extract_numbers(RunResult.nodes[0].recognition.best_result.text)
        #     logger.info(f"current layer {layers}")

        # 检查当前层数是否小于5层
        # while layers < 5:
        #     # 小怪层开始探索
        #     print(f"Start Explore {layers} layer.")
        #     context.run_task("TL01_clearMonsterLayer")
        #     time.sleep(3)
            
        #     # 检查当前层数
        #     RunResult = context.run_task("TL01_CheckLayer")
        #     if RunResult.nodes:
        #         layers = self.extract_numbers(RunResult.nodes[0].recognition.best_result.text)
                # print(f"current layer :{layers}")

        return CustomAction.RunResult(success=True)
    

    
@AgentServer.custom_action("JJC101_Select")
class JJC101_Select(CustomAction):

    

    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    )-> CustomAction.RunResult:
        logger.info("选择药剂中")
        context.run_task("JJC_SelectDrug")

        logger.info("选择神器中")
        context.run_task("JJC_SelectArtifact")

        # 选择帝释天
        img = context.tasker.controller.post_screencap().wait().get()
        recodetail = context.run_recognition("JJC_Select_Gumball_Check", img, pipeline_override={
            "JJC_Select_Gumball_Check": {
                "recognition": "FeatureMatch",
                "template": "fight/JJC/帝释天冈布奥.png",
                "roi": [
                    400,
                    645,
                    85,
                    84
                ]
            },
        })

        if recodetail:
            logger.info("帝释天已检测到")
        else: 
            logger.info("帝释天未检测到，自动选择中")
            context.run_task("JJC_Select_Gumball_1", pipeline_override={
                "JJC_Select_Gumball_Next":{
                    "template": "fight/JJC/帝释天冈布奥.png",
                }
            })

        # 选择夜叉
        img = context.tasker.controller.post_screencap().wait().get()
        recodetail = context.run_recognition("JJC_Select_Gumball_Check", img, pipeline_override={
            "JJC_Select_Gumball_Check": {
                "recognition": "FeatureMatch",
                "template": "monster/JJC/夜叉冈布奥.png",
                "roi": [
                    400,
                    645,
                    85,
                    84
                ]
            },
        })
        if recodetail:
            logger.info("夜叉已检测到")
        else :
            logger.info("夜叉未检测到, 自动选择中")
            context.run_task("JJC_Select_Gumball_2", pipeline_override={
                "JJC_Select_Gumball_Next":{
                "template": "monster/JJC/夜叉冈布奥.png",
                }
            })


        return CustomAction.RunResult(success=True)