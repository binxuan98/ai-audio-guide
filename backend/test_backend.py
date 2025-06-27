#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI语音导览后端测试脚本
用于测试后端API接口功能
"""

import requests
import json
import time
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:5001"
TEST_LOCATION = {
    "latitude": 35.5494,   # 平凉崆峒山附近
    "longitude": 106.6608
}

def test_ping():
    """
    测试ping接口
    """
    print("\n🔍 测试 /ping 接口...")
    try:
        response = requests.get(f"{BASE_URL}/ping")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ping测试失败: {e}")
        return False

def test_guide_styles():
    """
    测试获取讲解风格接口
    """
    print("\n🔍 测试 /guide/styles 接口...")
    try:
        response = requests.get(f"{BASE_URL}/guide/styles")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"❌ 讲解风格测试失败: {e}")
        return False

def test_guide_basic():
    """
    测试基础导览接口（不启用LLM和TTS）
    """
    print("\n🔍 测试 /guide 接口（基础功能）...")
    try:
        payload = {
            "latitude": TEST_LOCATION["latitude"],
            "longitude": TEST_LOCATION["longitude"],
            "type": "nearby",
            "range": 1000,
            "enable_llm": False,
            "enable_tts": False
        }
        
        response = requests.post(
            f"{BASE_URL}/guide",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"❌ 基础导览测试失败: {e}")
        return False

def test_guide_with_llm():
    """
    测试启用LLM的导览接口
    """
    print("\n🔍 测试 /guide 接口（启用LLM）...")
    try:
        payload = {
            "latitude": TEST_LOCATION["latitude"],
            "longitude": TEST_LOCATION["longitude"],
            "type": "nearby",
            "range": 1000,
            "enable_llm": True,
            "enable_tts": False,
            "guide_style": "历史文化",
            "use_cache": True
        }
        
        response = requests.post(
            f"{BASE_URL}/guide",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ LLM导览测试失败: {e}")
        return False

def test_guide_with_tts():
    """
    测试启用TTS的导览接口
    """
    print("\n🔍 测试 /guide 接口（启用TTS）...")
    try:
        payload = {
            "latitude": TEST_LOCATION["latitude"],
            "longitude": TEST_LOCATION["longitude"],
            "type": "nearby",
            "range": 1000,
            "enable_llm": False,
            "enable_tts": True,
            "use_cache": True
        }
        
        response = requests.post(
            f"{BASE_URL}/guide",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ TTS导览测试失败: {e}")
        return False

def test_guide_full_features():
    """
    测试完整功能的导览接口（LLM + TTS）
    """
    print("\n🔍 测试 /guide 接口（完整功能）...")
    try:
        payload = {
            "latitude": TEST_LOCATION["latitude"],
            "longitude": TEST_LOCATION["longitude"],
            "type": "nearby",
            "range": 1000,
            "enable_llm": True,
            "enable_tts": True,
            "guide_style": "趣闻轶事",
            "use_cache": True
        }
        
        print("⏳ 正在测试完整功能（可能需要较长时间）...")
        response = requests.post(
            f"{BASE_URL}/guide",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60  # 增加超时时间
        )
        
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 完整功能测试失败: {e}")
        return False

def test_clear_cache():
    """
    测试清理缓存接口
    """
    print("\n🔍 测试 /admin/clear-cache 接口...")
    try:
        response = requests.post(f"{BASE_URL}/admin/clear-cache")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"❌ 清理缓存测试失败: {e}")
        return False

def run_all_tests():
    """
    运行所有测试
    """
    print("🚀 开始测试AI语音导览后端API...")
    print(f"📍 测试服务器: {BASE_URL}")
    print(f"📍 测试位置: {TEST_LOCATION}")
    
    tests = [
        ("Ping接口", test_ping),
        ("讲解风格接口", test_guide_styles),
        ("基础导览功能", test_guide_basic),
        ("LLM导览功能", test_guide_with_llm),
        ("TTS导览功能", test_guide_with_tts),
        ("完整导览功能", test_guide_full_features),
        ("清理缓存功能", test_clear_cache)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 测试: {test_name}")
        print(f"{'='*50}")
        
        start_time = time.time()
        success = test_func()
        end_time = time.time()
        
        duration = end_time - start_time
        status = "✅ 通过" if success else "❌ 失败"
        
        print(f"\n结果: {status} (耗时: {duration:.2f}秒)")
        results.append((test_name, success, duration))
    
    # 输出测试总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, duration in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name:<20} (耗时: {duration:.2f}秒)")
    
    print(f"\n📈 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！后端功能正常。")
    else:
        print("⚠️  部分测试失败，请检查后端配置和服务状态。")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()