# -*- coding: utf-8 -*-
"""
AI语音导览小程序 - Prompt模板管理

这个文件包含了所有的Prompt模板和内容生成策略
支持多风格、多场景的个性化讲解内容生成
"""

from typing import Dict, List, Any
import random

# 基础系统提示词
SYSTEM_PROMPTS = {
    'default': """
你是一位专业的AI语音导览员，具有丰富的历史文化知识和生动的讲解技巧。
你的任务是为游客提供准确、有趣、富有感染力的景点讲解。

讲解要求：
1. 内容准确可靠，基于真实的历史文化信息
2. 语言生动有趣，适合语音播放
3. 长度控制在180-220字之间
4. 结构清晰，有开头、主体、结尾
5. 语调亲切自然，如同面对面交流
6. 适当使用修辞手法增强表现力
""",
    
    'professional': """
你是一位资深的文化遗产专家和旅游讲解员，拥有深厚的学术背景。
你擅长将专业知识转化为通俗易懂的讲解内容。

讲解特点：
1. 学术严谨但不失趣味性
2. 注重历史脉络和文化传承
3. 善于引用典故和文献资料
4. 语言优美，富有文化底蕴
""",
    
    'storyteller': """
你是一位擅长讲故事的民间文化传承人，熟知各地的传说故事。
你能够将历史事件和文化现象编织成引人入胜的故事。

讲解特点：
1. 故事性强，情节生动
2. 语言通俗易懂，贴近生活
3. 善用比喻和形象描述
4. 注重情感共鸣和想象空间
"""
}

# 讲解风格模板
GUIDE_STYLE_TEMPLATES = {
    '历史文化': {
        'name': '历史文化',
        'description': '突出历史价值和文化内涵的讲解风格',
        'system_prompt': SYSTEM_PROMPTS['professional'],
        'prompt_template': """
请为景点"{spot_name}"生成一段历史文化讲解。

基础信息：{spot_description}

讲解要求：
1. 突出历史价值和文化内涵
2. 介绍相关的历史背景和文化意义
3. 语言庄重而不失生动
4. 长度控制在180-220字
5. 结尾可以提出一个引导性的思考问题

请直接输出讲解内容，不要包含其他说明文字。
""",
        'keywords': ['历史', '文化', '传承', '价值', '意义', '背景']
    },
    
    '趣闻轶事': {
        'name': '趣闻轶事',
        'description': '包含有趣故事和传说的讲解风格',
        'system_prompt': SYSTEM_PROMPTS['storyteller'],
        'prompt_template': """
请为景点"{spot_name}"生成一段趣闻轶事讲解。

基础信息：{spot_description}

讲解要求：
1. 包含有趣的历史故事、传说或轶事
2. 语言轻松幽默，富有故事性
3. 能够激发游客的好奇心和探索欲
4. 长度控制在180-220字
5. 结尾留下悬念或引发思考

请直接输出讲解内容，不要包含其他说明文字。
""",
        'keywords': ['故事', '传说', '轶事', '趣闻', '神秘', '传奇']
    },
    
    '诗词文学': {
        'name': '诗词文学',
        'description': '富有文学色彩和诗词韵味的讲解风格',
        'system_prompt': SYSTEM_PROMPTS['professional'],
        'prompt_template': """
请为景点"{spot_name}"生成一段诗词文学讲解。

基础信息：{spot_description}

讲解要求：
1. 引用相关的古诗词或文学作品
2. 语言优美，富有文学色彩
3. 体现诗词的意境和美感
4. 长度控制在180-220字
5. 结尾以诗句或优美的文学语言收尾

请直接输出讲解内容，不要包含其他说明文字。
""",
        'keywords': ['诗词', '文学', '意境', '韵味', '美感', '雅致']
    },
    
    '人物故事': {
        'name': '人物故事',
        'description': '以历史人物故事为主的讲解风格',
        'system_prompt': SYSTEM_PROMPTS['storyteller'],
        'prompt_template': """
请为景点"{spot_name}"生成一段人物故事讲解。

基础信息：{spot_description}

讲解要求：
1. 讲述与此地相关的历史人物故事
2. 突出人物的精神品质和历史贡献
3. 情节生动，富有感染力
4. 长度控制在180-220字
5. 体现人物的时代价值和现实意义

请直接输出讲解内容，不要包含其他说明文字。
""",
        'keywords': ['人物', '故事', '精神', '品质', '贡献', '传奇']
    },
    
    '科普知识': {
        'name': '科普知识',
        'description': '注重科学知识和自然现象的讲解风格',
        'system_prompt': SYSTEM_PROMPTS['professional'],
        'prompt_template': """
请为景点"{spot_name}"生成一段科普知识讲解。

基础信息：{spot_description}

讲解要求：
1. 介绍相关的科学知识或自然现象
2. 语言通俗易懂，深入浅出
3. 激发游客的科学兴趣
4. 长度控制在180-220字
5. 结尾可以提出科学思考问题

请直接输出讲解内容，不要包含其他说明文字。
""",
        'keywords': ['科学', '知识', '现象', '原理', '探索', '发现']
    },
    
    '民俗风情': {
        'name': '民俗风情',
        'description': '展现当地民俗文化和风土人情的讲解风格',
        'system_prompt': SYSTEM_PROMPTS['storyteller'],
        'prompt_template': """
请为景点"{spot_name}"生成一段民俗风情讲解。

基础信息：{spot_description}

讲解要求：
1. 介绍当地的民俗文化和风土人情
2. 体现地域特色和文化差异
3. 语言亲切自然，贴近生活
4. 长度控制在180-220字
5. 让游客感受到浓厚的地方文化氛围

请直接输出讲解内容，不要包含其他说明文字。
""",
        'keywords': ['民俗', '风情', '文化', '传统', '特色', '生活']
    }
}

