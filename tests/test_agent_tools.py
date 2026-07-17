"""智能体工具测试"""

import pytest
from backend.app.services.agent_tools import (
    search_cats,
    get_cat_profile,
    get_cat_observations,
    get_recent_encounters,
    recommend_adoption_cats,
    get_attention_cats,
    query_knowledge_base,
)


class TestCatQueryTools:
    """猫咪查询工具测试"""

    def test_search_cats_all(self):
        result = search_cats.invoke({"keyword": "", "coat_color": "", "adoption_status": "", "limit": 10})
        assert "大橘" in result
        assert "芝麻" in result
        assert "共找到" in result

    def test_search_cats_by_color(self):
        result = search_cats.invoke({"keyword": "", "coat_color": "玳瑁", "adoption_status": "", "limit": 10})
        assert "芝麻" in result
        assert "大橘" not in result

    def test_search_cats_by_adoption_status(self):
        result = search_cats.invoke({"keyword": "", "coat_color": "", "adoption_status": "待领养", "limit": 10})
        assert "大橘" in result
        assert "奶茶" not in result

    def test_search_cats_no_result(self):
        result = search_cats.invoke({"keyword": "不存在的猫", "coat_color": "", "adoption_status": "", "limit": 10})
        assert "没有找到" in result

    def test_get_cat_profile_exists(self):
        result = get_cat_profile.invoke({"cat_id": 1})
        assert "大橘" in result
        assert "CAT-20240001" in result
        assert "橘白" in result

    def test_get_cat_profile_not_exists(self):
        result = get_cat_profile.invoke({"cat_id": 999})
        assert "未找到" in result

    def test_get_cat_observations(self):
        result = get_cat_observations.invoke({"cat_id": 1, "limit": 10})
        assert "大橘" not in result
        assert "放松" in result
        assert "图书馆" in result

    def test_get_recent_encounters_all(self):
        result = get_recent_encounters.invoke({"cat_id": 0, "days": 30})
        assert "图书馆" in result
        assert "出现记录" in result

    def test_get_recent_encounters_by_cat(self):
        result = get_recent_encounters.invoke({"cat_id": 2, "days": 30})
        assert "食堂" in result


class TestStatusTools:
    """状态工具测试"""

    def test_get_attention_cats(self):
        result = get_attention_cats.invoke({"limit": 10})
        assert "芝麻" in result
        assert "健康需关注" in result

    def test_get_attention_cats_no_issues(self):
        result = get_attention_cats.invoke({"limit": 10})
        assert len(result) > 0


class TestAdoptionTools:
    """领养推荐工具测试"""

    def test_recommend_adoption_cats(self):
        result = recommend_adoption_cats.invoke({"personality": "", "experience": "", "limit": 3})
        assert "大橘" in result or "黑仔" in result or "花花" in result
        assert "奶茶" not in result

    def test_recommend_adoption_cats_newbie(self):
        result = recommend_adoption_cats.invoke({"personality": "", "experience": "新手", "limit": 3})
        assert "新手" in result or "推荐" in result

    def test_recommend_adoption_cats_by_personality(self):
        result = recommend_adoption_cats.invoke({"personality": "亲人", "experience": "", "limit": 3})
        assert "大橘" in result


class TestKnowledgeTools:
    """知识库工具测试"""

    def test_query_knowledge_base_tnr_exact(self):
        """精确查 TNR"""
        result = query_knowledge_base.invoke({"query": "TNR"})
        assert "TNR" in result or "绝育" in result

    def test_query_knowledge_base_tnr_fuzzy(self):
        """模糊查 TNR：同义词匹配"""
        result = query_knowledge_base.invoke({"query": "流浪猫怎么救助"})
        assert "TNR" in result or "绝育" in result

    def test_query_knowledge_base_adoption_exact(self):
        """精确查领养流程"""
        result = query_knowledge_base.invoke({"query": "领养流程"})
        assert "申请" in result and "领养" in result

    def test_query_knowledge_base_adoption_fuzzy(self):
        """模糊查领养：同义词匹配"""
        result = query_knowledge_base.invoke({"query": "怎么申请领养"})
        assert "申请" in result or "领养" in result

    def test_query_knowledge_base_cloud_adoption(self):
        """云领养查询"""
        result = query_knowledge_base.invoke({"query": "云领养"})
        assert "云领养" in result and "远程" in result

    def test_query_knowledge_base_diet(self):
        """饮食查询"""
        result = query_knowledge_base.invoke({"query": "猫不能吃什么"})
        assert "巧克力" in result or "洋葱" in result or "禁忌" in result

    def test_query_knowledge_base_vaccine(self):
        """疫苗查询"""
        result = query_knowledge_base.invoke({"query": "猫三联"})
        assert "疫苗" in result or "猫瘟" in result or "疱疹" in result

    def test_query_knowledge_base_deworm(self):
        """驱虫查询"""
        result = query_knowledge_base.invoke({"query": "驱虫"})
        assert "驱虫" in result or "体内" in result or "体外" in result

    def test_query_knowledge_base_sterilize(self):
        """绝育查询"""
        result = query_knowledge_base.invoke({"query": "猫绝育"})
        assert "绝育" in result

    def test_query_knowledge_base_behavior(self):
        """行为解读查询"""
        result = query_knowledge_base.invoke({"query": "猫为什么呼噜"})
        assert "呼噜" in result or "放松" in result

    def test_query_knowledge_base_myth(self):
        """误区查询"""
        result = query_knowledge_base.invoke({"query": "猫不能喝牛奶吗"})
        assert "牛奶" in result or "乳糖" in result

    def test_query_knowledge_base_not_found(self):
        """完全无关问题应返回未找到"""
        result = query_knowledge_base.invoke({"query": "火星上有猫吗"})
        assert "暂无" in result or "建议" in result
