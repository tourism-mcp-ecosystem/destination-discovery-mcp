#!/usr/bin/env python3
"""
目的地发现MCP服务器基本测试
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from label_manager import DestinationLabelManager, LanguageCode, TagCategory
from mcp_server import DestinationDiscoveryServer

@pytest.fixture
def label_manager():
    """创建标签管理器fixture"""
    return DestinationLabelManager()

@pytest.fixture
def mcp_server():
    """创建MCP服务器fixture"""
    return DestinationDiscoveryServer()

def test_label_manager_initialization(label_manager):
    """测试标签管理器初始化"""
    assert len(label_manager.tags) > 0
    assert len(label_manager.tag_tries) > 0
    
    # 检查默认标签是否加载
    assert "beach" in label_manager.tags
    assert "mountain" in label_manager.tags
    
    # 检查分类索引
    assert TagCategory.SCENERY in label_manager.category_index
    assert len(label_manager.category_index[TagCategory.SCENERY]) >= 2

def test_tag_search(label_manager):
    """测试标签搜索"""
    # 英文搜索
    tags = label_manager.search_tags_by_prefix("bea", LanguageCode.EN)
    assert len(tags) > 0
    assert any("beach" in tag.get_all_names(LanguageCode.EN) for tag in tags)
    
    # 中文搜索
    tags_zh = label_manager.search_tags_by_prefix("海", LanguageCode.ZH)
    assert len(tags_zh) > 0
    
    # 空搜索
    tags_empty = label_manager.search_tags_by_prefix("xyz", LanguageCode.EN)
    assert len(tags_empty) == 0

def test_destination_operations(label_manager):
    """测试目的地操作"""
    # 添加目的地
    initial_count = len(label_manager.destinations)
    
    # 创建测试目的地
    from label_manager import Destination
    test_dest = Destination(
        id="test:123",
        names={LanguageCode.EN: "Test City", LanguageCode.ZH: "测试城市"},
        tags={"historical": 0.8, "beach": 0.6}
    )
    
    label_manager.add_destination(test_dest)
    assert len(label_manager.destinations) == initial_count + 1
    assert "test:123" in label_manager.destinations
    
    # 搜索目的地
    results = label_manager.search_destinations_by_tags(
        ["historical", "beach"], 
        LanguageCode.EN,
        min_match_score=0.1
    )
    assert len(results) > 0
    
    # 验证匹配分数计算
    dest = label_manager.destinations["test:123"]
    score = label_manager._calculate_tag_match_score(
        dest, ["historical", "beach"], LanguageCode.EN
    )
    assert 0 <= score <= 1

def test_tag_export_import(label_manager, tmp_path):
    """测试标签导出导入"""
    # 导出到临时文件
    export_file = tmp_path / "export_test.json"
    label_manager.export_tags(str(export_file))
    assert export_file.exists()
    
    # 导入到新管理器
    new_manager = DestinationLabelManager()
    # 清空默认标签
    new_manager.tags.clear()
    new_manager.category_index.clear()
    new_manager.tag_tries.clear()
    
    new_manager.import_tags(str(export_file))
    assert len(new_manager.tags) == len(label_manager.tags)
    
    # 验证导入的标签
    assert "beach" in new_manager.tags
    beach_tag = new_manager.tags["beach"]
    assert beach_tag.category == TagCategory.SCENERY
    assert LanguageCode.EN in beach_tag.synonyms

@pytest.mark.asyncio
async def test_mcp_server_tools(mcp_server):
    """测试MCP服务器工具"""
    # 测试标签搜索工具
    from mcp_server import TagSearchRequest
    request = TagSearchRequest(prefix="bea", language="en", limit=5)
    
    tags = await mcp_server.mcp._tools["search_tags_by_prefix"].func(
        request, mcp_server.mcp._tools["search_tags_by_prefix"].ctx
    )
    assert isinstance(tags, list)
    if tags:  # 如果有结果
        assert "id" in tags[0]
        assert "name" in tags[0]
    
    # 测试目的地搜索工具
    from mcp_server import DestinationSearchRequest
    dest_request = DestinationSearchRequest(
        tags=["historical", "culture"],
        language="en",
        min_match_score=0.1,
        limit=3
    )
    
    destinations = await mcp_server.mcp._tools["search_destinations_by_tags"].func(
        dest_request, mcp_server.mcp._tools["search_destinations_by_tags"].ctx
    )
    assert isinstance(destinations, list)
    if destinations:
        assert "id" in destinations[0]
        assert "name" in destinations[0]
        assert "match_score" in destinations[0]

def test_language_code_enum():
    """测试语言代码枚举"""
    assert LanguageCode("zh") == LanguageCode.ZH
    assert LanguageCode("en") == LanguageCode.EN
    assert LanguageCode("ja") == LanguageCode.JA
    
    # 测试不存在的语言代码
    with pytest.raises(ValueError):
        LanguageCode("xx")

def test_tag_category_enum():
    """测试标签分类枚举"""
    assert TagCategory("scenery") == TagCategory.SCENERY
    assert TagCategory("culture") == TagCategory.CULTURE
    assert TagCategory("budget") == TagCategory.BUDGET
    
    # 测试不存在的分类
    with pytest.raises(ValueError):
        TagCategory("invalid")

if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])