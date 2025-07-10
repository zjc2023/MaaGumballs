from enum import Enum
from collections import deque
import heapq
import math
import time
import cv2
import numpy as np
from typing import Tuple, List, Dict, Any, Optional, Set

from maa.context import Context # context.run_recognition 返回的对象类型在 Context 内部处理


from utils import logger
from action.fight import fightUtils # 假设这个模块存在，并包含 dragonwish 等方法

# ==============================================================================
# 常量和枚举定义
# ==============================================================================

class GridState(Enum):
    """
    定义地图格子的精确状态
    """
    UNOPENED = "未"         # 未翻开石板
    OPENED = "可"           # 可点击石板 (物理可点击，但尚未点击，其内容未知)
    EXPLORED = "空"         # 已探索空地 (安全区)
    OBSTACLE = "障"         # 障碍 (不可点击，不可通行)
    REMOTE_MONSTER = "远"   # 远程怪 (屏幕上可见，可直接攻击)
    MELEE_MONSTER = "近"    # 近战怪 (屏幕上可见，可直接攻击)
    DETECTED_MONSTER = "侦" # 侦测怪 (点击后翻出 MELEE_MONSTER)
    DOOR = "门"             # 门 (安全区)
    FRIEND = "友"           # 友方 (安全区)
    DEVICE = "设"           # 装置 (初始状态，未激活)
    DEVICE_ACTIVATED = "活" # 已激活的装置 (可作为安全区)
    UNKNOWN = "?"           # 未知状态，用于调试或初始填充

# 定义格子行列数
MAP_ROWS = 6
MAP_COLS = 5

# 定义各种识别的阈值和配置 (这些在实际项目中通常从配置文件加载)
RECOGNITION_THRESHOLDS = {
    "Find_DetectedMonster": 0.8,
    "Find_Obstacle": 0.8,
    "Find_SpecialDevice": 0.8,
    "Find_FriendlyUnits": 0.8,
    "Find_Bloodbar": 0.8, # 血条的阈值
    "Fight_ClosedDoor": 0.8,
    "Fight_OpenedDoor": 0.8,
    "Fight_FindDragon": 0.8,
}

# 寻路惩罚 (反映点击或开路的代价)
# 修正 COST_DETECTED_MONSTER_CLICK 为 2，表示翻出(1) + 攻击(1) 的总成本
COST_DETECTED_MONSTER_CLICK = 2 # 点击侦测怪的代价 (翻出1次点击 + 攻击1次)
COST_UNOPENED_CLICK = 1       # 点击 UNOPENED 石板的代价
COST_OPENED_CLICK = 1         # 点击 OPENED 石板的代价
COST_MONSTER_ATTACK = 1       # 攻击怪物（非开路）的代价，用于 find_path_to_make_target_clickable 中额外计算目标本身的攻击代价

# 方向向量 (上，下，左，右)
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# ==============================================================================
# FightProcessor 类实现
# ==============================================================================

