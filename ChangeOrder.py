# -*- coding: utf-8 -*-
from Order import *
import copy
import time
import hashlib
import requests
from Common.Logger import logger

def get_params(data):
    """根据请求参数获取算法sign，返回整个公共params，后续在请求时公共params使用params传递，请求参数使用data传递"""
    info = {
        "sid": "drrp02",
        "appkey": "drrp02-ot",
        "timestamp": int(time.time()),
    }
    tmp_params = copy.deepcopy(info)
    for k, v in data.items():
        tmp_params[k] = v
    tmp_params = dict(sorted(tmp_params.items()))
    string = str()
    for k, v in tmp_params.items():
        k_len = '0' + str(len(k.encode('utf8')))
        k_ = k_len[-2:]
        v_len = '000' + str(len(str(v).encode('utf8')))
        v_ = v_len[-4:]
        string += f'{k_}-{k}:{v_}-{v};'
    result = string[:-1] + '83819b55d08037ffcace863a0d5fcd71'  # appsecret

    md5_obj = hashlib.md5()
    md5_obj.update(result.encode('utf8'))
    sign = md5_obj.hexdigest()
    info["sign"] = sign
    return info

def get_shop_code(product, size, color):
    """根据千牛的商品编号获取商家编码"""
    url = 'https://api.wangdian.cn/openapi2/goods_query.php'

    now = time.time()
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now - 0 * 24 * 60 * 60))
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now - 30 * 24 * 60 * 60))
    data = {
        'start_time': start_time,
        'end_time': end_time,
        'page_no': 0,
        'page_size': 100,
        "warehouse_no": 3,
        "goods_no": product,
    }
    params = get_params(data)
    response = requests.post(url, params=params, data=data).json()['goods_list']
    if len(response) == 0:
        return None
    for item in response[0]['spec_list']:
        if item['spec_code'] == size and re.findall(r'[\u4e00-\u9fa5]+', item['spec_name'])[0] == color:
            return item['spec_no']
    return None

def get_stock(spec_no):
    """根据货品编号获取库存"""
    url = 'https://api.wangdian.cn/openapi2/stock_query_detail.php'
    now = time.time()
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now - 30 * 24 * 60 * 60))
    end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
    data = {
        'start_time': start_time,
        'end_time': end_time,
        'page_no': 0,
        'page_size': 100,
        "warehouse_no": 3,
        "spec_no": spec_no,
    }
    params = get_params(data)
    response = requests.post(url, params=params, data=data).json()
    response = response.get('stocks')
    if response:
        stock = response[0]['stock_num']
        return int(float(stock))
    else:
        return 0

def main():
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    content = now + '千牛系统自动识别库存'
    logger.info(content.center(100, '='))
    logger.info('开始千牛系统登录....')
    order_login()
    logger.info('开始获取白色旗帜订单....')
    orders = get_order('imgextra/i2')
    logger.info(f'所有订单：{orders}')
    if not orders:
        logger.info('暂无订单可处理')
        return True
    for order in orders:
        order_info = get_order_detail(order, prodcut_many=True)
        logger.info(f'\n{order}订单：{[i["title"] for i in order_info]}')
        for order_ in order_info:
            products = order_['product']
            for product in products:
                size = order_['size']
                color = order_['color']
                shop_code = get_shop_code(product, size, color)
                stock = get_stock(shop_code) if shop_code else 0
                order_['stock'] = stock
                logger.info(f'{order_["title"]}  {product} 库存：{order_["stock"]}')
                if stock:
                    break
        stocks = [i['stock'] for i in order_info]
        stocks = list(set(stocks))
        if stocks == [0]:
            logger.info(f'{order}订单所有商品均无库存，修改为紫色旗帜')
            chang_status(order)
            logger.info(f'{order}订单成功修改为紫色旗帜')
        else:
            logger.info(f'{order}订单存在商品有库存，暂不处理')
    return True

if __name__ == '__main__':
    # shop_code = get_shop_code('479611', 'M', '枣红色')
    # # logger.info(shop_code)
    # stock = get_stock(shop_code) if shop_code else 0
    # logger.info(shop_code)
    # logger.info(stock)
    for i in range(10000):
        main()
        logger.info(f'等待3分钟再次执行\n')
        time.sleep(3*60)