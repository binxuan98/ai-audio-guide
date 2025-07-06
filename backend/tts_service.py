# -*- coding: utf-8 -*-
"""
AI语音导览小程序 - TTS语音合成服务模块

这个文件提供了增强的文本转语音服务，支持多种TTS提供商和音频质量优化
"""

import os
import json
import time
import hashlib
import requests
import base64
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import wave
import io

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
    from azure.cognitiveservices.speech.audio import AudioOutputConfig
except ImportError:
    SpeechConfig = None
    SpeechSynthesizer = None
    AudioConfig = None
    AudioOutputConfig = None

class TTSService:
    """TTS语音合成服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tts_config = config.get('TTS_CONFIG', {})
        self.audio_folder = config.get('AUDIO_FOLDER', 'static/audio')
        self.retry_count = 3
        self.timeout = 30
        
        # 确保音频目录存在
        os.makedirs(self.audio_folder, exist_ok=True)
        
        # 初始化各个TTS客户端
        self._init_azure_client()
        self._init_local_tts()
    
    def _init_azure_client(self):
        """初始化Azure TTS客户端"""
        azure_config = self.tts_config.get('azure', {})
        if azure_config.get('api_key') and SpeechConfig:
            try:
                self.azure_speech_config = SpeechConfig(
                    subscription=azure_config['api_key'],
                    region=azure_config.get('region', 'eastus')
                )
                # 设置语音
                self.azure_speech_config.speech_synthesis_voice_name = azure_config.get(
                    'voice_name', 'zh-CN-XiaoxiaoNeural'
                )
            except Exception as e:
                print(f"Azure TTS初始化失败: {e}")
                self.azure_speech_config = None
        else:
            self.azure_speech_config = None
    
    def _init_local_tts(self):
        """初始化本地TTS"""
        if pyttsx3:
            try:
                self.local_tts_engine = pyttsx3.init()
                # 设置语音参数
                self.local_tts_engine.setProperty('rate', 150)  # 语速
                self.local_tts_engine.setProperty('volume', 0.9)  # 音量
                
                # 尝试设置中文语音
                voices = self.local_tts_engine.getProperty('voices')
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                        self.local_tts_engine.setProperty('voice', voice.id)
                        break
            except Exception as e:
                print(f"本地TTS初始化失败: {e}")
                self.local_tts_engine = None
        else:
            self.local_tts_engine = None
    
    def text_to_speech(self, text: str, voice_style: str = 'default', 
                      use_cache: bool = True) -> Dict[str, Any]:
        """
        将文本转换为语音
        
        Args:
            text: 要转换的文本
            voice_style: 语音风格
            use_cache: 是否使用缓存
        
        Returns:
            dict: 转换结果
        """
        try:
            # 生成音频文件名
            text_hash = hashlib.md5(f"{text}_{voice_style}".encode('utf-8')).hexdigest()
            audio_filename = f"audio_{text_hash}.mp3"
            audio_path = os.path.join(self.audio_folder, audio_filename)
            audio_url = f"/static/audio/{audio_filename}"
            
            # 检查缓存
            if use_cache and os.path.exists(audio_path):
                return {
                    'success': True,
                    'audio_url': audio_url,
                    'audio_path': audio_path,
                    'provider': 'cache',
                    'cached': True,
                    'file_size': os.path.getsize(audio_path)
                }
            
            # 尝试不同的TTS服务
            providers = ['azure', 'baidu', 'local']
            
            for provider in providers:
                try:
                    if self._is_tts_provider_available(provider):
                        result = self._call_tts_provider(
                            provider, text, audio_path, voice_style
                        )
                        
                        if result['success']:
                            return {
                                'success': True,
                                'audio_url': audio_url,
                                'audio_path': audio_path,
                                'provider': provider,
                                'cached': False,
                                'file_size': os.path.getsize(audio_path) if os.path.exists(audio_path) else 0,
                                'generation_time': result.get('generation_time', 0)
                            }
                except Exception as e:
                    print(f"TTS提供商 {provider} 调用失败: {e}")
                    continue
            
            # 如果所有TTS都失败，返回错误
            return {
                'success': False,
                'error': '所有TTS服务都不可用',
                'audio_url': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'audio_url': None
            }
    
    def _is_tts_provider_available(self, provider: str) -> bool:
        """检查TTS提供商是否可用"""
        if provider == 'azure':
            return self.azure_speech_config is not None
        elif provider == 'baidu':
            baidu_config = self.tts_config.get('baidu', {})
            return bool(baidu_config.get('api_key') and baidu_config.get('secret_key'))
        elif provider == 'local':
            return self.local_tts_engine is not None
        
        return False
    
    def _call_tts_provider(self, provider: str, text: str, audio_path: str, 
                          voice_style: str = 'default') -> Dict[str, Any]:
        """调用指定的TTS提供商"""
        start_time = time.time()
        
        try:
            if provider == 'azure':
                result = self._call_azure_tts(text, audio_path, voice_style)
            elif provider == 'baidu':
                result = self._call_baidu_tts(text, audio_path, voice_style)
            elif provider == 'local':
                result = self._call_local_tts(text, audio_path, voice_style)
            else:
                raise ValueError(f"不支持的TTS提供商: {provider}")
            
            generation_time = time.time() - start_time
            result['generation_time'] = generation_time
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _call_azure_tts(self, text: str, audio_path: str, voice_style: str = 'default') -> Dict[str, Any]:
        """调用Azure TTS"""
        try:
            if not self.azure_speech_config:
                raise Exception("Azure TTS未正确初始化")
            
            # 根据语音风格选择不同的语音
            voice_map = {
                'default': 'zh-CN-XiaoxiaoNeural',
                'gentle': 'zh-CN-XiaoyiNeural',
                'energetic': 'zh-CN-YunjianNeural',
                'warm': 'zh-CN-XiaochenNeural',
                'professional': 'zh-CN-XiaoxuanNeural'
            }
            
            voice_name = voice_map.get(voice_style, voice_map['default'])
            self.azure_speech_config.speech_synthesis_voice_name = voice_name
            
            # 创建音频配置
            audio_config = AudioOutputConfig(filename=audio_path)
            
            # 创建合成器
            synthesizer = SpeechSynthesizer(
                speech_config=self.azure_speech_config,
                audio_config=audio_config
            )
            
            # 构建SSML
            ssml = self._build_ssml(text, voice_name, voice_style)
            
            # 执行合成
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason.name == 'SynthesizingAudioCompleted':
                return {
                    'success': True,
                    'audio_length': len(result.audio_data) if result.audio_data else 0
                }
            else:
                raise Exception(f"Azure TTS合成失败: {result.reason}")
                
        except Exception as e:
            raise Exception(f"Azure TTS调用失败: {e}")
    
    def _call_baidu_tts(self, text: str, audio_path: str, voice_style: str = 'default') -> Dict[str, Any]:
        """调用百度TTS"""
        try:
            baidu_config = self.tts_config['baidu']
            
            # 获取access_token
            access_token = self._get_baidu_access_token()
            
            # 根据语音风格选择不同的发音人
            voice_map = {
                'default': 0,  # 女声
                'gentle': 1,   # 男声
                'energetic': 3, # 情感男声
                'warm': 4,     # 情感女声
                'professional': 106  # 标准女声
            }
            
            per = voice_map.get(voice_style, 0)
            
            # 构建请求参数
            params = {
                'tex': text,
                'tok': access_token,
                'cuid': 'ai_audio_guide',
                'ctp': 1,  # 客户端类型
                'lan': 'zh',  # 语言
                'spd': 5,  # 语速
                'pit': 5,  # 音调
                'vol': 9,  # 音量
                'per': per,  # 发音人
                'aue': 3   # 音频格式（MP3）
            }
            
            # 发送请求
            response = requests.post(
                baidu_config['url'],
                data=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # 检查返回内容类型
                content_type = response.headers.get('Content-Type', '')
                
                if 'audio' in content_type:
                    # 保存音频文件
                    with open(audio_path, 'wb') as f:
                        f.write(response.content)
                    
                    return {
                        'success': True,
                        'audio_length': len(response.content)
                    }
                else:
                    # 返回的是错误信息
                    error_info = response.json()
                    raise Exception(f"百度TTS返回错误: {error_info}")
            else:
                raise Exception(f"百度TTS请求失败: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"百度TTS调用失败: {e}")
    
    def _call_local_tts(self, text: str, audio_path: str, voice_style: str = 'default') -> Dict[str, Any]:
        """调用本地TTS"""
        try:
            if not self.local_tts_engine:
                raise Exception("本地TTS引擎未初始化")
            
            # 根据语音风格调整参数
            style_settings = {
                'default': {'rate': 150, 'volume': 0.9},
                'gentle': {'rate': 130, 'volume': 0.8},
                'energetic': {'rate': 170, 'volume': 1.0},
                'warm': {'rate': 140, 'volume': 0.85},
                'professional': {'rate': 160, 'volume': 0.9}
            }
            
            settings = style_settings.get(voice_style, style_settings['default'])
            
            # 设置语音参数
            self.local_tts_engine.setProperty('rate', settings['rate'])
            self.local_tts_engine.setProperty('volume', settings['volume'])
            
            # 保存到文件
            self.local_tts_engine.save_to_file(text, audio_path)
            self.local_tts_engine.runAndWait()
            
            # 检查文件是否生成成功
            if os.path.exists(audio_path):
                return {
                    'success': True,
                    'audio_length': os.path.getsize(audio_path)
                }
            else:
                raise Exception("音频文件生成失败")
                
        except Exception as e:
            raise Exception(f"本地TTS调用失败: {e}")
    
    def _get_baidu_access_token(self) -> str:
        """获取百度TTS access_token"""
        baidu_config = self.tts_config['baidu']
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            'grant_type': 'client_credentials',
            'client_id': baidu_config['api_key'],
            'client_secret': baidu_config['secret_key']
        }
        
        response = requests.post(url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['access_token']
        else:
            raise Exception(f"获取百度access_token失败: {response.text}")
    
    def _build_ssml(self, text: str, voice_name: str, voice_style: str = 'default') -> str:
        """构建SSML（Speech Synthesis Markup Language）"""
        
        # 根据风格设置不同的语音参数
        style_settings = {
            'default': {'style': 'general', 'rate': '0%', 'pitch': '0%'},
            'gentle': {'style': 'gentle', 'rate': '-10%', 'pitch': '-5%'},
            'energetic': {'style': 'cheerful', 'rate': '+10%', 'pitch': '+5%'},
            'warm': {'style': 'friendly', 'rate': '0%', 'pitch': '0%'},
            'professional': {'style': 'newscast', 'rate': '0%', 'pitch': '0%'}
        }
        
        settings = style_settings.get(voice_style, style_settings['default'])
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
            <voice name="{voice_name}">
                <mstts:express-as style="{settings['style']}">
                    <prosody rate="{settings['rate']}" pitch="{settings['pitch']}">
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        return ssml.strip()
    
    def batch_generate_audio(self, texts: List[Dict[str, str]], 
                           voice_style: str = 'default') -> Dict[str, Any]:
        """批量生成音频"""
        results = {}
        total_texts = len(texts)
        
        print(f"开始批量生成音频：{total_texts}个文本")
        
        for i, text_data in enumerate(texts):
            text_id = text_data.get('id', f'text_{i}')
            text_content = text_data.get('content', '')
            
            if not text_content:
                continue
            
            try:
                print(f"正在生成音频：{text_id} ({i + 1}/{total_texts})")
                
                result = self.text_to_speech(text_content, voice_style, use_cache=True)
                
                results[text_id] = result
                
                # 避免API调用过于频繁
                time.sleep(0.5)
                
            except Exception as e:
                print(f"音频生成失败：{text_id}: {e}")
                results[text_id] = {
                    'success': False,
                    'error': str(e),
                    'audio_url': None
                }
        
        return results
    
    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """获取音频文件信息"""
        try:
            if not os.path.exists(audio_path):
                return {'exists': False}
            
            file_size = os.path.getsize(audio_path)
            file_mtime = os.path.getmtime(audio_path)
            
            info = {
                'exists': True,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'modified_time': datetime.fromtimestamp(file_mtime).isoformat(),
                'format': os.path.splitext(audio_path)[1].lower()
            }
            
            # 如果是WAV文件，尝试获取更多信息
            if info['format'] == '.wav':
                try:
                    with wave.open(audio_path, 'rb') as wav_file:
                        info.update({
                            'channels': wav_file.getnchannels(),
                            'sample_width': wav_file.getsampwidth(),
                            'frame_rate': wav_file.getframerate(),
                            'frames': wav_file.getnframes(),
                            'duration': wav_file.getnframes() / wav_file.getframerate()
                        })
                except Exception:
                    pass
            
            return info
            
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }
    
    def cleanup_old_audio_files(self, days: int = 7) -> Dict[str, Any]:
        """清理旧的音频文件"""
        try:
            if not os.path.exists(self.audio_folder):
                return {'cleaned': 0, 'total_size': 0}
            
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 3600)
            
            cleaned_count = 0
            total_size = 0
            
            for filename in os.listdir(self.audio_folder):
                if filename.startswith('audio_') and filename.endswith('.mp3'):
                    file_path = os.path.join(self.audio_folder, filename)
                    
                    try:
                        file_mtime = os.path.getmtime(file_path)
                        
                        if file_mtime < cutoff_time:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_count += 1
                            total_size += file_size
                            
                    except Exception as e:
                        print(f"清理文件 {filename} 失败: {e}")
            
            return {
                'cleaned': cleaned_count,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'cleaned': 0,
                'total_size': 0
            }

# 全局TTS服务实例
tts_service = None

def init_tts_service(config: Dict[str, Any]):
    """初始化TTS服务"""
    global tts_service
    tts_service = TTSService(config)
    return tts_service

def get_tts_service() -> TTSService:
    """获取TTS服务实例"""
    global tts_service
    if tts_service is None:
        raise RuntimeError("TTS服务未初始化，请先调用init_tts_service()")
    return tts_service