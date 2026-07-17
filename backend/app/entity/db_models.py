"""
数据库模型定义
表结构总览：
用户权限：users, roles, permissions, user_roles, role_permissions
检测业务：detection_scenes, detection_tasks, detection_results
模型管理：training_tasks, training_metrics, model_versions
智能体：  chat_sessions, chat_messages
系统运维：operation_logs
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    JSON, Text, Boolean, BigInteger
)
from sqlalchemy.orm import relationship
from app.database.session import Base


# ══════════════════════════════════════════════════════════════
# 一、用户与权限（RBAC）
# ══════════════════════════════════════════════════════════════

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    nickname = Column(String(100), nullable=True, comment="昵称")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar = Column(String(500), nullable=True, comment="头像 URL")
    role = Column(String(20), default="user", nullable=False, index=True, comment="角色：user/admin/super_admin")
    campus_role = Column(String(100), nullable=True, comment="校园角色，如 校园志愿者/平台管理员")
    bio = Column(Text, nullable=True, comment="个人简介")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    detection_tasks = relationship("DetectionTask", back_populates="user")
    training_tasks = relationship("TrainingTask", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    operation_logs = relationship("OperationLog", back_populates="user")


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="角色标识，如 admin/operator/viewer")
    display_name = Column(String(100), nullable=False, comment="角色显示名，如 管理员/操作员/访客")
    description = Column(String(500), nullable=True, comment="角色描述")
    is_system = Column(Boolean, default=False, comment="是否系统内置角色（不可删除）")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, comment="权限编码，如 detection:task:create")
    name = Column(String(100), nullable=False, comment="权限名称")
    module = Column(String(50), nullable=False, comment="所属模块：auth/detection/training/agent/system")
    description = Column(String(500), nullable=True, comment="权限描述")

    # 关联
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class UserRole(Base):
    """用户-角色关联表（多对多）"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


class RolePermission(Base):
    """角色-权限关联表（多对多）"""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, index=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

# ══════════════════════════════════════════════════════════════
# 二、检测业务
# ══════════════════════════════════════════════════════════════

class DetectionScene(Base):
    """检测场景配置表
    每个小组/业务方向一个场景，如：遥感检测、工业缺陷、农业病害等
    场景决定了使用哪个模型、检测哪些类别
    """
    __tablename__ = "detection_scenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment="场景标识，如 remote_sensing")
    display_name = Column(String(100), nullable=False, comment="场景显示名，如 遥感目标检测")
    description = Column(Text, nullable=True, comment="场景描述")
    category = Column(String(50), nullable=False, comment="场景分类：agriculture/industry/remote_sensing/medical/traffic")
    class_names = Column(JSON, nullable=False, comment='类别列表，如 ["airplane","storage-tank"]')
    class_names_cn = Column(JSON, nullable=True, comment='类别中文名映射，如 {"airplane":"飞机"}')
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    detection_tasks = relationship("DetectionTask", back_populates="scene")
    model_versions = relationship("ModelVersion", back_populates="scene")
    training_tasks = relationship("TrainingTask", back_populates="scene")