# 场景化提示词
SCENE_PROMPTS = {
    'morning': {
        'name': '晨间时光',
        'prefix': '在这个美好的清晨，',
        'suffix': '让我们在晨光中感受这里的宁静与美好。'
    },
    'afternoon': {
        'name': '午后阳光',
        'prefix': '午后的阳光洒在',
        'suffix': '在这温暖的午后，让时光在这里慢慢流淌。'
    },
    'evening': {
        'name': '黄昏时分',
        'prefix': '夕阳西下，',
        'suffix': '在这黄昏时分，让我们静静感受历史的回响。'
    },
    'night': {
        'name': '夜幕降临',
        'prefix': '夜幕降临，',
        'suffix': '在这静谧的夜晚，让我们聆听历史的低语。'
    }
}

# 情感色彩模板
EMOTION_TEMPLATES = {
    'peaceful': {
        'name': '宁静祥和',
        'adjectives': ['宁静的', '祥和的', '安详的', '静谧的'],
        'verbs': ['静静地', '轻柔地', '缓缓地', '悠然地']
    },
    'magnificent': {
        'name': '雄伟壮观',
        'adjectives': ['雄伟的', '壮观的', '磅礴的', '恢宏的'],
        'verbs': ['巍然屹立', '气势磅礴', '雄伟壮观', '蔚为壮观']
    },
    'mysterious': {
        'name': '神秘莫测',
        'adjectives': ['神秘的', '莫测的', '幽深的', '玄妙的'],
        'verbs': ['神秘地', '悄然地', '隐约地', '若隐若现']
    },
    'romantic': {
        'name': '浪漫诗意',
        'adjectives': ['浪漫的', '诗意的', '优雅的', '唯美的'],
        'verbs': ['轻舞飞扬', '诗意盎然', '浪漫多情', '如诗如画']
    }
}

