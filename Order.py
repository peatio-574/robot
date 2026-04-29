import json
import time
import random
from Common.Vars import project_path
from Common.Logger import logger
import requests
import re
from Common.Deal import get_config_value, write_config_value
from Common.PlayWright import Playwright_
from Common.lgb import ESP32Controller
import os

location_info = dict()  # 所有坐标信息

def get_order(flag='imgextra/i3'):
    """
    获取指定旗帜类型的所有订单号，默认imgextra/i3为紫色
    返回形式：list
    """
    # 加入cookie
    cookie = get_config_value('order', 'order_cookie_')
    if cookie:
        Playwright_.add_cookie(eval(cookie))
    # 访问页面
    Playwright_.goto('https://qn.taobao.com/home.htm/trade-platform/tp/sold')
    result = Playwright_.wait_for_selector('//input[@aria-label="搜索"]', timeout=15*1000)
    if not result:  # 搜索按钮未加载出来
        return False
    time.sleep(5)
    # 点击待发货
    Playwright_.click('//div[@class="next-tabs-tab-inner" and contains(text(), "待发货")]')
    orders = dict()
    time.sleep(5)
    pages = Playwright_.page.locator('//div[@class="next-pagination-list"]/button').all()  # 页数
    for _page in range(1, len(pages)+1):
        # 单页订单量
        elements = Playwright_.page.locator('//table[contains(@class, "next-table-row")]//div[contains(text()[1], "订单号")]').all()
        for element in range(len(elements)):
            text = Playwright_.page.locator(f'//table[contains(@class, "next-table-row")][{element+1}]//div[contains(text()[1], "订单号")]').text_content()
            text = re.findall('\d+', text)[0]  # 订单号
            src_value = Playwright_.page.locator(f'//table[contains(@class, "next-table-row")][{element+1}]//div[contains(text()[1], "订单号")]/../div[2]//img').get_attribute("src")
            if flag in src_value:  # 对应旗帜类型
                date = Playwright_.page.locator(f'//table[contains(@class, "next-table-row")][{element + 1}]//div[contains(text()[1], "订单号")]/span[1]').text_content()
                date = re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', date)[0]
                orders[text] = date  # 日期，后续进行排序
        if len(pages) == 1 or _page == len(pages):
            break
        Playwright_.page.keyboard.press("End")  # 滚动
        Playwright_.click(f'//div[@class="next-pagination-list"]/button[{_page+1}]')  # 页码跳转
        time.sleep(5)
    orders = sorted(orders.items(), key=lambda x: x[1])  # 根据日期排序
    return [i[0] for i in orders]

def get_order_detail(order_id, prodcut_many=False, is_write=False):
    """
    获取指定订单的订单详情
    prodcut_many是否返回多个product_id
    is_write是否进行订单信息写入
    返回：[{'title': '', 'product': '', 'color_id': '', 'color': '', 'size': '', 'quantity': '', 'addr': ''}, {}]
    """
    cookie = get_config_value('order', 'order_cookie_')
    if cookie:
        Playwright_.add_cookie(eval(cookie))
    url = f'https://qn.taobao.com/home.htm/trade-platform/tp/detail?spm=a21dvs.23580594.0.0.60fb645eXEF8jc&bizOrderId={order_id}'
    Playwright_.goto(url)
    # 敏感信息是否自动展示
    look = Playwright_.wait_for_selector('//div[@role="switch" and @aria-checked="false"]/div[2]')
    if look:
        Playwright_.click('//div[@role="switch" and @aria-checked="false"]/div[2]')
    time.sleep(2)
    addr = '//span[@class="receive-address_value__Fmomy"]'
    addr = Playwright_.page.locator(addr).text_content()
    logger.info(f'地址：{addr}')

    count = '//tr[@class="order-item"]'
    count = len(Playwright_.page.locator(count).all())

    quantitys = '//div[contains(@class,"order-info_total-price")]/div[2]'
    titles = '//div[contains(@class, "first-right-title")]'
    infos = '//span[contains(text(),"颜色")]/../span[2]/span'
    size = '//span[contains(text(),"尺")]/../span[2]/span'

    order_list = list()
    for i in range(1, count + 1):
        order_info = dict()
        # 标题
        title_text_ = Playwright_.page.locator(f'({titles})[{i}]').text_content()
        order_info['title'] = f'【{title_text_}】'

        # 商品状态（未发货、已退款、待收货）
        status1 = f'(//tr[@class="order-item"])[{i}]/td[3]/div/span'
        status2 = f'(//tr[@class="order-item"])[{i}]/td[3]/div/a'
        status_count = Playwright_.page.locator(status1).count()
        status = status1 if status_count == 1 else status2
        status = Playwright_.page.locator(status).text_content()
        if '收货' in status:
            logger.info(f"{order_id} {order_info['title']}   已发货无需处理")
            continue
        elif '退款' in status:
            logger.info(f"{order_id} {order_info['title']}   已退款无需处理")
            continue

        # 商品编号
        info_text = Playwright_.page.locator(f'({infos})[{i}]').text_content()
        info_text = re.sub(r' ', '', info_text)
        product = re.findall('\d{6}', info_text)
        if not product:
            logger.info(f"{order_id} {order_info['title']}   商品编号异常")
            continue
        else:
            product = product[0] if not prodcut_many else product
        order_info['product'] = product

        # 商品颜色编号
        ids = re.findall(r'\[(\d+)', info_text)
        order_info['color_id'] = ids[0] if len(ids) > 0 else 'null'  # 商品颜色编号

        # 商品颜色
        order_info['color'] = re.findall(r'\D+[色红橙黄绿青蓝紫白灰黑]', info_text)[0]

        # 商品尺寸
        size_text = Playwright_.page.locator(f'({size})[{i}]').text_content()
        size_text = size_text.split(r'[')[0]
        size_tmp = re.findall('[SML]', size_text)
        size_text = size_text.split('/')[-1] if len(size_tmp) > 0 else size_text
        order_info['size'] = size_text

        # 商品数量
        quantity_text = Playwright_.page.locator(f'({quantitys})[{i}]').text_content()
        order_info['quantity'] = re.findall('\d+', quantity_text)[0]

        order_info['addr'] = addr
        order_info['title'] += '-->  ' + str(order_info["product"]) + f'[{order_info["color_id"]}]' + f' {order_info["color"]}' + order_info['size']
        order_list.append(order_info)
    if is_write:
        file = os.path.join(project_path, 'resources', '订单信息.txt')
        with open(file, mode='a', encoding='utf-8') as f:
            f.write(str({order_id: order_list}) + '\n')
    return order_list