class DetectionTask(Base):
    """检测任务表 — 每次检测操作生成一条任务记录"""
    __tablename__ = "detection_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="操作用户")
    scene_id = Column(Integer, ForeignKey("detection_scenes.id"), nullable=False, index=True, comment="使用的检测场景")
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=True, comment="使用的模型版本")
    task_type = Column(String(20), nullable=False, comment="检测类型：single/batch/folder/video/camera")
    status = Column(String(20), default="pending", comment="状态：pending/processing/completed/failed")

    # 检测统计
    total_images = Column(Integer, default=0, comment="处理图像总数")
    total_objects = Column(Integer, default=0, comment="检测到目标总数")
    total_inference_time = Column(Float, default=0, comment="总推理耗时（ms）")

    # 检测参数
    conf_threshold = Column(Float, default=0.25, comment="置信度阈值")
    iou_threshold = Column(Float, default=0.45, comment="NMS IoU 阈值")
    image_size = Column(Integer, default=640, comment="推理图像尺寸")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")

    # 分析与建议（AI 生成）
    analysis_report = Column(Text, nullable=True, comment="分析报告（Markdown 格式）")
    analysis_suggestion = Column(Text, nullable=True, comment="专业建议")
    risk_level = Column(String(20), nullable=True, comment="风险等级：low/medium/high/critical")
    analyzed_at = Column(DateTime, nullable=True, comment="分析完成时间")

    created_at = Column(DateTime, default=datetime.now, index=True, comment="创建时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 关联
    user = relationship("User", back_populates="detection_tasks")
    scene = relationship("DetectionScene", back_populates="detection_tasks")
    model_version = relationship("ModelVersion", back_populates="detection_tasks")
    results = relationship("DetectionResult", back_populates="task", cascade="all, delete-orphan")


class DetectionResult(Base):
    """检测结果表 — 每张图像中每个检测到的目标一条记录"""
    __tablename__ = "detection_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("detection_tasks.id"), nullable=False, index=True, comment="所属检测任务")
    image_path = Column(String(500), nullable=False, comment="原始图像路径")
    annotated_image_url = Column(String(500), nullable=True, comment="标注图像 MinIO URL")

    # 单个目标信息
    class_name = Column(String(50), nullable=False, index=True, comment="类别名称")
    class_name_cn = Column(String(50), nullable=True, comment="类别中文名")
    class_id = Column(Integer, nullable=False, comment="类别 ID")
    confidence = Column(Float, nullable=False, comment="置信度 0~1")
    bbox = Column(JSON, nullable=False, comment="边界框 [x1, y1, x2, y2]")

    # 图像级信息（冗余存储，方便查询）
    inference_time = Column(Float, nullable=True, comment="该图推理耗时（ms）")
    image_width = Column(Integer, nullable=True, comment="图像宽度")
    image_height = Column(Integer, nullable=True, comment="图像高度")
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    task = relationship("DetectionTask", back_populates="results")

# ══════════════════════════════════════════════════════════════
# 三、模型管理
# ══════════════════════════════════════════════════════════════

class TrainingTask(Base):
    """模型训练任务表"""
    __tablename__ = "training_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="操作用户")
    scene_id = Column(Integer, ForeignKey("detection_scenes.id"), nullable=False, index=True, comment="关联场景")
    task_uuid = Column(String(100), unique=True, nullable=False, index=True, comment="任务唯一标识")
    status = Column(String(20), default="pending", comment="状态：pending/running/completed/failed/cancelled")

    # 训练配置
    model_name = Column(String(50), default="yolov11n", comment="基础模型：yolov11n/s/m/l/x")
    epochs = Column(Integer, default=100, comment="训练轮数")
    img_size = Column(Integer, default=640, comment="图像尺寸")
    batch_size = Column(Integer, default=16, comment="批次大小")
    device = Column(String(20), default="0", comment="训练设备：0/1/cpu")
    optimizer = Column(String(20), default="SGD", comment="优化器：SGD/Adam/AdamW")
    lr0 = Column(Float, default=0.01, comment="初始学习率")
    augment_config = Column(JSON, nullable=True, comment="数据增强配置")

    # 训练进度
    current_epoch = Column(Integer, default=0, comment="当前轮数")
    progress = Column(Integer, default=0, comment="进度百分比 0~100")

    # 数据集信息
    dataset_path = Column(String(500), nullable=True, comment="数据集路径")
    dataset_size = Column(Integer, nullable=True, comment="数据集图像数量")
    data_yaml = Column(String(500), nullable=True, comment="data.yaml 路径")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="失败错误信息")

    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    started_at = Column(DateTime, nullable=True, comment="开始训练时间")
    completed_at = Column(DateTime, nullable=True, comment="训练完成时间")

    # 关联
    user = relationship("User", back_populates="training_tasks")
    scene = relationship("DetectionScene", back_populates="training_tasks")
    metrics = relationship("TrainingMetric", back_populates="task", cascade="all, delete-orphan")
    model_versions = relationship("ModelVersion", back_populates="training_task")


