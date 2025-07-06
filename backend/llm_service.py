# -*- coding: utf-8 -*-
"""
AI语音导览小程序 - LLM服务模块

这个文件提供了增强的大语言模型服务，支持多种LLM提供商和智能内容生成
"""

import json
import time
import hashlib
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import openai
from prompt_templates import get_prompt_for_style, enhance_prompt_with_context

class LLMService:
    """LLM服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config.get('LLM_CONFIG', {})
        self.retry_count = 3
        self.timeout = 30
        
        # 初始化各个LLM客户端
        self._init_openai_client()
        self._init_qianwen_client()
        self._init_wenxin_client()
    
    def _init_openai_client(self):
        """初始化OpenAI客户端"""
        openai_config = self.llm_config.get('openai', {})
        if openai_config.get('api_key'):
            openai.api_key = openai_config['api_key']
            openai.api_base = openai_config.get('base_url', 'https://api.openai.com/v1')
    
    def _init_qianwen_client(self):
        """初始化通义千问客户端"""
        # 通义千问的初始化逻辑
        pass
    
    def _init_wenxin_client(self):
        """初始化文心一言客户端"""
        # 文心一言的初始化逻辑
        pass
    
    def generate_content(self, spot_name: str, spot_description: str, 
                        guide_style: str = '历史文化',
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成景点讲解内容
        
        Args:
            spot_name: 景点名称
            spot_description: 景点描述
            guide_style: 讲解风格
            context: 上下文信息（时间、天气、游客类型等）
        
        Returns:
            dict: 生成结果
        """
        try:
            # 生成Prompt
            prompt_data = get_prompt_for_style(spot_name, spot_description, guide_style)
            
            # 根据上下文增强Prompt
            if context:
                prompt_data['user_prompt'] = enhance_prompt_with_context(
                    prompt_data['user_prompt'], context
                )
            
            # 尝试不同的LLM服务
            providers = ['openai', 'qianwen', 'wenxin']
            
            for provider in providers:
                try:
                    if self._is_provider_available(provider):
                        result = self._call_llm_provider(
                            provider, 
                            prompt_data['system_prompt'], 
                            prompt_data['user_prompt']
                        )
                        
                        if result['success']:
                            return {
                                'success': True,
                                'content': result['content'],
                                'provider': provider,
                                'style': guide_style,
                                'keywords': prompt_data.get('keywords', []),
                                'generation_time': result.get('generation_time', 0)
                            }
                except Exception as e:
                    print(f"LLM提供商 {provider} 调用失败: {e}")
                    continue
            
            # 如果所有LLM都失败，返回增强的默认描述
            enhanced_description = self._enhance_default_description(
                spot_name, spot_description, guide_style
            )
            
            return {
                'success': True,
                'content': enhanced_description,
                'provider': 'fallback',
                'style': guide_style,
                'keywords': [],
                'generation_time': 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'content': spot_description  # 降级到原始描述
            }
    
    def _is_provider_available(self, provider: str) -> bool:
        """检查LLM提供商是否可用"""
        provider_config = self.llm_config.get(provider, {})
        
        if provider == 'openai':
            return bool(provider_config.get('api_key'))
        elif provider == 'qianwen':
            return bool(provider_config.get('api_key'))
        elif provider == 'wenxin':
            return bool(provider_config.get('api_key') and provider_config.get('secret_key'))
        
        return False
    
    def _call_llm_provider(self, provider: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用指定的LLM提供商"""
        start_time = time.time()
        
        try:
            if provider == 'openai':
                result = self._call_openai(system_prompt, user_prompt)
            elif provider == 'qianwen':
                result = self._call_qianwen(system_prompt, user_prompt)
            elif provider == 'wenxin':
                result = self._call_wenxin(system_prompt, user_prompt)
            else:
                raise ValueError(f"不支持的LLM提供商: {provider}")
            
            generation_time = time.time() - start_time
            result['generation_time'] = generation_time
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用OpenAI API"""
        try:
            openai_config = self.llm_config['openai']
            
            response = openai.ChatCompletion.create(
                model=openai_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7,
                timeout=self.timeout
            )
            
            content = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'content': content,
                'usage': response.usage._asdict() if hasattr(response, 'usage') else {}
            }
            
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {e}")
    
    def _call_qianwen(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用通义千问API"""
        try:
            qianwen_config = self.llm_config['qianwen']
            
            headers = {
                'Authorization': f'Bearer {qianwen_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': qianwen_config.get('model', 'qwen-turbo'),
                'input': {
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ]
                },
                'parameters': {
                    'max_tokens': 300,
                    'temperature': 0.7
                }
            }
            
            response = requests.post(
                f"{qianwen_config['base_url']}/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['output']['text'].strip()
                
                return {
                    'success': True,
                    'content': content,
                    'usage': result.get('usage', {})
                }
            else:
                raise Exception(f"API返回错误: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"通义千问API调用失败: {e}")
    
    def _call_wenxin(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用文心一言API"""
        try:
            wenxin_config = self.llm_config['wenxin']
            
            # 首先获取access_token
            access_token = self._get_wenxin_access_token()
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # 合并系统提示词和用户提示词
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            data = {
                'messages': [
                    {'role': 'user', 'content': combined_prompt}
                ],
                'temperature': 0.7,
                'top_p': 0.8,
                'penalty_score': 1.0
            }
            
            response = requests.post(
                f"{wenxin_config['base_url']}/chat/{wenxin_config.get('model', 'ernie-bot-turbo')}?access_token={access_token}",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['result'].strip()
                
                return {
                    'success': True,
                    'content': content,
                    'usage': result.get('usage', {})
                }
            else:
                raise Exception(f"API返回错误: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"文心一言API调用失败: {e}")
    
    def _get_wenxin_access_token(self) -> str:
        """获取文心一言access_token"""
        wenxin_config = self.llm_config['wenxin']
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            'grant_type': 'client_credentials',
            'client_id': wenxin_config['api_key'],
            'client_secret': wenxin_config['secret_key']
        }
        
        response = requests.post(url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['access_token']
        else:
            raise Exception(f"获取access_token失败: {response.text}")
    
    def _enhance_default_description(self, spot_name: str, spot_description: str, guide_style: str) -> str:
        """增强默认描述（当所有LLM都不可用时的降级方案）"""
        
        # 根据风格添加不同的前缀和后缀
        style_enhancements = {
            '历史文化': {
                'prefix': f'欢迎来到{spot_name}，这里承载着深厚的历史文化底蕴。',
                'suffix': '让我们一起感受历史的厚重与文化的魅力。'
            },
            '趣闻轶事': {
                'prefix': f'关于{spot_name}，有着许多有趣的故事等待我们去发现。',
                'suffix': '这些故事让这里变得更加生动有趣。'
            },
            '诗词文学': {
                'prefix': f'{spot_name}自古以来就是文人墨客钟爱之地。',
                'suffix': '在这里，我们可以感受到诗词的韵味和文学的魅力。'
            },
            '人物故事': {
                'prefix': f'在{spot_name}的历史长河中，涌现出许多杰出的人物。',
                'suffix': '他们的故事激励着一代又一代的人们。'
            },
            '科普知识': {
                'prefix': f'{spot_name}蕴含着丰富的科学知识和自然奥秘。',
                'suffix': '让我们用科学的眼光来探索这里的奥秘。'
            },
            '民俗风情': {
                'prefix': f'{spot_name}展现着独特的民俗文化和地方风情。',
                'suffix': '这里的民俗风情让人流连忘返。'
            }
        }
        
        enhancement = style_enhancements.get(guide_style, style_enhancements['历史文化'])
        
        return f"{enhancement['prefix']}{spot_description}{enhancement['suffix']}"
    
    def batch_generate_content(self, spots_data: List[Dict[str, Any]], 
                              guide_styles: List[str] = None) -> Dict[str, Any]:
        """批量生成内容"""
        if guide_styles is None:
            guide_styles = ['历史文化', '趣闻轶事', '诗词文学', '人物故事']
        
        results = {}
        total_spots = len(spots_data)
        total_styles = len(guide_styles)
        
        print(f"开始批量生成内容：{total_spots}个景点 × {total_styles}种风格 = {total_spots * total_styles}个任务")
        
        for i, spot in enumerate(spots_data):
            spot_name = spot['name']
            spot_description = spot['description']
            
            results[spot_name] = {}
            
            for j, style in enumerate(guide_styles):
                try:
                    print(f"正在生成：{spot_name} - {style} ({i*total_styles + j + 1}/{total_spots * total_styles})")
                    
                    result = self.generate_content(spot_name, spot_description, style)
                    
                    if result['success']:
                        results[spot_name][style] = {
                            'content': result['content'],
                            'provider': result['provider'],
                            'keywords': result.get('keywords', []),
                            'generation_time': result.get('generation_time', 0)
                        }
                    else:
                        results[spot_name][style] = {
                            'content': spot_description,
                            'provider': 'fallback',
                            'error': result.get('error', '生成失败')
                        }
                    
                    # 避免API调用过于频繁
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"生成失败：{spot_name} - {style}: {e}")
                    results[spot_name][style] = {
                        'content': spot_description,
                        'provider': 'fallback',
                        'error': str(e)
                    }
        
        return results
    
    def get_content_quality_score(self, content: str, keywords: List[str] = None) -> float:
        """评估内容质量分数"""
        score = 0.0
        
        # 长度评分（180-220字为最佳）
        length = len(content)
        if 180 <= length <= 220:
            score += 30
        elif 150 <= length < 180 or 220 < length <= 250:
            score += 20
        elif 120 <= length < 150 or 250 < length <= 300:
            score += 10
        
        # 关键词覆盖评分
        if keywords:
            keyword_count = sum(1 for keyword in keywords if keyword in content)
            score += (keyword_count / len(keywords)) * 20
        
        # 结构评分（是否有开头、主体、结尾）
        sentences = content.split('。')
        if len(sentences) >= 3:
            score += 20
        elif len(sentences) >= 2:
            score += 10
        
        # 语言流畅度评分（简单的标点符号检查）
        punctuation_count = content.count('，') + content.count('。') + content.count('；')
        if punctuation_count >= 3:
            score += 15
        elif punctuation_count >= 2:
            score += 10
        
        # 情感色彩评分（检查是否包含情感词汇）
        emotion_words = ['美丽', '壮观', '神秘', '古老', '珍贵', '独特', '震撼', '感动', '敬畏']
        emotion_count = sum(1 for word in emotion_words if word in content)
        if emotion_count >= 2:
            score += 15
        elif emotion_count >= 1:
            score += 10
        
        return min(score, 100.0)  # 最高100分

# 全局LLM服务实例
llm_service = None

def init_llm_service(config: Dict[str, Any]):
    """初始化LLM服务"""
    global llm_service
    llm_service = LLMService(config)
    return llm_service

def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    global llm_service
    if llm_service is None:
        raise RuntimeError("LLM服务未初始化，请先调用init_llm_service()")
    return llm_service