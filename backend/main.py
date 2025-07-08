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
from llm_service import init_llm_service, get_llm_service
from tts_service import init_tts_service, get_tts_service
from prompt_templates import get_available_guide_styles

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

print(f"📁 音频文件目录: {config_obj.AUDIO_FOLDER}")
print(f"💾 缓存目录: {config_obj.CACHE_FOLDER}")

# 初始化LLM和TTS服务
print("🤖 初始化LLM服务...")
llm_service = init_llm_service(config_obj.__dict__)
print("🔊 初始化TTS服务...")
tts_service = init_tts_service(config_obj.__dict__)

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
def generate_guide_content(spot_name: str, spot_description: str, guide_style: str = '历史文化', context: dict = None) -> str:
    """
    使用大模型生成景点讲解内容
    
    Args:
        spot_name: 景点名称
        spot_description: 景点基础描述
        guide_style: 讲解风格
        context: 上下文信息（时间、天气、游客类型等）
    
    Returns:
        str: 生成的讲解内容
    """
    try:
        # 使用新的LLM服务
        llm_service = get_llm_service()
        result = llm_service.generate_content(
            spot_name=spot_name,
            spot_description=spot_description,
            guide_style=guide_style,
            context=context
        )
        
        if result['success']:
            print(f"✅ LLM生成成功 - 提供商: {result['provider']}, 风格: {guide_style}")
            return result['content']
        else:
            print(f"❌ LLM生成失败: {result.get('error', '未知错误')}")
            return result.get('content', spot_description)
            
    except Exception as e:
        print(f"生成讲解内容失败: {e}")
        # 返回增强的默认描述
        enhanced_description = f"欢迎来到{spot_name}。{spot_description}这里有着丰富的历史文化内涵，值得我们细细品味和探索。"
        return enhanced_description

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
def text_to_speech(text: str, voice_style: str = 'default') -> Optional[str]:
    """
    将文本转换为语音文件链接
    支持多种TTS服务提供商
    
    Args:
        text: 要转换的文本
        voice_style: 语音风格
    
    Returns:
        str: 音频文件的 URL，如果转换失败则返回 None
    """
    try:
        # 使用新的TTS服务
        tts_service = get_tts_service()
        result = tts_service.text_to_speech(
            text=text,
            voice_style=voice_style,
            use_cache=True
        )
        
        if result['success']:
            print(f"✅ TTS生成成功 - 提供商: {result['provider']}, 文件大小: {result.get('file_size', 0)} bytes")
            return result['audio_url']
        else:
            print(f"❌ TTS生成失败: {result.get('error', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"TTS转换失败: {e}")
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

@app.route("/", methods=["GET"])
def index():
    """根路由 - 服务状态"""
    return jsonify({
        "service": "AI语音导览后端服务",
        "status": "running",
        "version": "1.0.0",
        "message": "服务正常运行"
    })

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
        enable_tts = data.get('enable_tts', True)  # 默认启用TTS
        enable_llm = data.get('enable_llm', True)  # 默认启用LLM
        guide_style = data.get('guide_style', '历史文化')
        use_cache = data.get('use_cache', True)
        voice_style = data.get('voice_style', 'default')  # 语音风格
        
        # 获取上下文信息
        context = {
            'time_of_day': data.get('time_of_day'),  # 时间段：morning, afternoon, evening, night
            'weather': data.get('weather'),  # 天气：sunny, cloudy, rainy, snowy
            'visitor_type': data.get('visitor_type'),  # 游客类型：family, student, elderly, young
            'language': data.get('language', 'zh-CN'),  # 语言
            'duration_preference': data.get('duration_preference', 'medium')  # 时长偏好：short, medium, long
        }
        
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
                    guide_style,
                    context  # 传递上下文信息
                )
            
            # 如果启用 TTS，生成音频
            audio_url = None
            if enable_tts:
                audio_url = text_to_speech(generated_content, voice_style)  # 传递语音风格
            
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
        # 使用新的prompt_templates模块
        styles = get_available_guide_styles()
        
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

