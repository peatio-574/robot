# -*- coding: utf-8 -*-
from Order import buy_login
from Order import uniqo_walk
import time
from Order import get_config_value
from Order import logger


if __name__ == '__main__':
    number = int(get_config_value('login', 'number'))
    interval = int(get_config_value('login', 'interval'))
    for i in range(number):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        content = now + ' 模拟优衣库闲逛'
        logger.info(content.center(100, '='))
        buy_login()
        uniqo_walk()
        uniqo_walk()
        uniqo_walk()
        uniqo_walk()
        logger.info(f'等待{interval}秒再次执行')
        time.sleep(interval)




