# 我的城市 · 枣庄新城

一个把常去地点做成交互地图、并支持 AI 问答的小项目。

**在线体验**：https://hometown-map-bnzcbcigyxm3mbahrfwyit.streamlit.app/

**静态版**：https://yebuluoxingcheng.github.io/hometown-map/

## 功能

- 交互地图：4 个地点、5 km 缓冲圈、每个点到几何中心的距离
- AI 问答：根据地点数据回答“附近有什么”“谁最远”；数据里没有的，直接说不知道

## 怎么工作

```
places.csv ──pandas──▶ 距离计算 ──folium──▶ docs/index.html
                                              │
                                    Streamlit ─┴─▶ DeepSeek 问答
```

- 坐标来自高德坐标拾取器（GCJ-02），与高德底图一致，无需转换
- 距离用 haversine 公式，中心取各点经纬度的算术平均
- 问答把地点列表作为上下文传给 `deepseek-chat`，并要求“不知道就说不知道”

## 结果

| 地点 | 类别 | 到中心距离 (km) |
| --- | --- | --- |
| 常去的商场 | 商业 | 0.4 |
| 家 | 家 | 0.9 |
| 枣庄站 | 交通 | 1.8 |
| 高中 | 学校 | 1.8 |

最远的是枣庄站和高中，约 1.8 km；4 个点都在 2 km 范围内。

![地图截图](docs/screenshot.png)

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe hometown_map.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

AI 问答需要在项目根目录放 `.env`：

```
DEEPSEEK_API_KEY=sk-...
```

`.env` 已被 `.gitignore` 排除。

## 目录

```
hometown-map/
├── places.csv         # 地点与经纬度
├── hometown_map.py    # 计算距离、生成地图 HTML
├── app.py             # Streamlit 页面
├── qa.py              # 拼上下文、调用 DeepSeek
├── docs/index.html    # 生成的地图（GitHub Pages 用）
├── metrics.csv        # 距离表
└── requirements.txt
```

## 已知限制

- 单轮对话，模型不记得上一句
- 实体对齐依赖提示词，未做代码级校验：问“三中”仍可能被当成“高中”
- 应用公开，任何人访问都会消耗 API 额度

## 关于

山东科技大学 测绘与空间信息学院 · 地理信息科学 2026 级。
