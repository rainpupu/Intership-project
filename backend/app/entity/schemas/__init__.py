"""
Pydantic 请求/响应模型
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
    # 新增：对齐前端
    UserProfileResponse,
    LoginResponse,
    UpdateProfileRequest,
    CreateAdminRequest,
    UpdateUserRoleRequest,
    UserListQuery,
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

# 猫咪管理
from app.entity.schemas.cat import (
    CatBrief,
    CatResponse,
    CatDetailResponse,
    ObservationResponse,
    EncounterResponse,
    AdoptionApplicationResponse,
    AttentionCatResponse,
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
    # 新增对齐前端
    "UserProfileResponse",
    "LoginResponse",
    "UpdateProfileRequest",
    "CreateAdminRequest",
    "UpdateUserRoleRequest",
    "UserListQuery",
    # 检测
    "DetectionResultItem",
    "DetectionResponse",
    "SceneResponse",
    "AnalyzeRequest",
    "CandidateCat",
    "AnalyzeResponse",
    # 猫咪管理
    "CatBrief",
    "CatResponse",
    "CatDetailResponse",
    "ObservationResponse",
    "EncounterResponse",
    "AdoptionApplicationResponse",
    "AttentionCatResponse",
]