#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI语音导览后端API测试脚本

用于测试各个API接口的功能是否正常
"""

import requests
import json
import time

# 配置
BASE_URL = 'http://localhost:5001'
TEST_LAT = 36.0611  # 兰州大学纬度
TEST_LNG = 103.8343  # 兰州大学经度

def test_guide_api():
    """
    测试 /guide 接口
    """
    print("\n=== 测试 /guide 接口 ===")
    
    # 测试基本功能
    params = {
        'lat': TEST_LAT,
        'lng': TEST_LNG,
        'enable_llm': True,
        'enable_tts': True,
        'style': '历史文化',
        'voice_style': 'default'
    }
    
    try:
        response = requests.get(f'{BASE_URL}/guide', params=params)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_guide_styles_api():
    """
    测试 /guide/styles 接口
    """
    print("\n=== 测试 /guide/styles 接口 ===")
    
    try:
        response = requests.get(f'{BASE_URL}/guide/styles')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"可用讲解风格: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_voice_styles_api():
    """
    测试 /guide/voice-styles 接口
    """
    print("\n=== 测试 /guide/voice-styles 接口 ===")
    
    try:
        response = requests.get(f'{BASE_URL}/guide/voice-styles')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"可用语音风格: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_batch_generate_api():
    """
    测试 /admin/batch-generate 接口
    """
    print("\n=== 测试 /admin/batch-generate 接口 ===")
    
    payload = {
        'styles': ['历史文化', '趣闻轶事'],
        'enable_tts': False,  # 先不生成音频，避免耗时过长
        'voice_style': 'default'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/admin/batch-generate',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"批量生成结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_audio_info_api():
    """
    测试 /admin/audio/info 接口
    """
    print("\n=== 测试 /admin/audio/info 接口 ===")
    
    try:
        response = requests.get(f'{BASE_URL}/admin/audio/info')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"音频文件信息: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_clear_cache_api():
    """
    测试 /admin/clear-cache 接口
    """
    print("\n=== 测试 /admin/clear-cache 接口 ===")
    
    try:
        response = requests.post(f'{BASE_URL}/admin/clear-cache')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"清理缓存结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_server_health():
    """
    测试服务器健康状态
    """
    print("\n=== 测试服务器健康状态 ===")
    
    try:
        response = requests.get(f'{BASE_URL}/', timeout=5)
        print(f"服务器状态: {'正常' if response.status_code == 200 else '异常'}")
        print(f"状态码: {response.status_code}")
    except Exception as e:
        print(f"服务器连接失败: {e}")
        return False
    
    return True

def main():
    """
    主测试函数
    """
    print("🧪 开始测试AI语音导览后端API")
    print(f"测试目标: {BASE_URL}")
    
    # 首先测试服务器健康状态
    if not test_server_health():
        print("\n❌ 服务器连接失败，请确保后端服务已启动")
        return
    
    # 测试各个API接口
    test_guide_styles_api()
    test_voice_styles_api()
    test_audio_info_api()
    test_clear_cache_api()
    
    # 测试核心功能
    test_guide_api()
    
    # 测试批量生成（可能耗时较长）
    print("\n⚠️  即将测试批量生成功能，可能需要较长时间...")
    user_input = input("是否继续测试批量生成功能？(y/n): ")
    if user_input.lower() == 'y':
        test_batch_generate_api()
    
    print("\n✅ API测试完成")

if __name__ == '__main__':
    main()