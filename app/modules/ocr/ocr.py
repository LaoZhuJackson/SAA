import json
import os
import time

import cv2
import paddle
from PIL import Image
from paddleocr import PaddleOCR
import numpy as np

from app.common.logger import logger


class OCR:
    def __init__(self,logger,replacements=None):
        self.ocr = None
        self.logger = logger
        self.replacements = replacements

    def run(self, image,extract:list=None):
        """
        进行ocr识别并返回格式化后的识别结果
        :param extract: 是否提取文字，[(文字rgb颜色),threshold数值]
        :param image: 支持图像路径字符串，以及np.array类型(height, width, channels)
        :return:
        """
        self.instance_ocr()
        try:
            if isinstance(image, str):
                image = cv2.imread(image, cv2.IMREAD_UNCHANGED)  # 读取图像，保持原始通道
                if image.shape[2] == 4:  # 如果是RGBA图像
                    image = image[:, :, :3]  # 只保留RGB通道
            if extract:
                # 需要提取文字
                letter = extract[0]
                threshold = extract[1]
                image = self.extract_letters(image,letter,threshold)
            original_result = self.ocr(image)
            if original_result:
                return self.format_and_replace(original_result)
            else:
                return None
        except Exception as e:
            logger.error(e)
            return None

    def format_and_replace(self, result):
        """
        转换OCR结果格式，返回统一的数据格式并替换OCR结果中的错误字符串
        :param result: 原始ocr识别结果
        :return:输出示例
        ['16 +', 0.93, [[10.0, 23.0], [75.0, 58.0]]]
        ['CADPA', 0.99, [[12.0, 70.0], [69.0, 87.0]]]
        ['适龄提示', 1.0, [[7.0, 90.0], [75.0, 106.0]]]
        """
        formatted_result = []
        # print(f"original result: {result}")

        # 获取坐标和文本+置信度
        boxes = result[0]  # OCR 输出的坐标
        text_confidences = result[1]  # OCR 输出的文本和置信度

        for i in range(len(boxes)):
            # 获取当前框的坐标
            box = boxes[i]
            # 左上角坐标
            top_left = box[0]
            # 右下角坐标
            bottom_right = box[2]

            # 获取当前文本和置信度
            text, confidence = text_confidences[i]

            # 进行错误文本替换
            # 直接替换
            for old_text,new_text in self.replacements['direct'].items():
                text = text.replace(old_text, new_text)

            # 条件替换：只有当 new_str 不出现在 item["text"] 中时，才进行替换
            for old_text,new_text in self.replacements['conditional'].items():
                if new_text not in text:
                    text = text.replace(old_text,new_text)

            # 格式化输出: [文本, 置信度, 左上和右下坐标]
            formatted_result.append([text, round(confidence, 2), [top_left.tolist(), bottom_right.tolist()]])
        return formatted_result

    def extract_letters(self, image, letter=(255, 255, 255), threshold=128):
        """
        将目标颜色的文字转成黑色，将背景转成白色
        :param image:
        :param letter: 文字颜色
        :param threshold:
        :return: np.ndarray: Shape (height, width, 3)
        """
        # (*letter, 0) 将 letter 转换为 (255, 255, 255, 0),表示四个通道（RGB + Alpha），diff 是图像和字母颜色之间的差异
        # 逐像素地将图像中的每个像素减去给定的字母颜色,字母部分归0
        diff = cv2.subtract(image, (*letter, 0))
        # 分离通道
        r, g, b = cv2.split(diff)
        # 从 r、g 和 b 三个通道中选择最大值，最终，r 存储的是每个像素通道中最大的差异值
        cv2.max(r, g, dst=r)
        cv2.max(r, b, dst=r)
        # 正向差异最大值
        positive = r
        # 反向再减一次，得到的是图像与字母的反向差异
        cv2.subtract((*letter, 0), image, dst=diff)
        r, g, b = cv2.split(diff)
        cv2.max(r, g, dst=r)
        cv2.max(r, b, dst=r)
        # 反向差异最大值
        negative = r
        # 通过 cv2.add，将它们加起来，得到整个图像中包含字母和背景的综合差异值
        cv2.add(positive, negative, dst=positive)
        # alpha 参数控制图像的亮度比例，255.0 / threshold 用于调整图像的对比度，这个操作会将综合差异值放大，白的更白，黑的更黑
        cv2.convertScaleAbs(positive, alpha=255.0 / threshold, dst=positive)
        # 将单通道图像转换为3通道图像
        three_channel_image = cv2.merge([positive, positive, positive])
        # cv2.imshow("bw", three_channel_image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        return three_channel_image

    def instance_ocr(self):
        """实例化OCR，若ocr实例未创建，则创建之"""
        if self.ocr is None:
            try:
                # 自动检测是否可用NVIDIA GPU
                # FIXME ocr用上高贵的gpu use_gpu = paddle.is_compiled_with_cuda() and paddle.device.get_device().startswith("gpu")
                use_gpu = False
                print(f"{use_gpu=}")
                self.logger.debug("开始初始化OCR...")
                self.ocr = PaddleOCR(use_gpu=use_gpu, use_angle_cls=False, lang='ch')
                self.logger.debug("初始化OCR完成")
            except Exception as e:
                self.logger.error(f"初始化OCR失败：{e}")
                raise Exception("初始化OCR失败")

    def exit_ocr(self):
        """退出OCR实例，清理资源"""
        if self.ocr is not None:
            self.ocr.exit_ocr()
            self.ocr = None
