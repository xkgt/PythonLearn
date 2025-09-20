import time

import numpy as np

def create_radial_decay_matrix(size, radius, sigma=None):
    """
    创建一个从中心向外逐渐减小值的矩阵。

    参数:
        size (int): 矩阵的大小（size x size）。
        radius (float): 圆的最大半径。
        sigma (float): 高斯衰减的标准差。如果为 None，则默认为 radius / 3。

    返回:
        numpy.ndarray: 包含逐渐减小值的二维矩阵。
    """
    if sigma is None:
        sigma = radius / 3  # 默认标准差为半径的三分之一

    # 创建一个 size x size 的空矩阵
    matrix = np.zeros((size, size))

    # 计算中心点坐标
    center = size // 2

    # 创建网格，获取每个点的坐标
    y, x = np.ogrid[:size, :size]

    # 计算每个点到中心的距离平方
    distance_squared = (x - center) ** 2 + (y - center) ** 2

    # 使用高斯函数计算衰减值
    matrix = np.exp(-distance_squared / (2 * sigma ** 2))

    return matrix


PosCircleType = list[float, float, np.ndarray]


def map_pos_circle_to_image(pos_circle, background_image):
    """
    将 PosCircleType 映射到背景图片上，并使用非线性叠加处理重叠区域。

    参数:
        pos_circle (tuple): 包含位置 (x, y) 和矩阵的元组，格式为 ((x, y), matrix)。
        background_image (numpy.ndarray): 背景图片（二维数组）。

    返回:
        numpy.ndarray: 更新后的背景图片。
    """
    # 解包位置和矩阵
    (pos_x, pos_y), matrix = pos_circle
    pos_x, pos_y = int(pos_x), int(pos_y)  # 确保位置是整数

    # 获取矩阵和背景图片的尺寸
    matrix_height, matrix_width = matrix.shape
    bg_height, bg_width = background_image.shape

    # 计算矩阵在背景图片中的范围
    start_x = max(0, pos_x)
    start_y = max(0, pos_y)
    end_x = min(bg_width, pos_x + matrix_width)
    end_y = min(bg_height, pos_y + matrix_height)

    # 计算矩阵的裁剪范围（防止越界）
    crop_start_x = max(0, -pos_x)
    crop_start_y = max(0, -pos_y)
    crop_end_x = crop_start_x + (end_x - start_x)
    crop_end_y = crop_start_y + (end_y - start_y)

    # 获取背景图片中对应区域的子矩阵
    bg_submatrix = background_image[start_y:end_y, start_x:end_x]

    # 获取矩阵中对应区域的子矩阵
    matrix_submatrix = matrix[crop_start_y:crop_end_y, crop_start_x:crop_end_x]

    # 使用非线性叠加公式更新背景图片的对应区域
    updated_submatrix = 1 - (1 - bg_submatrix) * (1 - matrix_submatrix)

    # 将更新后的子矩阵写回背景图片
    background_image[start_y:end_y, start_x:end_x] = updated_submatrix

    return background_image



def threshold_matrix(matrix, threshold):
    """
    筛选矩阵的值，将大于某个阈值的值设为 1，其余设为 0。

    参数:
        matrix (numpy.ndarray): 输入的二维矩阵。
        threshold (float): 阈值。

    返回:
        numpy.ndarray: 处理后的二值矩阵。
    """
    # 使用布尔索引筛选，并将布尔值转换为整数（1 或 0）
    return (matrix > threshold).astype(int)


from PIL import Image

def matrix_to_pil_image(matrix):
    """
    将二维矩阵转换为 PIL 图片，值 1 映射为白色，值 0 映射为黑色。

    参数:
        matrix (numpy.ndarray): 输入的二维矩阵，值为 0 或 1。

    返回:
        PIL.Image.Image: 转换后的 PIL 图片。
    """
    # 将矩阵的值从 {0, 1} 转换为 {0, 255}，并设置数据类型为 uint8
    image_data = (matrix * 255).astype(np.uint8)

    # 使用 PIL 的 fromarray 方法创建图片
    pil_image = Image.fromarray(image_data, mode='L')  # 'L' 表示灰度模式

    return pil_image



import tkinter as tk
from PIL import ImageTk

def main():
    """
    创建一个长方形 Tkinter 窗口，并在其中放置一个占满屏幕的 Canvas 组件。
    """
    # 创建主窗口
    root = tk.Tk()
    root.title("Full Screen Canvas Example")

    # 获取屏幕的宽度和高度（以像素为单位）
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 设置窗口大小为屏幕大小
    root.geometry(f"{screen_width}x{screen_height}")

    # 创建一个 Canvas 组件，占满整个窗口
    canvas = tk.Canvas(root, bg="lightgray")  # 设置背景颜色为浅灰色
    canvas.pack(fill=tk.BOTH, expand=True)  # 让 Canvas 占满整个窗口
    
    # 初始化图像引用，确保在循环中可以更新
    tk_image = None

    # 预先创建球的矩阵并缓存
    circle_matrix = create_radial_decay_matrix(100, 50)
    # 预计算球的位置
    pos_circle = ((screen_width // 2 - 50, screen_height // 2 - 50), circle_matrix)

    # 预先创建第二个球的矩阵并缓存（与第一个球相同）
    circle_matrix2 = create_radial_decay_matrix(100, 50)
    # 计算第二个球的位置（在第一个球上方）
    pos_circle2 = ((screen_width // 2 - 50, screen_height // 2 - 150), circle_matrix2)


    while True:
        # 获取当前第二个球的y坐标
        current_y = pos_circle2[0][1]
        # 每次移动5个像素
        new_y = current_y + 3
        # 更新第二个球的位置
        pos_circle2 = ((pos_circle2[0][0], new_y), pos_circle2[1])

        # 创建一个与屏幕大小相同的矩阵
        screen_matrix = np.zeros((screen_height, screen_width))

        # 将预先计算好的径向衰减矩阵映射到屏幕矩阵上
        screen_matrix = map_pos_circle_to_image(pos_circle, screen_matrix)
        screen_matrix = map_pos_circle_to_image(pos_circle2, screen_matrix)

        # 应用阈值将矩阵转换为二值矩阵
        thresholded_matrix = threshold_matrix(screen_matrix, 0.1)
        pil_image = matrix_to_pil_image(thresholded_matrix)

        # 更新画布上的图像
        new_tk_image = ImageTk.PhotoImage(pil_image)
        
        if tk_image is None:
            # 首次创建图像
            canvas.create_image(0, 0, image=new_tk_image, anchor=tk.NW)
        else:
            # 更新现有图像
            canvas.itemconfig(canvas.find_all()[0], image=new_tk_image)
        
        # 保持引用以防止垃圾回收
        tk_image = new_tk_image
        
        root.update()
        time.sleep(1/60)

if __name__ == "__main__":
    main()
