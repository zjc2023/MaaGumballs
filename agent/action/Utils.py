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
