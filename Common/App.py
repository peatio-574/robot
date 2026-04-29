# -*- coding: utf-8 -*-
import sys
import time
from pathlib import Path

# 把项目根目录 D:\robot 加入Python路径
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify
from Common.Control import controls
from Common.Control import check_robot_status

app = Flask(__name__)



@app.route('/api/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    if not data or 'name' not in data or 'account' not in data or 'amount' not in data:
        return jsonify({
            'code': 400,
            'message': '参数缺失： name / account / amount'
        }), 400

    name = str(data['name'])
    account = str(data['account'])
    amount = str(data['amount'])
    first = data.get('first')
    controller, device_ip = check_robot_status()
    if controller == 0:
        return jsonify({'status': controller, 'message': device_ip})
    code, info = controls(name=name, tel=account, amount=amount, first=first, controller=controller, device_ip=device_ip)
    return jsonify({'status': code, 'message': info})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)