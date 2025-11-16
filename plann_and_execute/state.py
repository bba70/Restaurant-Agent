from typing import List, Dict, Optional, Any, TypedDict
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    '''计划步骤'''
    step_id: int = Field(description="计划步骤序号，从1开始")
    subgraph_name: str = Field(description="需要调用的子图名称")
    description: str = Field(description="计划步骤的简短描述")
    input_mapping: Optional[Dict[str, str]] = Field(
        default=None, 
        description="定义如何将之前步骤的输出映射到当前步骤的输入"
    )


class Plan(BaseModel):
    '''计划'''
    steps: List[PlanStep] = Field(description="计划步骤列表")


class OrchestratorState(TypedDict, total=False):
    '''编排器状态'''
    query: str  # 用户查询
    plan: Plan  # 生成的计划
    past_plans: List[str]  # 之前失败的计划
    current_step: int  # 当前执行到的计划步骤序号
    step_results: Dict[int, str]  # 计划步骤序号到结果映射
    error_info: Optional[Dict[str, Any]]  # 错误信息
    replan_count: int  # 重试次数
    final_result: str  # 最终结果