def get_product_id(product, color_id, color):
    """
    根据千牛的product/color/color_id获取优衣库对应product_id
    返回：[]
    """
    url = 'https://d.uniqlo.cn/p/hmall-sc-service/search/searchWithDescriptionAndConditions/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'content-type': 'application/json',

    }
    params = {
        "url": f"/search.html?description={product}&searchType=4",
        "pageInfo": {
            "page": 1,
            "pageSize": 20,
            "withSideBar": "Y"
        },
        "belongTo": "pc",
        "rank": "overall",
        "priceRange": {
            "low": 0,
            "high": 0
        },
        "color": [],
        "size": [],
        "season": [],
        "material": [],
        "sex": [],
        "categoryFilter": {},
        "identity": [],
        "insiteDescription": "",
        "exist": [],
        "searchFlag": True,
        "description": str(product)
    }
    info = requests.post(url, headers=headers, data=json.dumps(params)).json()
    result = list()
    for i in info['resp'][1]:  # 多个结果
        if i.get('code') and i.get('code') != str(product):
            continue
        styles = i['styleText']
        if isinstance(styles, str):
            if '/' in styles:
                if f'{product}{color_id}{color}' in re.sub('[ /]', '', styles):
                    result.append(i['productCode'])
            else:
                if f'{color_id}{color}' in re.sub(' ', '', styles):
                    result.append(i['productCode'])
        elif isinstance(styles, list):
            for style in styles:
                if '/' in style:
                    if f'{product}{color_id}{color}' in re.sub('[ /]', '', style):
                        result.append(i['productCode'])
                else:
                    if f'{color_id}{color}' in re.sub(' ', '', style):
                        result.append(i['productCode'])
    return result

def get_product_size_code(product, product_id, color_id, size):
    """根据product_id、color_id、size获取product_size_code
    product_id为优衣库获取
    product、color_id、size为千牛获取
    """
    cookie = get_config_value('buy', 'buy_cookie_')
    if cookie:
        Playwright_.add_cookie(eval(cookie))

    url = f'https://www.uniqlo.cn/data/products/spu/zh_CN/{product_id}.json'
    Playwright_.goto(url)
    text = Playwright_.page.locator('//pre').text_content()
    if size == '2XL':
        size = [size, 'XXL']
    elif size == '3XL':
        size = [size, 'XXXL']
    elif size == '4XL':
        size = [size, 'XXXXL']
    elif size == '1XL':
        size = 'XL'
    else:
        size = str(size)
    for i in eval(text)['rows']:
        if isinstance(size, str):
            if f'{product}/{color_id}' in i['styleText'] and re.sub(' ', '', i['size']) == size:
                product_size_code = i['productId']
                return product_size_code
        else:
            if f'{product}/{color_id}' in i['styleText'] and re.sub(' ', '', i['size']) in size:
                product_size_code = i['productId']
                return product_size_code
    for i in eval(text)['rows']:
        color = i['styleText'] if isinstance(i['styleText'], str) else i['styleText'][0]
        color = color.split('/')[-1]
        color = re.findall(r'\d+', color)[0]
        if i.get('enabledFlag') and i.get('enabledFlag') == 'N':
            continue
        if isinstance(size, str):
            if color == str(color_id) and re.sub(' ', '', i['size']) == size:
                product_size_code = i['productId']
                return product_size_code
        else:
            if color == str(color_id) and re.sub(' ', '', i['size']) in size:
                product_size_code = i['productId']
                return product_size_code
    return False  # 没有对应尺寸

