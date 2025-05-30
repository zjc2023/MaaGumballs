from loguru import logger
import re

def extract_numbers(input_string):
    """从字符串中识别并返回第一个数字"""
    numbers = re.findall(r'\d+', input_string)
    if numbers:
        return int(numbers[0])
    else:
        return None
