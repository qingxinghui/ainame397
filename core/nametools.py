import asyncio
from langchain_deepseek import ChatDeepSeek
import settings
from pydantic import SecretStr
from langchain_core.prompts import ChatPromptTemplate
# 确保你的环境中有这些 schema
# from schemas.agent import NameSchema, NameResultSchema
# from schemas.name import NameIn

# 开发起名智能体
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    # 为了让模型返回数据的时候根据我们给定的格式输出，所以稍微低一点
    temperature=0.5,
    timeout=120
)

system_prompt = """你是一位精通汉语言文学与传统文化的命名专家。请为用户创作富有文化底蕴的人名。
原则：平仄协调，寓意深远，优先从《诗经》《楚辞》或唐诗宋词中汲取灵感。
请给出 5 个候选方案。"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "【姓氏】:{username} 【性别】:{gender} 【字数限制】:{length} 【其它要求】:{other} 【避讳字】:{exclude}")
])

from schemas.name_schemas import NameResultSchema
# with_structured_output 让大模型输出数据的时候，遵守我的格式要求.此处的格式要求是 nanmes:List[NameSchema\NameSchema\NameSchema]
structured_llm = llm.with_structured_output(NameResultSchema)

# 准备好了，大模型
chain = prompt_template | structured_llm

from schemas.name_schemas import NameIn
#  生成名字：用户的要求
async def generate_names(name_info: NameIn):
    # 把list转化成字符串
    exclude_str = '、'.join(name_info.exclude) if name_info.exclude else "无"
    # 访问大模型，最多重试3次。因为大模型有一定的随机性，按照我们给定的格式输出不是100%。
    max_retries = 3
    for attempt in range(max_retries):
        try:
           result = chain.invoke(
                {
                    "username": name_info.username,
                    "gender": name_info.gender,
                    "length": name_info.length,
                    "other": name_info.other,
                    "exclude": exclude_str
                }
            )
           if result is not None:
               return result
           print(f"⚠️ 第 {attempt + 1} 次模型未按规范输出，正在重试...")
        except Exception as e:
            print(e)
    # 如果3次重试都出错，报告错误
    raise ValueError("大模型服务器当前较拥挤或未正确响应，生成失败，请稍后重新点击生成。")

# 测试
async def main():
    name_info = NameIn(
        username="张",
        gender="女",
        length="两字",
        other="希望名字里带点水的意象",
        exclude=["李", "王"]
    )
    names = await generate_names(name_info)
    print("最终结果:", names)


if __name__ == '__main__':
    asyncio.run(main())





