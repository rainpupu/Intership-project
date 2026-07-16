"""
Pydantic 请求/响应模型
用于 API 接口的数据验证和序列化

分层原则：
- Create 模型：创建资源时的请求体
- Update 模型：更新资源时的请求体（所有字段可选）
- Response 模型：API 返回的响应体（过滤敏感字段）
- List 模型：分页列表查询的参数和响应
"""

# 通用模型
from app.entity.schemas.common import ApiResponse, PageParams, PageResponse

# 用户认证与权限
from app.entity.schemas.auth import (
    UserRegister,
    UserLogin,
    UserBrief,
    TokenResponse,
    UserResponse,
    UserUpdate,
    ChangePassword,
    RoleResponse,
    RoleCreate,
    PermissionResponse,
)

# 训练模块
from app.entity.schemas.training import (
    CreateTrainingRequest,
    ValidateModelRequest,
    DatasetValidateRequest,
    DatasetSplitRequest,
    GenerateYamlRequest,
    CreateSceneRequest,
)

# 检测模块
from app.entity.schemas.detection import (
    DetectionResultItem,
    DetectionResponse,
    SceneResponse,
    AnalyzeRequest,
    CandidateCat,
    AnalyzeResponse,
)

# 对话模块
from app.entity.schemas.chat import (
    CreateSessionRequest,
    SendMessageRequest,
    SessionResponse,
)

__all__ = [
    # 通用
    "ApiResponse",
    "PageParams",
    "PageResponse",
    # 认证
    "UserRegister",
    "UserLogin",
    "UserBrief",
    "TokenResponse",
    "UserResponse",
    "UserUpdate",
    "ChangePassword",
    "RoleResponse",
    "RoleCreate",
    "PermissionResponse",
    # 训练
    "CreateTrainingRequest",
    "ValidateModelRequest",
    "DatasetValidateRequest",
    "DatasetSplitRequest",
    "GenerateYamlRequest",
    "CreateSceneRequest",
    "DatasetUploadRequest",
    "AutoLabelRequest",
    "DatasetInfo",
    # 检测
    "DetectionResultItem",
    "DetectionResponse",
    "SceneResponse",
    "AnalyzeRequest",
    "CandidateCat",
    "AnalyzeResponse",
    # 对话
    "CreateSessionRequest",
    "SendMessageRequest",
    "SessionResponse",
]
