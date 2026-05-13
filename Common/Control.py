# -*- coding: utf-8 -*-
import sys
import time
from pathlib import Path

# 把项目根目录 D:\robot 加入Python路径
sys.path.append(str(Path(__file__).parent.parent))

from Common.lgb import ESP32Controller
from Common.Logger import logger

def check_robot_status():
    msg = '未识别到机械臂设备'
    for i in range(1, 11):
        logger.info(f'开始扫描机械设备_第{i}次')
        controller = ESP32Controller()
        devices = ESP32Controller.scan_lan()
        if len(devices) == 1:
            logger.info(f"发现机械设备: {devices}")
            return controller, devices[0]
        logger.error(msg)
    return 0, msg


def controls(name='戴宝林', tel='2840588414@qq.com', amount='5',first=False, controller=None, device_ip=None):
    try:
        rotation = 3
        server = '127.0.0.1'
        back_local = (0.07145, 0.07804)  # 返回坐标

        if first:  # 首次使用
            logger.info('点击支付-->进入支付宝')
            pay_local = controller.ocr_get_text_location(server, device_ip, rotation, '支付宝', home=False)
            controller.move_click(device_ip=device_ip, x_ratio=pay_local[0], y_ratio=pay_local[1]-0.05, home=True)

            logger.info('点击转账')
            transfer_local = controller.ocr_get_text_location(server, device_ip, rotation, '转账', home=False)
            controller.move_click(device_ip=device_ip, x_ratio=transfer_local[0], y_ratio=transfer_local[1]-0.05, home=True)


        controller.capture_photo(device_ip, rotation)
        ocr_result = controller.get_ocr(server=server, device_ip=device_ip, rotation=rotation)
        valid_flag = False
        for ocr in ocr_result:
            if '转到支付宝' in ocr['text']:
                valid_flag = True
                break
        if not valid_flag:
            logger.info('当前未处于初始页')
            logger.info('点击主页')
            controller.move_click(device_ip=device_ip, x_ratio=0.48318, y_ratio=0.96903, delay_ms=200, home=False)
            logger.info('点击多任务')
            controller.move_click(device_ip=device_ip, x_ratio=0.23530, y_ratio=0.96903, delay_ms=200, home=False)
            logger.info('点击清除')
            controller.move_click(device_ip=device_ip, x_ratio=0.48318, y_ratio=0.87199, delay_ms=200, home=False)
            logger.info('点击支付宝')
            controller.move_click(device_ip=device_ip, x_ratio=0.37450, y_ratio=0.88224, delay_ms=200, home=False)
            logger.info('点击转账')
            controller.move_click(device_ip=device_ip, x_ratio=0.87795, y_ratio=0.23402, delay_ms=200, home=False)
            # return 0, '当前未处于初始页面'

        logger.info('点击转到支付宝')
        controller.move_click(device_ip=device_ip, x_ratio=0.18898, y_ratio=0.24170, click_count=2, home=False)

        logger.info('输入账号')
        local_dict = {
            'q': (0.05835, 0.70944),
            'w': (0.15420, 0.70871),
            'e': (0.25446, 0.70707),
            'r': (0.35158, 0.70767),
            't': (0.44798, 0.70458),
            'y': (0.54667, 0.70561),
            'u': (0.64486, 0.70670),
            'i': (0.73846, 0.70676),
            'o': (0.83791, 0.70676),
            'p': (0.94120, 0.70848),
            'a': (0.10345, 0.77386),
            's': (0.20291, 0.77214),
            'd': (0.29854, 0.77042),
            'f': (0.40183, 0.77214),
            'g': (0.49746, 0.77386),
            'h': (0.59692, 0.77386),
            'j': (0.69255, 0.77558),
            'k': (0.79201, 0.77042),
            'l': (0.88968, 0.77002),
            'z': (0.20291, 0.83924),
            'x': (0.30237, 0.83924),
            'c' : (0.40183, 0.84096),
            'v': (0.49746, 0.83924),
            'b': (0.59692, 0.83752),
            'n': (0.69255, 0.83924),
            'm': (0.78818, 0.83924),
            '.': (0.67598, 0.90296),
        }

        tmp = {'1': 'q', '2': 'w', '3': 'e', '4': 'r', '5': 't', '6': 'y', '7': 'u', '8': 'i', '9': 'o', '0': 'p', '@': 'd'}
        for word in tel:
            delay_ms = 0
            if word in list(tmp.keys()):
                word = tmp[word]
                delay_ms = 800
            local = local_dict[word]
            logger.info(f'输入账号字符：{word}')
            controller.move_click(device_ip=device_ip, x_ratio=local[0], y_ratio=local[1], delay_ms=delay_ms, home=False)

        controller.capture_photo(device_ip, rotation)
        ocr_result = controller.get_ocr(server=server, device_ip=device_ip, rotation=rotation)
        tel_flag = False
        for ocr in ocr_result:
            if tel in ocr['text']:
                logger.info(f'{tel}账号输入正确')
                tel_flag = True
                break
        if not tel_flag:
            logger.info(f'{tel}账号输入错误')
            logger.info('点击返回')
            controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
            logger.info('点击转到支付宝')
            controller.move_click(device_ip=device_ip, x_ratio=0.18898, y_ratio=0.24170, click_count=2, home=False)
            logger.info('再次输入账号')
            for word in tel:
                delay_ms = 0
                if word in list(tmp.keys()):
                    word = tmp[word]
                    delay_ms = 800
                local = local_dict[word]
                logger.info(f'输入账号字符：{word}')
                controller.move_click(device_ip=device_ip, x_ratio=local[0], y_ratio=local[1], delay_ms=delay_ms, home=False)

        logger.info('识别姓名')
        controller.capture_photo(device_ip, rotation)
        ocr_result = controller.get_ocr(server=server, device_ip=device_ip, rotation=rotation)
        name_flag = False
        for text in ocr_result:
            if name[-1] in text['text']:
                name_flag = True
                account_local = text['center']
                controller.move_click(device_ip=device_ip, x_ratio=account_local[0], y_ratio=account_local[1], delay_ms=300, home=False)
                break

        if not name_flag:  # 姓名不匹配
            msg = f'{tel}_{name}_账号未识别到姓名'
            logger.error(msg)
            logger.info('点击返回')
            controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
            return 0, msg
        logger.info('姓名匹配成功')
        time.sleep(1)

        amount_locals = {
            '1': (0.12054, 0.68824),
            '2': (0.37301, 0.69237),
            '3': (0.62089, 0.68824),
            '4': (0.12972, 0.76050),
            '5': (0.36842, 0.76463),
            '6': (0.62089, 0.76050),
            '7': (0.12513, 0.83276),
            '8': (0.36842, 0.83483),
            '9': (0.61630, 0.83483),
            '0': (0.24907, 0.90503),
            '.': (0.62089, 0.91122)
        }
        for amount_ in amount:
            logger.info(f'输入转账金额数字{amount}')
            local = amount_locals[amount_]
            controller.move_click(device_ip=device_ip, x_ratio=local[0], y_ratio=local[1], delay_ms=1200, home=False)

        logger.info('点击转账')
        controller.move_click(device_ip=device_ip, x_ratio=0.87104, y_ratio=0.86015, home=False)

        # 识别转账时各种异常情况
        logger.info('识别点击转账后是否存在异常情况....')
        time.sleep(3)
        controller.capture_photo(device_ip, rotation)
        ocr_result = controller.get_ocr(server=server, device_ip=device_ip, rotation=rotation)[::-1][:10]

        is_right = False
        for text in ocr_result:
            if '取消' == text['text']:
                msg = f'{tel}_{name}_当日收款额度已达上限'
                logger.error(msg)
                logger.info('点击取消')
                controller.move_click(device_ip=device_ip, x_ratio=text['center'][0], y_ratio=text['center'][1], home=False)
                logger.info('点击返回')
                controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
                logger.info('点击返回')
                controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
                return 0, msg
            elif '确认' == text['text']:
                msg = f'{tel}_{name}_手机号已不再使用'
                logger.error(msg)
                logger.info('点击确认')
                controller.move_click(device_ip=device_ip, x_ratio=text['center'][0], y_ratio=text['center'][1],home=False)
                logger.info('点击返回')
                controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
                logger.info('点击返回')
                controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
                return 0, msg
            elif '我知道了' == text['text']:
                msg = f'{tel}_{name}_对方账号存在安全风险'
                logger.error(msg)
                logger.info('我知道了')
                controller.move_click(device_ip=device_ip, x_ratio=text['center'][0], y_ratio=text['center'][1],home=False)
                logger.info('点击返回')
                controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
                logger.info('点击返回')
                controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
                return 0, msg
            elif '继续转账' == text['text']:
                logger.info('点击继续转账')
                controller.move_click(device_ip=device_ip, x_ratio=text['center'][0], y_ratio=text['center'][1],home=True)
                is_right = True
                break
            elif '储蓄卡' in text['text']:
                is_right = True
                break
        if not is_right:
            msg = f'{tel}_{name}_流程异常，请联系开发人员'
            logger.error(msg)
            logger.info('点击返回')
            controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
            logger.info('点击返回')
            controller.move_click(device_ip=device_ip, x_ratio=back_local[0], y_ratio=back_local[1], home=False)
            return 0, msg

        password = '987670'
        password_local = {
            '1': (0.16185, 0.69237),
            '2': (0.49695, 0.69030),
            '3': (0.82746, 0.69237),
            '4': (0.16644, 0.76050),
            '5': (0.49695, 0.76257),
            '6': (0.82746, 0.76257),
            '7': (0.16185, 0.83483),
            '8': (0.49695, 0.83483),
            '9': (0.82746, 0.83483),
            '0': (0.49695, 0.90709)
        }
        time.sleep(2)
        logger.info('输入密码')
        for word in password:
            controller.move_click(device_ip=device_ip, x_ratio=password_local[word][0], y_ratio=password_local[word][1], home=False)
        time.sleep(5)

        controller.capture_photo(device_ip, rotation)
        ocr_result = controller.get_ocr(server=server, device_ip=device_ip, rotation=rotation)
        success_flag = False
        for text in ocr_result:
            if f'￥{amount}' in text['text']:
                success_flag = True
                break
        success_msg = f'{tel}_{name}_已成功转账{amount}元' if success_flag else f'{tel}_{name}_转账金额错误'
        logger.info(success_msg)
        logger.info('点击完成')
        controller.move_click(device_ip=device_ip, x_ratio=0.49236, y_ratio=0.89677, home=True)
        return 1, success_msg
    except Exception as e:
        error_msg = f'{tel}_{name}_流程执行异常：{e[-300:]}'
        logger.error(error_msg)
        return 0, error_msg

if __name__ == '__main__':
    controls()