def uniqo_walk():
    """
    优衣库闲逛，为了减少账号风控，在网页上进行闲逛浏览
    返回：闲逛时长int
    """
    t1 = time.time()
    cookie = get_config_value('buy', 'buy_cookie_')
    if cookie:
        Playwright_.add_cookie(eval(cookie))
    url = 'https://www.uniqlo.cn/c/2wouter.html'
    Playwright_.goto(url)
    choose = ['休闲外套', '大衣', '空气感快干外套', '西装外套', '空气棉服', '羽绒服']
    for i in range(4):
        time.sleep(random.randint(5, 10))
        clothes_count = Playwright_.page.locator('//div[@class="h-product"]/a').all()
        Playwright_.click(f'(//div[@class="h-product"]/a)[{random.randint(1, len(clothes_count)+1)}]')
        Playwright_.page.mouse.wheel(0, 1200)  # 滚动
        time.sleep(random.randint(10, 30))
        url = 'https://www.uniqlo.cn/c/2wouter.html'
        Playwright_.goto(url)
        time.sleep(random.randint(5, 10))
        Playwright_.click(f'//a[@class="h-a-label a-enable" and text()="{random.choice(choose)}"]')
    t2 = time.time()
    return int(t2-t1)

def get_product_count(product_id, product_size_code):
    """
    根据product_id，product_size_code获取商品库存
    返回：int
    """
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'content-type': 'application/json',
    }
    url3 = 'https://d.uniqlo.cn/p/stock/stock/query/zh_CN'
    params = {
        "distribution": "EXPRESS",
        "productCode": product_id,
        "type": "DETAIL"
    }
    info = requests.post(url3, headers=headers, data=json.dumps(params)).json()
    product_count = info['resp'][0]['skuStocks'].get(product_size_code)
    return int(product_count)

def get_addr_list():
    """获取地址列表"""
    url = 'https://i.uniqlo.cn/p/hmall-ur-service/customer/address/list/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token'),
        'cookie': get_config_value('buy', 'buy_cookie')
    }
    response = requests.get(url, headers=headers).json()
    tmp = response.get('resp')
    addr_list = [i['addressId'] for i in tmp] if tmp else []
    return addr_list

def delete_addr(addr_id):
    """删除单个地址"""
    url = f'https://i.uniqlo.cn/p/hmall-ur-service/customer/address/delete/{addr_id}/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'content-type': 'application/json',
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token'),
        'cookie': get_config_value('buy', 'buy_cookie')
    }
    requests.post(url, headers=headers).json()

def deal_addr_str(add_str):
    """处理千牛获取到的地址，用于优衣库地址新增
    add_str： '杨智斌，14735147458-8192，山西省 太原市 杏花岭区 职工新街街道 东方雅园2号楼1单元801 ，030009'
    返回：{}
    """
    add_str = add_str.split('，')
    # 地址
    address = ''.join([i for i in add_str[2].split(' ')])
    address = ''.join([char if char.isalnum() or '\u4e00' <= char <= '\u9fa5' else '' for char in address])
    address = address if '86-' in add_str[1] else address + ' 电话转' + add_str[1].split('-')[1]
    # 电话
    mobilenumber = re.findall('1[3-9]\d{9}', add_str[1])[0]
    # 姓名
    consignee = add_str[0]
    # 省份
    cookie = get_config_value('buy', 'buy_cookie_')
    if cookie:
        Playwright_.add_cookie(eval(cookie))

    Playwright_.goto('https://www.uniqlo.cn/data/zh_CN/provinces.json')
    text = Playwright_.page.locator('//pre').text_content()
    provinces = eval(text)
    provinceName = add_str[2].split(' ')[0]
    provincecode = provinceName
    for k, v in provinces.items():
        if provinceName in v:
            provincecode = k
            break
    # 城市
    Playwright_.goto(f'https://www.uniqlo.cn/data/zh_CN/city/{provincecode}.json')
    text = Playwright_.page.locator('//pre').text_content()
    citys = eval(text)
    cityName = add_str[2].split(' ')[1]
    citycode = cityName
    for k, v in citys.items():
        if v == cityName:
            citycode = k
            break
    # 区县
    Playwright_.goto(f'https://www.uniqlo.cn/data/zh_CN/district/{citycode}.json')
    text = Playwright_.page.locator('//pre').text_content()
    districts = eval(text)
    districtName = add_str[2].split(' ')[2]
    district = list(districts.keys())[0]
    for k, v in districts.items():
        if v == districtName:
            district = k
            break
        elif '其他' in v:
            district = k

    params = {
        "address": address,
        "consignee": consignee,
        "nationalCode": "+86",
        "mobilenumber": mobilenumber,
        "zipcode": "",
        "state": provincecode,
        "city": citycode,
        "district": district,
        "fixednumber": "",
        "provinceName": provinceName,
        "cityName": cityName,
        "districtName": districtName,
        "areaCode": ""
    }
    return params

