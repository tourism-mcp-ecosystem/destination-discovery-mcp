"""
目的地标签管理系统
提供高效的多语言标签存储、检索和管理功能
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import defaultdict


class LanguageCode(str, Enum):
    """ISO 639-1 语言代码枚举"""
    ZH = "zh"  # 中文
    EN = "en"  # 英语
    JA = "ja"  # 日语
    KO = "ko"  # 韩语
    FR = "fr"  # 法语
    ES = "es"  # 西班牙语
    DE = "de"  # 德语


class TagCategory(str, Enum):
    """标签分类枚举"""
    SCENERY = "scenery"  # 景观类型
    ACTIVITY = "activity"  # 活动类型
    CULTURE = "culture"  # 文化特色
    CLIMATE = "climate"  # 气候类型
    CROWD = "crowd"  # 人群适合度
    BUDGET = "budget"  # 预算等级
    TRANSPORT = "transport"  # 交通便利度
    FACILITY = "facility"  # 设施完善度


@dataclass
class MultilingualTag:
    """多语言标签数据类"""
    id: str  # 标签唯一标识
    category: TagCategory  # 标签分类
    synonyms: Dict[LanguageCode, List[str]] = field(default_factory=dict)  # 各语言同义词
    description: Dict[LanguageCode, str] = field(default_factory=dict)  # 各语言描述
    weight: float = 1.0  # 标签权重 (用于推荐排序)
    parent_id: Optional[str] = None  # 父标签ID (用于层级关系)
    
    def get_name(self, lang: LanguageCode, default_lang: LanguageCode = LanguageCode.EN) -> str:
        """获取指定语言的标签名称"""
        if self.synonyms.get(lang):
            return self.synonyms[lang][0]  # 返回第一个同义词作为主名称
        elif self.synonyms.get(default_lang):
            return self.synonyms[default_lang][0]
        return self.id  # 回退到ID
    
    def get_all_names(self, lang: LanguageCode) -> List[str]:
        """获取指定语言的所有同义词"""
        return self.synonyms.get(lang, [])


@dataclass
class Destination:
    """目的地数据类"""
    id: str  # 目的地唯一标识 (建议使用GeoNames ID或自定义ID)
    names: Dict[LanguageCode, str] = field(default_factory=dict)  # 多语言名称
    coordinates: Optional[Dict[str, float]] = None  # 经纬度坐标 {"lat": 30.25, "lng": 120.16}
    country_code: Optional[str] = None  # ISO 3166-1 国家代码
    administrative_level: Optional[str] = None  # 行政区划级别 (city, province, etc.)
    tags: Dict[str, float] = field(default_factory=dict)  # 标签ID -> 相关性分数 (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据
    
    def get_name(self, lang: LanguageCode, default_lang: LanguageCode = LanguageCode.EN) -> str:
        """获取指定语言的目的地名称"""
        return self.names.get(lang) or self.names.get(default_lang) or self.id


class TagTrieNode:
    """Trie树节点，用于高效前缀搜索"""
    def __init__(self):
        self.children: Dict[str, 'TagTrieNode'] = {}
        self.tag_ids: Set[str] = set()  # 该节点结束的标签ID集合


class DestinationLabelManager:
    """目的地标签管理器"""
    
    def __init__(self):
        self.tags: Dict[str, MultilingualTag] = {}  # 标签ID -> 标签对象
        self.destinations: Dict[str, Destination] = {}  # 目的地ID -> 目的地对象
        self.tag_tries: Dict[LanguageCode, TagTrieNode] = {}  # 各语言的Trie树
        self.category_index: Dict[TagCategory, Set[str]] = defaultdict(set)  # 分类索引
        self._initialize_default_tags()
    
    def _initialize_default_tags(self) -> None:
        """初始化默认标签库"""
        default_tags = [
            MultilingualTag(
                id="beach",
                category=TagCategory.SCENERY,
                synonyms={
                    LanguageCode.EN: ["beach", "seaside", "coast"],
                    LanguageCode.ZH: ["海滩", "沙滩", "海滨"],
                    LanguageCode.JA: ["ビーチ", "海岸", "浜辺"]
                },
                description={
                    LanguageCode.EN: "Sandy or pebbly shore by the ocean or sea",
                    LanguageCode.ZH: "海洋或湖泊旁的沙滩或砾石滩"
                }
            ),
            MultilingualTag(
                id="mountain",
                category=TagCategory.SCENERY,
                synonyms={
                    LanguageCode.EN: ["mountain", "alpine", "peak"],
                    LanguageCode.ZH: ["山脉", "山峰", "山区"],
                    LanguageCode.JA: ["山", "マウンテン", "山岳"]
                }
            ),
            MultilingualTag(
                id="historical",
                category=TagCategory.CULTURE,
                synonyms={
                    LanguageCode.EN: ["historical", "ancient", "heritage"],
                    LanguageCode.ZH: ["历史古迹", "古迹", "文化遗产"],
                    LanguageCode.JA: ["歴史的", "遺跡", "文化遺産"]
                }
            ),
            MultilingualTag(
                id="family_friendly",
                category=TagCategory.CROWD,
                synonyms={
                    LanguageCode.EN: ["family-friendly", "kids-friendly", "child-friendly"],
                    LanguageCode.ZH: ["适合家庭", "亲子友好", "儿童友好"],
                    LanguageCode.JA: ["家族向け", "子供連れOK", "ファミリー向け"]
                }
            ),
            MultilingualTag(
                id="budget",
                category=TagCategory.BUDGET,
                synonyms={
                    LanguageCode.EN: ["budget", "economical", "affordable"],
                    LanguageCode.ZH: ["经济型", "平价", "实惠"],
                    LanguageCode.JA: ["低予算", "経済的", "手頃"]
                }
            ),
            MultilingualTag(
                id="luxury",
                category=TagCategory.BUDGET,
                synonyms={
                    LanguageCode.EN: ["luxury", "premium", "high-end"],
                    LanguageCode.ZH: ["豪华", "高端", "奢华"],
                    LanguageCode.JA: ["ラグジュアリー", "高級", "贅沢"]
                }
            )
        ]
        
        for tag in default_tags:
            self.add_tag(tag)
    
    def add_tag(self, tag: MultilingualTag) -> None:
        """添加新标签"""
        self.tags[tag.id] = tag
        self.category_index[tag.category].add(tag.id)
        
        # 更新各语言的Trie树
        for lang, names in tag.synonyms.items():
            if lang not in self.tag_tries:
                self.tag_tries[lang] = TagTrieNode()
            
            for name in names:
                self._add_to_trie(name.lower(), tag.id, self.tag_tries[lang])
    
    def _add_to_trie(self, name: str, tag_id: str, root: TagTrieNode) -> None:
        """将标签名称添加到Trie树"""
        node = root
        for char in name:
            if char not in node.children:
                node.children[char] = TagTrieNode()
            node = node.children[char]
        node.tag_ids.add(tag_id)
    
    def search_tags_by_prefix(self, prefix: str, lang: LanguageCode, 
                             limit: int = 10) -> List[MultilingualTag]:
        """根据前缀搜索标签"""
        if lang not in self.tag_tries:
            return []
        
        prefix = prefix.lower()
        node = self.tag_tries[lang]
        
        # 导航到前缀节点
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # 收集所有匹配的标签
        tag_ids = self._collect_tag_ids(node)
        tags = [self.tags[tag_id] for tag_id in tag_ids if tag_id in self.tags]
        
        # 按权重排序并限制数量
        tags.sort(key=lambda t: t.weight, reverse=True)
        return tags[:limit]
    
    def _collect_tag_ids(self, node: TagTrieNode) -> Set[str]:
        """收集节点及其子节点的所有标签ID"""
        result = set(node.tag_ids)
        for child in node.children.values():
            result.update(self._collect_tag_ids(child))
        return result
    
    def add_destination(self, destination: Destination) -> None:
        """添加目的地"""
        self.destinations[destination.id] = destination
    
    def search_destinations_by_tags(self, tag_queries: List[str], 
                                   lang: LanguageCode = LanguageCode.EN,
                                   min_match_score: float = 0.3,
                                   limit: int = 20) -> List[Destination]:
        """
        根据标签搜索目的地
        tag_queries: 标签查询字符串列表
        min_match_score: 最小匹配分数阈值
        """
        results = []
        
        for dest in self.destinations.values():
            match_score = self._calculate_tag_match_score(dest, tag_queries, lang)
            if match_score >= min_match_score:
                results.append((dest, match_score))
        
        # 按匹配分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [dest for dest, score in results[:limit]]
    
    def _calculate_tag_match_score(self, destination: Destination, 
                                  tag_queries: List[str], 
                                  lang: LanguageCode) -> float:
        """计算目的地与标签查询的匹配分数"""
        if not tag_queries or not destination.tags:
            return 0.0
        
        total_score = 0.0
        matched_queries = 0
        
        for query in tag_queries:
            query_lower = query.lower()
            best_tag_score = 0.0
            
            # 查找匹配的标签
            for tag_id, relevance in destination.tags.items():
                if tag_id not in self.tags:
                    continue
                
                tag = self.tags[tag_id]
                tag_names = tag.get_all_names(lang)
                
                # 检查标签名称是否包含查询词
                for name in tag_names:
                    name_lower = name.lower()
                    if query_lower in name_lower:
                        # 完全匹配得分更高
                        score = relevance * (2.0 if query_lower == name_lower else 1.0)
                        best_tag_score = max(best_tag_score, score)
                        break
            
            total_score += best_tag_score
            if best_tag_score > 0:
                matched_queries += 1
        
        # 综合分数：考虑匹配数量和匹配质量
        query_match_ratio = matched_queries / len(tag_queries)
        average_score = total_score / len(tag_queries) if tag_queries else 0
        
        return (query_match_ratio * 0.4) + (average_score * 0.6)
    
    def get_tags_by_category(self, category: TagCategory) -> List[MultilingualTag]:
        """获取指定分类的所有标签"""
        tag_ids = self.category_index.get(category, set())
        return [self.tags[tag_id] for tag_id in tag_ids if tag_id in self.tags]
    
    def export_tags(self, filepath: str) -> None:
        """导出标签数据到JSON文件"""
        data = {
            "tags": {
                tag_id: {
                    "id": tag.id,
                    "category": tag.category.value,
                    "synonyms": {lang.value: syns for lang, syns in tag.synonyms.items()},
                    "description": {lang.value: desc for lang, desc in tag.description.items()},
                    "weight": tag.weight,
                    "parent_id": tag.parent_id
                }
                for tag_id, tag in self.tags.items()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_tags(self, filepath: str) -> None:
        """从JSON文件导入标签数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for tag_id, tag_data in data.get("tags", {}).items():
            tag = MultilingualTag(
                id=tag_data["id"],
                category=TagCategory(tag_data["category"]),
                synonyms={LanguageCode(lang): syns for lang, syns in tag_data.get("synonyms", {}).items()},
                description={LanguageCode(lang): desc for lang, desc in tag_data.get("description", {}).items()},
                weight=tag_data.get("weight", 1.0),
                parent_id=tag_data.get("parent_id")
            )
            self.add_tag(tag)


