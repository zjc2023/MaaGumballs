from loguru import logger
import re


# 从字符串中识别并返回第一个数字
def extract_numbers(input_string):
    numbers = re.findall(r"\d+", input_string)
    if numbers:
        return int(numbers[0])
    else:
        return None


# 初始化地板的 ROI 列表
def calRoiList():
    start_x, start_y = 15, 222
    width, height = 138, 126
    cols, rows = 5, 6

    roi_list = []

    for r in range(rows):
        for c in range(cols):
            x = start_x + c * width
            y = start_y + r * height
            roi = [x, y, width, height]
            roi_list.append(roi)
    return roi_list


# 假设存在一个辅助函数用于判断两个 ROI 区域是否重叠或者大部分重叠
# 这里需要根据实际的 ROI 数据结构实现具体逻辑
def is_roi_in_or_mostly_in(roi1, roi2):
    # 简单示例：假设 ROI 是 (x, y, width, height) 元组
    # 计算两个 ROI 的交集面积
    x1 = max(roi1[0], roi2[0])
    y1 = max(roi1[1], roi2[1])
    x2 = min(roi1[0] + roi1[2], roi2[0] + roi2[2])
    y2 = min(roi1[1] + roi1[3], roi2[1] + roi2[3])
    if x2 > x1 and y2 > y1:
        intersection_area = (x2 - x1) * (y2 - y1)
        roi1_area = roi1[2] * roi1[3]
        # 判断交集面积是否超过 roi1 面积的一半
        return intersection_area / roi1_area >= 0.5
    return False
