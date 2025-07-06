# -*- coding: utf-8 -*-
"""
AI语音导览小程序 - 配置文件

这个文件包含了所有的API配置和系统设置
请根据实际情况修改API密钥和配置项
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础配置
class Config:
    """基础配置类"""
    
    # Flask基础配置
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5001))
    
    # 文件路径配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SPOTS_DATA_FILE = os.path.join(BASE_DIR, os.getenv('SPOTS_DATA_FILE', 'spots.json'))
    AUDIO_FOLDER = os.path.join(BASE_DIR, os.getenv('AUDIO_FOLDER', 'static/audio'))
    CACHE_FOLDER = os.path.join(BASE_DIR, os.getenv('CACHE_FOLDER', 'static/cache'))
    
    # 缓存配置
    CACHE_EXPIRE_HOURS = int(os.getenv('CACHE_EXPIRE_HOURS', 24))  # 缓存过期时间（小时）
    
    # TTS 配置
    TTS_CONFIG = {
        'baidu': {
            'api_key': os.getenv('BAIDU_TTS_API_KEY', ''),
            'secret_key': os.getenv('BAIDU_TTS_SECRET_KEY', ''),
            'url': os.getenv('BAIDU_TTS_BASE_URL', 'https://tsn.baidu.com/text2audio')
        },
        'azure': {
            'api_key': os.getenv('AZURE_TTS_API_KEY', ''),
            'region': os.getenv('AZURE_TTS_REGION', ''),
            'url': os.getenv('AZURE_TTS_BASE_URL', 'https://your_region.tts.speech.microsoft.com')
        },
        'local': {
            'engine': 'pyttsx3'  # 本地TTS引擎
        }
    }
    
    # LLM 大模型配置
    LLM_CONFIG = {
        'openai': {
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            'model': 'gpt-3.5-turbo'
        },
        'qianwen': {
            'api_key': os.getenv('QIANWEN_API_KEY', ''),
            'base_url': os.getenv('QIANWEN_BASE_URL', 'https://dashscope.aliyuncs.com/api/v1'),
            'model': 'qwen-turbo'
        },
        'wenxin': {
            'api_key': os.getenv('WENXIN_API_KEY', ''),
            'secret_key': os.getenv('WENXIN_SECRET_KEY', ''),
            'base_url': os.getenv('WENXIN_BASE_URL', 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop'),
            'model': 'ernie-bot-turbo'
        }
    }
    
    # 讲解风格配置
    GUIDE_STYLES = {
        '历史文化': {
            'name': '历史文化',
            'description': '突出历史价值和文化内涵的讲解风格',
            'prompt_template': '请为景点"{spot_name}"生成一段200字左右的历史文化讲解。基础信息：{spot_description}。要求：1）突出历史价值和文化内涵；2）语言生动有趣；3）适合语音播放；4）结尾可以提出一个引导性问题。'
        },
        '趣闻轶事': {
            'name': '趣闻轶事',
            'description': '包含有趣故事和传说的讲解风格',
            'prompt_template': '请为景点"{spot_name}"生成一段200字左右的趣闻轶事讲解。基础信息：{spot_description}。要求：1）包含有趣的历史故事或传说；2）语言轻松幽默；3）适合语音播放；4）让游客产生探索兴趣。'
        },
        '诗词文学': {
            'name': '诗词文学',
            'description': '富有文学色彩和诗词韵味的讲解风格',
            'prompt_template': '请为景点"{spot_name}"生成一段200字左右的诗词文学讲解。基础信息：{spot_description}。要求：1）引用相关古诗词或文学作品；2）富有文学色彩；3）适合语音播放；4）结尾以诗句收尾。'
        },
        '人物故事': {
            'name': '人物故事',
            'description': '以历史人物故事为主的讲解风格',
            'prompt_template': '请为景点"{spot_name}"生成一段200字左右的人物故事讲解。基础信息：{spot_description}。要求：1）讲述与此地相关的历史人物故事；2）情节生动；3）适合语音播放；4）体现人物精神品质。'
        }
    }
    
    # 系统提示词
    SYSTEM_PROMPT = "你是一位专业的旅游讲解员，擅长为游客提供生动有趣的景点讲解。你的讲解应该准确、生动、富有感染力，能够激发游客的兴趣和想象力。"
    
    # 距离阈值配置
    DISTANCE_THRESHOLD = int(os.getenv('DISTANCE_THRESHOLD', 100))  # 米，用户距离景点多少米内触发讲解
    
    # 默认讲解风格
    DEFAULT_GUIDE_STYLE = os.getenv('DEFAULT_GUIDE_STYLE', '历史文化')
    
    DISTANCE_CONFIG = {
        'max_distance': 50.0,      # 最大搜索距离（公里）
        'auto_trigger_distance': 0.1,  # 自动触发距离（公里）
        'nearby_distance': 1.0     # 附近景点距离（公里）
    }

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    
# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    
# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前配置
def get_config(config_name: str = None) -> Config:
    """
    获取配置对象
    
    Args:
        config_name: 配置名称 ('development', 'production')
    
    Returns:
        Config: 配置对象
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config.get(config_name, config['default'])

# 验证配置
def validate_config(config_obj: Config) -> Dict[str, Any]:
    """
    验证配置是否正确
    
    Args:
        config_obj: 配置对象
    
    Returns:
        dict: 验证结果
    """
    result = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    # 检查TTS配置
    tts_enabled = False
    for provider, config_data in config_obj.TTS_CONFIG.items():
        if config_data.get('enabled', False):
            tts_enabled = True
            if provider == 'baidu':
                if config_data['api_key'] == 'your_baidu_api_key':
                    result['warnings'].append(f'百度TTS API密钥未配置')
            elif provider == 'azure':
                if config_data['subscription_key'] == 'your_azure_speech_key':
                    result['warnings'].append(f'Azure TTS API密钥未配置')
    
    if not tts_enabled:
        result['warnings'].append('所有TTS服务都未启用，将使用本地TTS')
    
    # 检查LLM配置
    llm_enabled = False
    for provider, config_data in config_obj.LLM_CONFIG.items():
        if config_data.get('enabled', False):
            llm_enabled = True
            if config_data['api_key'].startswith('your_'):
                result['warnings'].append(f'{provider.upper()} API密钥未配置')
    
    if not llm_enabled:
        result['warnings'].append('所有LLM服务都未启用，将使用默认增强描述')
    
    return result