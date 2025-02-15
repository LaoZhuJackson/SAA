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
        - image1: 第一张图像
        - image2: 第二张图像

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

        # 计算SSIM
        # print(image1.shape, image2.shape)
        similarity_index, _ = ssim(image1, image2, full=True)
        return similarity_index

    @staticmethod
    def match_template(screenshot, template,mask=None):
        """
        对模版与截图进行匹配，找出匹配位置
        :param screenshot:待匹配的截图图像
        :param template:用于匹配的模板图像，通常是一个较小的图像片段
        :param mask:掩码，用于图像匹配中的区域选择。
        :return:
        """
        match_method = cv2.TM_SQDIFF_NORMED
        # ImageUtils.show_ndarray(screenshot)
        if mask is not None:
            # cv2.TM_CCOEFF_NORMED 是针对缩放情况下最推荐的模板匹配方法，因为它对亮度和对比度的变化更具有鲁棒性。
            result = cv2.matchTemplate(screenshot, template ,match_method, mask=mask)
        else:
            result = cv2.matchTemplate(screenshot, template, match_method)
        # 获取最匹配的位置,TM_SQDIFF_NORMED是返回值越小，匹配度越高
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # print(f"{min_val=},{max_val=}")
        return 1-max_val, max_loc

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
        img_resized = cv2.resize(img_cropped,
                                 (int(img_cropped.shape[1] * scale_x), int(img_cropped.shape[0] * scale_y)),interpolation=cv2.INTER_CUBIC)

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

