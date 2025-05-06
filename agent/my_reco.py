from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


@AgentServer.custom_recognition("my_reco_222")
class MyRecongition(CustomRecognition):

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        reco_detail = context.run_recognition(
            "MyCustomOCR",
            argv.image,
            pipeline_override={"MyCustomOCR": {"roi": [100, 100, 200, 300]}},
        )

        # context is a reference, will override the pipeline for whole task
        context.override_pipeline({"MyCustomOCR": {"roi": [1, 1, 114, 514]}})
        # context.run_recognition ...

        # make a new context to override the pipeline, only for itself
        new_context = context.clone()
        new_context.override_pipeline({"MyCustomOCR": {"roi": [100, 200, 300, 400]}})
        reco_detail = new_context.run_recognition("MyCustomOCR", argv.image)

        click_job = context.tasker.controller.post_click(10, 20)
        click_job.wait()

        context.override_next(argv.node_name, ["TaskA", "TaskB"])

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 100, 100), detail="Hello World!"
        )

@AgentServer.custom_recognition("GridCheck")
class GridCheck(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        # 这里可以根据需要添加自定义的逻辑
        # 例如，调用自定义的函数或执行特定的操作
        # 这里只是一个示例，返回一个固定的结果
        img = context.tasker.post_screencap().wait().get()

        roi_list = [
            [15, 222, 138, 126],
            [153, 222, 138, 126],
            [291, 222, 138, 126],
            [429, 222, 138, 126],
            [567, 222, 138, 126],
            [15, 348, 138, 126],
            [153, 348, 138, 126],
            [291, 348, 138, 126],
            [429, 348, 138, 126],
            [567, 348, 138, 126],
            [15, 474, 138, 126],
            [153, 474, 138, 126],
            [291, 474, 138, 126],
            [429, 474, 138, 126],
            [567, 474, 138, 126],
            [15, 600, 138, 126],
            [153, 600, 138, 126],
            [291, 600, 138, 126],
            [429, 600, 138, 126],
            [567, 600, 138, 126],
            [15, 726, 138, 126],
            [153, 726, 138, 126],
            [291, 726, 138, 126],
            [429, 726, 138, 126],
            [567, 726, 138, 126],
            [15, 852, 138, 126],
            [153, 852, 138, 126],
            [291, 852, 138, 126],
            [429, 852, 138, 126],
            [567, 852, 138, 126],
        ]  # 假设 detail 是 JSON 格式的字符串

        for i, roi in enumerate(roi_list):
            try:
                reco_detail = context.run_recognition(
                    "GridCheckTemplate",
                    img,
                    {
                        "GridCheckTemplate": {
                            "recognition": "ColorMatch",
                            "roi": roi,
                            "method": 4,
                            "lower": [130, 135, 143],
                            "upper": [170, 175, 183],
                        }
                    },
                )
            except Exception as e:
                print(f"Error processing ROI {i}: {e}")
                continue

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 100, 100), detail="Hello World!"
        )
