from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class ClassicalCitation(BaseModel):
    source: str = Field(..., description="典籍或作品名称")
    original_text: str = Field(..., description="相关原文，无法确认时不得杜撰")
    interpretation: str = Field(..., description="原文与名字之间的联系")


class NameSchema(BaseModel):
    name: str = Field(..., description="候选名称")
    reference: str = Field(..., description="名称的核心出处或创意来源")
    moral: str = Field(..., description="名称寓意")
    pronunciation_analysis: str = Field("", description="声调、音节、朗读感受及谐音分析")
    cultural_analysis: str = Field("", description="国学文化或品牌文化分析")
    five_elements_analysis: str = Field("", description="可选的传统五行分析；信息不足时说明限制")
    brand_analysis: str = Field("", description="行业、竞品差异和品牌调性分析")
    creativity_note: str = Field("", description="宠物或虚拟 IP 的趣味性、记忆点分析")
    citations: list[ClassicalCitation] = Field(default_factory=list, description="可核验的引经据典")
    domain: str = Field("", description="企业/品牌名称建议的纯小写 .com 域名")
    domain_status: str = Field("无需查询", description="域名注册状态")


class NameResultSchema(BaseModel):
    names: list[NameSchema]
    report_summary: str = Field("", description="本轮命名策略与综合结论")
    naming_strategy: list[str] = Field(default_factory=list, description="本轮采用的命名原则")
    disclaimer: str = Field("", description="传统文化推演或外部信息的适用边界")


CategoryLiteral = Literal[
    "人名", "个人/宝宝起名", "宝宝起名",
    "企业名", "商业/品牌起名",
    "宠物名", "宠物/虚拟IP起名", "宠物起名", "虚拟IP起名",
]


class BirthInfo(BaseModel):
    birth_date: str | None = Field(None, description="出生日期，建议 YYYY-MM-DD")
    birth_time: str | None = Field(None, description="出生时间，建议 HH:mm；未知可不填")
    birth_place: str | None = Field(None, description="出生地，用于说明时区和地域语境")
    calendar_type: Literal["公历", "农历"] = "公历"


class NameIn(BaseModel):
    category: CategoryLiteral
    surname: str = Field("", description="个人/宝宝起名时的姓氏")
    gender: Literal["不限", "男", "女"] = "不限"
    person_type: Literal["不限", "男孩", "女孩"] = Field(
        "不限", description="宝宝性别"
    )
    length: str = Field("", description="期望字数")
    other: str | None = Field("", description="其它要求或核心诉求")
    exclude: list[str] = Field(default_factory=list, description="避讳字或排除词")

    # 个人/宝宝起名
    preferred_classics: list[str] = Field(default_factory=lambda: ["诗经", "楚辞"], description="偏好的典籍")
    birth_info: BirthInfo | None = None
    use_bazi: bool = Field(False, description="是否按传统文化角度进行八字五行参考分析")

    # 商业/品牌起名
    industry: str = Field("", description="行业或赛道")
    competitors: list[str] = Field(default_factory=list, description="竞品名称")
    brand_tone: list[str] = Field(default_factory=list, description="品牌调性，如科技感、亲和力")

    # 宠物/虚拟 IP 起名
    ip_type: str = Field("", description="宠物品种、角色类型或虚拟 IP 类型")
    personality: list[str] = Field(default_factory=list, description="性格和形象关键词")

    @model_validator(mode="after")
    def validate_category_fields(self):
        if self.category in {"人名", "个人/宝宝起名", "宝宝起名"} and not self.surname:
            raise ValueError("宝宝起名时必须给定姓氏")
        if self.use_bazi and (not self.birth_info or not self.birth_info.birth_date):
            raise ValueError("启用八字五行参考时，至少需要提供出生日期")
        if self.category in {"企业名", "商业/品牌起名"} and not (self.industry or self.other):
            raise ValueError("商业/品牌起名时必须提供行业或核心诉求")
        if self.person_type == "男孩":
            self.gender = "男"
        elif self.person_type == "女孩":
            self.gender = "女"
        return self


class NameOutSchema(NameResultSchema):
    pass


class NameSchemaWithThreadOut(NameResultSchema):
    thread_id: str


class FeedbackSchema(BaseModel):
    thread_id: str
    category: CategoryLiteral
    feedback: Annotated[str, Field(..., min_length=1, description="用户的修改意见")]
