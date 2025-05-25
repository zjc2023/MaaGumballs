from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
from utils import logger

import time
import re
import json

@AgentServer.custom_action("SunlightTrick_Test")
class SunlightTrick_Test(CustomAction):
    def getImprintNumber(self, context: Context)-> list:
        # Init
        sunlightimprintnumber = 0
        starlightimprintnumber = 0

        # 打开刻印背包
        context.run_task("OpenArmorPage")
        context.run_task("OpenImprintPage")

        # 这里检查日光和星光
        context.run_task("ClickSunlightImprint")
        sunLightDetail = context.run_task("findpercent")
        context.run_task("ClickStarlightImprint")
        starLightDetail = context.run_task("findpercent")

        # 如果检测到星光和日光，提取数字，否则默认0
        if sunLightDetail.nodes:
            sunlightimprintnumber = sunLightDetail.nodes[0].recognition.best_result.text
            sunlightimprintnumber = re.findall(r'\d+', sunlightimprintnumber)
        if starLightDetail.nodes:
            starlightimprintnumber = starLightDetail.nodes[0].recognition.best_result.text
            starlightimprintnumber = re.findall(r'\d+', starlightimprintnumber)

        res = [int(sunlightimprintnumber[0]), int(starlightimprintnumber[0])]
        # print(res)
        context.run_task("BackText")
        context.run_task("BackText")
        return res
    
    # 这里检查火神
    def checkFiregod(self, context: Context):
        time.sleep(0.5)
        img = context.tasker.controller.post_screencap().wait().get()
        checkfiregodDetail = context.run_recognition("CheckEternalSuit",
                                img,
                                pipeline_override={
                                    "CheckEternalSuit": {
                                        "recognition": "TemplateMatch",
                                        "template": [
                                            "divineForgeLand\\Firegod.png",
                                            "divineForgeLand\\RedHatBody.png",
                                            "divineForgeLand\\Weapon.png"
                                        ],
                                        "roi" : [8,131,710,997],
                                        "timeout": 3000
                                    }
                                }
                            )
        return checkfiregodDetail
    
    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    )-> CustomAction.RunResult:
        
        # 这里确定是否要星光
        starlight_accept_para = json.loads(argv.custom_action_param)["accept_sunlight"]
        
        # 这里检查日光和星光
        before_sunlightimprintnumber,  before_starlightimprintnumber = self.getImprintNumber(context)
        
        # 这里保存状态
        context.run_task("Save_Status")

        #先找到尸体
        checkCount = 10
        searchbodypos = None
        searchDetail = context.run_task("SearchBody")
        while not (searchDetail.nodes or checkCount <= 0):
            checkCount -= 1
            searchDetail = context.run_task("SearchBody")
        if searchDetail.nodes:
            searchbodypos = searchDetail.nodes[0].recognition.best_result.box
        else:
            logger.warning("没有找到尸体或者兵器")
            return CustomAction.RunResult(success=False)
        
        #检查是否有火神，如果有可以不用释放技能推序
        firegod = self.checkFiregod(context)        

        #这里进行小退，恢复现场
        context.run_task("LogoutGame")
        context.run_task("ReturnMaze")
        
        for i in range(31):
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)
            
            logger.info(f"黑日光第{i}次尝试")
            if not firegod:
                context.run_task("PushOne")
            context.run_task("Save_Status")

            
            #每次暂离之后，执行点击尸体的操作
            click_job = context.tasker.controller.post_click(searchbodypos[0] + searchbodypos[2] // 2, searchbodypos[1] + searchbodypos[3] // 2)
            click_job.wait()
            time.sleep(0.1)
            
            #翻找尸体
            context.run_task("SearchBody_Next")
            
            #检查是否出日光或者星光
            after_sunlightimprintnumber,  after_starlightimprintnumber = self.getImprintNumber(context)
            condition_met = False
            if starlight_accept_para:
                if (after_sunlightimprintnumber != before_sunlightimprintnumber or
                    after_starlightimprintnumber != before_starlightimprintnumber):
                    condition_met = True
            else:
                if after_sunlightimprintnumber != before_sunlightimprintnumber:
                    condition_met = True

            # 这里检查是否满足条件
            if condition_met: 
                logger.info("黑日光成功，检测到日光或者星光: ")
                context.run_task("Save_Status")
                return CustomAction.RunResult(success=True)
            else:
                context.run_task("LogoutGame")
                context.run_task("ReturnMaze")

        logger.warning("黑日光失败")
        return CustomAction.RunResult(success=False)