# 动态内容生成器
class PromptGenerator:
    """Prompt生成器"""
    
    def __init__(self):
        self.style_templates = GUIDE_STYLE_TEMPLATES
        self.scene_prompts = SCENE_PROMPTS
        self.emotion_templates = EMOTION_TEMPLATES
    
    def generate_prompt(self, spot_name: str, spot_description: str, 
                       guide_style: str = '历史文化', 
                       scene: str = None, 
                       emotion: str = None,
                       custom_requirements: List[str] = None) -> Dict[str, str]:
        """
        生成个性化的Prompt
        
        Args:
            spot_name: 景点名称
            spot_description: 景点描述
            guide_style: 讲解风格
            scene: 场景（可选）
            emotion: 情感色彩（可选）
            custom_requirements: 自定义要求（可选）
        
        Returns:
            dict: 包含system_prompt和user_prompt的字典
        """
        # 获取风格模板
        style_config = self.style_templates.get(guide_style, self.style_templates['历史文化'])
        
        # 构建系统提示词
        system_prompt = style_config['system_prompt']
        
        # 构建用户提示词
        user_prompt = style_config['prompt_template'].format(
            spot_name=spot_name,
            spot_description=spot_description
        )
        
        # 添加场景化内容
        if scene and scene in self.scene_prompts:
            scene_config = self.scene_prompts[scene]
            user_prompt += f"\n\n场景要求：{scene_config['prefix']}...{scene_config['suffix']}"
        
        # 添加情感色彩
        if emotion and emotion in self.emotion_templates:
            emotion_config = self.emotion_templates[emotion]
            user_prompt += f"\n\n情感色彩：请使用{emotion_config['name']}的语言风格。"
        
        # 添加自定义要求
        if custom_requirements:
            user_prompt += "\n\n额外要求：\n" + "\n".join([f"- {req}" for req in custom_requirements])
        
        return {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'style': guide_style,
            'keywords': style_config.get('keywords', [])
        }
    
    def get_available_styles(self) -> List[Dict[str, str]]:
        """
        获取可用的讲解风格列表
        
        Returns:
            list: 风格列表
        """
        styles = []
        for key, config in self.style_templates.items():
            styles.append({
                'key': key,
                'name': config['name'],
                'description': config['description']
            })
        return styles
    
    def get_random_scene(self) -> str:
        """
        随机获取一个场景
        
        Returns:
            str: 场景key
        """
        return random.choice(list(self.scene_prompts.keys()))
    
    def get_random_emotion(self) -> str:
        """
        随机获取一个情感色彩
        
        Returns:
            str: 情感key
        """
        return random.choice(list(self.emotion_templates.keys()))

# 全局实例
prompt_generator = PromptGenerator()

# 导出函数
def get_prompt_for_style(spot_name: str, spot_description: str, guide_style: str) -> Dict[str, str]:
    """
    为指定风格生成Prompt
    
    Args:
        spot_name: 景点名称
        spot_description: 景点描述
        guide_style: 讲解风格
    
    Returns:
        dict: Prompt字典
    """
    return prompt_generator.generate_prompt(spot_name, spot_description, guide_style)

def get_available_guide_styles() -> List[Dict[str, str]]:
    """
    获取可用的讲解风格
    
    Returns:
        list: 风格列表
    """
    return prompt_generator.get_available_styles()

def enhance_prompt_with_context(base_prompt: str, context: Dict[str, Any]) -> str:
    """
    根据上下文增强Prompt
    
    Args:
        base_prompt: 基础Prompt
        context: 上下文信息
    
    Returns:
        str: 增强后的Prompt
    """
    enhanced_prompt = base_prompt
    
    # 添加时间上下文
    if 'time_of_day' in context:
        time_context = {
            'morning': '在这个清新的早晨',
            'afternoon': '在这个温暖的午后',
            'evening': '在这个美丽的黄昏',
            'night': '在这个宁静的夜晚'
        }
        if context['time_of_day'] in time_context:
            enhanced_prompt += f"\n\n时间背景：{time_context[context['time_of_day']]}，请在讲解中体现相应的时间氛围。"
    
    # 添加天气上下文
    if 'weather' in context:
        weather_context = {
            'sunny': '阳光明媚',
            'cloudy': '云雾缭绕',
            'rainy': '细雨蒙蒙',
            'snowy': '雪花纷飞'
        }
        if context['weather'] in weather_context:
            enhanced_prompt += f"\n\n天气背景：{weather_context[context['weather']]}，请在讲解中融入相应的天气元素。"
    
    # 添加游客类型上下文
    if 'visitor_type' in context:
        visitor_context = {
            'family': '适合家庭游客，语言亲切温馨',
            'student': '适合学生群体，注重知识性和教育意义',
            'elderly': '适合老年游客，语速适中，内容丰富',
            'young': '适合年轻游客，语言活泼有趣'
        }
        if context['visitor_type'] in visitor_context:
            enhanced_prompt += f"\n\n游客特点：{visitor_context[context['visitor_type']]}。"
    
    return enhanced_prompt