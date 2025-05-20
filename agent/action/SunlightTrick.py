from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
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
        context.run_task("BackButton")
        context.run_task("BackButton")
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
        searchbodypos = None
        searchDetail = context.run_task("SearchBody")
        while not searchDetail.nodes:
            searchDetail = context.run_task("SearchBody")
        if searchDetail.nodes:
            searchbodypos = searchDetail.nodes[0].recognition.best_result.box
        
        #检查是否有火神，如果有可以不用释放技能推序
        firegod = self.checkFiregod(context)        

        #这里进行小退，恢复现场
        context.run_task("LogoutGame")
        context.run_task("ReturnMaze")
        
        for i in range(31):
            if context.tasker.stopping:
                print("检测到停止，退出")
                return CustomAction.RunResult(success=False)
            
            print("第", i, "次尝试")
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
            if starlight_accept_para:
                if after_sunlightimprintnumber != before_sunlightimprintnumber or after_starlightimprintnumber != before_starlightimprintnumber:
                #满足条件之后暂离保存
                    context.run_task("Save_Status")
                    return CustomAction.RunResult(success=True)
            else:
                if after_sunlightimprintnumber != before_sunlightimprintnumber:
                #满足条件之后暂离保存
                    context.run_task("Save_Status")
                    return CustomAction.RunResult(success=True)
            #不满足条件则小退恢复尸体
            context.run_task("LogoutGame")
            context.run_task("ReturnMaze")
            
            
        return CustomAction.RunResult(success=False)