import cv2
import numpy as np
import win32gui
from skimage.metrics import structural_similarity as ssim


class ImageUtils:
    @staticmethod
    def get_image_info(image_path):
        """
        获取图片的信息，如尺寸。
        :param image_path: 图片路径。
        :return: 图片的宽度和高度。
        """
        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        return template.shape[::-1]

    @staticmethod
    def get_template_mask(target):
        """
        读取模板图片，并根据需要生成掩码。
        :param target: 目标图片路径。
        :return: 如果图片包含透明通道，并且存在部分透明的像素，就返回 mask，即 alpha 通道；否则，返回 None，表示没有生成掩码。
        """
        template = cv2.imread(target, cv2.IMREAD_UNCHANGED)  # 保留图片的透明通道
        if template is None:
            raise ValueError(f"读取图片失败：{target}")

        mask = None
        if template.shape[-1] == 4:  # 检查通道数是否为4（含有透明通道）
            alpha_channel = template[:, :, 3]
            if np.any(alpha_channel < 255):  # 检查是否存在非完全透明的像素
                mask = alpha_channel

        return mask

    @staticmethod
    def calculate_ssim(image1, image2) -> float:
        """
        计算两张图像的结构相似度（SSIM）。传入的两张图像需要长宽一致

        参数:
        - image1: 第一张图像,一般为模板
        - image2: 第二张图像，一般为target

        返回:
        - SSIM值：0到1之间，值越接近1表示图像越相似。
        """
        if isinstance(image1,str):
            image1 = cv2.imread(image1)
        if isinstance(image2,str):
            image2 = cv2.imread(image2)
        # 确保图像是灰度图像，转换为灰度图
        image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # 检查图像形状是否一致，如果不一致，将image2调整为image1的大小
        if image1.shape != image2.shape:
            image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))

        # 计算SSIM
        similarity_index, _ = ssim(image1, image2, full=True)
        return similarity_index

    @staticmethod
    def match_template(screenshot, template,mask=None,match_method=cv2.TM_SQDIFF_NORMED):
        """
        对模版与截图进行匹配，找出匹配位置
        :param match_method: 模版匹配的方法
        :param screenshot:待匹配的截图图像
        :param template:用于匹配的模板图像，通常是一个较小的图像片段
        :param mask:掩码，用于图像匹配中的区域选择。
        :return:
        """
        # ImageUtils.show_ndarray(screenshot)
        if mask is not None:
            # cv2.TM_CCOEFF_NORMED 是针对缩放情况下最推荐的模板匹配方法，因为它对亮度和对比度的变化更具有鲁棒性。
            result = cv2.matchTemplate(screenshot, template ,match_method, mask=mask)
        else:
            result = cv2.matchTemplate(screenshot, template, match_method)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if match_method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            val = 1-min_val
            loc = min_loc
        elif match_method in [cv2.TM_CCOEFF_NORMED,cv2.TM_CCORR_NORMED]:
            val = max_val
            loc = max_loc
        else:
            val = max_val
            loc = max_loc
        # print(f"{min_val=},{max_val=}")
        return val, loc

    @staticmethod
    def resize_screenshot(hwnd,screenshot,crop,is_starter):
        # 获取带标题的窗口尺寸
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        # print(left, top, right, bottom)
        w = right - left
        h = bottom - top

        # 计算裁剪区域裁剪图像
        crop_left = int(crop[0] * w)
        crop_top = int(crop[1] * h)
        crop_right = int(crop[2] * w)
        crop_bottom = int(crop[3] * h)
        img_cropped = screenshot[crop_top:crop_bottom, crop_left:crop_right]

        # 缩放图像以自适应分辨率图像识别
        if is_starter:
            scale_x = 1
            scale_y = 1
        else:
            scale_x = 1920 / w
            scale_y = 1080 / h
        # if img_cropped is None or img_cropped.size == 0:
        #     print(f"{img_cropped.size=}")
        try:
            img_resized = cv2.resize(img_cropped,
                                 (int(img_cropped.shape[1] * scale_x), int(img_cropped.shape[0] * scale_y)),interpolation=cv2.INTER_CUBIC)
        except Exception as e:
            print(e)
            return None

        relative_pos = (
            int(w * crop[0]),
            int(h * crop[1]),
            int(w * crop[2]),
            int(h * crop[3])
        )

        return img_resized,relative_pos

    @staticmethod
    def show_ndarray(image,title="show_ndarray"):
        cv2.imshow(title, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    @staticmethod
    def intersected(top_left1, botton_right1, top_left2, botton_right2):
        """判断两个矩形是否相交。

        参数:
        - top_left1: 第一个矩形的左上角坐标 (x, y)。
        - botton_right1: 第一个矩形的右下角坐标 (x, y)。
        - top_left2: 第二个矩形的左上角坐标 (x, y)。
        - botton_right2: 第二个矩形的右下角坐标 (x, y)。

        返回:
        - bool: 如果矩形相交返回True，否则返回False。

        逻辑说明:
        - 如果一个矩形在另一个矩形的右侧或左侧，它们不相交。
        - 如果一个矩形在另一个矩形的上方或下方，它们也不相交。
        - 否则，矩形相交。
        """
        # 检查矩形1是否在矩形2的右侧或矩形2是否在矩形1的右侧
        if top_left1[0] > botton_right2[0] or top_left2[0] > botton_right1[0]:
            return False
        # 检查矩形1是否在矩形2的下方或矩形2是否在矩形1的下方
        if top_left1[1] > botton_right2[1] or top_left2[1] > botton_right1[1]:
            return False
        # 上述条件都不成立，则矩形相交
        return True

    @staticmethod
    def is_match_non_overlapping(top_left, matches, width, height):
        """检查给定的匹配位置是否与已有的匹配重叠。

        参数:
        - top_left: 当前匹配的左上角坐标。
        - matches: 已有的匹配位置列表。
        - width: 模板宽度。
        - height: 模板高度。

        返回:
        - bool: 是否不重叠。
        """
        botton_right = (top_left[0] + width, top_left[1] + height)
        for match_top_left in matches:
            match_botton_right = (match_top_left[0] + width, match_top_left[1] + height)
            if ImageUtils.intersected(top_left, botton_right, match_top_left, match_botton_right):
                return False
        return True

    @staticmethod
    def filter_overlapping_matches(locations, template_size):
        """过滤掉重叠的匹配。

        参数:
        - locations: 匹配的位置数组。
        - template_size: 模板图片的大小 (宽度, 高度)。

        返回:
        - matches: 不重叠的匹配位置列表。
        """
        matches = []
        height, width = template_size
        for top_left in zip(*locations[::-1]):
            if ImageUtils.is_match_non_overlapping(top_left, matches, width, height):
                matches.append(top_left)
        return matches

    @staticmethod
    def count_template_matches(target, template, threshold):
        """使用模板匹配计算目标图片中的匹配数。

        参数:
        - target: 目标图片数组。
        - template: 模板图片数组。
        - threshold: 匹配阈值，用于决定哪些结果被认为是匹配。

        返回:
        - match_count: 匹配的数量。
        """
        # 执行模板匹配
        result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        matches = ImageUtils.filter_overlapping_matches(locations, template.shape[:2])
        return len(matches)

    @staticmethod
    def extract_letters(image, letter=(255, 255, 255), threshold=128):
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
