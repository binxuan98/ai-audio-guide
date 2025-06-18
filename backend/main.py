from flask import Flask, request, jsonify
import json
import math
import os
import requests
from typing import Optional

app = Flask(__name__)

# 计算两点间距离的函数（使用 Haversine 公式）
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine 公式计算两个经纬度点之间的距离（单位：公里）
    
    Args:
        lat1, lon1: 第一个点的纬度和经度
        lat2, lon2: 第二个点的纬度和经度
    
    Returns:
        float: 两点间的距离（公里）
    """
    # 将角度转换为弧度
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine 公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 地球半径（公里）
    r = 6371
    
    return c * r

# 读取景点数据
def load_spots_data():
    """
    从 JSON 文件中读取景点数据
    
    Returns:
        list: 景点数据列表
    """
    try:
        with open('spots.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

# TTS 转换函数（可选功能）
def text_to_speech(text: str) -> Optional[str]:
    """
    将文本转换为语音文件链接
    这里是一个示例实现，实际使用时需要替换为真实的 TTS API
    
    Args:
        text: 要转换的文本
    
    Returns:
        str: 音频文件的 URL，如果转换失败则返回 None
    """
    try:
        # 这里是示例代码，实际使用时需要调用真实的 TTS API
        # 例如：百度语音合成、阿里云语音合成、讯飞语音合成等
        
        # 示例：假设我们有一个 TTS 服务
        # tts_api_url = "https://your-tts-api.com/synthesize"
        # response = requests.post(tts_api_url, json={"text": text, "voice": "zh-CN"})
        # if response.status_code == 200:
        #     return response.json().get("audio_url")
        
        # 暂时返回 None，表示 TTS 功能未实现
        return None
    except Exception as e:
        print(f"TTS 转换失败: {e}")
        return None

@app.route("/ping", methods=["GET"])
def ping():
    """健康检查接口"""
    return jsonify({"message": "pong"})

@app.route("/guide", methods=["POST"])
def get_nearest_spot():
    """
    根据用户位置返回最近的景点信息
    
    请求体格式:
    {
        "latitude": 39.9042,
        "longitude": 116.4074,
        "enable_tts": true  // 可选，是否启用 TTS 功能
    }
    
    返回格式:
    {
        "success": true,
        "data": {
            "id": 1,
            "name": "景点名称",
            "latitude": 39.9042,
            "longitude": 116.4074,
            "description": "景点描述",
            "distance": 0.5,  // 距离（公里）
            "audio_url": "http://example.com/audio.mp3"  // TTS 音频链接（可选）
        },
        "message": "success"
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "请求体不能为空"
            }), 400
        
        # 验证必需参数
        user_lat = data.get('latitude')
        user_lon = data.get('longitude')
        enable_tts = data.get('enable_tts', False)
        
        if user_lat is None or user_lon is None:
            return jsonify({
                "success": False,
                "message": "缺少必需参数：latitude 和 longitude"
            }), 400
        
        # 验证参数类型
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "latitude 和 longitude 必须是数字"
            }), 400
        
        # 验证经纬度范围
        if not (-90 <= user_lat <= 90) or not (-180 <= user_lon <= 180):
            return jsonify({
                "success": False,
                "message": "经纬度超出有效范围"
            }), 400
        
        # 读取景点数据
        spots = load_spots_data()
        
        if not spots:
            return jsonify({
                "success": False,
                "message": "暂无景点数据"
            }), 404
        
        # 计算距离并找到最近的景点
        nearest_spot = None
        min_distance = float('inf')
        
        for spot in spots:
            distance = calculate_distance(
                user_lat, user_lon,
                spot['latitude'], spot['longitude']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_spot = spot.copy()
                nearest_spot['distance'] = round(distance, 2)
        
        if not nearest_spot:
            return jsonify({
                "success": False,
                "message": "未找到合适的景点"
            }), 404
        
        # 如果启用 TTS 且当前没有音频链接，则生成音频
        if enable_tts and not nearest_spot.get('audio_url'):
            audio_url = text_to_speech(nearest_spot['description'])
            if audio_url:
                nearest_spot['audio_url'] = audio_url
        
        return jsonify({
            "success": True,
            "data": nearest_spot,
            "message": "success"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)