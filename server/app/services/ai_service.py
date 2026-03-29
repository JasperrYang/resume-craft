"""
AI 服务 - 腾讯云智能体平台调用
核心：简历解析、JD分析、智能改写、对话调整
"""
import json
from datetime import datetime
from bson import ObjectId
import httpx

from app.config import get_settings


class AIService:
    """AI 服务（腾讯云智能体开发平台）"""

    def __init__(self, db):
        self.db = db
        self.settings = get_settings()
        self.base_url = self.settings.AI_PLATFORM_BASE_URL
        self.api_key = self.settings.AI_PLATFORM_API_KEY

    async def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """调用腾讯云智能体平台 API"""
        # TODO: 替换为实际的腾讯云智能体平台API格式
        # 当前使用兼容 OpenAI 格式的调用方式
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "default",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def parse_resume_text(self, raw_text: str) -> dict:
        """简历文本结构化提取"""
        system_prompt = """你是一个简历解析专家。将OCR识别的简历文本解析为结构化JSON。

要求：
1. 严格基于原文提取，不添加任何不存在的信息
2. 无法识别的字段标记为 null
3. 技能关键词尽量拆分为独立项"""

        user_prompt = f"""请将以下简历文本解析为JSON格式：

{raw_text}

输出JSON格式（严格遵守）：
{{
  "basic_info": {{ "name": null, "phone": null, "email": null, "location": null, "birth_year": null, "gender": null }},
  "education": [{{ "school": "", "degree": "", "major": "", "start_date": "", "end_date": "", "gpa": null, "highlights": [] }}],
  "experience": [{{
    "company": "", "title": "", "department": null, "start_date": "", "end_date": "", "is_current": false,
    "description": "", "keywords": [], "metrics": [{{ "text": "", "type": "growth" }}],
    "responsibilities": [], "achievements": []
  }}],
  "projects": [{{ "name": "", "role": "", "start_date": "", "end_date": "", "description": "", "tech_stack": [], "highlights": [] }}],
  "skills": [{{ "name": "", "category": "language|framework|tool|soft_skill", "level": "精通|熟练|了解" }}],
  "certifications": [{{ "name": "", "issuer": null, "date": null }}],
  "additional": {{ "self_assessment": null, "languages": [], "others": null }}
}}"""

        result_text = await self._call_ai(system_prompt, user_prompt)
        return json.loads(result_text)

    async def parse_jd(self, jd_text: str) -> dict:
        """JD 关键词提取与分析"""
        system_prompt = """你是一个招聘需求分析专家。分析职位描述(JD)，提取关键信息并评估各关键词的重要性权重。"""

        user_prompt = f"""分析以下JD，提取关键信息：

{jd_text}

输出JSON格式：
{{
  "company": "公司名称",
  "position": "职位名称",
  "location": "工作地点",
  "salary_range": null,
  "required_skills": [{{ "name": "技能名", "weight": 1到10 }}],
  "preferred_skills": [{{ "name": "技能名", "weight": 1到10 }}],
  "responsibilities": ["职责1", "职责2"],
  "requirements": ["要求1（如学历、年限）"],
  "keywords": [{{ "word": "关键词", "weight": 1到10, "category": "skill|tool|soft_skill|domain" }}]
}}"""

        result_text = await self._call_ai(system_prompt, user_prompt)
        return json.loads(result_text)

    async def analyze_and_rewrite(self, task_id: str) -> None:
        """核心：分析JD + 改写简历"""
        task = await self.db.tasks.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise ValueError("任务不存在")

        # 更新状态
        await self.db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": "analyzing_jd", "updated_at": datetime.utcnow()}},
        )

        # Step 1: 解析JD
        jd_text = task["jd"]["raw_text"]
        jd_analysis = await self.parse_jd(jd_text)

        await self.db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"jd.analysis": jd_analysis, "status": "rewriting"}},
        )

        # Step 2: 读取简历数据
        resume = await self.db.resumes.find_one({"_id": task["resume_id"]})
        resume_data = resume.get("parsed_data", {})

        # Step 3: 智能改写
        system_prompt = """你是一个资深简历优化师。原则是"绝不捏造经历，只做精准翻译"。

改写规则（严格遵守）：
1.【绝对禁止】编造用户没有的经历、技能、项目
2.【绝对禁止】虚构数据指标
3.【允许】调整描述的侧重点，突出与JD匹配的部分
4.【允许】使用STAR法则重新组织语言
5.【允许】添加JD中的关键词（前提是用户确实具备该能力）
6.【允许】调整经历排列顺序，匹配度高的排前面
7.【必须】对JD要求但用户缺失的能力，标注为"缺失项"
8.【必须】每处改动标注改动原因"""

        user_prompt = f"""请基于用户简历和目标JD进行简历优化。

用户简历结构化数据：
{json.dumps(resume_data, ensure_ascii=False, indent=2)}

目标JD分析结果：
{json.dumps(jd_analysis, ensure_ascii=False, indent=2)}

输出JSON格式：
{{
  "optimized_sections": [{{
    "section": "区域名称",
    "section_type": "experience|project|skill|summary",
    "original": "原文",
    "optimized": "改写后",
    "reason": "改动原因",
    "matched_keywords": ["匹配到的JD关键词"]
  }}],
  "match_score": {{
    "before": 0到100,
    "after": 0到100,
    "details": {{
      "skills_match": 0到100,
      "experience_match": 0到100,
      "keyword_match": 0到100,
      "education_match": 0到100
    }}
  }},
  "missing_items": [{{
    "requirement": "JD要求",
    "importance": "high|medium|low",
    "suggestion": "建议"
  }}],
  "tips": ["额外建议"],
  "full_resume_text": "完整的优化后简历纯文本"
}}"""

        result_text = await self._call_ai(system_prompt, user_prompt)
        ai_result = json.loads(result_text)

        # 整理存储格式
        task_result = {
            "match_score": ai_result.get("match_score", {}),
            "optimized_text": ai_result.get("full_resume_text", ""),
            "changes": ai_result.get("optimized_sections", []),
            "missing_items": ai_result.get("missing_items", []),
            "tips": ai_result.get("tips", []),
        }

        # 更新任务结果
        await self.db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "result": task_result,
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    async def chat_adjust(
        self,
        task_id: str,
        user_message: str,
        chat_history: list,
    ) -> dict:
        """对话式调整"""
        task = await self.db.tasks.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise ValueError("任务不存在")

        current_resume = task.get("result", {}).get("optimized_text", "")
        jd_analysis = task.get("jd", {}).get("analysis", {})

        system_prompt = """你是简历优化师，正在帮用户微调简历。

规则：
1. 理解用户意图，进行局部修改
2. 如果用户要求修改事实数据（如数字、公司名），弹出确认提醒
3. 返回修改的diff和更新后的匹配度
4. 绝不主动编造内容"""

        # 构建对话上下文
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in chat_history[-6:]  # 最近6轮
        ])

        user_prompt = f"""当前简历内容：
{current_resume}

目标JD关键词：
{json.dumps(jd_analysis, ensure_ascii=False)}

历史对话：
{history_text}

用户新的调整需求：{user_message}

输出JSON格式：
{{
  "reply": "向用户解释做了什么调整",
  "changes": [{{ "section": "改动位置", "before": "改动前", "after": "改动后" }}],
  "updated_match_score": 0到100,
  "needs_confirmation": false,
  "confirmation_message": "",
  "updated_full_text": "完整更新后的简历文本"
}}"""

        result_text = await self._call_ai(system_prompt, user_prompt)
        return json.loads(result_text)