def add_addr(add_str):
    """新增地址，并返回对应addr_id
    addr_str：从千牛获取
    """
    url = 'https://i.uniqlo.cn/p/hmall-ur-service/customer/address/insert/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'content-type': 'application/json',
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token'),
        'cookie': get_config_value('buy', 'buy_cookie')
    }
    params = deal_addr_str(add_str)
    response = requests.post(url, headers=headers, data=json.dumps(params)).json()
    addr_id = response.get('resp')[0]['addressId']
    return addr_id

def get_purchase_list():
    """获取购物车列表"""
    url = 'https://i.uniqlo.cn/p/cart/cart/query/pc/zh_CN?salechannel=PC'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token'),
        'cookie': get_config_value('buy', 'buy_cookie')
    }
    response = requests.get(url, headers=headers).json()
    tmp = response.get('resp')
    addr_list = [i['cartId'] for i in tmp if '未上架' not in i['msg']] if tmp else []
    return addr_list

def detele_purchase_list(purchase_list):
    """清空购物车列表"""
    url = 'https://i.uniqlo.cn/p/cart/cart/multDelete/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'content-type': 'application/json',
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token'),
        'cookie': get_config_value('buy', 'buy_cookie')
    }
    params = {"select": purchase_list}
    requests.post(url, headers=headers, data=json.dumps(params)).json()

def add_to_purchase(product_id, product_size_code, quantity):
    """加入购物车"""
    url = 'https://i.uniqlo.cn/p/cart/cart/insert/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'content-type': 'application/json',
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token')
    }
    params = [
        {
            "productCode": product_id,
            "productId": product_size_code,
            "quantity": int(quantity),
            "distribution": "EXPRESS",
            "distributionId": "",
            "alterMode": "",
            "finalInseam": None,
            "caseFlag": "N",
            "checkFlag": "Y"
        }
    ]
    response = requests.post(url, headers=headers, data=json.dumps(params)).json()
    return response['success']

def get_phone():
    """获取优衣库手机号"""
    url = 'https://i.uniqlo.cn/h/auth/user/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token'),
        'cookie': get_config_value('buy', 'buy_cookie')
    }
    response = requests.get(url, headers=headers).json()

    result = response['mobileNumber']
    write_config_value('login', {'phone': result})
    return result

def buy_login():
    """优衣库登录"""
    # 验证优衣库cookie有效性
    cookie = get_config_value('buy', 'buy_cookie_')
    if cookie:
        Playwright_.add_cookie(eval(cookie))

    url = 'https://www.uniqlo.cn/account/person_ship_code.html'
    location = '//div[contains(text(),"会员码")]'
    Playwright_.goto(url)
    time.sleep(5)
    element = Playwright_.wait_for_selector(location, timeout=3 * 60 * 1000)
    if not element:
        return False

    cookie_list = Playwright_.context.cookies()
    key = 'access_token'
    buy_cookie = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookie_list])
    for cookie in cookie_list:
        if cookie.get("name") == key:
            reuslt = {'Uniqlo_token': cookie["value"], 'buy_cookie_': str(cookie_list), 'buy_cookie': buy_cookie}
            write_config_value('buy', reuslt)  # token写入ini配置项
            get_phone()
    return True

def order_login():
    """登录千牛"""
    cookie = get_config_value('order', 'order_cookie_')
    if cookie:
        Playwright_.add_cookie(eval(cookie))

    url = 'https://myseller.taobao.com/home.htm/QnworkbenchHome/'
    location = '//span[contains(text(),"首页")]'
    Playwright_.goto(url)
    element = Playwright_.wait_for_selector(location, timeout=3 * 60 * 1000)
    if not element:
        return False
    time.sleep(5)
    # 写入页面cookie
    cookie_list = Playwright_.context.cookies()
    reuslt = {'order_cookie_': str(cookie_list)}
    write_config_value('order', reuslt)  # cookie写入ini配置项
    # 写入接口cookie
    value = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookie_list])
    reuslt = {'order_cookie': value}
    write_config_value('order', reuslt)
    return True

def get_count(order_id, order_info):
    """查询优衣库库存"""
    if order_info["color_id"] == 'null':
        logger.info(f'订单:{order_id}，{order_info["title"]}无颜色编号')
        return order_info
    product_id = get_product_id(order_info["product"], order_info["color_id"], order_info["color"])
    if not product_id:
        order_info['title'] += '优衣库商品已下架'
        return order_info
    elif len(product_id) > 1:
        order_info['title'] += '优衣库存在多个商品'
        return order_info
    product_id = product_id[0]
    product_size_code = get_product_size_code(order_info["product"], product_id, order_info["color_id"], order_info["size"])
    if not product_size_code:
        order_info['title'] += '优衣库无对应尺寸'
        return order_info
    count = get_product_count(product_id, product_size_code)
    if count == 0:
        order_info['title'] += '优衣库商品已售罄'
        order_info['flag'] = 'error'
        return order_info
    elif count < int(order_info['quantity']):
        order_info['title'] += f'优衣库商品库库存{count}存少于订单数量{order_info["quantity"]}'
        order_info['flag'] = 'error'
        return order_info
    order_info['product_id'] = product_id
    order_info['product_size_code'] = product_size_code
    order_info['product_count'] = count
    order_info['title'] += f'库存:{count}'
    return order_info