# 添加批量生成内容的接口
@app.route('/admin/batch-generate', methods=['POST'])
def batch_generate_content():
    """
    批量生成景点讲解内容（管理员接口）
    
    请求体格式:
    {
        "styles": ["历史文化", "趣闻轶事"],  // 可选，默认所有风格
        "enable_tts": true,  // 可选，是否同时生成音频
        "voice_style": "default"  // 可选，语音风格
    }
    """
    try:
        data = request.get_json() or {}
        
        # 获取参数
        styles = data.get('styles', ['历史文化', '趣闻轶事', '诗词文学', '人物故事', '科普知识', '民俗风情'])
        enable_tts = data.get('enable_tts', False)
        voice_style = data.get('voice_style', 'default')
        
        # 读取景点数据
        spots = load_spots_data()
        if not spots:
            return jsonify({
                'success': False,
                'message': '暂无景点数据'
            }), 404
        
        # 批量生成LLM内容
        llm_service = get_llm_service()
        llm_results = llm_service.batch_generate_content(spots, styles)
        
        # 如果启用TTS，批量生成音频
        tts_results = {}
        if enable_tts:
            tts_service = get_tts_service()
            
            # 准备文本数据
            texts = []
            for spot_name, style_contents in llm_results.items():
                for style, content_data in style_contents.items():
                    texts.append({
                        'id': f"{spot_name}_{style}",
                        'content': content_data.get('content', '')
                    })
            
            tts_results = tts_service.batch_generate_audio(texts, voice_style)
        
        return jsonify({
            'success': True,
            'data': {
                'llm_results': llm_results,
                'tts_results': tts_results,
                'total_spots': len(spots),
                'total_styles': len(styles),
                'total_generated': len(llm_results) * len(styles)
            },
            'message': '批量生成完成'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量生成失败: {str(e)}'
        }), 500

# 添加音频文件管理接口
@app.route('/admin/audio/info', methods=['GET'])
def get_audio_info():
    """
    获取音频文件信息（管理员接口）
    """
    try:
        if not os.path.exists(config_obj.AUDIO_FOLDER):
            return jsonify({
                'success': True,
                'data': {
                    'total_files': 0,
                    'total_size': 0,
                    'files': []
                }
            })
        
        files_info = []
        total_size = 0
        
        for filename in os.listdir(config_obj.AUDIO_FOLDER):
            if filename.endswith('.mp3'):
                file_path = os.path.join(config_obj.AUDIO_FOLDER, filename)
                tts_service = get_tts_service()
                file_info = tts_service.get_audio_info(file_path)
                
                if file_info.get('exists'):
                    files_info.append({
                        'filename': filename,
                        'size': file_info['file_size'],
                        'size_mb': file_info['file_size_mb'],
                        'modified_time': file_info['modified_time']
                    })
                    total_size += file_info['file_size']
        
        return jsonify({
            'success': True,
            'data': {
                'total_files': len(files_info),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files': files_info
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取音频信息失败: {str(e)}'
        }), 500

# 添加清理音频文件的接口
@app.route('/admin/audio/cleanup', methods=['POST'])
def cleanup_audio_files():
    """
    清理旧的音频文件（管理员接口）
    
    请求体格式:
    {
        "days": 7  // 清理多少天前的文件，默认7天
    }
    """
    try:
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        tts_service = get_tts_service()
        result = tts_service.cleanup_old_audio_files(days)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'清理完成，删除了 {result["cleaned"]} 个文件'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清理音频文件失败: {str(e)}'
        }), 500

# 添加语音风格列表接口
@app.route('/guide/voice-styles', methods=['GET'])
def get_voice_styles():
    """
    获取可用的语音风格列表
    
    返回格式:
    {
        "success": true,
        "data": {
            "styles": [
                {
                    "key": "default",
                    "name": "标准",
                    "description": "标准语音风格"
                }
            ]
        }
    }
    """
    try:
        voice_styles = [
            {
                'key': 'default',
                'name': '标准',
                'description': '标准语音风格，适合大多数场景'
            },
            {
                'key': 'gentle',
                'name': '温和',
                'description': '温和亲切的语音风格，适合家庭游客'
            },
            {
                'key': 'energetic',
                'name': '活力',
                'description': '充满活力的语音风格，适合年轻游客'
            },
            {
                'key': 'warm',
                'name': '温暖',
                'description': '温暖感人的语音风格，适合情感类内容'
            },
            {
                'key': 'professional',
                'name': '专业',
                'description': '专业严谨的语音风格，适合学术类内容'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'styles': voice_styles
            },
            'message': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取语音风格失败: {str(e)}'
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