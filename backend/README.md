# AI语音导览后端服务

基于Flask的AI语音导览后端服务，集成了大语言模型(LLM)和文本转语音(TTS)功能，为用户提供智能化的景点讲解服务。

## 🚀 功能特性

### 核心功能
- **智能定位导览**: 根据用户GPS位置自动推荐最近景点
- **AI内容生成**: 集成多种大语言模型，生成个性化讲解内容
- **多风格讲解**: 支持历史文化、趣闻轶事、诗词文学、人物故事、科普知识、民俗风情等多种讲解风格
- **语音合成**: 集成多种TTS服务，生成高质量语音讲解
- **智能缓存**: 自动缓存生成内容，提升响应速度
- **批量处理**: 支持批量生成景点内容和音频

### 技术特性
- **多LLM支持**: OpenAI GPT、通义千问、文心一言
- **多TTS支持**: Azure语音服务、百度语音、本地TTS
- **RESTful API**: 标准化API接口设计
- **管理接口**: 提供缓存管理、音频文件管理等功能
- **上下文感知**: 支持时间、天气、游客类型等上下文信息

## 📁 项目结构

```
backend/
├── main.py                 # Flask主应用
├── config.py              # 配置文件
├── llm_service.py         # LLM服务模块
├── tts_service.py         # TTS服务模块
├── prompt_templates.py    # Prompt模板管理
├── spots.json            # 景点数据
├── requirements.txt      # 依赖包列表
├── test_api.py          # API测试脚本
├── api_example.py       # API使用示例（旧版）
└── README.md            # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:5000` 启动。

### 3. 测试接口

```bash
python api_example.py
```

## 📚 API接口文档

### 核心接口

#### 1. 获取景点导览
```http
GET /guide?lat={纬度}&lng={经度}&style={讲解风格}&enable_llm={是否启用LLM}&enable_tts={是否启用TTS}
```

**参数说明:**
- `lat`: 用户纬度 (必需)
- `lng`: 用户经度 (必需)
- `style`: 讲解风格，默认"历史文化"
- `enable_llm`: 是否启用LLM生成内容，默认true
- `enable_tts`: 是否启用TTS生成语音，默认true
- `voice_style`: 语音风格，默认"default"
- `time_of_day`: 时间段（morning/afternoon/evening）
- `weather`: 天气情况
- `visitor_type`: 游客类型（family/student/business/tourist）
- `language`: 语言偏好，默认"zh"
- `duration_preference`: 时长偏好（short/medium/long）

**响应示例:**
```json
{
  "success": true,
  "data": {
    "spot_name": "兰州大学",
    "distance": 50.2,
    "content": "兰州大学创建于1909年...",
    "audio_url": "/static/audio/lanzhou_university_history.mp3",
    "style": "历史文化",
    "generated_at": "2024-01-01 12:00:00",
    "voice_style": "default",
    "context": {
      "time_of_day": "afternoon",
      "weather": "sunny",
      "visitor_type": "student"
    }
  },
  "message": "success"
}
```

#### 2. 获取讲解风格列表
```http
GET /guide/styles
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "styles": [
      {
        "key": "历史文化",
        "name": "历史文化",
        "description": "深入挖掘景点的历史背景和文化内涵"
      },
      {
        "key": "趣闻轶事",
        "name": "趣闻轶事",
        "description": "生动有趣的故事和传说"
      }
    ]
  }
}
```

#### 3. 获取语音风格列表
```http
GET /guide/voice-styles
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "styles": [
      {
        "key": "default",
        "name": "标准",
        "description": "标准语音风格，适合大多数场景"
      },
      {
        "key": "gentle",
        "name": "温和",
        "description": "温和亲切的语音风格，适合家庭游客"
      }
    ]
  }
}
```

### 管理接口

#### 1. 批量生成内容
```http
POST /admin/batch-generate
Content-Type: application/json

{
  "styles": ["历史文化", "趣闻轶事"],
  "enable_tts": true,
  "voice_style": "default"
}
```

#### 2. 获取音频文件信息
```http
GET /admin/audio/info
```

#### 3. 清理缓存
```http
POST /admin/clear-cache
```

#### 4. 清理音频文件
```http
POST /admin/audio/cleanup
Content-Type: application/json

{
  "days": 7
}
```

## 景点数据格式

`spots.json` 文件包含景点数据，格式如下：

```json
[
  {
    "id": 1,
    "name": "景点名称",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "description": "景点详细描述",
    "audio_url": null
  }
]
```

## TTS 功能扩展

当前 TTS 功能为示例实现，要启用真实的 TTS 功能，请修改 `text_to_speech` 函数：

```python
def text_to_speech(text: str) -> Optional[str]:
    # 示例：使用百度语音合成 API
    api_url = "https://tsn.baidu.com/text2audio"
    params = {
        "tex": text,
        "tok": "your_access_token",
        "cuid": "your_client_id",
        "ctp": 1,
        "lan": "zh",
        "spd": 5,
        "pit": 5,
        "vol": 5,
        "per": 1
    }
    
    response = requests.post(api_url, data=params)
    if response.status_code == 200:
        # 保存音频文件并返回 URL
        audio_filename = f"audio_{hash(text)}.mp3"
        audio_path = f"static/audio/{audio_filename}"
        
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        
        return f"http://localhost:5000/static/audio/{audio_filename}"
    
    return None
```

## 使用示例

### cURL 示例

```bash
# 获取最近景点
curl -X POST http://localhost:5000/guide \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 39.9042,
    "longitude": 116.4074,
    "enable_tts": false
  }'
```

### Python 示例

```python
import requests

response = requests.post('http://localhost:5000/guide', json={
    'latitude': 39.9042,
    'longitude': 116.4074,
    'enable_tts': True
})

result = response.json()
if result['success']:
    spot = result['data']
    print(f"最近景点: {spot['name']}")
    print(f"距离: {spot['distance']} 公里")
    print(f"描述: {spot['description']}")
else:
    print(f"错误: {result['message']}")
```

## 错误码说明

- `400`: 请求参数错误
- `404`: 未找到景点数据
- `500`: 服务器内部错误

## 开发说明

### 添加新景点

编辑 `spots.json` 文件，添加新的景点数据：

```json
{
  "id": 5,
  "name": "新景点",
  "latitude": 39.9000,
  "longitude": 116.4000,
  "description": "新景点的详细描述",
  "audio_url": null
}
```

### 距离计算

使用 Haversine 公式计算球面距离，精度较高，适合地理位置计算。

### 性能优化

- 对于大量景点数据，可以考虑使用空间索引（如 R-tree）
- 可以添加缓存机制减少文件读取
- 可以使用数据库存储景点数据

## 许可证

MIT License