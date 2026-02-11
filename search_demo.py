#!/usr/bin/env python3
"""
目的地发现工具搜索演示脚本
"""

import sys
from mcp_server import DestinationDiscoveryServer, LanguageCode

def main():
    """搜索含有'海滩'和'历史'标签的目的地"""
    
    # 创建服务器实例（会自动加载示例目的地）
    server = DestinationDiscoveryServer()
    
    print("\n" + "="*60)
    print("🔍 搜索含有 '海滩' 和 '历史' 标签的目的地")
    print("="*60)
    
    # 使用中文搜索
    tags_to_search = ["海滩", "历史"]
    lang = LanguageCode.ZH
    min_match_score = 0.1  # 降低阈值以显示可能的结果
    
    print(f"\n📌 搜索条件:")
    print(f"   标签: {tags_to_search}")
    print(f"   语言: 中文")
    print(f"   最小匹配分数: {min_match_score}")
    
    # 执行搜索
    destinations = server.label_manager.search_destinations_by_tags(
        tag_queries=tags_to_search,
        lang=lang,
        min_match_score=min_match_score,
        limit=10
    )
    
    if not destinations:
        print(f"\n❌ 未找到匹配的目的地")
        print("\n💡 提示: 当前系统中缺少包含 '海滩' 标签的目的地")
        print("   建议先添加更多目的地数据")
    else:
        print(f"\n✅ 找到 {len(destinations)} 个匹配的目的地:\n")
        
        for idx, dest in enumerate(destinations, 1):
            # 计算匹配分数
            match_score = server.label_manager._calculate_tag_match_score(
                dest, tags_to_search, lang
            )
            
            print(f"{idx}. {dest.get_name(lang)}")
            print(f"   ID: {dest.id}")
            print(f"   匹配分数: {match_score:.3f}")
            
            if dest.coordinates:
                print(f"   坐标: ({dest.coordinates['lat']}, {dest.coordinates['lng']})")
            
            if dest.country_code:
                print(f"   国家代码: {dest.country_code}")
            
            if dest.tags:
                print(f"   标签:")
                for tag_id, relevance in dest.tags.items():
                    if tag_id in server.label_manager.tags:
                        tag = server.label_manager.tags[tag_id]
                        tag_name = tag.get_name(lang)
                        print(f"      • {tag_name} (相关性: {relevance})")
            
            if dest.metadata:
                print(f"   其他信息:")
                for key, value in dest.metadata.items():
                    if isinstance(value, list):
                        print(f"      • {key}: {', '.join(value)}")
                    else:
                        print(f"      • {key}: {value}")
            
            print()
    
    # 显示系统中所有可用的目的地
    print("\n" + "="*60)
    print("📍 系统中的所有目的地")
    print("="*60 + "\n")
    
    for idx, (dest_id, dest) in enumerate(server.label_manager.destinations.items(), 1):
        print(f"{idx}. {dest.get_name(lang)}")
        print(f"   ID: {dest_id}")
        if dest.tags:
            tag_names = []
            for tag_id in dest.tags.keys():
                if tag_id in server.label_manager.tags:
                    tag = server.label_manager.tags[tag_id]
                    tag_names.append(tag.get_name(lang))
            if tag_names:
                print(f"   标签: {', '.join(tag_names)}")
        print()


if __name__ == "__main__":
    main()
