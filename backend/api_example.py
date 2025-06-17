#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 使用示例
演示如何调用 /guide 接口获取最近的景点信息
"""

import requests
import json

# API 基础 URL
BASE_URL = "http://localhost:5000"

def test_ping():
    """测试健康检查接口"""
    print("=== 测试 /ping 接口 ===")
    try:
        response = requests.get(f"{BASE_URL}/ping")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def test_guide_api():
    """测试景点导览接口"""
    print("=== 测试 /guide 接口 ===")
    
    # 测试数据：天安门广场附近的位置
    test_cases = [
        {
            "name": "天安门广场附近",
            "data": {
                "latitude": 39.9042,
                "longitude": 116.4074,
                "enable_tts": False
            }
        },
        {
            "name": "故宫博物院附近",
            "data": {
                "latitude": 39.9163,
                "longitude": 116.3972,
                "enable_tts": True
            }
        },
        {
            "name": "颐和园附近",
            "data": {
                "latitude": 39.9998,
                "longitude": 116.2755
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"--- {test_case['name']} ---")
        try:
            response = requests.post(
                f"{BASE_URL}/guide",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('success') and 'data' in result:
                data = result['data']
                print(f"最近景点: {data['name']}")
                print(f"距离: {data['distance']} 公里")
                
        except Exception as e:
            print(f"请求失败: {e}")
        print()

def test_error_cases():
    """测试错误情况"""
    print("=== 测试错误情况 ===")
    
    error_cases = [
        {
            "name": "缺少参数",
            "data": {"latitude": 39.9042}
        },
        {
            "name": "无效的经纬度",
            "data": {"latitude": "invalid", "longitude": 116.4074}
        },
        {
            "name": "超出范围的经纬度",
            "data": {"latitude": 91, "longitude": 181}
        },
        {
            "name": "空请求体",
            "data": None
        }
    ]
    
    for test_case in error_cases:
        print(f"--- {test_case['name']} ---")
        try:
            response = requests.post(
                f"{BASE_URL}/guide",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            print(f"请求失败: {e}")
        print()

if __name__ == "__main__":
    print("AI 语音导览 API 测试")
    print("请确保服务器已启动: python main.py")
    print("=" * 50)
    
    # 测试各个接口
    test_ping()
    test_guide_api()
    test_error_cases()
    
    print("测试完成！")