# 测试用例
if __name__ == "__main__":
    import sys
    
    # 创建标签管理器
    manager = DestinationLabelManager()
    
    # 测试1: 搜索标签
    print("=== 测试1: 标签前缀搜索 ===")
    beach_tags = manager.search_tags_by_prefix("bea", LanguageCode.EN)
    print(f"搜索 'bea' 找到 {len(beach_tags)} 个标签:")
    for tag in beach_tags:
        print(f"  - {tag.get_name(LanguageCode.EN)} (ID: {tag.id})")
    
    # 测试2: 按分类获取标签
    print("\n=== 测试2: 按分类获取标签 ===")
    scenery_tags = manager.get_tags_by_category(TagCategory.SCENERY)
    print(f"景观类标签 ({len(scenery_tags)} 个):")
    for tag in scenery_tags:
        print(f"  - {tag.get_name(LanguageCode.ZH)}")
    
    # 测试3: 添加目的地并搜索
    print("\n=== 测试3: 目的地搜索 ===")
    
    # 创建测试目的地
    hangzhou = Destination(
        id="geoname:1808926",
        names={
            LanguageCode.EN: "Hangzhou",
            LanguageCode.ZH: "杭州",
            LanguageCode.JA: "杭州"
        },
        coordinates={"lat": 30.25, "lng": 120.16},
        country_code="CN",
        administrative_level="city",
        tags={
            "historical": 0.9,
            "mountain": 0.7,
            "family_friendly": 0.8
        },
        metadata={
            "population": 10360000,
            "timezone": "Asia/Shanghai"
        }
    )
    
    manager.add_destination(hangzhou)
    
    # 搜索目的地
    query_tags = ["historical", "mountain", "family"]
    results = manager.search_destinations_by_tags(query_tags, LanguageCode.EN, min_match_score=0.2)
    
    print(f"搜索标签 {query_tags} 找到 {len(results)} 个目的地:")
    for dest in results:
        print(f"  - {dest.get_name(LanguageCode.EN)} (ID: {dest.id})")
        print(f"    标签匹配: {dest.tags}")
    
    # 测试4: 导出导入标签
    print("\n=== 测试4: 标签数据导出导入 ===")
    manager.export_tags("test_tags.json")
    print("标签已导出到 test_tags.json")
    
    # 创建新管理器并导入
    new_manager = DestinationLabelManager()
    new_manager.import_tags("test_tags.json")
    print(f"新管理器加载了 {len(new_manager.tags)} 个标签")
    
    print("\n所有测试完成!")
