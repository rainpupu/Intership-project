# CatTrace Agent Backend

当前后端只提供无数据库版 YOLO 猫咪识别接口，用于前端上传图片后调用本地模型推理。

## 运行

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

服务默认运行在：

```text
http://localhost:8888
```

## 已提供接口

- `GET /api/health`：健康检查。
- `POST /api/recognition/analyze`：上传一张或多张图片，使用 `models/cat_breeds/best.pt` 执行 YOLO 识别。

`POST /api/recognition/analyze` 请求字段：

- `files`: 图片文件数组，表单字段名固定为 `files`。
- `conf_threshold`: 可选，默认 `0.25`。

响应会返回：

- `candidates`: Top 3 YOLO 候选结果。
- `analysis`: 前端分析卡片需要的摘要信息。
- `uploadedImages`: 后端保存的上传图片 URL。
- `detectedCount`: 检测到的目标数量。
- `elapsedMs`: 推理耗时。

## 当前不包含

- 数据库。
- 登录鉴权。
- 猫咪个体身份匹配。
- 出现记录保存。
- 领养业务接口。

训练脚本、评估脚本、训练报告和评估结果已移动到项目根目录的 `yolo_training_artifacts/`。
