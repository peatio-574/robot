import pyautogui
import pyperclip
import time
import ctypes


# ============== 基础配置 ==============
# 延迟时间（根据你的电脑速度调整，慢电脑适当加大）
DELAY_SHORT = 0.3
DELAY_MID = 0.8
DELAY_LONG = 1.2

# 解决Windows高分屏缩放问题（关键！避免坐标偏移）
ctypes.windll.user32.SetProcessDPIAware()

# 关闭pyautogui自动暂停，提高执行速度
pyautogui.PAUSE = 0.1


# ============== 自动化函数 ==============
def open_wangdiantong_audit():
    """打开旺店通订单审核页面"""
    print("步骤1：激活旺店通窗口，按下F2打开订单审核...")

    # 激活旺店通窗口（点击任务栏/窗口任意位置，你也可以手动前置窗口）
    # 如果你知道窗口标题，可以用win32gui精准激活，这里用通用方案
    pyautogui.hotkey('alt', 'tab')  # 切换到旺店通
    time.sleep(DELAY_SHORT)

    # 按下F2快捷键
    pyautogui.press('f2')
    time.sleep(DELAY_MID)


def double_click_first_order():
    """双击第一条订单"""
    print("步骤2：定位并双击第一条订单...")

    # 方案1：直接定位屏幕左上角区域（通用，适合订单列表在左上的布局）
    # moveTo移动鼠标到第一条订单位置，x/y坐标根据你的屏幕自行微调
    # 通用坐标：列表第一条一般在 左侧200，顶部200 位置，可自行修改
    pyautogui.moveTo(x=200, y=300, duration=0.2)
    time.sleep(DELAY_SHORT)

    # 双击
    pyautogui.doubleClick()
    time.sleep(DELAY_LONG)


def get_order_info():
    """获取订单详情文本"""
    print("步骤3：获取订单信息文本...")
    time.sleep(5)
    pyautogui.hotkey('alt', 'tab')  # 切换到旺店通
    pyautogui.hotkey('alt', 'tab')  # 切换到旺店通
    time.sleep(DELAY_SHORT)

    # 全选订单详情内容
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(DELAY_SHORT)

    # 复制内容
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(DELAY_SHORT)

    # 读取剪贴板内容
    order_text = pyperclip.paste()
    return order_text


def save_order_info(text, save_path="旺店通订单信息.txt"):
    """保存订单信息到本地文件"""
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"订单信息已保存到：{save_path}")


# ============== 主流程 ==============
if __name__ == "__main__":
    print("=" * 50)
    print("旺店通订单审核自动化脚本启动")
    print("=" * 50)
    print("⚠️  警告：脚本运行期间不要操作鼠标键盘！")
    time.sleep(2)

    try:
        # 1. 打开订单审核
        open_wangdiantong_audit()

        # 2. 双击第一条订单
        double_click_first_order()

        # 3. 获取订单文本
        order_info = get_order_info()

        # 4. 输出结果
        print("\n" + "=" * 50)
        print("获取到的订单信息：")
        print("=" * 50)
        print(order_info)

        # 5. 保存到文件
        save_order_info(order_info)

        print("\n✅ 订单审核信息获取完成！")

    except Exception as e:
        print(f"\n❌ 执行失败：{str(e)}")