def read():
    file = os.path.join(project_path, 'resources', '密码.txt')
    with open(file, mode='r', encoding='utf-8') as f:
        text = f.readlines()
        password = text[0]
        number = text[1].split('：')[1]
        intervla = eval(text[2].split('：')[1])
        result = {'password': password, 'number': number, 'interval': str(intervla)}
        write_config_value('login', result)

def check_robot_status():
    logger.info('开始扫描机械设备')
    controller = ESP32Controller()
    devices = ESP32Controller.scan_lan()
    if len(devices) == 0:
        return False
    logger.info(f"发现机械设备: {devices}")
    # status = controller.get_status(devices[0])
    # logger.info(f"设备{devices[0]}全部属性:\n{json.dumps(status, ensure_ascii=False)}")
    return controller, devices[0]

def control(controller, device_ip, server='127.0.0.1', rotation=3, finish=False):
    """控制机械臂购买
    controller机械臂实例
    device_ip机械臂ip
    server服务器地址（本地）
    rotation手机屏幕方向 3竖屏 2横屏
    status：首次为False，后续均为True
    """
    # logger.info('打开微信')
    # controller.ocr_text_and_click(server, device_ip, rotation, '微信', home=False)
    global location_info
    if not location_info.get('扫码'):
        logger.info('点击对话框：文件传输')
        controller.ocr_text_and_click(server, device_ip, rotation, '文件助手', home=False)
        logger.info('点击小程序二维码')
        controller.ocr_text_and_click(server, device_ip, rotation, 'UNI', home=False)
        logger.info('长按图片')
        controller.ocr_text_and_click(server, device_ip, rotation, 'UNI', keep=2000, home=True)
        logger.info('进入小程序，等待15秒')
        location3 = controller.ocr_get_text_location(server, device_ip, rotation, '优衣库', home=True)
        controller.move_click(device_ip=device_ip, x_ratio=location3[0], y_ratio=location3[1]+0.02, home=True)
        time.sleep(15)
        location_info['扫码'] = True

    logger.info('点击购物车坐标')
    if not location_info.get('优衣库'):
        location1 = controller.ocr_get_text_location(server, device_ip, rotation, '优衣库', home=True)
        location_info['优衣库'] = location1
    controller.move_click(device_ip=device_ip, x_ratio=location_info['优衣库'][0] + 0.4, y_ratio=location_info['优衣库'][1]-0.02, home=False)

    logger.info('判断是否已登录')
    if not location_info.get('登录'):
        locatio2 = controller.ocr_get_text_location(server, device_ip, rotation, '确定', home=True)
        if len(locatio2) == 1:
            logger.info('未登录，开始登录流程，点击确定')
            controller.move_click(device_ip=device_ip, x_ratio=locatio2[0], y_ratio=locatio2[1], home=True)
            logger.info('勾选同意')
            location3 = controller.ocr_get_text_location(server, device_ip, rotation, '同意', home=False)
            controller.move_click(device_ip=device_ip, x_ratio=0.05, y_ratio=location3[1], home=False)
            logger.info('点击快速登录')
            controller.ocr_text_and_click(server, device_ip, rotation, '快速', home=True)
            logger.info('点击第一个手机号')
            location4 = controller.ocr_get_text_location(server, device_ip, rotation, '你的手机号', home=False)
            controller.move_click(device_ip=device_ip, x_ratio=location4[0], y_ratio=location4[1] + 0.1, home=True)
    time.sleep(15)
    location_info['登录'] = True

    logger.info('点击结算')
    controller.move_click(device_ip=device_ip, x_ratio=0.95, y_ratio=0.95, home=True)

    lose_stock = controller.ocr_get_text_location(server, device_ip, rotation, '库存不足', home=True)
    if lose_stock:
        logger.info('库存不足，不允许下单')
        logger.info('点击小程序左上方返回，返回首页')
        controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=False)
        return False

    not_support = controller.ocr_get_text_location(server, device_ip, rotation, '不支持', home=True)
    if not_support:
        controller.drag(device_ip=device_ip, start_x=0.4, start_y=0.8, end_x=0.4, end_y=0.25)
        controller.drag(device_ip=device_ip, start_x=0.4, start_y=0.8, end_x=0.4, end_y=0.25)
        logger.info('勾选不支持退货选项')
        choose = controller.ocr_get_text_location(server, device_ip, rotation, '以下商品不支持', home=True)
        controller.move_click(device_ip=device_ip, x_ratio=0.01, y_ratio=choose[1], home=False)

    logger.info('点击微信支付')
    controller.move_click(device_ip=device_ip, x_ratio=0.95, y_ratio=0.95, home=False)
    time.sleep(5)

    logger.info('输入支付密码')
    password = str(get_config_value('login', 'password'))
    if not location_info.get('密码'):
        controller.capture_photo(device_ip, rotation)
        ocr_result = controller.get_ocr(server=server, device_ip=device_ip, rotation=rotation)[::-1][:10]
        if not ocr_result:
            logger.info('摄像头密码识别错误')
            return False

        logger.info([i['text'] for i in ocr_result])
        location_info['1'] = (0.1788, 0.7307+0.03)
        location_info['0'] = (0.5008, 0.9168+0.03)
        location_info['6'] = (0.9008, 0.7907+0.03)
        location_info['9'] = (0.9008, 0.8507+0.03)
        for word in password:
            if word in '0169':
                continue
            for i in ocr_result:
                find_result = re.findall(word, str(i['text']))
                if len(find_result) > 0:
                    location_info[word] = i['center'] if word != '8' else (i['center'][0], i['center'][1]+0.03)
                    break
        location_info['密码'] = True

    for word in password:
        logger.info(f'{word}文本坐标：{location_info[word]}')
        controller.move_click(device_ip=device_ip, x_ratio=location_info[word][0], y_ratio=location_info[word][1], home=False)
    write_config_value('login', {'date': time.strftime("%m-%d %H:%M", time.localtime())})

    logger.info('人脸识别判断')
    controller.ocr_text_and_click(server, device_ip, rotation, '暂不开启', home=True)

    logger.info('点击返回商家')
    if not location_info.get('返回商家'):
        over = controller.ocr_get_text_location(server, device_ip, rotation, '返回商家', home=True)
        location_info['返回商家'] = over
    controller.move_click(device_ip=device_ip, x_ratio=location_info['返回商家'][0], y_ratio=location_info['返回商家'][1], home=True)

    logger.info('点击小程序左上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1]-0.03, home=False)

    logger.info('点击小程序左上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1]-0.03, home=False)
    if not finish:
        return True
    logger.info('点击小程序右上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.97, y_ratio=location_info['优衣库'][1] - 0.01, home=False)

    logger.info('点击对话框左上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=True)

    logger.info('点击对话框左上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=False)

    location_info = dict()

    return True

def chang_status(order_id, expect_text=None):
    """修改紫旗、蓝旗状态"""
    cookie = get_config_value('order', 'order_cookie_')
    order_login()
    if cookie:
        Playwright_.add_cookie(eval(cookie))
    # 访问页面
    Playwright_.goto('https://qn.taobao.com/home.htm/trade-platform/tp/sold')
    Playwright_.wait_for_selector('//input[@aria-label="搜索"]')
    time.sleep(10)
    # 输入order_id
    Playwright_.input('//input[@aria-label="搜索"]', str(order_id))
    # 点击搜索订单
    Playwright_.click('//span[text()="搜索订单"]')

    # 点击编辑
    Playwright_.page.evaluate("window.scrollBy(0, 400)")  # 滚动
    Playwright_.click(f'//div[contains(text()[2], "{order_id}")]/../div[2]/div')

    # 点击旗帜颜色
    if expect_text:
        Playwright_.click('(//span[text()="添加标签"])[1]/../../label/span//input')
        # 添加备注
        Playwright_.input('//textarea', expect_text)
    else:
        Playwright_.click('(//span[text()="添加标签"])[5]/../../label/span//input')
    # 点击确定
    Playwright_.click('//span[text()="取消"]/../../button[1]/span')
    return expect_text if expect_text else True

def clear():
    """清除cookie"""
    write_config_value('order', {'order_cookie_': '', 'order_cookie': ''})
    write_config_value('buy', {'buy_cookie_': '', 'buy_cookie': '', 'uniqlo_token': ''})

def main(controller, devive_ip, pay_way='1'):
    """start首次运行为False，后续为True"""
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    content = now + '电商订单自动下单'
    logger.info(content.center(100, '='))

    logger.info('开始千牛登录....')
    login = order_login()
    if not login:
        logger.info('千牛登录异常')
        return False

    logger.info('开始优衣库登录....')
    login = buy_login()
    if not login:
        logger.info('优衣库登录异常')
        return False

    logger.info('获取千牛订单....')
    orders = get_order()
    logger.info(f'千牛订单：{orders}')
    if len(orders) == 0:
        logger.info('暂无需要处理订单')
        return False

    # 读取已有订单信息
    file = os.path.join(project_path, 'resources', '订单信息.txt')
    with open(file, mode='r', encoding='utf-8') as f:
        exist_order_infos = f.readlines()
        exist_order_infos = exist_order_infos if len(exist_order_infos) <= 100 else exist_order_infos[-100:]

    logger.info('获取千牛订单详情....')
    for order in orders:
        # 获取订单信息
        order_info = False
        for exist_order in exist_order_infos:
            if order in exist_order:  # 已存在订单
                order_info = eval(exist_order)[order]
                # 处理已存在的，但有多个单子的
                order_info = order_info if len(order_info) == 1 else get_order_detail(order)
                break
            else:
                continue
        order_info = order_info if order_info else get_order_detail(order, is_write=True)
        logger.info(f'\n{order}订单：{[i["title"] for i in order_info]}')
        # 获取库存
        flag = 0
        info = list()
        for single in order_info:
            single = get_count(order, single)
            logger.info(f'{order}订单详情：{single["title"]}')
            if single.get("product_count") and single.get("product_count") > 0:
                flag += 1
                info.append(single)
            elif single.get("flag") == 'error':
                info.append(single)
        if flag == 0:
            logger.info(f'{order}订单暂无需处理\n')
            continue
        # 删除地址
        addr_list = get_addr_list()
        for add_id in addr_list:
            delete_addr(add_id)
        # 清空购物车
        purchase_list = get_purchase_list()
        detele_purchase_list(purchase_list)
        # 添加地址
        addr = info[0]['addr']
        try:
            add_addr(addr)
            logger.info(f'{order}订单地址已添加:{addr}')
        except Exception as e:
            logger.error(f'{order}订单添加地址异常：{e}')
            continue
        expect_text = str()
        # 添加购物车
        for single in info:
            if single.get('flag') == 'error':
                continue
            add_to_purchase(single['product_id'], single['product_size_code'], single['quantity'])
            expect_text += single['title'] + '已下单\n'
            logger.info(f'{order}订单已加入购物车:{single["title"]}')
        # 支付
        finish = False if order != orders[-1] else True
        start_time = time.time()
        if pay_way == '1':
            status = control(controller, devive_ip, finish=finish)
        else:
            status = zfb_pay(controller, devive_ip, finish=finish)
        end_time = time.time()
        uniqo_buy_id = get_uniqo_bug_id(start_time, end_time)
        if not uniqo_buy_id:
            logger.error(f'{order}订单未找到对应优衣库购买编号！！！')
            logger.error(f'{order}订单未找到对应优衣库购买编号！！！')
            logger.error(f'{order}订单未找到对应优衣库购买编号！！！')
            continue
        else:
            logger.info(f'{order}订单对应优衣库购买编号为{uniqo_buy_id}')
        # 备注
        if status:
            tel = get_config_value('login', 'phone')[:3]
            date = get_config_value('login', 'date')
            text = f'总仓发{tel}【{date}】'
            expect_text = expect_text.strip('\n') if 'error' in [i.get('flag') for i in info] else text
            expect_text = chang_status(order, expect_text)
            if '总仓发' in expect_text:
                logger.info(f'{order}订单已修改旗帜为红色，并添加备注信息：{expect_text}')
            else:
                logger.info(f'{order}订单已修改备注信息：{expect_text}')
    return True

def get_uniqo_bug_id(start_time, end_time):
    """根据时间戳，获取购买订单编号"""
    buy_login()
    start_time = start_time * 1000
    end_time = end_time * 1000
    url = 'https://i.uniqlo.cn/p/hmall-od-service/order/queryForUserOrders/1/10/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'content-type': 'application/json',
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token')
    }
    params = {}
    response = requests.post(url, headers=headers, data=json.dumps(params)).json()['resp'][0]
    if start_time <= response['creationTime'] <= end_time and response['status'] == 'WAIT_SHIP':
        return response["orderId"]
    return None

def zfb_pay(controller, device_ip, server='127.0.0.1', rotation=3, finish=False):
    """支付宝支付"""
    global location_info
    logger.info('微信操作')
    if not location_info.get('首次'):
        logger.info('点击对话框：文件传输')
        controller.ocr_text_and_click(server, device_ip, rotation, '文件助手', home=False)
        logger.info('点击小程序二维码')
        controller.ocr_text_and_click(server, device_ip, rotation, 'UNI', home=False)
        logger.info('长按图片')
        controller.ocr_text_and_click(server, device_ip, rotation, 'UNI', keep=2000, home=True)
        logger.info('进入小程序，等待15秒')
        location3 = controller.ocr_get_text_location(server, device_ip, rotation, '优衣库', home=True)
        controller.move_click(device_ip=device_ip, x_ratio=location3[0], y_ratio=location3[1] + 0.02, home=True)
        time.sleep(3)
        logger.info('点击购物车坐标')
        location1 = controller.ocr_get_text_location(server, device_ip, rotation, '优衣库', home=True)
        location_info['优衣库'] = location1
        controller.move_click(device_ip=device_ip, x_ratio=location1[0] + 0.4, y_ratio=location1[1] - 0.02, home=False)
        location_info['优衣库'] = location1
    else:
        logger.info('点击小程序左上方返回，返回购物车')
        controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=False)
        time.sleep(3)

    logger.info('点击结算')
    controller.move_click(device_ip=device_ip, x_ratio=0.95, y_ratio=0.95, home=True)

    lose_stock = controller.ocr_get_text_location(server, device_ip, rotation, '库存不足', home=True)
    if lose_stock:
        logger.info('库存不足，不允许下单')
        logger.info('点击小程序左上方返回，返回首页')
        controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=False)
        return False
    not_support = controller.ocr_get_text_location(server, device_ip, rotation, '不支持', home=True)
    if not_support:
        controller.drag(device_ip=device_ip, start_x=0.4, start_y=0.8, end_x=0.4, end_y=0.25)
        controller.drag(device_ip=device_ip, start_x=0.4, start_y=0.8, end_x=0.4, end_y=0.25)
        logger.info('勾选不支持退货选项')
        choose = controller.ocr_get_text_location(server, device_ip, rotation, '以下商品不支持', home=True)
        controller.move_click(device_ip=device_ip, x_ratio=0.01, y_ratio=choose[1], home=False)

    logger.info('点击微信支付')
    controller.move_click(device_ip=device_ip, x_ratio=0.95, y_ratio=0.95, home=False)
    time.sleep(3)

    logger.info('关闭微信支付')
    close_location = controller.ocr_get_text_location(server, device_ip, rotation, '付款方式', home=True)
    controller.move_click(device_ip=device_ip, x_ratio=0.06501-0.008, y_ratio=close_location[1]-0.18113, home=False)

    logger.info('优衣库APP操作')
    controller.drag(device_ip=device_ip, start_x=0.46301, start_y=0.99721, end_x=0.46301, end_y=0.72421)
    logger.info('切换至优衣库APP')
    uniq_app = controller.ocr_get_text_location(server, device_ip, rotation, '优衣库', home=True, flag=True)
    controller.move_click(device_ip=device_ip, x_ratio=uniq_app[0], y_ratio=uniq_app[1] + 0.05, home=False)
    time.sleep(3)
    if not location_info.get('首次'):
        logger.info('点击会员')
        controller.ocr_text_and_click(server, device_ip, rotation, '会员', home=False)
        logger.info('点击所有订单')
        controller.ocr_text_and_click(server, device_ip, rotation, '所有订单', home=False)
        location_info['首次'] = True
    else:
        logger.info('点击返回')
        controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=False)

    logger.info('点击立即支付')
    controller.ocr_text_and_click(server, device_ip, rotation, '立即支付', home=False)
    logger.info('点击支付宝')
    tmp_location = controller.ocr_get_text_location(server, device_ip, rotation, '支付宝', home=True)
    controller.move_click(device_ip=device_ip, x_ratio=tmp_location[0]+0.2, y_ratio=tmp_location[1], home=True)
    logger.info('点击确认支付')
    controller.ocr_text_and_click(server, device_ip, rotation, '确认支付', home=False)
    time.sleep(3)
    logger.info('输入支付密码')
    password = str(get_config_value('login', 'password'))
    if not location_info.get('密码'):
        controller.capture_photo(device_ip, rotation)
        ocr_result = controller.get_ocr(server=server, device_ip=device_ip, rotation=rotation)[::-1][:10]
        if not ocr_result:
            logger.info('摄像头密码识别错误')
            return False

        logger.info([i['text'] for i in ocr_result])
        location_info['1'] = (0.1788, 0.7307 + 0.03)
        location_info['0'] = (0.5008, 0.9168 + 0.03)
        location_info['6'] = (0.9008, 0.7907 + 0.03)
        location_info['9'] = (0.9008, 0.8507 + 0.03)
        for word in password:
            if word in '0169':
                continue
            for i in ocr_result:
                find_result = re.findall(word, str(i['text']))
                if len(find_result) > 0:
                    location_info[word] = i['center'] if word != '8' else (i['center'][0], i['center'][1] + 0.03)
                    break
        location_info['密码'] = True

    for word in password:
        logger.info(f'{word}文本坐标：{location_info[word]}')
        controller.move_click(device_ip=device_ip, x_ratio=location_info[word][0], y_ratio=location_info[word][1],
                              home=False)
    write_config_value('login', {'date': time.strftime("%m-%d %H:%M", time.localtime())})

    time.sleep(3)
    logger.info('点击完成')
    controller.ocr_text_and_click(server, device_ip, rotation, '完成', home=False)

    logger.info('切换至微信-优衣库小程序')
    controller.drag(device_ip=device_ip, start_x=0.46301, start_y=0.99721, end_x=0.46301, end_y=0.72421)
    tmp_location = controller.ocr_get_text_location(server, device_ip, rotation, '优衣库UN', home=True)
    controller.move_click(device_ip=device_ip, x_ratio=tmp_location[0], y_ratio=tmp_location[1] + 0.2, home=True)

    if not finish:
        return True
    logger.info('点击小程序右上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.97, y_ratio=location_info['优衣库'][1] - 0.01, home=False)

    logger.info('点击对话框左上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=True)

    logger.info('点击对话框左上方返回')
    controller.move_click(device_ip=device_ip, x_ratio=0.02, y_ratio=location_info['优衣库'][1] - 0.03, home=False)

    location_info = dict()

    return True

if __name__ == '__main__':
    os.system(".\python3.10\python.exe -m playwright install")
    read()

    pay_way = input("请选择支付方式（1微信支付、2支付宝支付）：")
    number = int(get_config_value('login', 'number'))
    interval = int(get_config_value('login', 'interval'))

    controller, devive_ip = check_robot_status()

    for i in range(number):
        main(controller, devive_ip, pay_way)
        logger.info(f'等待{interval}秒再次执行')
        stay_time = uniqo_walk() + uniqo_walk() + uniqo_walk()
        time.sleep(interval-stay_time)