class FightProcessor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self.rows = MAP_ROWS
            self.cols = MAP_COLS
            self.roi_matrix = [] # 存储每个格子的 [x, y, w, h]
            self.GridState = GridState # 将枚举绑定到实例，方便访问

            # 智能清理相关的新增属性
            self.grid_status = np.full((self.rows, self.cols), self.GridState.UNOPENED, dtype=object)
            self.just_killed_a_monster = False # 标记刚刚是否击杀了一个怪物

            # 颜色识别阈值 (用于OPENED石板和REMOTE_MONSTER的物理检测，优先级低于Maa识别节点)
            self._monster_lower = [190, 35, 35]
            self._monster_upper = [235, 65, 65]
            self._monster_count = 20
            self._grid_lower = [130, 135, 143]
            self._grid_upper = [170, 175, 183]
            self._grid_count = 10

            # 旧版参数，在新版策略中可能不再直接使用，但保留兼容性
            self.max_grid_loop = 18
            self.max_monster_loop_fail = 5
            self.max_grid_loop_fail = 3
            self._hit_monster_count = 3 # 默认攻击次数，实际会使用 _attack_and_verify_kill 中的 max_attacks

            self.isCheckDragon = False # 神龙处理
            self.targetWish = "工资"

            # 初始化物理ROI网格
            self.roi_matrix = self.generate_floor_roi_grid()
            self.initialized = True

            # 日志辅助：用于在打印地图状态时显示编号
            self._log_map_status_count = 0

    # ==========================================================================
    # 属性的 Getter/Setter (保持与您原有代码一致)
    # ==========================================================================
    @property
    def monster_lower(self):
        return self._monster_lower

    @monster_lower.setter
    def monster_lower(self, value):
        if not isinstance(value, list) or len(value) != 3:
            raise ValueError("monster_lower must be a list of 3 integers")
        if not all(isinstance(x, int) for x in value):
            raise TypeError("All elements in monster_lower must be integers")
        self._monster_lower = value

    @property
    def monster_upper(self):
        return self._monster_upper

    @monster_upper.setter
    def monster_upper(self, value):
        if not isinstance(value, list) or len(value) != 3:
            raise ValueError("monster_upper must be a list of 3 integers")
        if not all(isinstance(x, int) for x in value):
            raise TypeError("All elements in monster_upper must be integers")
        self._monster_upper = value

    @property
    def monster_count(self):
        return self._monster_count

    @monster_count.setter
    def monster_count(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("monster_count must be a positive integer")
        self._monster_count = value

    @property
    def grid_lower(self):
        return self._grid_lower

    @grid_lower.setter
    def grid_lower(self, value):
        if not isinstance(value, list) or len(value) != 3:
            raise ValueError("grid_lower must be a list of 3 integers")
        if not all(isinstance(x, int) for x in value):
            raise TypeError("All elements in grid_lower must be integers")
        self._grid_lower = value

    @property
    def grid_upper(self):
        return self._grid_upper

    @grid_upper.setter
    def grid_upper(self, value):
        if not isinstance(value, list) or len(value) != 3:
            raise ValueError("grid_upper must be a list of 3 integers")
        if not all(isinstance(x, int) for x in value):
            raise TypeError("All elements in grid_upper must be integers")
        self._grid_upper = value

    @property
    def grid_count(self):
        return self._grid_count

    @grid_count.setter
    def grid_count(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("grid_count must be a positive integer")
        self._grid_count = value

    @property
    def hit_monster_count(self):
        return self._hit_monster_count

    @hit_monster_count.setter
    def hit_monster_count(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("hit_monster_count must be a positive integer")
        self._hit_monster_count = value

    # ==========================================================================
    # 辅助函数
    # ==========================================================================

    def generate_floor_roi_grid(self) -> List[List[int]]:
        """
        生成地板网格的ROI区域列表。
        根据预设的网格布局参数，计算并返回所有地板格子的ROI坐标。
        ROI格式为 [x, y, width, height]。
        """
        # 网格布局常量 (硬编码，建议从配置文件加载以提高灵活性)
        START_X, START_Y = 15, 222
        CELL_WIDTH, CELL_HEIGHT = 138, 126
        
        # 返回一个扁平化列表，方便通过 r * self.cols + c 索引
        return [
            [
                START_X + col * CELL_WIDTH,
                START_Y + row * CELL_HEIGHT,
                CELL_WIDTH,
                CELL_HEIGHT,
            ]
            for row in range(self.rows)
            for col in range(self.cols)
        ]

    def _log_map_status(self, prefix_message: str = ""):
        """
        打印当前地图状态的模拟图。
        使用 GridState 中定义的简写。
        """
        if prefix_message:
            logger.info(prefix_message)
        logger.info(f"==================== 当前地图状态 ({self._log_map_status_count}) ====================")
        self._log_map_status_count += 1
        for r in range(self.rows):
            row_str = " ".join([self.grid_status[r, c].value for c in range(self.cols)])
            logger.info(f"[{row_str}]")
        logger.info("=======================================================")


    def is_roi_mostly_overlapping(
        self,
        roi1: Tuple[int, int, int, int],
        roi2: Tuple[int, int, int, int],
        threshold: float = 0.5,
    ) -> bool:
        """
        判断 roi1 是否大部分与 roi2 重叠。
        当 roi1 与 roi2 的交集面积占 roi1 面积的比例大于等于阈值时返回 True。
        """
        # 验证 ROI 参数有效性
        if any(v <= 0 for v in roi1[2:] + roi2[2:]):
            # logger.warning(f"ROI 参数包含非正值: roi1={roi1}, roi2={roi2}")
            return False # 直接返回False，不抛出异常以避免中断流程

        # 计算交集区域坐标
        inter_x1 = max(roi1[0], roi2[0])
        inter_y1 = max(roi1[1], roi2[1])
        inter_x2 = min(roi1[0] + roi1[2], roi2[0] + roi2[2])
        inter_y2 = min(roi1[1] + roi1[3], roi2[1] + roi2[3])

        # 计算交集面积和 roi1 面积
        if inter_x2 > inter_x1 and inter_y2 > inter_y1:
            intersection_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
            roi1_area = roi1[2] * roi1[3]
            if roi1_area == 0: # 避免除以零
                return False
            return intersection_area / roi1_area >= threshold
        return False

    def bgrColorMatch(
        self,
        image: np.ndarray,
        lower: List[int],
        upper: List[int],
        count: int,
        context: Context, # 这里的context是为了兼容Maa的ColorMatch，但在纯OpenCV实现中可能不需要
        method="opencv", # 默认使用opencv，兼容旧代码逻辑
    ) -> int:
        """
        BGR颜色空间像素计数。
        这个函数主要用于物理检测OPENED石板和REMOTE_MONSTER的颜色特征。
        返回匹配的像素数量，如果不足count则返回0。
        """
        # RGB转BGR，因为lower和upper是从RGB传入的
        lower_bgr = [lower[2], lower[1], lower[0]]
        upper_bgr = [upper[2], upper[1], upper[0]]

        if method == "opencv":
            lower_bound = np.array(lower_bgr, dtype=np.uint8)
            upper_bound = np.array(upper_bgr, dtype=np.uint8)
            mask = cv2.inRange(image, lower_bound, upper_bound)
            valid_pixel_count = cv2.countNonZero(mask)
            return valid_pixel_count if valid_pixel_count > count else 0
        else:
            # 如果尝试用Maa ColorMatch，这里通常需要完整的Maa识别上下文和图像，而非roi_image
            logger.warning("bgrColorMatch: 'Maa' method is not directly supported for raw image input. Using 'opencv' method.")
            return self.bgrColorMatch(image, lower, upper, count, context, method="opencv")

    def _run_recognition_and_map_to_grid(self, context: Context, reco_name: str, current_img: np.ndarray) -> List[Tuple[int, int]]:
        """
        运行指定的Maa识别，并将识别结果映射到地图格子上。
        根据 RECOGNITION_THRESHOLDS 中定义的阈值进行过滤。
        返回识别到的格子坐标 (r, c) 列表。
        """
        detected_coords = []
        # 使用 context.run_recognition 执行识别，不传入 threshold 参数
        if recoDetail := context.run_recognition(reco_name, current_img):
            # 获取识别该名称对应的阈值
            recognition_threshold = RECOGNITION_THRESHOLDS.get(reco_name, 0.7) # 默认值0.7

            # 兼容性处理：检查 all_results 是否存在，否则尝试 best_result
            results_to_process = []
            # Maa v4.x 的 RecognitionDetail 对象通常有 .all_results 和 .best_result 属性
            if hasattr(recoDetail, 'all_results') and recoDetail.all_results is not None:
                results_to_process = recoDetail.all_results
            elif hasattr(recoDetail, 'best_result') and recoDetail.best_result is not None:
                # 即使只有 best_result，也封装成列表以便统一处理
                results_to_process = [recoDetail.best_result] 

            if results_to_process:
                for result in results_to_process:
                    # 手动过滤匹配度
                    if result.score >= recognition_threshold:
                        reco_box = result.box
                        # 遍历所有格子，判断识别结果落在哪个格子
                        for r_idx in range(self.rows):
                            for c_idx in range(self.cols):
                                # 使用 self.roi_matrix[r_idx * self.cols + c_idx] 来获取格子ROI
                                grid_roi = self.roi_matrix[r_idx * self.cols + c_idx]
                                if self.is_roi_mostly_overlapping(reco_box, grid_roi):
                                    detected_coords.append((r_idx, c_idx))
                                    break # 假设一个Maa识别结果只对应一个格子，找到后跳出内层循环
        return list(set(detected_coords)) # 返回去重后的结果列表

    def _is_safe_zone(self, r: int, c: int) -> bool:
        """判断一个格子是否是安全区（可作为寻路起点）"""
        return self.grid_status[r, c] in [
            self.GridState.DOOR,
            self.GridState.FRIEND,
            self.GridState.EXPLORED, # EXPLORED 状态的格子，玩家也可以“瞬移”过去
            self.GridState.DEVICE_ACTIVATED
        ]

    def _is_melee_monster_blocking(self, r: int, c: int) -> bool:
        """
        判断目标格子 (r, c) 是否被相邻的 MELEE_MONSTER 阻碍。
        只针对 UNOPENED, OPENED, DETECTED_MONSTER 类型。
        """
        # 只有这些类型的格子会被近战怪阻碍
        if self.grid_status[r, c] not in [
            self.GridState.UNOPENED,
            self.GridState.OPENED,
            self.GridState.DETECTED_MONSTER,
        ]:
            return False

        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid_status[nr, nc] == self.GridState.MELEE_MONSTER:
                    return True # 发现相邻近战怪，阻碍
        return False

    def is_grid_clickable(self, r: int, c: int) -> bool:
        """
        判断一个格子是否是“可点击”的。
        - 必须是可点击类型 (UNOPENED, OPENED, REMOTE_MONSTER, MELEE_MONSTER, DETECTED_MONSTER)。
        - 必须满足“可点击性判定” (Adjacent to Safe Zone)。
        - 对于特定类型 (UNOPENED, OPENED, DETECTED_MONSTER)，不能被相邻近战怪阻碍。
        """
        target_status = self.grid_status[r, c]

        # 1. 必须是可点击类型
        if target_status not in [
            self.GridState.UNOPENED,
            self.GridState.OPENED,
            self.GridState.REMOTE_MONSTER,
            self.GridState.MELEE_MONSTER,
            self.GridState.DETECTED_MONSTER,
        ]:
            return False

        # 2. 必须满足“可点击性判定” (Adjacent to Safe Zone)
        adjacent_to_safe_zone = False
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self._is_safe_zone(nr, nc):
                    adjacent_to_safe_zone = True
                    break
        if not adjacent_to_safe_zone:
            return False

        # 3. 对于 UNOPENED, OPENED, DETECTED_MONSTER，不能被相邻近战怪阻碍
        if target_status in [
            self.GridState.UNOPENED,
            self.GridState.OPENED,
            self.GridState.DETECTED_MONSTER,
        ]:
            if self._is_melee_monster_blocking(r, c):
                return False # 被阻碍，不可点击

        return True # 所有条件满足，可点击

    def click_grid(self, context: Context, r: int, c: int, clicks: int = 1):
        """
        点击指定格子。
        """
        x, y, w, h = self.roi_matrix[r * self.cols + c]
        for i in range(clicks):
            logger.info(f"[INFO] 正在点击格子 ({r+1},{c+1}) - 第 {i+1} 次")
            context.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
            time.sleep(0.1) # 短暂延迟，模拟点击间隔

    def _attack_and_verify_kill(self, context: Context, r: int, c: int, max_attacks: int = 20) -> bool:
        """
        循环攻击指定格子上的怪物并验证是否击杀。
        成功则更新格子状态为 EXPLORED。
        使用 Find_Bloodbar 来判断怪物是否被消灭。
        """
        logger.info(f"开始循环攻击并验证格子 ({r+1},{c+1}) 的怪物...")
        
        for i in range(max_attacks):
            self.click_grid(context, r, c, clicks=1)
            # 修正：每点击5次才检测一次
            if (i + 1) % 5 == 0 or (i + 1) == max_attacks: # 最后一次点击也检测
                time.sleep(0.2) # 攻击后稍作等待，让画面更新

                post_attack_image = context.tasker.controller.post_screencap().wait().get()
                
                monster_still_present = False
                latest_bloodbar_score = 0.0 # 用于存储最新的血条匹配度
                
                # 检查 Find_Bloodbar 是否仍然存在于该格子区域
                if recoDetail := context.run_recognition("Find_Bloodbar", post_attack_image): # 不传入threshold
                    bloodbar_threshold = RECOGNITION_THRESHOLDS["Find_Bloodbar"]
                    grid_roi = self.roi_matrix[r * self.cols + c]
                    
                    results_to_process = []
                    if hasattr(recoDetail, 'all_results') and recoDetail.all_results is not None:
                        results_to_process = recoDetail.all_results
                    elif hasattr(recoDetail, 'best_result') and recoDetail.best_result is not None:
                        results_to_process = [recoDetail.best_result]

                    # 遍历所有识别结果，找到血条并判断是否属于当前格子
                    for result in results_to_process:
                        if result.score >= bloodbar_threshold and self.is_roi_mostly_overlapping(result.box, grid_roi, threshold=0.3): # 降低重叠阈值，因为血条可能很小
                            monster_still_present = True
                            latest_bloodbar_score = result.score # 更新匹配度
                            # 如果有多个血条，这里可以取最高分的，或者第一个符合条件的
                            # 为了调试方便，取第一个找到的即可
                            break 
                
                if not monster_still_present:
                    logger.info(f"[INFO] 确认格子 ({r+1},{c+1}) 的怪物在第 {i+1} 次点击后被消灭。")
                    self.grid_status[r, c] = self.GridState.EXPLORED # 击杀后变为已探索
                    self.just_killed_a_monster = True # 标记刚刚击杀怪物
                    
                    # 怪物死亡后，重新检查DEVICE的触发，因为新的EXPLORED可能激活DEVICE
                    logger.info(f"怪物死亡后，检查DEVICE的触发...")
                    self.check_and_trigger_devices(context)
                    
                    return True # 怪物已被消灭
                else:
                    # 怪物仍在，打印匹配度
                    logger.info(f"[INFO] 第 {i+1}/{max_attacks} 次点击后，怪物仍在 ({r+1},{c+1})。血条匹配度: {latest_bloodbar_score:.2f}")

        logger.error(f"[ERROR] 攻击了 {max_attacks} 次后，仍未能消灭格子 ({r+1},{c+1}) 的怪物！标记为障碍。")
        self.grid_status[r, c] = self.GridState.OBSTACLE # 攻击失败后，将该格子标记为障碍
        return False # 怪物未被消灭

    # ==========================================================================
    # 地图状态初始化与动态更新
    # ==========================================================================

    def initialize_grid_state(self, context: Context):
        """
        屏幕扫描，利用Maa识别和颜色识别，全面识别初始地图元素。
        并循环检查DEVICE激活状态。
        """
        logger.info("[INFO] 初始化地图状态...")
        current_img = context.tasker.controller.post_screencap().wait().get()

        # 1. 默认所有格子都是UNOPENED
        self.grid_status = np.full((self.rows, self.cols), self.GridState.UNOPENED, dtype=object)

        # 2. 优先级赋值 (从高到低)
        # OBSTACLE, DOOR (最高优先级，结构性固定)
        for r, c in self._run_recognition_and_map_to_grid(context, "Find_Obstacle", current_img): # 不传入threshold
            self.grid_status[r, c] = self.GridState.OBSTACLE
        
        # 门识别：关闭的门和打开的门都映射为 DOOR 状态
        for r, c in self._run_recognition_and_map_to_grid(context, "Fight_ClosedDoor", current_img): # 不传入threshold
            self.grid_status[r, c] = self.GridState.DOOR
        for r, c in self._run_recognition_and_map_to_grid(context, "Fight_OpenedDoor", current_img): # 不传入threshold
            self.grid_status[r, c] = self.GridState.DOOR

        # FRIEND
        for r, c in self._run_recognition_and_map_to_grid(context, "Find_FriendlyUnits", current_img): # 不传入threshold
            # 只有当格子状态为 UNOPENED 时才赋值，避免覆盖更高优先级的 OBSTACLE/DOOR
            if self.grid_status[r, c] == self.GridState.UNOPENED:
                self.grid_status[r, c] = self.GridState.FRIEND

        # DEVICE (初始为未激活状态)
        for r, c in self._run_recognition_and_map_to_grid(context, "Find_SpecialDevice", current_img): # 不传入threshold
            if self.grid_status[r, c] == self.GridState.UNOPENED:
                self.grid_status[r, c] = self.GridState.DEVICE

        # ======================================================================
        # REMOTE_MONSTER (使用Find_Bloodbar) - 修正后的逻辑：只取匹配度最高的3个
        # ======================================================================
        # 用于临时存储识别到的远程怪的格子坐标，后续会限制数量
        top_n_remote_monsters_coords = [] 
        bloodbar_threshold = RECOGNITION_THRESHOLDS["Find_Bloodbar"]

        if recoDetail := context.run_recognition("Find_Bloodbar", current_img):
            results_to_process = []
            if hasattr(recoDetail, 'all_results') and recoDetail.all_results is not None:
                results_to_process = recoDetail.all_results
            elif hasattr(recoDetail, 'best_result') and recoDetail.best_result is not None:
                results_to_process = [recoDetail.best_result]

            # 按照匹配度从高到低排序，并筛选出达到阈值的
            eligible_results_sorted = sorted([res for res in results_to_process if res.score >= bloodbar_threshold],
                                             key=lambda x: x.score, reverse=True)

            # 为了确保一个格子只被标记一次，先收集唯一的格子，然后取前3个
            unique_monster_grid_candidates = [] # 存储 (r, c)
            processed_grids_for_unique = set() # 记录已处理的格子，防止重复添加

            for result in eligible_results_sorted:
                reco_box = result.box
                center_x = reco_box[0] + reco_box[2] // 2
                center_y = reco_box[1] + reco_box[3] // 2

                grid_found = False
                for r_idx in range(self.rows):
                    for c_idx in range(self.cols):
                        grid_roi = self.roi_matrix[r_idx * self.cols + c_idx]
                        
                        if ((grid_roi[0] <= center_x < grid_roi[0] + grid_roi[2] and \
                             grid_roi[1] <= center_y < grid_roi[1] + grid_roi[3]) or \
                            self.is_roi_mostly_overlapping(reco_box, grid_roi, threshold=0.3)):
                            
                            # 确保该格子未被其他高优先级识别标记，且未被当前循环处理过
                            if (r_idx, c_idx) not in processed_grids_for_unique and \
                               self.grid_status[r_idx, c_idx] in [self.GridState.UNOPENED, self.GridState.OPENED, self.GridState.DETECTED_MONSTER]:
                                unique_monster_grid_candidates.append((r_idx, c_idx))
                                processed_grids_for_unique.add((r_idx, c_idx))
                                grid_found = True
                            break
                    if grid_found:
                        break

            # 最终从唯一的候选格子中取前3个
            top_n_remote_monsters_coords = unique_monster_grid_candidates[:3]


        if top_n_remote_monsters_coords:
            logger.info("==================== 发现远程怪 ====================")
            for r_idx, c_idx in top_n_remote_monsters_coords:
                self.grid_status[r_idx, c_idx] = self.GridState.REMOTE_MONSTER
                logger.info(f"远程怪位于 ({r_idx+1},{c_idx+1})")
            logger.info("===================================================")
        # ======================================================================


        # DETECTED_MONSTER
        for r, c in self._run_recognition_and_map_to_grid(context, "Find_DetectedMonster", current_img): # 不传入threshold
            # DETECTED_MONSTER 优先级低于已识别出的障碍/门/友方/DEVICE/远程怪
            if self.grid_status[r, c] == self.GridState.UNOPENED:
                self.grid_status[r, c] = self.GridState.DETECTED_MONSTER


        # OPENED (基于物理可点击判断，使用原有的bgrColorMatch)
        # 遍历所有UNOPENED的格子，如果其物理上是OPENED，则更新
        for r in range(self.rows):
            for c in range(self.cols):
                # 只有当前是UNOPENED的格子才可能被物理识别为OPENED
                if self.grid_status[r, c] == self.GridState.UNOPENED:
                    x, y, w, h = self.roi_matrix[r * self.cols + c]
                    roi_image = current_img[y : y + h, x : x + w] # 修正：正确的切片语法
                    
                    left_img = roi_image[h - 15 : h, 0:20].copy()
                    right_img = roi_image[h - 15 : h, w - 20 : w].copy()
                    
                    left_detected_pixels = self.bgrColorMatch(left_img, self.grid_lower, self.grid_upper, self.grid_count, context)
                    right_detected_pixels = self.bgrColorMatch(right_img, self.grid_lower, self.grid_upper, self.grid_count, context)

                    if left_detected_pixels > 0 or right_detected_pixels > 0: # 只要有物理特征就认为可点击
                        self.grid_status[r, c] = self.GridState.OPENED
        
        # 玩家是幽灵，不占据格子，无需 Find_Player 和默认起始点设置
        # 初始安全区就是 DOOR, FRIEND, 以及被动成为EXPLORED的格子

        logger.info("[INFO] 地图状态初始化完成，检查初始DEVICE触发...")
        self._log_map_status("初始化状态")
        self.check_and_trigger_devices(context) # 初始DEVICE激活循环
        self._log_map_status("初始化及初始DEVICE激活完成。")


    def _is_device_activable(self, r: int, c: int) -> bool:
        """判断一个DEVICE格子是否可被激活"""
        if self.grid_status[r, c] != self.GridState.DEVICE:
            return False # 只有未激活的DEVICE才能被激活

        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                adjacent_status = self.grid_status[nr, nc]
                if adjacent_status in [
                    self.GridState.DOOR,
                    self.GridState.FRIEND,
                    self.GridState.EXPLORED,
                    self.GridState.DEVICE_ACTIVATED # 另一个已激活的DEVICE
                ]:
                    return True # 发现相邻的安全区，可激活
        return False

    def check_and_trigger_devices(self, context: Context):
        """
        循环检查所有DEVICE，直到没有新的DEVICE被激活。
        每次激活DEVICE都可能解锁新的邻近格子。
        """
        device_activated_this_round = True
        loop_count = 0
        max_device_activation_loops = 10 # 防止无限循环
        while device_activated_this_round and loop_count < max_device_activation_loops:
            device_activated_this_round = False
            loop_count += 1
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.grid_status[r, c] == self.GridState.DEVICE:
                        if self._is_device_activable(r, c):
                            self.grid_status[r, c] = self.GridState.DEVICE_ACTIVATED
                            logger.info(f"[INFO] 装置({r+1},{c+1})被激活！")
                            # 激活DEVICE使其成为安全区，从而让相邻格子“可点击”
                            device_activated_this_round = True
            
            if device_activated_this_round: # 如果本轮有DEVICE被激活，可能又会触发其他DEVICE
                time.sleep(0.1) # 稍作等待，让状态传播
                self._log_map_status("DEVICE激活后，地图状态更新：")
        
        if loop_count >= max_device_activation_loops:
            logger.warning("[WARNING] DEVICE激活循环达到最大次数，可能存在无法激活的DEVICE或循环依赖。")


    def update_grid_status_after_click(self, context: Context, clicked_r: int, clicked_c: int):
        """
        在每次点击操作后，立即截屏并根据游戏逻辑更新被点击格子及其周围的 grid_status。
        重要：每次状态变化（例如，有新的 EXPLORED 格子出现）后，
        必须重新执行装置激活循环 check_and_trigger_devices。
        """
        logger.info(f"[INFO] 更新点击 ({clicked_r+1},{clicked_c+1}) 后的地图状态...")
        new_img = context.tasker.controller.post_screencap().wait().get()
        
        status_changed = False # 标记是否有任何状态改变，以便触发 DEVICE 检查

        # 获取识别阈值
        bloodbar_threshold = RECOGNITION_THRESHOLDS["Find_Bloodbar"]
        detected_monster_threshold = RECOGNITION_THRESHOLDS["Find_DetectedMonster"]
        obstacle_threshold = RECOGNITION_THRESHOLDS["Find_Obstacle"]

        # --- 在函数开头执行所有一次性识别，避免重复调用 ---
        detected_obstacle_coords = self._run_recognition_and_map_to_grid(context, "Find_Obstacle", new_img)
        detected_bloodbar_coords = set() # 存储 (r, c)
        if recoDetail := context.run_recognition("Find_Bloodbar", new_img):
            results_to_process = []
            if hasattr(recoDetail, 'all_results') and recoDetail.all_results is not None:
                results_to_process = recoDetail.all_results
            elif hasattr(recoDetail, 'best_result') and recoDetail.best_result is not None:
                results_to_process = [recoDetail.best_result]
            for result in results_to_process:
                if result.score >= bloodbar_threshold:
                    reco_box = result.box
                    for r_idx_inner in range(self.rows):
                        for c_idx_inner in range(self.cols):
                            grid_roi = self.roi_matrix[r_idx_inner * self.cols + c_idx_inner]
                            if self.is_roi_mostly_overlapping(reco_box, grid_roi, threshold=0.3):
                                detected_bloodbar_coords.add((r_idx_inner, c_idx_inner))
                                break
        
        detected_detected_monster_coords = set() # 存储 (r, c)
        if recoDetail := context.run_recognition("Find_DetectedMonster", new_img):
            results_to_process = []
            if hasattr(recoDetail, 'all_results') and recoDetail.all_results is not None:
                results_to_process = recoDetail.all_results
            elif hasattr(recoDetail, 'best_result') and recoDetail.best_result is not None:
                results_to_process = [recoDetail.best_result]
            for result in results_to_process:
                if result.score >= detected_monster_threshold:
                    reco_box = result.box
                    for r_idx_inner in range(self.rows):
                        for c_idx_inner in range(self.cols):
                            grid_roi = self.roi_matrix[r_idx_inner * self.cols + c_idx_inner]
                            if self.is_roi_mostly_overlapping(reco_box, grid_roi, threshold=0.5):
                                detected_detected_monster_coords.add((r_idx_inner, c_idx_inner))
                                break

        # !!! 在所有状态更新之前，保存点击前的地图状态副本 !!!
        pre_click_grid_status = np.copy(self.grid_status)

        # --- 开始更新地图状态，按优先级从高到低 ---

        # 遍历所有格子
        for r_idx in range(self.rows):
            for c_idx in range(self.cols):
                current_grid_state = self.grid_status[r_idx, c_idx] # 这个是当前循环的 self.grid_status[r_idx, c_idx]
                
                # *** 优先级最高的处理：OBSTACLE ***
                # 无论之前是什么状态，只要识别到是障碍，就将其标记为障碍
                if (r_idx, c_idx) in detected_obstacle_coords:
                    if self.grid_status[r_idx, c_idx] != self.GridState.OBSTACLE:
                        self.grid_status[r_idx, c_idx] = self.GridState.OBSTACLE
                        logger.warning(f"[WARNING] 格子 ({r_idx+1},{c_idx+1}) 变为障碍！")
                        status_changed = True
                    continue # 当前格子是障碍，跳过后续所有更低优先级的判断
                
                # 2. 处理血条检测到的怪物 (MELEE_MONSTER 或 REMOTE_MONSTER 保持不变，新发现的标记为 MELEE_MONSTER)
                if (r_idx, c_idx) in detected_bloodbar_coords:
                    if current_grid_state not in [self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER]:
                        self.grid_status[r_idx, c_idx] = self.GridState.MELEE_MONSTER
                        logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 检测到怪物血条，标记为近战怪。")
                        status_changed = True
                    continue # 当前格子已确定为怪物，跳过后续更低优先级的判断
                
                # 3. 处理侦测怪
                if (r_idx, c_idx) in detected_detected_monster_coords:
                    # 只有当格子不是其他怪物时，才将其标记为侦测怪
                    if current_grid_state not in [self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER, self.GridState.DETECTED_MONSTER]:
                        self.grid_status[r_idx, c_idx] = self.GridState.DETECTED_MONSTER
                        logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 检测到侦测怪，标记为侦测怪。")
                        status_changed = True
                    continue # 当前格子已确定为侦测怪，跳过后续更低优先级的判断


                # 4. 如果没有检测到血条或侦测怪，且之前是怪物/侦测怪，则可能被消灭或变为 EXPLORED
                if current_grid_state in [
                    self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER,
                    self.GridState.DETECTED_MONSTER
                ]:
                    # 此时已经排除了当前帧还存在血条/侦测怪的情况
                    self.grid_status[r_idx, c_idx] = self.GridState.EXPLORED
                    logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 怪物/侦测怪消失，标记为已探索。")
                    status_changed = True
                    continue # 状态已确定为EXPLORED，跳过后续更低优先级的判断


                # 5. 处理装置状态 (如果从 DEVICE 变为 DEVICE_ACTIVATED)
                # 装置的激活在 check_and_trigger_devices 中处理，这里只做一次检测
                if current_grid_state == self.GridState.DEVICE:
                     # 检查是否满足激活条件，如果满足，check_and_trigger_devices 会处理
                    continue # DEVICE 状态不在此处直接改变，由专门函数处理


                # 6. 处理物理可点击 (OPENED) 和已探索 (EXPLORED)
                x, y, w, h = self.roi_matrix[r_idx * self.cols + c_idx]
                roi_image = new_img[y : y + h, x : x + w]
                
                # 计算物理可点击性
                left_img = roi_image[h - 15 : h, 0:20].copy()
                right_img = roi_image[h - 15 : h, w - 20 : w].copy()
                left_detected_pixels = self.bgrColorMatch(left_img, self.grid_lower, self.grid_upper, self.grid_count, context)
                right_detected_pixels = self.bgrColorMatch(right_img, self.grid_lower, self.grid_upper, self.grid_count, context)
                is_physically_clickable = (left_detected_pixels > 0 or right_detected_pixels > 0)


                if (r_idx, c_idx) == (clicked_r, clicked_c):
                    # 如果是被点击的格子 (last_clicked_r, last_clicked_c)
                    # 此时已经排除了是 OBSTACLE 的情况 (因为 OBSTACLE 逻辑在最上面)
                    
                    # 检查是否应该将其标记为 EXPLORED
                    left_top_for_monster_check = roi_image[0:60, 0:60].copy() # 左上角60x60
                    # 如果没有检测到新的近战怪物颜色
                    if not self.bgrColorMatch(left_top_for_monster_check, self.monster_lower, self.monster_upper, self.monster_count, context):
                        if current_grid_state != self.GridState.EXPLORED:
                            self.grid_status[r_idx, c_idx] = self.GridState.EXPLORED
                            logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 被点击后变为已探索。")
                            status_changed = True

                elif current_grid_state == self.GridState.UNOPENED:
                    # 如果是非被点击的 UNOPENED 格子，进行物理可点击判断
                    if is_physically_clickable:
                        self.grid_status[r_idx, c_idx] = self.GridState.OPENED
                        logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 检测到物理可点击状态，标记为可点击石板。")
                        status_changed = True
                elif current_grid_state == self.GridState.OPENED:
                    # 如果是 OPENED 格子，且不再物理可点击，则变为 EXPLORED
                    if not is_physically_clickable:
                        self.grid_status[r_idx, c_idx] = self.GridState.EXPLORED
                        logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 曾为'可'但不再物理可点击，变为已探索。")
                        status_changed = True

        # !!! 回溯逻辑 (基于新障碍发现) !!!
        # 检查是否有任何格子从非OBSTACLE变为OBSTACLE
        found_new_obstacle = False
        for r_idx in range(self.rows):
            for c_idx in range(self.cols):
                if self.grid_status[r_idx, c_idx] == self.GridState.OBSTACLE and \
                   pre_click_grid_status[r_idx, c_idx] != self.GridState.OBSTACLE:
                    found_new_obstacle = True
                    logger.info(f"[INFO] 发现新障碍格子: ({r_idx+1},{c_idx+1})。")
                    break
            if found_new_obstacle:
                break
        
        if found_new_obstacle:
            logger.warning("[WARNING] 检测到新障碍。回溯批量点击带来的探索状态。")
            # 遍历所有格子，将那些在点击前是UNOPENED/OPENED，现在变为EXPLORED的格子回滚
            for r_idx in range(self.rows):
                for c_idx in range(self.cols):
                    # 如果该格子在点击前是UNOPENED或OPENED，且现在是EXPLORED
                    if self.grid_status[r_idx, c_idx] == self.GridState.EXPLORED and \
                       pre_click_grid_status[r_idx, c_idx] in [self.GridState.UNOPENED, self.GridState.OPENED]:
                        
                        # 重新计算该格子的物理可点击性
                        x, y, w, h = self.roi_matrix[r_idx * self.cols + c_idx]
                        roi_image_check = new_img[y : y + h, x : x + w]
                        left_img_check = roi_image_check[h - 15 : h, 0:20].copy()
                        right_img_check = roi_image_check[h - 15 : h, w - 20 : w].copy()
                        is_physically_clickable_current = (
                            self.bgrColorMatch(left_img_check, self.grid_lower, self.grid_upper, self.grid_count, context) > 0 or
                            self.bgrColorMatch(right_img_check, self.grid_lower, self.grid_upper, self.grid_count, context) > 0
                        )

                        if pre_click_grid_status[r_idx, c_idx] == self.GridState.UNOPENED:
                            if is_physically_clickable_current:
                                self.grid_status[r_idx, c_idx] = self.GridState.OPENED
                                logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 从探索回滚到可点击石板。")
                            else:
                                self.grid_status[r_idx, c_idx] = self.GridState.UNOPENED # 无法物理点击，保持未探索
                                logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 从探索回滚到未翻开石板。")
                        elif pre_click_grid_status[r_idx, c_idx] == self.GridState.OPENED:
                            if is_physically_clickable_current:
                                self.grid_status[r_idx, c_idx] = self.GridState.OPENED
                                logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 从探索回滚到可点击石板。")
                            else:
                                self.grid_status[r_idx, c_idx] = self.GridState.EXPLORED # 曾为可，但现在不再物理可点击，仍视为已探索
                                logger.info(f"[INFO] 格子 ({r_idx+1},{c_idx+1}) 曾为'可'但不再物理可点击，仍视为已探索（不回滚）。")
                        
                        # 确保障碍本身不被回滚
                        # 这部分逻辑在for循环一开始就排除了OBSTACLE，所以这里不需要再处理OBSTACLE
                        # 如果需要回滚，这个格子肯定不是OBSTACLE

        # !!! 新增一致性检查 !!!
        # 在所有更新和回溯逻辑之后，确保 EXPLORED 状态的格子，其相邻的 UNOPENED 格子变为 OPENED
        # 如果不是，则该 EXPLORED 状态的格子应被回滚到 UNOPENED/OPENED
        
        # 收集需要回滚的 EXPLORED 格子
        explored_to_revert = []
        for r_idx in range(self.rows):
            for c_idx in range(self.cols):
                if self.grid_status[r_idx, c_idx] == self.GridState.EXPLORED:
                    # 检查其相邻的 UNOPENED 格子是否变为 OPENED
                    is_consistent_explored = True
                    for dr, dc in DIRECTIONS:
                        nr, nc = r_idx + dr, c_idx + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.grid_status[nr, nc] == self.GridState.UNOPENED:
                                # 检查该相邻 UNOPENED 格子在当前截图中是否物理可点击
                                x_n, y_n, w_n, h_n = self.roi_matrix[nr * self.cols + nc]
                                roi_image_n = new_img[y_n : y_n + h_n, x_n : x_n + w_n]
                                left_img_n = roi_image_n[h_n - 15 : h_n, 0:20].copy()
                                right_img_n = roi_image_n[h_n - 15 : h_n, w_n - 20 : w_n].copy()
                                is_adjacent_unopened_physically_clickable = (
                                    self.bgrColorMatch(left_img_n, self.grid_lower, self.grid_upper, self.grid_count, context) > 0 or
                                    self.bgrColorMatch(right_img_n, self.grid_lower, self.grid_upper, self.grid_count, context) > 0
                                )
                                if not is_adjacent_unopened_physically_clickable:
                                    is_consistent_explored = False # 发现不一致的相邻 UNOPENED
                                    break
                    if not is_consistent_explored:
                        explored_to_revert.append((r_idx, c_idx))
        
        for r_rev, c_rev in explored_to_revert:
            logger.warning(f"[WARNING] 格子 ({r_rev+1},{c_rev+1}) 的EXPLORED状态不一致，回滚。")
            # 回滚到点击前的状态，或者根据物理可点击性判断
            # 如果它本来就是被点击的格子，且被强制变为EXPLORED，现在回滚
            # 最简单的回滚：变回 UNOPENED，让主循环重新处理
            # 也可以是根据 pre_click_grid_status[r_rev, c_rev] 及其物理状态来判断
            
            # 这里采取相对保守的策略：回滚到点击前的状态，如果点击前是UNOPENED/OPENED
            # 如果回滚后它仍无法物理点击，它会保持UNOPENED或变成EXPLORED（如果之前是OPENED）
            original_state_before_clicks = pre_click_grid_status[r_rev, c_rev]
            
            if original_state_before_clicks == self.GridState.UNOPENED:
                # 重新判断物理可点击性
                x_rev, y_rev, w_rev, h_rev = self.roi_matrix[r_rev * self.cols + c_rev]
                roi_image_rev = new_img[y_rev : y_rev + h_rev, x_rev : x_rev + w_rev]
                left_img_rev = roi_image_rev[h_rev - 15 : h_rev, 0:20].copy()
                right_img_rev = roi_image_rev[h_rev - 15 : h_rev, w_rev - 20 : w_rev].copy()
                is_current_physically_clickable = (
                    self.bgrColorMatch(left_img_rev, self.grid_lower, self.grid_upper, self.grid_count, context) > 0 or
                    self.bgrColorMatch(right_img_rev, self.grid_lower, self.grid_upper, self.grid_count, context) > 0
                )
                if is_current_physically_clickable:
                    self.grid_status[r_rev, c_rev] = self.GridState.OPENED
                else:
                    self.grid_status[r_rev, c_rev] = self.GridState.UNOPENED
            elif original_state_before_clicks == self.GridState.OPENED:
                # 重新判断物理可点击性
                x_rev, y_rev, w_rev, h_rev = self.roi_matrix[r_rev * self.cols + c_rev]
                roi_image_rev = new_img[y_rev : y_rev + h_rev, x_rev : x_rev + w_rev]
                left_img_rev = roi_image_rev[h_rev - 15 : h_rev, 0:20].copy()
                right_img_rev = roi_image_rev[h_rev - 15 : h_rev, w_rev - 20 : w_rev].copy()
                is_current_physically_clickable = (
                    self.bgrColorMatch(left_img_rev, self.grid_lower, self.grid_upper, self.grid_count, context) > 0 or
                    self.bgrColorMatch(right_img_rev, self.grid_lower, self.grid_upper, self.grid_count, context) > 0
                )
                if is_current_physically_clickable:
                    self.grid_status[r_rev, c_rev] = self.GridState.OPENED
                else:
                    self.grid_status[r_rev, c_rev] = self.GridState.EXPLORED # 曾为可，但现在不是，那就探索
            # 对于其他状态（怪物，DEVICE等），如果被误判为EXPLORED，这里也强制回滚
            else: # 如果点击前是怪物、侦测怪、DEVICE等，且被误判为EXPLORED，这里回滚到它们点击前的状态
                self.grid_status[r_rev, c_rev] = original_state_before_clicks

            status_changed = True # 回滚导致状态变化


        # 每次状态变化（尤其是 EXPLORED 出现）后，必须重新执行装置激活循环
        if status_changed or self.just_killed_a_monster: # 怪物击杀后 also sets just_killed_a_monster
            logger.info("[INFO] 地图状态发生变化，重新检查DEVICE激活。")
            self.check_and_trigger_devices(context)
            self._log_map_status("点击后状态更新及DEVICE激活完成。")
            self.just_killed_a_monster = False # 重置标记





    # ==========================================================================
    # A* 寻路算法 及 开路寻路逻辑
    # ==========================================================================

    def manhattan_distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
        """计算两个格子之间的曼哈顿距离，用于A*算法的启发函数。"""
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def a_star_search(self, start_coords: Tuple[int, int], goal_coords: Tuple[int, int], current_simulated_grid_status: np.ndarray) -> Optional[Tuple[List[Tuple[int, int]], int]]:
        """
        A* 寻路算法，在模拟地图状态下，寻找从 start_coords 到 goal_coords 的路径。
        返回 (路径, 路径代价)。这里的代价主要反映“开路点击”的成本。
        
        Args:
            start_coords: 起始格子 (r, c)。必须是安全区。
            goal_coords: 目标格子 (r, c)。
            current_simulated_grid_status: 当前模拟的地图状态。
            
        Returns:
            Tuple[List[Tuple[int, int]], int]: (从起点到目标的路径, 路径总代价)，如果找不到则返回 None。
        """
        # A* 算法的开放列表：(f_score, g_score, (r, c))
        open_set = []
        # g_score: 从起点到当前节点的实际代价（点击次数）
        # h_score: 从当前节点到目标估计的代价（曼哈顿距离）
        # f_score: g_score + h_score
        
        # heapq 最小堆的第一个元素是优先级
        heapq.heappush(open_set, (0, 0, start_coords))

        # 记录从起点到某个节点的最低实际代价
        g_scores = {start_coords: 0}
        came_from = {start_coords: None}
        
        # 用于临时存储并修改 self.grid_status 的副本，以供 is_grid_clickable 和 _is_safe_zone 使用
        # 实际操作时，我们会传入当前的模拟状态
        original_grid_status = self.grid_status 
        self.grid_status = current_simulated_grid_status # 临时切换到模拟状态

        try:
            while open_set:
                current_f, current_g, current_coords = heapq.heappop(open_set)

                # 达到目标
                if current_coords == goal_coords:
                    # 构建路径
                    path = []
                    temp = current_coords
                    while temp is not None:
                        path.append(temp)
                        temp = came_from[temp]
                    return path[::-1], current_g

                # 遍历邻居
                for dr, dc in DIRECTIONS:
                    neighbor_coords = (current_coords[0] + dr, current_coords[1] + dc)

                    # 检查边界
                    if not (0 <= neighbor_coords[0] < self.rows and 0 <= neighbor_coords[1] < self.cols):
                        continue

                    # 如果邻居已经探索过，或者即将被探索，并且路径代价更低，则更新
                    neighbor_status = self.grid_status[neighbor_coords[0], neighbor_coords[1]]

                    # 计算从当前节点到邻居的移动代价 (即点击代价)
                    move_cost = 0 # 默认不点击则为0

                    if neighbor_status == self.GridState.UNOPENED:
                        move_cost = COST_UNOPENED_CLICK
                    elif neighbor_status == self.GridState.OPENED:
                        move_cost = COST_OPENED_CLICK
                    elif neighbor_status == self.GridState.DETECTED_MONSTER:
                        move_cost = COST_DETECTED_MONSTER_CLICK # 修正后的值 (2)
                    elif neighbor_status == self.GridState.REMOTE_MONSTER or \
                         neighbor_status == self.GridState.MELEE_MONSTER:
                        # 如果目标是怪物，并且是从安全区或已开路的格子跳过来攻击，这算一次攻击代价
                        # 但这个A* 是找“开路”路径的，攻击怪物本身不是开路
                        # 这里的代价应该只计算到“可点击”为止，攻击怪物的代价在外部计算
                        move_cost = 0 # 抵达怪兽格子不额外加开路代价
                    elif neighbor_status in [self.GridState.OBSTACLE, self.GridState.DEVICE]:
                        # 障碍和未激活装置不可通过，视作无限代价
                        continue # 不可走
                    
                    # 检查是否有近战怪阻碍
                    if neighbor_status in [self.GridState.UNOPENED, self.GridState.OPENED, self.GridState.DETECTED_MONSTER]:
                        if self._is_melee_monster_blocking(neighbor_coords[0], neighbor_coords[1]):
                            continue # 被阻碍，不可走


                    new_g_score = current_g + move_cost

                    # 如果通过当前路径到达邻居的代价更低
                    if new_g_score < g_scores.get(neighbor_coords, float('inf')):
                        g_scores[neighbor_coords] = new_g_score
                        came_from[neighbor_coords] = current_coords
                        
                        # 启发函数：曼哈顿距离
                        h_score = self.manhattan_distance(neighbor_coords, goal_coords)
                        
                        f_score = new_g_score + h_score
                        heapq.heappush(open_set, (f_score, new_g_score, neighbor_coords))

            return None # 找不到路径
        finally:
            self.grid_status = original_grid_status # 恢复原始地图状态


    def find_path_to_make_target_clickable(self, target_coords: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        找到一条“开路”路径（一系列点击操作），使得指定的目标格子（target_coords）最终变得可点击。
        
        返回的是一个点击序列，从当前的某个安全区出发，一步步点击，直到目标格子可点击。
        """
        # 1. 如果目标本身已经是安全区或可点击的，直接返回一个空列表（表示无需开路点击）
        if self._is_safe_zone(target_coords[0], target_coords[1]) or self.is_grid_clickable(target_coords[0], target_coords[1]):
            logger.debug(f"目标 ({target_coords[0]+1},{target_coords[1]+1}) 已可直接点击或已是安全区，无需开路。")
            return []

        # 2. 找到所有可能的安全区起点
        start_nodes = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self._is_safe_zone(r, c):
                    start_nodes.append((r, c))

        if not start_nodes:
            logger.warning("当前地图上没有安全区起点，无法规划开路路径。")
            return None

        # 3. BFS/A* 搜索开路路径
        # 状态定义：(当前格子坐标, 累计点击序列, 模拟地图状态副本)
        
        # 优先级队列：(cost, current_coords, clicks_so_far, simulated_grid_state_hash)
        # cost: 总代价 (点击次数)
        # current_coords: 当前模拟达到的格子
        # clicks_so_far: 为了达到当前模拟状态所执行的实际点击序列
        # simulated_grid_state_hash: 当前模拟地图状态的哈希值，用于 visited_states
        
        # visited 集合用于避免重复计算，存储 (当前格子, tuple(模拟地图状态的字节串))
        visited_states = set() 
        
        pq = [] # Priority Queue (total_clicks_cost, current_coords, clicks_so_far)

        # 初始状态：从每个安全区开始，0点击，当前模拟状态就是实际状态
        initial_sim_grid_hash = hash(self.grid_status.tobytes())
        for start_node in start_nodes:
            if (start_node, initial_sim_grid_hash) not in visited_states:
                heapq.heappush(pq, (0, start_node, [])) # (点击代价, 当前格子,  clicks_so_far)
                visited_states.add((start_node, initial_sim_grid_hash))


        while pq:
            current_clicks_cost, current_coords, clicks_so_far = heapq.heappop(pq)
            
            # 动态模拟地图状态：根据 clicks_so_far 推演地图状态
            # 这是一个关键步骤，我们需要一个临时的地图状态来评估 is_grid_clickable
            simulated_grid_status = np.copy(self.grid_status)
            for r_c, c_c in clicks_so_far:
                if simulated_grid_status[r_c, c_c] == self.GridState.UNOPENED:
                    simulated_grid_status[r_c, c_c] = self.GridState.EXPLORED
                elif simulated_grid_status[r_c, c_c] == self.GridState.OPENED:
                    simulated_grid_status[r_c, c_c] = self.GridState.EXPLORED
                elif simulated_grid_status[r_c, c_c] == self.GridState.DETECTED_MONSTER:
                    simulated_grid_status[r_c, c_c] = self.GridState.MELEE_MONSTER # 侦测怪点击后变近战怪

            # 模拟 DEVICE 激活的连锁反应
            device_activated_in_sim = True
            sim_loop_count = 0
            max_sim_device_loops = 5
            while device_activated_in_sim and sim_loop_count < max_sim_device_loops:
                device_activated_in_sim = False
                sim_loop_count += 1
                for r_s, c_s in np.ndindex(simulated_grid_status.shape):
                    if simulated_grid_status[r_s, c_s] == self.GridState.DEVICE:
                        for dr_s, dc_s in DIRECTIONS:
                            nr_s, nc_s = r_s + dr_s, c_s + dc_s
                            if 0 <= nr_s < self.rows and 0 <= nc_s < self.cols and \
                               simulated_grid_status[nr_s, nc_s] in [self.GridState.DOOR, self.GridState.FRIEND, self.GridState.EXPLORED, self.GridState.DEVICE_ACTIVATED]:
                                simulated_grid_status[r_s, c_s] = self.GridState.DEVICE_ACTIVATED
                                device_activated_in_sim = True
                                break # 找到一个激活邻居就够了
            
            # 临时将 self.grid_status 指向模拟状态，以便 is_grid_clickable 和 _is_safe_zone 使用
            original_grid_status_ref = self.grid_status
            self.grid_status = simulated_grid_status

            # 检查目标是否在当前模拟状态下可点击
            target_becomes_clickable = self.is_grid_clickable(target_coords[0], target_coords[1]) or \
                                       self._is_safe_zone(target_coords[0], target_coords[1])
            
            # 恢复 self.grid_status
            self.grid_status = original_grid_status_ref

            if target_becomes_clickable:
                logger.debug(f"找到开路路径，使目标 ({target_coords[0]+1},{target_coords[1]+1}) 可点击。点击序列: {[(r+1,c+1) for r,c in clicks_so_far]}")
                return clicks_so_far # 返回需要点击的格子序列

            # 扩展邻居
            for dr, dc in DIRECTIONS:
                neighbor_coords = (current_coords[0] + dr, current_coords[1] + dc)
                if not (0 <= neighbor_coords[0] < self.rows and 0 <= neighbor_coords[1] < self.cols):
                    continue

                # 注意：这里判断的是 original_grid_status_ref，而不是 simulated_grid_status，因为我们关心“接下来能点击什么”
                neighbor_original_status = original_grid_status_ref[neighbor_coords[0], neighbor_coords[1]] 

                # 只有 UNOPENED, OPENED, DETECTED_MONSTER, REMOTE_MONSTER, MELEE_MONSTER 才能被“点击”或“攻击”
                # 且不能是 OBSTACLE, DEVICE, 或被近战怪阻碍
                is_valid_click_target = False
                if neighbor_original_status in [self.GridState.UNOPENED, self.GridState.OPENED, self.GridState.DETECTED_MONSTER]:
                    if not self._is_melee_monster_blocking(neighbor_coords[0], neighbor_coords[1]): # 且未被近战怪阻碍
                         is_valid_click_target = True
                elif neighbor_original_status in [self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER]:
                    # 怪物可以被攻击，但也需要判断可点击性
                    if self.is_grid_clickable(neighbor_coords[0], neighbor_coords[1]): # 必须是可点击的怪物
                        is_valid_click_target = True

                if not is_valid_click_target:
                    continue # 这个格子不可作为开路点击的对象

                # 如果这个格子在 clicks_so_far 中已经存在，说明形成了环，或者重复点击，应避免
                if neighbor_coords in clicks_so_far:
                    continue

                new_clicks_so_far = clicks_so_far + [neighbor_coords]
                new_clicks_cost = current_clicks_cost + 1 # 每多点击一个格子，代价+1

                # 生成新的模拟状态的哈希值，用于 visited_states
                temp_sim_grid_for_hash = np.copy(simulated_grid_status)
                if temp_sim_grid_for_hash[neighbor_coords[0], neighbor_coords[1]] == self.GridState.UNOPENED:
                    temp_sim_grid_for_hash[neighbor_coords[0], neighbor_coords[1]] = self.GridState.EXPLORED
                elif temp_sim_grid_for_hash[neighbor_coords[0], neighbor_coords[1]] == self.GridState.OPENED:
                    temp_sim_grid_for_hash[neighbor_coords[0], neighbor_coords[1]] = self.GridState.EXPLORED
                elif temp_sim_grid_for_hash[neighbor_coords[0], neighbor_coords[1]] == self.GridState.DETECTED_MONSTER:
                    temp_sim_grid_for_hash[neighbor_coords[0], neighbor_coords[1]] = self.GridState.MELEE_MONSTER
                
                # 模拟 DEVICE 激活 (简化版)
                # 这个模拟 DEVICE 激活的逻辑是关键，因为它会改变模拟地图，影响后续可点击性
                device_activated_in_sim_hash_calc = True
                sim_loop_count_hash_calc = 0
                max_sim_device_loops_hash_calc = 5
                while device_activated_in_sim_hash_calc and sim_loop_count_hash_calc < max_sim_device_loops_hash_calc:
                    device_activated_in_sim_hash_calc = False
                    sim_loop_count_hash_calc += 1
                    for r_s, c_s in np.ndindex(temp_sim_grid_for_hash.shape):
                        if temp_sim_grid_for_hash[r_s, c_s] == self.GridState.DEVICE:
                            for dr_s, dc_s in DIRECTIONS:
                                nr_s, nc_s = r_s + dr_s, c_s + dc_s
                                if 0 <= nr_s < self.rows and 0 <= nc_s < self.cols and \
                                   temp_sim_grid_for_hash[nr_s, nc_s] in [self.GridState.DOOR, self.GridState.FRIEND, self.GridState.EXPLORED, self.GridState.DEVICE_ACTIVATED]:
                                    temp_sim_grid_for_hash[r_s, c_s] = self.GridState.DEVICE_ACTIVATED
                                    device_activated_in_sim_hash_calc = True
                                    break
                
                new_state_tuple_hash = hash(temp_sim_grid_for_hash.tobytes())
                
                if (neighbor_coords, new_state_tuple_hash) not in visited_states:
                    visited_states.add((neighbor_coords, new_state_tuple_hash))
                    
                    # 启发函数：当前点击序列的最后一个格子到目标格子的曼哈顿距离
                    heuristic_cost = new_clicks_cost + self.manhattan_distance(neighbor_coords, target_coords)
                    heapq.heappush(pq, (heuristic_cost, neighbor_coords, new_clicks_so_far))

        logger.warning(f"无法找到开路路径使目标 ({target_coords[0]+1},{target_coords[1]+1}) 可点击。")
        return None # 无法找到路径

    # ==========================================================================
    # 主清理流程 (clearCurrentLayer)
    # ==========================================================================

    def clearCurrentLayer(self, context: Context):
        """
        智能清层的主循环逻辑。
        实现有策略、有目的的地图清理。
        """
        logger.info(">>> 智能清层 V 1.3 开始 (玩家幽灵模式)。")
        self.initialize_grid_state(context) # 初始地图状态扫描和DEVICE激活

        max_clear_loops = 500 # 防止无限循环，设置最大清理循环次数
        current_loop = 0
        
        # 用于卡死检测：哈希当前地图状态，如果连续几次状态不变，则可能卡死
        last_grid_status_hash = hash(self.grid_status.tobytes()) 
        no_progress_count = 0 # 记录没有进展的循环次数
        MAX_NO_PROGRESS_COUNT = 5 # 连续5次无进展则认为卡死

        while current_loop < max_clear_loops:
            if context.tasker.stopping:
                logger.info("JJC_Fight_ClearCurrentLayer 被停止")
                break

            current_loop += 1
            self._log_map_status(f"===== 智能清层主循环 ({current_loop}) =====")

            # ------------------------------------------------------------------
            # 1. 神龙处理 (保持原有逻辑，每次循环开始时检测)
            # ------------------------------------------------------------------
            if self.isCheckDragon:
                if recoDetail := context.run_recognition("Fight_FindDragon", context.tasker.controller.post_screencap().wait().get()):
                    dragon_threshold = RECOGNITION_THRESHOLDS["Fight_FindDragon"]
                    if hasattr(recoDetail, 'best_result') and recoDetail.best_result and recoDetail.best_result.score >= dragon_threshold:
                        logger.info("是神龙,俺,俺们有救了！！！")
                        fightUtils.dragonwish(self.targetWish, context)
                        logger.info("智能清层 V 1.3 结束 (神龙带回)。")
                        return True # 任务成功结束

            # ------------------------------------------------------------------
            # 2. 寻找并执行优先级最高的行动 (支持开路)
            # ------------------------------------------------------------------
            action_taken_this_loop = False # 标记本轮是否有行动

            target_priorities = [
                (self.GridState.REMOTE_MONSTER, "远程怪"),
                (self.GridState.MELEE_MONSTER, "近战怪"), # 近战怪优先级在开路完成后高于侦测怪
                (self.GridState.DETECTED_MONSTER, "侦测怪"),
                (self.GridState.OPENED, "可点击石板"), # OPENED 优先级高于 UNOPENED
                (self.GridState.UNOPENED, "未翻开石板"), 
                (self.GridState.DEVICE, "未激活装置") # 确保DEVICE最终也会被激活
            ]

            best_action_clicks = None
            best_target_coords = None
            min_path_clicks_cost = float('inf') # 记录优先级最高的行动的开路点击代价

            for target_state, target_name in target_priorities:
                current_target_coords_list = []
                for r in range(self.rows):
                    for c in range(self.cols):
                        if self.grid_status[r, c] == target_state:
                            current_target_coords_list.append((r, c))
                
                if not current_target_coords_list:
                    continue # 当前优先级没有目标

                logger.debug(f"正在寻找 {target_name} 的开路方案...")
                
                # 对于当前优先级的所有目标，找到开路代价最小的那一个
                for target_coords in current_target_coords_list:
                    
                    clicks_to_make_clickable = self.find_path_to_make_target_clickable(target_coords)

                    if clicks_to_make_clickable is not None: # 找到了开路路径（包括空路径）
                        current_clicks_cost = len(clicks_to_make_clickable) # 开路代价就是点击次数
                        
                        # 额外处理目标本身的点击代价：如果是怪物或侦测怪，需要额外一次点击
                        # 如果 target_coords 已经包含在 clicks_to_make_clickable 且是最后一步，那么它既是开路点击也是攻击点击
                        # 否则，攻击是额外一步
                        is_target_monster_or_detected = target_state in [self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER, self.GridState.DETECTED_MONSTER]
                        if is_target_monster_or_detected:
                            # 只有当点击序列的最后一步不是目标格子本身时，才加上额外的攻击成本
                            # 因为目标格子如果是 DETECTED_MONSTER/UNOPENED/OPENED，其点击本身就算作翻出
                            # 远程怪和近战怪则需要额外攻击
                            if not clicks_to_make_clickable or clicks_to_make_clickable[-1] != target_coords:
                                if target_state in [self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER]:
                                    current_clicks_cost += COST_MONSTER_ATTACK 
                                # DETECTED_MONSTER 的攻击成本已在 COST_DETECTED_MONSTER_CLICK 中包含
                                # 所以这里不重复加
                                
                        if current_clicks_cost < min_path_clicks_cost:
                            min_path_clicks_cost = current_clicks_cost
                            best_action_clicks = clicks_to_make_clickable # 这里的点击序列是开路点击
                            best_target_coords = target_coords
                
                # 如果当前优先级下找到了最优行动，就执行并退出本轮优先级扫描
                if best_action_clicks is not None and min_path_clicks_cost != float('inf'): # 确保找到了有效路径
                    logger.info(f"[INFO] 找到优先级最高行动: 处理 {target_name} ({best_target_coords[0]+1},{best_target_coords[1]+1})，预计点击 {min_path_clicks_cost} 次。开路点击序列: {[(r+1,c+1) for r,c in best_action_clicks]}")
                    
                    # --- 优化核心：批量执行点击并最后一次性更新状态 ---
                    clicks_performed = [] # 记录实际执行的点击
                    
                    if not best_action_clicks: # 如果开路点击序列为空，说明目标本身就可点击
                        logger.info(f"[INFO] 目标 ({best_target_coords[0]+1},{best_target_coords[1]+1}) 已可直接点击，直接进行处理。")
                        # 此时不需要额外的开路点击，直接将目标作为待处理项
                        # 这一步通常意味着目标是可直接攻击的怪物或者可直接翻开的石板
                        # 它的处理逻辑将在下面的 if final_target_status_after_open_path in [...] 中执行
                        pass # 无需执行开路点击，直接进入后续目标处理
                    else:
                        for click_r, click_c in best_action_clicks:
                            self.click_grid(context, click_r, click_c)
                            clicks_performed.append((click_r, click_c))
                            # 不再在这里立即调用 update_grid_status_after_click
                            action_taken_this_loop = True
                            if context.tasker.stopping: return False # 如果中途停止，则退出
                            time.sleep(0.3) # 每个开路点击之间加短暂延迟

                        # 开路点击序列执行完毕后，进行一次全图状态更新
                        logger.info(f"[INFO] 开路点击序列执行完毕，更新全图状态。最后点击 ({clicks_performed[-1][0]+1},{clicks_performed[-1][1]+1})")
                        self.update_grid_status_after_click(context, clicks_performed[-1][0], clicks_performed[-1][1])
                    
                    # 此时，best_target_coords 应该已经根据开路点击后的实际情况更新了
                    # 重新获取目标格子在当前地图上的实际状态
                    final_target_status_after_open_path = self.grid_status[best_target_coords[0], best_target_coords[1]]

                    # 只有当它是怪物或侦测怪且需要攻击时才调用 _attack_and_verify_kill
                    if final_target_status_after_open_path in [self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER, self.GridState.DETECTED_MONSTER]:
                        # 如果目标是怪物或侦测怪，在开路后进行攻击
                        # 此时，如果它仍然是 DETECTED_MONSTER，则 click_grid 已经将其变为 MELEE_MONSTER (因为update_grid_status_after_click会处理)
                        # _attack_and_verify_kill 会处理 MELEE_MONSTER 和 REMOTE_MONSTER
                        # 注意：如果目标是侦测怪，它的点击本身就是开路的一部分，但侦测怪需要额外一次攻击才能触发后续状态
                        # 所以这里 _attack_and_verify_kill 仍然是必要的
                        if final_target_status_after_open_path == self.GridState.DETECTED_MONSTER:
                            logger.info(f"[INFO] 侦测怪 ({best_target_coords[0]+1},{best_target_coords[1]+1}) 已翻出，即将攻击。")
                            # 此时它可能已经在上一个 update_grid_status_after_click 中被转为 MELEE_MONSTER 了
                            # 但为了明确意图，确保它是 MELEE_MONSTER
                            self.grid_status[best_target_coords[0], best_target_coords[1]] = self.GridState.MELEE_MONSTER 
                        else:
                            logger.info(f"[INFO] 目标 {target_name} ({best_target_coords[0]+1},{best_target_coords[1]+1}) 已可点击，进行攻击。")
                        
                        # _attack_and_verify_kill 内部会进行点击和更新
                        self._attack_and_verify_kill(context, best_target_coords[0], best_target_coords[1])
                        action_taken_this_loop = True
                    elif final_target_status_after_open_path == self.GridState.DEVICE_ACTIVATED:
                        # 如果是 DEVICE，在开路点击后，它应该已经变为 DEVICE_ACTIVATED
                        logger.info(f"[INFO] 装置 ({best_target_coords[0]+1},{best_target_coords[1]+1}) 已激活。")
                        action_taken_this_loop = True
                    elif final_target_status_after_open_path == self.GridState.EXPLORED:
                        # 如果是石板，开路点击已经处理了，使其变为 EXPLORED
                        logger.info(f"[INFO] 石板 ({best_target_coords[0]+1},{best_target_coords[1]+1}) 已翻开并探索。")
                        action_taken_this_loop = True
                    elif final_target_status_after_open_path == self.GridState.DEVICE: # 目标是 DEVICE，但未激活
                        logger.info(f"[INFO] 目标装置 ({best_target_coords[0]+1},{best_target_coords[1]+1}) 尚未激活，继续尝试。")
                        action_taken_this_loop = True # 算作尝试过行动
                    else:
                        # 这种情况可能是目标变成了意想不到的状态，比如 OBSTACLE
                        logger.warning(f"[WARNING] 目标 ({best_target_coords[0]+1},{best_target_coords[1]+1}) 变为意外状态: {final_target_status_after_open_path.value}，重新评估。")
                        action_taken_this_loop = True # 算作有行动，避免卡死

                    # 处理完一个优先级最高的行动后，立即跳出当前优先级循环，回到主循环重新评估地图状态
                    # 这样可以确保始终优先处理最高优先级目标，并应对地图变化
                    break 

            # ------------------------------------------------------------------
            # 3. 循环结束条件和卡死检测
            # ------------------------------------------------------------------

            # 检查探索是否完成 (无远程怪，无近战怪，无可点击石板)
            exploration_finished = True
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.grid_status[r, c] in [
                        self.GridState.REMOTE_MONSTER,
                        self.GridState.MELEE_MONSTER,
                        self.GridState.OPENED
                    ]:
                        exploration_finished = False
                        break
                if not exploration_finished:
                    break

            if exploration_finished:
                logger.info("[INFO] 探索完成：地图上已无怪物和可点击石板。")
                break # 退出循环

            # *** 新增：神秘条件触发检测和处理 ***
            # 当本轮没有有效行动，且出现“意外状态”的可能性时，进行此检查
            current_grid_status_hash = hash(self.grid_status.tobytes())
            if not action_taken_this_loop and current_grid_status_hash == last_grid_status_hash:
                no_progress_count += 1
                logger.warning(f"[WARNING] 第 {no_progress_count} 次没有进展。")
                
                if no_progress_count >= MAX_NO_PROGRESS_COUNT:
                    logger.info("[INFO] 连续多次没有进展，尝试判断是否触发神秘条件（全图清场）。")
                    
                    has_monster_bloodbar = False
                    has_physical_clickable_tiles = False

                    for r in range(self.rows):
                        for c in range(self.cols):
                            if self.grid_status[r, c] in [self.GridState.REMOTE_MONSTER, self.GridState.MELEE_MONSTER]:
                                has_monster_bloodbar = True
                            if self.grid_status[r, c] == self.GridState.OPENED:
                                has_physical_clickable_tiles = True
                            
                            if has_monster_bloodbar and has_physical_clickable_tiles: # 提前跳出
                                break
                        if has_monster_bloodbar and has_physical_clickable_tiles: # 提前跳出
                            break
                    
                    if not has_monster_bloodbar and not has_physical_clickable_tiles:
                        logger.info("[INFO] 触发神秘条件：全图无怪物血条，且无物理可点击石板。")
                        logger.info("[INFO] 强制将所有'未'和'可'的石板标记为'空'，完成本层探索。")
                        for r in range(self.rows):
                            for c in range(self.cols):
                                if self.grid_status[r, c] in [self.GridState.UNOPENED, self.GridState.OPENED, self.GridState.DETECTED_MONSTER]:
                                    self.grid_status[r, c] = self.GridState.EXPLORED
                                elif self.grid_status[r, c] == self.GridState.DEVICE: # 未激活的DEVICE也视为已探索
                                    self.grid_status[r, c] = self.GridState.EXPLORED
                        exploration_finished = True # 标记为已完成
                        break # 跳出主循环
                    else:
                        logger.error("[ERROR] 连续多次没有进展，但未触发神秘条件。任务可能卡住。强制退出。")
                        break
            else:
                no_progress_count = 0 # 有进展则重置计数
            
            last_grid_status_hash = current_grid_status_hash

            time.sleep(0.5) # 每轮主循环之间稍作等待

        if current_loop >= max_clear_loops:
            logger.warning(f"[WARNING] 清层循环达到最大次数 ({max_clear_loops})，可能仍有未清理的格子。")
            self._log_map_status("最终地图状态")
        
        if exploration_finished: # 检查是否是由于神秘条件而完成
            logger.info("智能清层 V 1.3 结束 (探索完成)。")
        else:
            logger.info("智能清层 V 1.3 结束 (其他原因)。")
        return True # 任务完成或终止

