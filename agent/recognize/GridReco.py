from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from loguru import logger
from action import Utils


@AgentServer.custom_recognition("Reco_Door")
class Reco_Door(CustomRecognition):
    # 从一个字符串里面识仅识别一串数字, 并返回

    # 执行函数
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        # matrix init
        cols, rows = 5, 6
        roi_list = Utils.calRoiList()
        roi_matrix = [roi_list[i * cols : (i + 1) * cols] for i in range(rows)]

        image = context.tasker.controller.post_screencap().wait().get()
        recoDetail = context.run_recognition("Fight_ClosedDoor", image)
        if recoDetail:
            logger.info("识别到 Fight_ClosedDoor")
            for r in range(rows):
                for c in range(cols):
                    if Utils.is_roi_in_or_mostly_in(recoDetail.box, roi_matrix[r][c]):
                        logger.info(f"识别到 Fight_ClosedDoor 位于 {r},{c}")
                        return CustomRecognition.AnalyzeResult(
                            recoDetail.box, "success"
                        )

        return CustomRecognition.AnalyzeResult(recoDetail.box, "fail")
