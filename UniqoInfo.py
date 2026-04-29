# -*- coding: utf-8 -*-
import time

import re
from openpyxl.styles import Font
import os
import pandas
from Order import buy_login, get_phone
import requests
from Common.Deal import get_config_value
from Common.Logger import logger

infos = dict()

def get_page_info(page=1):
    """获取每页数据"""
    url = f'https://i.uniqlo.cn/p/hmall-od-service/order/queryForUserOrders/{page}/10/zh_CN'
    headers = {
        'user-agent': get_config_value('login', 'user-agent'),
        'authorization': 'bearer ' + get_config_value('buy', 'Uniqlo_token'),
        'cookie': get_config_value('buy', 'buy_cookie')
    }
    logger.info(f'查询第{page}页订单数据')
    response = requests.post(url, headers=headers, json={}).json()
    logger.info(response)
    return response['total'], response['resp']

def deal_info(page_info):
    """处理每页数据"""
    global infos
    for order_info in page_info:  # 每条订单
        for order in order_info['details']:  # 订单的每条数据
            status = order['status']
            if status in ['CANCELLED', 'CLOSED']:  # 无效订单
                continue
            good_no = order['summaryInfo']['code']
            color = order['productDetailInfo']['styleText'].replace(' ', '')
            color = re.findall(r'\d+[\u4e00-\u9fff]+', color)[0] if '色' in color else color
            size = order['productDetailInfo']['sizeText']
            price = '价格：' + order['productDetailInfo']['price']

            if size == 'XXL':
                size = '2XL'
            elif size == 'XXXL':
                size = '3XL'
            elif size == 'XXXXL':
                size = '4XL'

            if not infos.get(good_no):
                infos[good_no] = dict()
            if not infos.get(good_no).get(color):
                infos[good_no][color] = dict()
            if not infos.get(good_no).get(color).get(size):
                infos[good_no][color][size] = [order['quantity'], price]
            else:
                infos[good_no][color][size][0] += order['quantity']
    return True

def GetUniqoInfos():
    """获取所有页数据，并进行处理"""
    global infos
    buy_login()
    total, page_info= get_page_info()
    deal_info(page_info)
    pages = total // 10 if total % 10 == 0 else total // 10 + 1
    for page in range(2, pages+1):
        page_info = get_page_info(page)[1]
        deal_info(page_info)

def add_data_to_xlxl(data, filename):
    """追加写入"""
    try:
        pd = pandas.DataFrame(data)
        with pandas.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            workbook = writer.book
            sheet = workbook.active
            start_row = sheet.max_row
            pd.to_excel(writer, sheet_name='Sheet1', startrow=start_row, index=False, header=True)
            cols = pd.shape[1]  # 列数
            for col in range(1, cols + 1):
                sheet.cell(row=start_row + 1, column=col).font = Font(bold=True)
        logger.info('数据写入成功')
        return True
    except Exception as e:
        logger.error('数据写入失败：%s' % e)
        return False

def main():
    global infos
    date = time.strftime('%Y-%m-%d %H:%M:%S')
    filename = os.path.join(os.path.dirname(__file__), '优衣库订单统计表.xlsx')

    logger.info('开始获取优衣库订单数据.....')
    GetUniqoInfos()
    time.sleep(2)
    phone = get_phone()

    while True:
        text = input('请输入查询货号（附带查询价格时请用逗号隔开，如：482295 99）：')
        if text == '1':
            exit()
        text = text.split(' ')
        goods_no = text[0]
        current_info = infos.get(goods_no)
        if current_info is None:
            logger.info(f'当前货号：{goods_no}暂无数据')
            continue
        if len(text) == 1:
            current_info = {k: {a:b[0] for a, b in v.items()} for k, v in current_info.items()}
        elif len(text) == 2:
            current_info = {k: {a: b[0] for a, b in v.items() if b[1][3:] == text[1]} for k, v in current_info.items()}

        if not current_info:
            logger.info(f'{goods_no}货号暂无数据！！！')
            continue

        logger.info(f'{goods_no}货号数据为：{current_info}')

        size_ = list()  # 当前商品的全部尺寸
        for v in current_info.values():
            for key in v.keys():
                if key not in size_:
                    size_.append(key)

        tmp_size = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', '6XL']
        is_size = False
        for i in size_:
            if i in tmp_size:
                is_size = True
                break
        size_ = sorted(size_) if not is_size else tmp_size

        colum_keys = ['优衣库账号', '日期', '货号', '色号'] + size_
        end_text = f'查询价格：' + text[1] if len(text) == 2 else f'查询价格：'
        colum_keys.append(end_text)
        data = {i:list() for i in colum_keys}

        for color_, info_ in current_info.items():
            data['优衣库账号'].append(phone)
            data['日期'].append(date)
            data['货号'].append(goods_no)
            data['色号'].append(color_)

            valid_size = list(info_.keys())
            for size in size_:
                if size not in valid_size:
                    data[size].append(0)
                else:
                    data[size].append(info_[size])
            data[end_text].append(None)

        add_data_to_xlxl(data, filename)

if __name__ == '__main__':
    main()