class TrainingMetric(Base):
    """训练指标表 — 每个 epoch 记录一条，用于绘制训练曲线"""
    __tablename__ = "training_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("training_tasks.id"), nullable=False, index=True, comment="所属训练任务")
    epoch = Column(Integer, nullable=False, comment="当前轮数")

    # 损失值
    box_loss = Column(Float, nullable=True, comment="边界框损失")
    cls_loss = Column(Float, nullable=True, comment="分类损失")
    dfl_loss = Column(Float, nullable=True, comment="DFL 损失")

    # 评估指标
    precision = Column(Float, nullable=True, comment="精确率")
    recall = Column(Float, nullable=True, comment="召回率")
    map50 = Column(Float, nullable=True, comment="mAP@0.50")
    map50_95 = Column(Float, nullable=True, comment="mAP@0.50:0.95")

    # 学习率
    lr = Column(Float, nullable=True, comment="当前学习率")
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    task = relationship("TrainingTask", back_populates="metrics")


class ModelVersion(Base):
    """模型版本管理表 — 每次训练产出或手动上传的模型版本"""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey("detection_scenes.id"), nullable=False, index=True, comment="所属场景")
    training_task_id = Column(Integer, ForeignKey("training_tasks.id"), nullable=True, comment="来源训练任务（可为空，支持手动上传）")
    version = Column(String(50), nullable=False, comment="版本号，如 v1.0.0")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    model_type = Column(String(50), default="yolov11n", comment="模型类型：yolov11n/s/m/l/x")
    status = Column(String(20), default="active", comment="状态：active/archived/deleted")

    # 模型文件
    model_path = Column(String(500), nullable=False, comment="本地模型文件路径")
    minio_url = Column(String(500), nullable=True, comment="MinIO 存储 URL")

    # 评估指标（训练完成后写入）
    map50 = Column(Float, nullable=True, comment="mAP@0.50")
    map50_95 = Column(Float, nullable=True, comment="mAP@0.50:0.95")
    precision = Column(Float, nullable=True, comment="精确率")
    recall = Column(Float, nullable=True, comment="召回率")
    per_class_ap = Column(JSON, nullable=True, comment='各类别 AP，如 {"airplane":0.85,"tank":0.72}')

    # 元信息
    description = Column(Text, nullable=True, comment="版本描述/变更说明")
    file_size = Column(BigInteger, nullable=True, comment="模型文件大小（字节）")
    is_default = Column(Boolean, default=False, comment="是否为该场景的默认模型")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联
    scene = relationship("DetectionScene", back_populates="model_versions")
    training_task = relationship("TrainingTask", back_populates="model_versions")
    detection_tasks = relationship("DetectionTask", back_populates="model_version")

# ══════════════════════════════════════════════════════════════
# 四、智能体对话
# ══════════════════════════════════════════════════════════════

