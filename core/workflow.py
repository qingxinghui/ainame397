import asyncio
import uuid
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr
from core.tools import check_com_domain
from schemas.name_schemas import NameIn
from schemas.name_schemas import NameResultSchema
import settings


# 定义工作流状态。这个状态是工作流的参数。也可以叫数据清单。是伴随整个流程的
# TypedDict 把我们的python类进行字典校验
class WorkFlowState(TypedDict):
    user_id: int
    category: str
    surname: str
    gender: str
    length: str
    other: str
    exclude: List[str]
    final_output: Dict[str, Any]  # 用来存大模型生成的数据
    thread_id: str
    history_names: str
    feedback: str
    preferred_classics: List[str]
    birth_info: Dict[str, Any]
    use_bazi: bool
    industry: str
    competitors: List[str]
    brand_tone: List[str]
    ip_type: str
    personality: List[str]
    person_type: str


llm = ChatDeepSeek(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0.5
)

# 告诉大模型，输出的格式是怎么的
structured_llm = llm.with_structured_output(NameResultSchema).with_retry(stop_after_attempt=3)


# 定义工作流的节点  这是一个工作流的入口，负责转发任务
async def supervisor_node(state: WorkFlowState):
    """主管节点：后续可在这里扩展意图清洗或记录日志"""
    return {}


def feedback_instruction(state: WorkFlowState) -> str:
    if not state.get("feedback"):
        return ""
    return f"""
    这是一次基于上一轮结果的修改请求。
    上一轮候选及分析：{state.get('history_names', '无')}
    用户最新意见：{state['feedback']}
    请保留用户认可的部分，只调整用户要求修改的内容，并重新给出完整报告。
    """


def result_with_history(response: NameResultSchema) -> Dict[str, Any]:
    history = "\n".join(
        f"【{item.name}】出处：{item.reference}；寓意：{item.moral}"
        for item in response.names
    )
    return {"final_output": response.model_dump(), "history_names": history}


async def human_naming_node(state: WorkFlowState):
    """人名专家节点"""
    birth_info = state.get("birth_info") or {}
    bazi_instruction = "不进行八字五行分析。" if not state.get("use_bazi") else f"""
        请从传统文化角度提供五行参考。出生信息：{birth_info}。
        不得把简化推演表述为确定命理结论；缺少准确时辰时必须明确说明局限。
    """
    prompt = f"""你是一位精通汉语言文学、古典文献和现代汉语音韵的宝宝起名专家。请为新生宝宝创作名字。
        【命名对象】: {state.get('person_type', '不限')}
        【姓氏】: {state['surname']}
        【性别倾向】: {state['gender']}
        【字数限制】: {state['length']}
        【其它具体要求】: {state['other']}
        【避讳排除字】: {'、'.join(state['exclude'])}
        【偏好典籍】: {'、'.join(state.get('preferred_classics') or ['诗经', '楚辞'])}
        【传统五行参考】: {bazi_instruction}
        {feedback_instruction(state)}

        请给出 5 个候选方案并生成详细报告：逐一说明字义、声调音节、常见谐音、文化出处和适用气质。
        引文必须是真实且有把握的原文；无法确认时应明确写“无直接典籍原句”，不得杜撰出处。
        人名无需生成域名，domain 留空、domain_status 写“无需查询”。"""

    response = await  structured_llm.ainvoke(prompt)
    return result_with_history(response)

from core.tools import check_com_domain
from core.rag_service import retrive_user_from_knowledge


async def company_naming_node(state: WorkFlowState):
    """企业品牌节点"""
    # 增加用户的新要求和上次的生成结果到提示词
    # feedback = state.get("feedback")
    # history_names = state.get("history_names")

    user_id = state.get("user_id")
    search_query = " ".join(filter(None, [state.get("industry"), state.get("other")]))

    # 1.查 通过用户的要求和useid查询语义数据库
    rag_context = await asyncio.to_thread(retrive_user_from_knowledge, user_id, search_query)
    # 2.用
    prompt = f"""你是一位精通商业品牌传播的资深顾问。请创作符合商业规范的公司名。
    [用户需求]
    行业/赛道: {state.get('industry') or state.get('other')}
    核心诉求: {state.get('other')}
    已知竞品: {'、'.join(state.get('competitors') or []) or '未提供'}
    品牌调性: {'、'.join(state.get('brand_tone') or []) or '未提供'}
    字数限制: {state['length']}
    避讳排除字: {'、'.join(state['exclude'])}

    【用户的专属私有知识库参考】
    {rag_context}

      {feedback_instruction(state)}
      请给出 5 个候选方案。逐一分析名称辨识度、行业关联、竞品差异、品牌调性、传播与潜在负面联想，
      并给出纯小写 .com 域名建议。不得声称已经完成实时市场或商标检索；竞品结论仅基于用户提供的信息。
     """

    response = await  structured_llm.ainvoke(prompt)
    tasks = [check_com_domain(n.domain) if n.domain else asyncio.sleep(0, result="未提供域名") for n in response.names]
    status = await asyncio.gather(*tasks)

    for n,status in zip(response.names, status):
        n.domain_status = status

    # return {"final_output": response.model_dump()}
    #  "history_names": names_str}  主要是存到数据库，用来下次微调，从数据库中查询出来，给大模型，让他参考这些数据
    return result_with_history(response)


