import cv2
import re
import numpy as np
def calCoordinate():
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

    # print (roi_list)
    return roi_list


def color_match(image, lower_bound=None, upper_bound=None, count=300):
    """
    检测图像是否包含目标颜色。

    :param image: 输入的图像 (numpy array)
    :param lower_bound: 颜色范围的下界 (list or numpy array)
    :param upper_bound: 颜色范围的上界 (list or numpy array)
    :param count: 匹配像素的最小数量
    :return: 是否匹配 (True/False)
    """
    if lower_bound is None or upper_bound is None:
        raise ValueError("必须提供 lower_bound 和 upper_bound 参数")

    # 将图像转换为 HSV 色彩空间
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 创建掩码
    mask = cv2.inRange(hsv_image, np.array(lower_bound), np.array(upper_bound))

    # 检查是否有足够的匹配像素
    match = cv2.countNonZero(mask) > count
    return match

def detect_stats(image):
        # 定义左上角和左下角的 ROI 区域
        h, w = image.shape[:2]
        life_roi = image[0:int(h * 0.2), 0:int(w * 0.3)]  # 左上角区域
        attack_roi = image[int(h * 0.8):h, 0:int(w * 0.3)]  # 左下角区域
        cv2.imwrite("life_roi.png", life_roi)  # 保存 ROI 区域以供调试
        cv2.imwrite("attack_roi.png", attack_roi)  # 保存 ROI 区域以供调试

        # 转换为灰度图
        gray_life = cv2.cvtColor(life_roi, cv2.COLOR_BGR2GRAY)
        gray_attack = cv2.cvtColor(attack_roi, cv2.COLOR_BGR2GRAY)

        # 二值化处理
        _, binary_life = cv2.threshold(gray_life, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        _, binary_attack = cv2.threshold(gray_attack, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # 使用 OCR 提取数字
        life_value = pytesseract.image_to_string(binary_life, config='--psm 6 digits')
        attack_value = pytesseract.image_to_string(binary_attack, config='--psm 6 digits')

        # 转换为整数
        try:
            life_value = int(life_value.strip())
        except ValueError:
            life_value = None  # 如果无法提取，返回 None

        try:
            attack_value = int(attack_value.strip())
        except ValueError:
            attack_value = None  # 如果无法提取，返回 None

        return life_value, attack_value

def detect_stats_with_contours(image):
    """
    使用轮廓检测提取图片的左上角（生命值）和左下角（攻击力）。

    :param image: 输入的图片 (numpy array)
    :return: 生命值和攻击力的数值 (生命值, 攻击力)
    """
    h, w = image.shape[:2]
    life_roi = image[0:int(h * 0.3), 0:int(w * 0.3)]  # 左上角区域
    attack_roi = image[int(h * 0.7):h, 0:int(w * 0.3)]  # 左下角区域

    def extract_number(roi):
        # 转换为灰度图
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # 二值化
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # 检测轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 找到最大的轮廓（假设数字区域是最大的）
        max_contour = max(contours, key=cv2.contourArea, default=None)

        if max_contour is not None:
            x, y, w, h = cv2.boundingRect(max_contour)
            number_roi = binary[y:y + h, x:x + w]

            # 使用 OCR 提取数字
            number = pytesseract.image_to_string(number_roi, config='--psm 6 digits')
            try:
                return int(number.strip())
            except ValueError:
                return None  # 如果无法提取，返回 None
        return None

    # 提取生命值和攻击力
    life_value = extract_number(life_roi)
    attack_value = extract_number(attack_roi)

    return life_value, attack_value

def checkMonster_py(image, roi_matrix):
    # 获取当前屏幕截图
    # 计算ROI坐标
    
    # 将 roi_list 转换为 6x5 的二维矩阵
    rows, cols = 6, 5
    # 定义颜色范围（偏白色）
    lower_bound = [0, 0, 150]
    upper_bound = [40, 60, 255]
    # 检测偏白色的格子
    for r in range(rows):
        for c in range(cols):
            x, y, w, h = roi_matrix[r][c]
            roi_image = image[y:y + h, x:x + w]

            attack, blood = detect_stats_with_contours(roi_image)
            print(f'Attack = {attack}, Blood = {blood}')

            # if utils.color_match(roi_image, lower_bound, upper_bound):
                # self.send_log(f"检测到偏白色格子: ({r + 1}, {c + 1})")
                # self.tasker.controller.post_click(x + w // 2, y + h // 2).wait()
                # time.sleep(0.3)

# 从一个字符串里面识仅识别一串数字, 并返回
def extract_numbers(input_string):
    # 使用正则表达式匹配所有的数字
    numbers = re.findall(r'\d+', input_string)
    # 如果找到数字，返回第一个数字，否则返回 None, 返回类型为 int
    if numbers:
        return int(numbers[0])
    else:
        return None