#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Flask测试服务器
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'AI语音导览测试服务',
        'status': 'running',
        'message': '服务正常运行'
    })

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'pong'})

if __name__ == '__main__':
    print("🚀 启动测试服务器...")
    print("📍 服务地址: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)