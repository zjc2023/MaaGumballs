from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context



# auto register by decorator, can also call `resource.register_custom_recognition` manually
@resource.custom_recognition("DetectWhiteTile_Code")
class MyRecongition(CustomRecognition):

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        reco_detail = context.run_recognition(
            "DetectWhiteTile",
            argv.image,
            pipeline_override={            
                "DetectWhiteTile": {
                "recognition": "ColorMatch",
                "roi": [100, 100, 200, 300],
                "method": 40,
                "lower": [0, 0, 150],
                "upper": [40, 60, 255],
                "count": 300,
                "order_by": "Score",
                "index": 0,
                "action": "Click",
                "pre_delay": 80,
                "post_delay": 120,
                "next": [
                    "MonsterLayerStart"
                ]
            }},
        )

        # context is a reference, will override the pipeline for whole task
        context.override_pipeline({"DetectWhiteTile": {"roi": [1, 1, 114, 514]}})
        # context.run_recognition ...

        reco_detail = new_context.run_recognition("MyCustomOCR", argv.image)

        click_job = context.tasker.controller.post_click(10, 20)
        click_job.wait()

        context.override_next(argv.node_name, ["TaskA", "TaskB"])

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 100, 100), detail="Hello World!"
        )

@AgentServer.custom_action("my_action_111")
class MyCustomAction(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        print("my_action_111 is running!")

        return True
