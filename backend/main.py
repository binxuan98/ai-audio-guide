from flask import Flask, request, jsonify
import json
import math
import os
import requests
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime
from config import get_config, validate_config

# 初始化配置
config_obj = get_config()
app = Flask(__name__)
app.config.from_object(config_obj)

# 验证配置
config_validation = validate_config(config_obj)
if config_validation['warnings']:
    for warning in config_validation['warnings']:
        print(f"⚠️  配置警告: {warning}")
if config_validation['errors']:
    for error in config_validation['errors']:
        print(f"❌ 配置错误: {error}")

# 确保必要的目录存在
os.makedirs(config_obj.AUDIO_FOLDER, exist_ok=True)
os.makedirs(config_obj.CACHE_FOLDER, exist_ok=True)

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
        with open(config_obj.SPOTS_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 为每个景点添加ID（如果没有的话）
            for i, spot in enumerate(data):
                if 'id' not in spot:
                    spot['id'] = i + 1
            return data
    except FileNotFoundError:
        print(f"❌ 景点数据文件 {config_obj.SPOTS_DATA_FILE} 未找到")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ 景点数据文件格式错误: {e}")
        return []

# 从配置文件获取配置
TTS_CONFIG = config_obj.TTS_CONFIG
LLM_CONFIG = config_obj.LLM_CONFIG
GUIDE_STYLES = config_obj.GUIDE_STYLES

# LLM 内容生成函数
def generate_guide_content(spot_name: str, spot_description: str, style: str = "历史文化") -> Optional[str]:
    """
    使用大模型生成个性化讲解内容
    
    Args:
        spot_name: 景点名称
        spot_description: 景点基础描述
        style: 讲解风格（历史文化、趣闻轶事、诗词文学、人物故事等）
    
    Returns:
        str: 生成的讲解内容，失败返回原描述
    """
    try:
        # 获取风格配置
        style_config = GUIDE_STYLES.get(style, GUIDE_STYLES["历史文化"])
        prompt = style_config['prompt_template'].format(
            spot_name=spot_name,
            spot_description=spot_description
        )
        
        # 尝试调用各种LLM服务
        for provider, config in LLM_CONFIG.items():
            if not config.get('enabled', False):
                continue
                
            try:
                if provider == 'openai':
                    result = call_openai_api(prompt, config)
                    if result:
                        return result
                elif provider == 'qianwen':
                    result = call_qianwen_api(prompt, config)
                    if result:
                        return result
                elif provider == 'wenxin':
                    result = call_wenxin_api(prompt, config)
                    if result:
                        return result
            except Exception as e:
                print(f"{provider} API调用失败: {e}")
                continue
        
        # 如果所有API调用都失败，返回增强版的原描述
        enhanced_description = f"欢迎来到{spot_name}。{spot_description}这里承载着深厚的历史文化底蕴，每一处景观都诉说着动人的故事。让我们一起探索这片神奇的土地，感受它独特的魅力吧！"
        return enhanced_description
        
    except Exception as e:
        print(f"LLM 内容生成失败: {e}")
        return spot_description

def call_openai_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """
    调用OpenAI API
    """
    if config['api_key'].startswith('your_'):
        return None
        
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": config['model'],
        "messages": [
            {"role": "system", "content": config_obj.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": config['max_tokens'],
        "temperature": config['temperature']
    }
    
    response = requests.post(
        config['base_url'] + '/chat/completions',
        headers=headers,
        json=data,
        timeout=config['timeout']
    )
    
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    return None

def call_qianwen_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """
    调用通义千问API
    """
    if config['api_key'].startswith('your_'):
        return None
        
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": config['model'],
        "input": {
            "messages": [
                {"role": "system", "content": config_obj.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "max_tokens": config['max_tokens'],
            "temperature": config['temperature']
        }
    }
    
    response = requests.post(
        config['base_url'],
        headers=headers,
        json=data,
        timeout=config['timeout']
    )
    
    if response.status_code == 200:
        result = response.json()
        return result["output"]["choices"][0]["message"]["content"].strip()
    
    return None

def call_wenxin_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """
    调用文心一言API
    """
    if config['api_key'].startswith('your_'):
        return None
        
    # 文心一言需要先获取access_token
    # 这里简化处理，实际使用时需要实现完整的认证流程
    return None

# TTS 转换函数（集成真实API）
def text_to_speech(text: str, voice_style: str = None) -> Optional[str]:
    """
    将文本转换为语音文件链接
    支持多种TTS服务提供商
    
    Args:
        text: 要转换的文本
        voice_style: 语音风格（可选）
    
    Returns:
        str: 音频文件的 URL，如果转换失败则返回 None
    """
    try:
        # 生成音频文件名（基于文本内容的哈希值）
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        audio_filename = f"audio_{text_hash}.mp3"
        audio_path = os.path.join(config_obj.AUDIO_FOLDER, audio_filename)
        
        # 如果音频文件已存在，直接返回URL
        if os.path.exists(audio_path):
            return f"/static/audio/{audio_filename}"
        
        # 尝试调用各种TTS服务
        for provider, config in TTS_CONFIG.items():
            if not config.get('enabled', False):
                continue
                
            try:
                if provider == 'baidu':
                    result = call_baidu_tts(text, audio_path, config)
                    if result:
                        return f"/static/audio/{audio_filename}"
                elif provider == 'azure':
                    result = call_azure_tts(text, audio_path, config, voice_style)
                    if result:
                        return f"/static/audio/{audio_filename}"
                elif provider == 'local':
                    result = call_local_tts(text, audio_path, config)
                    if result:
                        return f"/static/audio/{audio_filename}"
            except Exception as e:
                print(f"{provider} TTS调用失败: {e}")
                continue
        
        # 如果所有TTS方案都失败，返回None
        return None
        
    except Exception as e:
        print(f"TTS 转换失败: {e}")
        return None

def call_baidu_tts(text: str, audio_path: str, config: Dict[str, Any]) -> bool:
    """
    调用百度TTS API
    """
    if config['api_key'].startswith('your_'):
        return False
        
    # 百度TTS需要复杂的认证流程
    # 这里提供框架代码，实际使用时需要完善
    try:
        # 1. 获取access_token
        # 2. 调用TTS API
        # 3. 保存音频文件
        pass
    except Exception as e:
        print(f"百度TTS调用失败: {e}")
        return False
    
    return False

def call_azure_tts(text: str, audio_path: str, config: Dict[str, Any], voice_style: str = None) -> bool:
    """
    调用Azure TTS API
    """
    if config['subscription_key'].startswith('your_'):
        return False
        
    try:
        # Azure Speech Services实现
        # 这里需要安装 azure-cognitiveservices-speech 包
        # import azure.cognitiveservices.speech as speechsdk
        
        # speech_config = speechsdk.SpeechConfig(
        #     subscription=config['subscription_key'], 
        #     region=config['region']
        # )
        # speech_config.speech_synthesis_voice_name = voice_style or config['voice_name']
        # 
        # synthesizer = speechsdk.SpeechSynthesizer(
        #     speech_config=speech_config, 
        #     audio_config=speechsdk.audio.AudioOutputConfig(filename=audio_path)
        # )
        # 
        # result = synthesizer.speak_text_async(text).get()
        # return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted
        
        pass
    except Exception as e:
        print(f"Azure TTS调用失败: {e}")
        return False
    
    return False

def call_local_tts(text: str, audio_path: str, config: Dict[str, Any]) -> bool:
    """
    调用本地TTS（pyttsx3）
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', config.get('rate', 150))  # 语速
        engine.setProperty('volume', config.get('volume', 0.9))  # 音量
        
        # 设置中文语音（如果可用）
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        
        engine.save_to_file(text, audio_path)
        engine.runAndWait()
        
        return os.path.exists(audio_path)
        
    except ImportError:
        print("pyttsx3 未安装，无法使用本地TTS")
        return False
    except Exception as e:
        print(f"本地TTS调用失败: {e}")
        return False

# 缓存管理函数
def get_cached_content(spot_id: str, style: str) -> Optional[Dict[str, Any]]:
    """
    获取缓存的内容
    
    Args:
        spot_id: 景点ID
        style: 讲解风格
    
    Returns:
        dict: 缓存的内容，包含text和audio_url
    """
    cache_file = f"cache_{spot_id}_{style}.json"
    cache_path = os.path.join(config_obj.CACHE_FOLDER, cache_file)
    
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # 检查缓存是否过期
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
                expire_seconds = config_obj.CACHE_EXPIRE_HOURS * 3600
                if (datetime.now() - cache_time).total_seconds() < expire_seconds:
                    return cache_data
    except Exception as e:
        print(f"读取缓存失败: {e}")
    
    return None

def save_cached_content(spot_id: str, style: str, content: Dict[str, Any]):
    """
    保存内容到缓存
    
    Args:
        spot_id: 景点ID
        style: 讲解风格
        content: 要缓存的内容
    """
    try:
        cache_file = f"cache_{spot_id}_{style}.json"
        cache_path = os.path.join(config_obj.CACHE_FOLDER, cache_file)
        
        cache_data = {
            **content,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"保存缓存失败: {e}")

def clear_expired_cache():
    """
    清理过期的缓存文件
    """
    try:
        if not os.path.exists(config_obj.CACHE_FOLDER):
            return
            
        expire_seconds = config_obj.CACHE_EXPIRE_HOURS * 3600
        current_time = datetime.now()
        
        for filename in os.listdir(config_obj.CACHE_FOLDER):
            if filename.startswith('cache_') and filename.endswith('.json'):
                file_path = os.path.join(config_obj.CACHE_FOLDER, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        cache_time = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
                        if (current_time - cache_time).total_seconds() > expire_seconds:
                            os.remove(file_path)
                            print(f"清理过期缓存: {filename}")
                except Exception as e:
                    print(f"清理缓存文件 {filename} 失败: {e}")
                    
    except Exception as e:
        print(f"清理缓存失败: {e}")

@app.route("/ping", methods=["GET"])
def ping():
    """健康检查接口"""
    return jsonify({"message": "pong"})

@app.route("/guide", methods=["POST"])
def get_nearest_spot():
    """
    根据用户位置返回最近的景点信息，支持LLM内容生成和TTS语音合成
    
    请求体格式:
    {
        "latitude": 39.9042,
        "longitude": 116.4074,
        "enable_tts": true,  // 可选，是否启用 TTS 功能
        "enable_llm": true,  // 可选，是否启用 LLM 内容生成
        "guide_style": "历史文化",  // 可选，讲解风格：历史文化、趣闻轶事、诗词文学、人物故事
        "use_cache": true  // 可选，是否使用缓存
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
            "generated_content": "LLM生成的个性化讲解内容",
            "distance": 0.5,  // 距离（公里）
            "audio_url": "/static/audio/audio_hash.mp3",  // TTS 音频链接
            "guide_style": "历史文化",
            "cached": false  // 是否来自缓存
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
        enable_llm = data.get('enable_llm', False)
        guide_style = data.get('guide_style', '历史文化')
        use_cache = data.get('use_cache', True)
        
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
        
        # 生成景点唯一ID（用于缓存）
        spot_id = str(nearest_spot.get('id', hashlib.md5(nearest_spot['name'].encode()).hexdigest()[:8]))
        
        # 检查缓存
        cached_content = None
        if use_cache:
            cached_content = get_cached_content(spot_id, guide_style)
        
        if cached_content:
            # 使用缓存内容
            nearest_spot.update({
                'generated_content': cached_content.get('generated_content', nearest_spot['description']),
                'audio_url': cached_content.get('audio_url'),
                'guide_style': guide_style,
                'cached': True
            })
        else:
            # 生成新内容
            generated_content = nearest_spot['description']
            
            # 如果启用 LLM，生成个性化内容
            if enable_llm:
                generated_content = generate_guide_content(
                    nearest_spot['name'], 
                    nearest_spot['description'], 
                    guide_style
                )
            
            # 如果启用 TTS，生成音频
            audio_url = None
            if enable_tts:
                audio_url = text_to_speech(generated_content)
            
            # 更新景点信息
            nearest_spot.update({
                'generated_content': generated_content,
                'audio_url': audio_url,
                'guide_style': guide_style,
                'cached': False
            })
            
            # 保存到缓存
            if use_cache:
                cache_content = {
                    'generated_content': generated_content,
                    'audio_url': audio_url
                }
                save_cached_content(spot_id, guide_style, cache_content)
        
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

# 添加静态文件服务
@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """
    提供音频文件服务
    """
    from flask import send_from_directory
    return send_from_directory(config_obj.AUDIO_FOLDER, filename)

# 添加获取讲解风格列表的接口
@app.route('/guide/styles', methods=['GET'])
def get_guide_styles():
    """
    获取可用的讲解风格列表
    
    返回格式:
    {
        "success": true,
        "data": {
            "styles": [
                {
                    "key": "历史文化",
                    "name": "历史文化",
                    "description": "突出历史价值和文化内涵的讲解风格"
                }
            ]
        }
    }
    """
    try:
        styles = []
        for key, config in GUIDE_STYLES.items():
            styles.append({
                'key': key,
                'name': config['name'],
                'description': config['description']
            })
        
        return jsonify({
            'success': True,
            'data': {
                'styles': styles
            },
            'message': 'success'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取讲解风格失败: {str(e)}'
        }), 500

# 添加清理缓存的接口
@app.route('/admin/clear-cache', methods=['POST'])
def clear_cache_endpoint():
    """
    清理过期缓存（管理员接口）
    """
    try:
        clear_expired_cache()
        return jsonify({
            'success': True,
            'message': '缓存清理完成'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'缓存清理失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 启动AI语音导览后端服务...")
    print(f"📍 服务地址: http://{config_obj.HOST}:{config_obj.PORT}")
    print(f"📁 音频文件目录: {config_obj.AUDIO_FOLDER}")
    print(f"💾 缓存目录: {config_obj.CACHE_FOLDER}")
    
    # 启动时清理过期缓存
    clear_expired_cache()
    
    # 启动Flask应用
    app.run(
        debug=config_obj.DEBUG,
        host=config_obj.HOST,
        port=config_obj.PORT
    )