async def pet_naming_node(state: WorkFlowState) -> Dict[str, Any]:
    """宠物起名节点"""
    prompt = f"""你是一位擅长角色塑造、语言节奏和互联网传播的创意命名师。请完成{state.get('category', '宠物或虚拟IP')}任务。
    【宠物/角色类型】: {state.get('ip_type') or '未指定'}
    【宠物特征/性格】: {state['other']}
    【性格与形象关键词】: {'、'.join(state.get('personality') or []) or '未提供'}
    【字数限制】: {state['length']}
    【避讳排除字】: {'、'.join(state['exclude'])}
    {feedback_instruction(state)}

    请给出 5 个候选方案，兼顾趣味、叫喊顺口、角色辨识度、昵称衍生和社交媒体记忆点；
    同时检查明显谐音和负面联想。无需生成域名，domain 留空、domain_status 写“无需查询”。"""
    response = await structured_llm.ainvoke(prompt)
    return result_with_history(response)


# 节点都设计了有4个，如何组成工作流，如何流转
def route_by_category(state: WorkFlowState):
    """条件路由：根据前端传来的 category 决定走哪个节点"""
    category_map = {
        "人名": "human_node", "个人/宝宝起名": "human_node", "宝宝起名": "human_node",
        "企业名": "company_node", "商业/品牌起名": "company_node",
        "宠物名": "pet_node", "宠物/虚拟IP起名": "pet_node",
        "宠物起名": "pet_node", "虚拟IP起名": "pet_node",
    }
    # 人名\企业名\宠物名
    category = state.get("category")
    # human\company\pet
    return category_map.get(category)


workflow = StateGraph(WorkFlowState)
# 第一个节点的名字是supervisor_node
workflow.add_node("supervisor_node", supervisor_node)
# 给起人名的节点起一个名字叫human
workflow.add_node("human", human_naming_node)
workflow.add_node("company", company_naming_node)
workflow.add_node("pet", pet_naming_node)

# 设置工作流的入口
workflow.set_entry_point("supervisor_node")

# 从入口进来后，如何走
workflow.add_conditional_edges("supervisor_node", route_by_category,
                               # { "条件路由函数的返回值" : "目标节点的名称" }
                               {"human_node": "human", "company_node": "company", "pet_node": "pet"})

workflow.add_edge("human", END)
workflow.add_edge("pet", END)
workflow.add_edge("company", END)

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

# 1. 全局初始化：只执行一次，复用连接
# thread_id 存入psotgress
DB_URI = settings.POSTGRES_URI
connection_pool = None
naming_graph = None


async def init_workflow_graph():
    """在 FastAPI 启动时调用此函数来初始化图和连接池"""
    global connection_pool, naming_graph
    connection_pool = AsyncConnectionPool(DB_URI, max_size=10)
    memory = AsyncPostgresSaver(connection_pool)
    # 编译带记忆的智能体
    naming_graph = workflow.compile(checkpointer=memory)


async def close_workflow_graph():
    """在 FastAPI 关闭时清理连接"""
    global connection_pool
    if connection_pool:
        await connection_pool.close()


# 完成起名流程的定义
# naming_graph = workflow.compile()

# 用户传过来的信息  告诉我给什么起名字，这些名字的对应要求有哪些
async def generate_naming(name_info: NameIn, user_id: int):
    workflowsatae = {
        **name_info.model_dump(),
        "user_id": user_id,
        "final_output": {}
    }
    final_state = await  naming_graph.ainvoke(workflowsatae)
    return final_state["final_output"]


async def generate_naming_v2(name_info: NameIn, user_id: int):
    # 生成窗口id
    thread_id = str(uuid.uuid4())
    workflowsatae = {
        **name_info.model_dump(),
        "thread_id": thread_id,
        "user_id": user_id,
        "final_output": {}
    }
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await  naming_graph.ainvoke(workflowsatae, config)
    return {"thread_id": thread_id, "names": final_state["final_output"]}


from schemas.name_schemas import FeedbackSchema


async def feedback_names(name_info: FeedbackSchema, user_id: int):
    # 生成窗口id
    update_state = {
        "feedback": name_info.feedback,
        "category": name_info.category
    }
    config = {"configurable": {"thread_id": name_info.thread_id}}

    snapshot = await naming_graph.aget_state(config)
    if not snapshot.values:
        raise ValueError("起名会话不存在或已经失效")
    if str(snapshot.values.get("user_id")) != str(user_id):
        raise PermissionError("无权访问该起名会话")

    final_state = await  naming_graph.ainvoke(update_state, config)
    return {"thread_id": name_info.thread_id, "names": final_state["final_output"]}





