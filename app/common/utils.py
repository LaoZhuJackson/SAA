import numpy as np

def random_normal_distribution_int(a, b, n=3):
    """
    在区间 [a, b) 内产生符合正态分布的随机数，原理是取n个随机数的平均值来模拟正态分布
    :param a: 最小值
    :param b: 最大值
    :param n: 随机数的数量，值越大分布越集中
    :return:int
    """
    if a < b:
        output = np.mean(np.random.randint(a, b, size=n))
        return int(output.round())
    else:
        return b

def random_rectangle_point(area, n=3):
    """
    在区域内产生符合二维正态分布的随机点，通常在点击操作中使用
    :param area: ((upper_left_x, upper_left_y), (bottom_right_x, bottom_right_y)).
    :param n: 随机数的数量，值越大分布越集中
    :return: tuple(int): (x, y)
    """
    print(f"{area=}")
    # area=((1285, 873), (1417, 921))
    x = random_normal_distribution_int(area[0][0], area[1][0], n=n)
    y = random_normal_distribution_int(area[0][1], area[1][1], n=n)
    return x, y