class ChatSession(Base):
    """对话会话表 — 每次对话创建一个会话"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="所属用户")
    session_uuid = Column(String(100), unique=True, nullable=False, index=True, comment="会话唯一标识")
    title = Column(String(200), nullable=True, comment="会话标题（取第一条消息摘要）")
    status = Column(String(20), default="active", comment="状态：active/archived")
    message_count = Column(Integer, default=0, comment="消息数量")
    last_message_at = Column(DateTime, nullable=True, comment="最后消息时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan",
                            order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """对话消息表 — 每条消息（用户/AI/工具调用）一条记录"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True, comment="所属会话")
    role = Column(String(20), nullable=False, comment="消息角色：user/assistant/tool/system")
    content = Column(Text, nullable=False, comment="消息内容")

    # 智能体路由信息
    agent_used = Column(String(50), nullable=True, comment="处理的 Agent：supervisor/detection/analysis/qa")
    tool_calls = Column(JSON, nullable=True, comment='工具调用记录，如 [{"tool":"detect_objects","args":{...}}]')
    tool_result = Column(Text, nullable=True, comment="工具调用返回结果")

    # 元信息
    tokens_used = Column(Integer, nullable=True, comment="Token 消耗量")
    latency_ms = Column(Integer, nullable=True, comment="响应耗时（毫秒）")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="创建时间")

    # 关联
    session = relationship("ChatSession", back_populates="messages")


# ══════════════════════════════════════════════════════════════
# 五、猫咪识别 — 个体档案、出现事件、观察记录、领养
# ══════════════════════════════════════════════════════════════

class Cat(Base):
    """猫咪个体档案表（成员4 设计）"""
    __tablename__ = "cats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="猫咪编号，如 CAT-20240001")
    name = Column(String(50), nullable=False, comment="猫咪名称")
    coat_color = Column(String(20), nullable=False, comment="花色：橘白/玳瑁/三花/纯黑/乳白")
    age_stage = Column(String(10), nullable=False, comment="年龄阶段：幼猫/成年/老年")
    gender = Column(String(6), nullable=False, comment="性别：公/母/未知")
    personality_tags = Column(String(100), nullable=False, comment="性格标签，逗号分隔")
    adoption_status = Column(String(10), nullable=False, default="待领养", comment="领养状态：待领养/观察中/已领养/领养中")
    last_seen_at = Column(DateTime, nullable=False, comment="最近出现日期")
    cover_image_url = Column(String(255), nullable=False, comment="封面图 URL")
    description = Column(Text, nullable=True, comment="简介")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联
    encounters = relationship("Encounter", back_populates="cat")
    observations = relationship("Observation", back_populates="cat", cascade="all, delete-orphan")
    identity_candidates = relationship("IdentityCandidate", back_populates="candidate_cat", cascade="all, delete-orphan")
    adoption_applications = relationship("AdoptionApplication", back_populates="cat", cascade="all, delete-orphan")
    support_orders = relationship("SupportOrder", back_populates="cat", cascade="all, delete-orphan")


class Encounter(Base):
    """猫咪出现事件表 — 合并成员3（视觉识别）与成员4（猫咪管理）"""
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True, comment="关联猫咪")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="记录人")
    title = Column(String(200), nullable=True, comment="事件标题")
    description = Column(Text, nullable=True, comment="事件描述")
    location = Column(String(200), nullable=False, comment="发现地点")
    occurred_at = Column(DateTime, nullable=False, comment="出现时间")
    status = Column(String(20), default="待审核", comment="状态：待审核/已确认/已驳回/analyzing/completed/failed")
    result_analysis = Column(JSON, nullable=True, comment="识别结果快照")

    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    cat = relationship("Cat", back_populates="encounters")
    images = relationship("EncounterImage", back_populates="encounter", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="encounter")
    identity_candidates = relationship("IdentityCandidate", back_populates="encounter", cascade="all, delete-orphan")


class EncounterImage(Base):
    """出现事件中的单张图片 — 合并成员3与成员4"""
    __tablename__ = "encounter_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False, comment="原图 URL")
    cropped_url = Column(String(500), nullable=True, comment="裁剪后的猫咪区域 URL")
    embedding = Column(Text, nullable=True, comment="特征向量（JSON 字符串）")
    bbox = Column(JSON, nullable=True, comment="检测到的猫咪边界框 [x1,y1,x2,y2]")
    is_reference = Column(Boolean, default=False, comment="是否作为识别参考图")
    quality_score = Column(Float, nullable=True, comment="图片质量评分")
    width = Column(Integer, nullable=True, comment="图片宽度")
    height = Column(Integer, nullable=True, comment="图片高度")

    created_at = Column(DateTime, default=datetime.now)

    # 关联
    encounter = relationship("Encounter", back_populates="images")


