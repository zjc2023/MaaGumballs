from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail
from utils import logger

import time
import json


@AgentServer.custom_action("Find_Stove_Sequence_Test")
class Find_Stove_Sequence_Test(CustomAction):

    def split_zero_sequence_advanced(self, input_list):
        """
        用来处理101序列，返回垫子序列和日光装备等级序列
        参数:
            input_list (list): 输入列表，例如 [5,3]
        返回:
            zero_counts (list): 包含开头零、非零间零和结尾零的列表，如 [0]
            non_zero_values (list): 非零值列表，如 [5,3]
        """
        zero_counts = []
        non_zero_values = []
        current_index = 0
        list_length = len(input_list)

        # 处理开头的零
        has_leading_zeros = False
        while current_index < list_length and input_list[current_index] == 0:
            current_index += 1
            has_leading_zeros = True
        if has_leading_zeros:
            zero_counts.append(current_index)
        else:
            # 如果没有前导零，并且列表不为空，则添加一个0
            if list_length > 0:
                zero_counts.append(0)

        # 处理中间的非零值和零
        previous_was_non_zero = False

        while current_index < list_length:
            current_value = input_list[current_index]

            if current_value != 0:
                # 遇到非零值
                non_zero_values.append(current_value)

                if previous_was_non_zero:
                    # 如果前一个也是非零值，记录0表示它们之间没有零
                    zero_counts.append(0)
                previous_was_non_zero = True
            else:
                # 遇到零
                previous_was_non_zero = False

                # 计算连续零的数量
                consecutive_zeros = 1
                current_index += 1
                while current_index < list_length and input_list[current_index] == 0:
                    consecutive_zeros += 1
                    current_index += 1

                # 添加连续零的数量到结果
                zero_counts.append(consecutive_zeros)
                continue  # 跳过下面的索引递增，因为在内层循环中已经处理过了

            current_index += 1

        # 处理结尾的零
        # （在当前逻辑中，结尾的零已经在主循环中处理，无需额外步骤）

        # 处理空输入的情况
        if not non_zero_values and not zero_counts and list_length > 0:
            zero_counts.append(list_length)

        return zero_counts, non_zero_values

    # 这里是填入高星装备,从最右边找到最左边
    def find_and_click_equipment_from_right(
        self, context: Context, equipment_level: int
    ):
        equipment_level_to_action_name = {
            6: "Find_and_Click_level6_Equipmnet",
            5: "Find_and_Click_level5_Equipmnet",
            4: "Find_and_Click_level4_Equipmnet",
            3: "Find_and_Click_level3_Equipmnet",
        }
        # 首先在当前页查找目标等级装备
        find_equipment_detail = context.run_task(
            equipment_level_to_action_name[equipment_level]
        )
        if not find_equipment_detail.nodes:
            context.run_task("GoToTheRightestPage")

        # 当前页找不到就往右往左找
        while not find_equipment_detail.nodes:

            find_equipment_detail = context.run_task(
                equipment_level_to_action_name[equipment_level]
            )
            if not find_equipment_detail.nodes:
                previous_page_button_detail = context.run_task("GoToPreviousPage")
                # 如果找不到装备又没有上一页按钮则说明需要SL
                if not previous_page_button_detail.nodes:
                    return find_equipment_detail

        return find_equipment_detail

    def add_low_level_equipment(self, context: Context, num: int, page: int = 2):
        context.run_task("GoToTheLeftestPage")
        for _ in range(page):
            context.run_task("GoToNextPage")
        for _ in range(num):

            context.run_task("AddLowLevelEquipment")
            context.run_task("Click_Select_Equipment")
            context.run_task("Click_Smelt_Equipment")
            context.run_task("OpenEquipmentStovePage_Next")
        logger.info(f"填入低星装备{num}个成功")

    def get_base_stove_sequence(self, context: Context, stove_sequence: list = None):
        assert len(stove_sequence) == 101
        context.run_task("ConfirmPutonArmor")
        context.run_task("OpenEquipmentStovePage")
        for i in range(101):
            logger.info(f"第{i}次尝试")
            find_equipment_detail = self.find_and_click_equipment_from_right(context, 6)
            if find_equipment_detail.nodes:
                # 找到装备并且点击，进入后续操作，点击选择--点击熔炼装备--判断是否出现天下布武
                context.run_task("Click_Select_Equipment")
                context.run_task("Click_Smelt_Equipment")
                if context.run_task("Find_Stove_Sequence_Check").nodes:
                    # 出现天下布武,记录
                    logger.info(f"第{i}次出现天下布武")
                    stove_sequence[i] = 6
                context.run_task("OpenEquipmentStovePage_Next")
            else:
                # 没找到装备，进入后续操作，点击返回--点击返回--小SL--回到之前的状态--根据当前轮次填入一定数量的低星装备--找到装备--点击选择--点击熔炼装备--判断是否出现天下布武
                context.run_task("BackText")
                context.run_task("BackText")
                context.run_task("LogoutGame")
                context.run_task("ReturnMaze")
                context.run_task("ConfirmPutonArmor")
                context.run_task("OpenEquipmentStovePage")
                # 这里要填入i次低星装备，填入低星装备之后正常填入高星装备
                self.add_low_level_equipment(context, i)
                find_equipment_detail = self.find_and_click_equipment_from_right(
                    context, 6
                )
                if find_equipment_detail.nodes:
                    # 找到装备并且点击，进入后续操作，点击选择--点击熔炼装备--判断是否出现天下布武
                    context.run_task("Click_Select_Equipment")
                    context.run_task("Click_Smelt_Equipment")
                    if context.run_task("Find_Stove_Sequence_Check").nodes:
                        # 出现天下布武,记录
                        stove_sequence[i] = 6
                    context.run_task("OpenEquipmentStovePage_Next")
        # 恢复现场
        logger.info("恢复现场")
        context.run_task("BackText")
        context.run_task("BackText")
        context.run_task("LogoutGame")
        context.run_task("ReturnMaze")

        return stove_sequence

    def upgrade_stove_sequence(
        self, context: Context, low_star_seq: list = None, sun_star_seq: list = None
    ):
        context.run_task("ConfirmPutonArmor")
        context.run_task("OpenEquipmentStovePage")
        assert len(low_star_seq) >= len(sun_star_seq)
        for i in range(len(sun_star_seq)):
            # 当前轮次状态
            logger.info(
                f"当前目标: 轮次为{sum(low_star_seq[: i + 1]) + i},日光装备为{sun_star_seq[i]}星装备"
            )
            # 先填入低星装备
            self.add_low_level_equipment(context, low_star_seq[i])

            # 进入后续操作，点击选择--点击熔炼装备--判断是否出现天下布武
            find_equipment_detail = self.find_and_click_equipment_from_right(
                context, sun_star_seq[i] - 1
            )
            if find_equipment_detail.nodes:
                context.run_task("Click_Select_Equipment")
                context.run_task("Click_Smelt_Equipment")
                if context.run_task("Find_Stove_Sequence_Check").nodes:
                    # 出现天下布武,记录

                    logger.info(
                        f"当前轮次为{sum(low_star_seq[: i + 1]) + i},{sun_star_seq[i]}星装备更换为{sun_star_seq[i]-1}星装备"
                    )
                    sun_star_seq[i] = sun_star_seq[i] - 1
                context.run_task("OpenEquipmentStovePage_Next")
            else:
                context.run_task("BackText")
                context.run_task("BackText")
                context.run_task("LogoutGame")
                context.run_task("ReturnMaze")
                context.run_task("ConfirmPutonArmor")
                context.run_task("OpenEquipmentStovePage")

                # 这里要计算填入的装备数量：
                need_add = sum(low_star_seq[: i + 1]) + i
                logger.info(f"需要填入低星装备{need_add}个")
                self.add_low_level_equipment(context, need_add)
                find_equipment_detail = self.find_and_click_equipment_from_right(
                    context, sun_star_seq[i] - 1
                )
                if find_equipment_detail.nodes:
                    context.run_task("Click_Select_Equipment")
                    context.run_task("Click_Smelt_Equipment")
                    if context.run_task("Find_Stove_Sequence_Check").nodes:

                        # 出现天下布武,记录
                        logger.info(
                            f"当前轮次为{sum(low_star_seq[:i+1]) + i},{sun_star_seq[i]}星装备更换为{sun_star_seq[i]-1}星装备"
                        )
                        sun_star_seq[i] = sun_star_seq[i] - 1
                    context.run_task("OpenEquipmentStovePage_Next")
        # 恢复现场
        logger.info("恢复现场")
        context.run_task("BackText")
        context.run_task("BackText")
        context.run_task("LogoutGame")
        context.run_task("ReturnMaze")
        return low_star_seq, sun_star_seq

    # 执行函数
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        # 这里确定是否要星光
        target_sunlight_para = json.loads(argv.custom_action_param)["target_sunlight"]

        base_stove_sequence = [0 for _ in range(101)]
        stove_sequence = self.get_base_stove_sequence(context, base_stove_sequence)
        logger.info(stove_sequence)
        count = len([x for x in stove_sequence if x != 0])
        logger.info(
            f"本次101序列中共有{count}个日光, 目标为{target_sunlight_para}个日光"
        )
        if count >= target_sunlight_para:

            low_star_seq, sun_star_seq = self.split_zero_sequence_advanced(
                stove_sequence
            )
            logger.info(low_star_seq)
            logger.info(sun_star_seq)
            low_star_seq, sun_star_seq = self.upgrade_stove_sequence(
                context, low_star_seq, sun_star_seq
            )
            logger.info(low_star_seq)
            logger.info(sun_star_seq)
            low_star_seq, sun_star_seq = self.upgrade_stove_sequence(
                context, low_star_seq, sun_star_seq
            )
            logger.info(low_star_seq)
            logger.info(sun_star_seq)
            low_star_seq, sun_star_seq = self.upgrade_stove_sequence(
                context, low_star_seq, sun_star_seq
            )
            logger.info(low_star_seq)
            logger.info(sun_star_seq)
        return CustomAction.RunResult(success=True)
