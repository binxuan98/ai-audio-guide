# AI语音导览后端服务

这是AI语音导览小程序的后端服务，基于Flask框架开发，集成了TTS语音合成和LLM大模型功能。

## 🚀 功能特性

- **智能导览**: 根据用户位置自动推荐附近景点
- **个性化讲解**: 支持多种讲解风格（历史文化、趣闻轶事、诗词文学、人物故事）
- **语音合成**: 集成多种TTS服务（百度、Azure、本地pyttsx3）
- **大模型集成**: 支持OpenAI、通义千问、文心一言等LLM服务
- **智能缓存**: 自动缓存生成的内容，提高响应速度
- **距离计算**: 精确计算用户与景点的距离

## 项目结构

```
backend/
├── main.py              # 主应用文件
├── spots.json           # 景点数据文件
├── requirements.txt     # Python 依赖
├── api_example.py       # API 使用示例
└── README.md           # 项目说明
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

## API 接口

### 1. 健康检查

**GET** `/ping`

**响应示例：**
```json
{
  "message": "pong"
}
```

### 2. 获取最近景点

**POST** `/guide`

**请求体：**
```json
{
  "latitude": 39.9042,
  "longitude": 116.4074,
  "enable_tts": true
}
```

**参数说明：**
- `latitude` (必需): 用户纬度 (-90 到 90)
- `longitude` (必需): 用户经度 (-180 到 180)
- `enable_tts` (可选): 是否启用 TTS 功能，默认 false

**成功响应：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "天安门广场",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "description": "天安门广场位于北京市中心...",
    "distance": 0.05,
    "audio_url": null
  },
  "message": "success"
}
```

**错误响应：**
```json
{
  "success": false,
  "message": "错误信息"
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