class Observation(Base):
    """猫咪观察记录表（成员4）"""
    __tablename__ = "cat_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True, comment="关联猫咪")
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, comment="关联出现事件（可选）")
    observed_at = Column(DateTime, nullable=False, comment="观察日期")
    mood_status = Column(String(10), nullable=False, comment="情绪状态：放松/正常/警惕/活泼/紧张/虚弱")
    visible_health_status = Column(String(10), nullable=False, comment="健康状况：良好/需观察/异常")
    notes = Column(Text, nullable=True, comment="观察备注")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联
    cat = relationship("Cat", back_populates="observations")
    encounter = relationship("Encounter", back_populates="observations")


class IdentityCandidate(Base):
    """身份识别候选结果表（成员4）"""
    __tablename__ = "identity_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True, comment="所属事件")
    candidate_cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True, comment="候选猫咪")
    similarity_score = Column(Float, nullable=False, comment="相似度分数")
    ranking = Column(Integer, nullable=False, comment="排名：1/2/3")
    evidence_image_url = Column(String(255), nullable=True, comment="匹配证据图 URL")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联
    encounter = relationship("Encounter", back_populates="identity_candidates")
    candidate_cat = relationship("Cat", back_populates="identity_candidates")


class AdoptionApplication(Base):
    """领养申请表（成员4）"""
    __tablename__ = "adoption_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="申请用户")
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True, comment="申请领养的猫咪")
    applicant_name = Column(String(50), nullable=False, comment="申请人姓名")
    phone = Column(String(20), nullable=False, comment="联系电话")
    address = Column(Text, nullable=True, comment="家庭住址")
    reason = Column(Text, nullable=True, comment="领养理由")
    status = Column(String(20), nullable=False, default="待审核", comment="状态：待审核/已通过/已拒绝")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联
    cat = relationship("Cat", back_populates="adoption_applications")


class SupportOrder(Base):
    """云养猫支持订单表（成员4）"""
    __tablename__ = "support_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户")
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True, comment="支持的猫咪")
    item_name = Column(String(50), nullable=False, comment="物资名称")
    quantity = Column(Integer, default=1, comment="数量")
    amount = Column(Float, default=0, comment="金额")
    status = Column(String(20), nullable=False, default="待支付", comment="状态：待支付/已支付/已发货/已完成")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联
    cat = relationship("Cat", back_populates="support_orders")


# ══════════════════════════════════════════════════════════════
# 六、系统运维
# ══════════════════════════════════════════════════════════════

class OperationLog(Base):
    """操作审计日志表 — 记录用户关键操作"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="操作用户（可为空表示系统操作）")
    username = Column(String(50), nullable=True, comment="冗余用户名，方便查询")

    # 操作信息
    module = Column(String(50), nullable=False, comment="操作模块：auth/detection/training/agent/system")
    action = Column(String(50), nullable=False, comment="操作类型：create/update/delete/login/export")
    target_type = Column(String(50), nullable=True, comment="操作对象类型：user/task/model/session")
    target_id = Column(String(100), nullable=True, comment="操作对象 ID")
    description = Column(String(500), nullable=True, comment="操作描述")

    # 请求信息
    ip_address = Column(String(50), nullable=True, comment="客户端 IP")
    user_agent = Column(String(500), nullable=True, comment="客户端 User-Agent")
    request_method = Column(String(10), nullable=True, comment="HTTP 方法")
    request_path = Column(String(500), nullable=True, comment="请求路径")

    # 结果
    status = Column(String(20), default="success", comment="操作结果：success/failure")
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="创建时间")

    # 关联
    user = relationship("User", back_populates="operation_logs")
