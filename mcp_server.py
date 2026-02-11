"""
目的地发现MCP服务器 - 修复兼容性版本
基于FastMCP框架,提供旅游目的地发现和标签管理功能
"""

import asyncio
import sys
import json
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

# 数据模型定义
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


# 尝试导入 FastMCP，如果失败则使用模拟版本
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
    print("✅ 使用 FastMCP 框架")
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️  FastMCP 未安装，使用模拟模式")
    
    # 创建模拟的 FastMCP 类
    class FastMCP:
        def __init__(self, name="mock-server"):
            self.name = name
            self._tools = {}
            self._resources = {}
        
        def tool(self, func=None, **kwargs):
            def decorator(f):
                self._tools[f.__name__] = f
                return f
            return decorator(func) if func else decorator
        
        def resource(self, uri):
            def decorator(f):
                self._resources[uri] = f
                return f
            return decorator
        
        def run(self, host="0.0.0.0", port=8000):
            """模拟 run 方法"""
            print(f"模拟服务器运行在 http://{host}:{port}")
            print("可用工具:", list(self._tools.keys()))
            print("可用资源:", list(self._resources.keys()))
            
            # 在模拟模式下，我们不实际启动服务器
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n服务器已停止")


class DestinationDiscoveryServer:
    """目的地发现MCP服务器"""
    
    def __init__(self, name: str = "destination-discovery"):
        self.mcp = FastMCP(name)
        self.label_manager = DestinationLabelManager()
        self._setup_tools()
        self._setup_resources()
        
        # 初始化一些示例数据
        self._initialize_sample_data()
        print(f"✅ 目的地发现服务器 '{name}' 初始化完成")
    
    def _setup_tools(self) -> None:
        """设置MCP工具"""
        
        @self.mcp.tool()
        async def search_tags_by_prefix(
            prefix: str,
            language: str = "en",
            limit: int = 10
        ) -> List[Dict]:
            """
            根据前缀搜索标签
            
            这个工具允许你通过输入前缀来搜索相关的旅游标签。
            例如，搜索"bea"可以找到"beach"相关的标签。
            """
            try:
                lang = LanguageCode(language.lower())
            except ValueError:
                lang = LanguageCode.EN
            
            tags = self.label_manager.search_tags_by_prefix(
                prefix=prefix,
                lang=lang,
                limit=limit
            )
            
            return [
                {
                    "id": tag.id,
                    "name": tag.get_name(lang),
                    "category": tag.category.value,
                    "description": tag.description.get(lang),
                    "synonyms": tag.get_all_names(lang),
                    "weight": tag.weight
                }
                for tag in tags
            ]
        
        @self.mcp.tool()
        async def search_destinations_by_tags(
            tags: List[str],
            language: str = "en",
            min_match_score: float = 0.3,
            limit: int = 20
        ) -> List[Dict]:
            """
            根据标签搜索目的地
            
            使用多个标签来查找匹配的旅游目的地。
            系统会计算每个目的地与查询标签的匹配分数。
            """
            try:
                lang = LanguageCode(language.lower())
            except ValueError:
                lang = LanguageCode.EN
            
            destinations = self.label_manager.search_destinations_by_tags(
                tag_queries=tags,
                lang=lang,
                min_match_score=min_match_score,
                limit=limit
            )
            
            results = []
            for dest in destinations:
                # 计算匹配分数
                match_score = self.label_manager._calculate_tag_match_score(
                    dest, tags, lang
                )
                
                results.append({
                    "id": dest.id,
                    "name": dest.get_name(lang),
                    "names": {k.value: v for k, v in dest.names.items()},
                    "coordinates": dest.coordinates,
                    "country_code": dest.country_code,
                    "administrative_level": dest.administrative_level,
                    "matched_tags": dest.tags,
                    "match_score": round(match_score, 3),
                    "metadata": dest.metadata
                })
            
            return results
        
        @self.mcp.tool()
        async def get_tags_by_category(
            category: str,
            language: str = "en"
        ) -> List[Dict]:
            """
            获取指定分类的所有标签
            """
            try:
                tag_category = TagCategory(category.lower())
                lang = LanguageCode(language.lower())
            except ValueError:
                return []
            
            tags = self.label_manager.get_tags_by_category(tag_category)
            
            return [
                {
                    "id": tag.id,
                    "name": tag.get_name(lang),
                    "category": tag.category.value,
                    "description": tag.description.get(lang),
                    "synonyms": tag.get_all_names(lang),
                    "weight": tag.weight
                }
                for tag in tags
            ]
        
        @self.mcp.tool()
        async def add_destination(
            destination_id: str,
            names: Dict[str, str],
            tags: Dict[str, float],
            coordinates: Optional[Dict[str, float]] = None,
            country_code: Optional[str] = None,
            administrative_level: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            添加新目的地到数据库
            """
            # 转换语言代码
            name_dict = {}
            for lang_str, name in names.items():
                try:
                    lang = LanguageCode(lang_str.lower())
                    name_dict[lang] = name
                except ValueError:
                    continue
            
            destination = Destination(
                id=destination_id,
                names=name_dict,
                coordinates=coordinates,
                country_code=country_code,
                administrative_level=administrative_level,
                tags=tags,
                metadata=metadata or {}
            )
            
            self.label_manager.add_destination(destination)
            
            return {
                "success": True,
                "message": f"目的地 '{destination_id}' 已添加",
                "destination_id": destination_id
            }
        
        @self.mcp.tool()
        async def export_tags_to_file(filepath: str) -> Dict[str, Any]:
            """
            导出标签数据到文件
            """
            try:
                self.label_manager.export_tags(filepath)
                return {
                    "success": True,
                    "message": f"标签数据已导出到 {filepath}",
                    "filepath": filepath
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"导出失败: {str(e)}"
                }
    
    def _setup_resources(self) -> None:
        """设置MCP资源"""
        
        @self.mcp.resource("destinations://categories")
        async def get_tag_categories() -> str:
            """获取所有可用的标签分类"""
            categories = [category.value for category in TagCategory]
            return "\n".join([f"- {cat}" for cat in categories])
        
        @self.mcp.resource("destinations://stats")
        async def get_system_stats() -> str:
            """获取系统统计信息"""
            tag_count = len(self.label_manager.tags)
            dest_count = len(self.label_manager.destinations)
            languages = list(self.label_manager.tag_tries.keys())
            
            return f"""
目的地发现系统统计:
- 标签总数: {tag_count}
- 目的地总数: {dest_count}
- 支持的语言: {', '.join([lang.value for lang in languages])}

可用分类:
{', '.join([cat.value for cat in TagCategory])}
            """
    
    def _initialize_sample_data(self) -> None:
        """初始化示例目的地数据"""
        
        # 添加一些示例目的地
        sample_destinations = [
            Destination(
                id="geoname:1816670",
                names={
                    LanguageCode.EN: "Beijing",
                    LanguageCode.ZH: "北京",
                    LanguageCode.JA: "北京"
                },
                coordinates={"lat": 39.90, "lng": 116.41},
                country_code="CN",
                administrative_level="municipality",
                tags={
                    "historical": 0.95,
                    "culture": 0.9,
                    "family_friendly": 0.7,
                    "luxury": 0.6
                },
                metadata={
                    "population": 21540000,
                    "timezone": "Asia/Shanghai",
                    "famous_for": ["Great Wall", "Forbidden City"]
                }
            ),
            Destination(
                id="geoname:1850147",
                names={
                    LanguageCode.EN: "Tokyo",
                    LanguageCode.ZH: "东京",
                    LanguageCode.JA: "東京"
                },
                coordinates={"lat": 35.68, "lng": 139.76},
                country_code="JP",
                administrative_level="metropolis",
                tags={
                    "culture": 0.85,
                    "luxury": 0.8,
                    "family_friendly": 0.75,
                    "historical": 0.6
                },
                metadata={
                    "population": 13960000,
                    "timezone": "Asia/Tokyo",
                    "famous_for": ["Shibuya Crossing", "Senso-ji Temple"]
                }
            ),
            Destination(
                id="geoname:5128581",
                names={
                    LanguageCode.EN: "New York City",
                    LanguageCode.ZH: "纽约",
                    LanguageCode.JA: "ニューヨーク"
                },
                coordinates={"lat": 40.71, "lng": -74.01},
                country_code="US",
                administrative_level="city",
                tags={
                    "luxury": 0.9,
                    "culture": 0.85,
                    "family_friendly": 0.65
                },
                metadata={
                    "population": 8419000,
                    "timezone": "America/New_York",
                    "famous_for": ["Statue of Liberty", "Times Square"]
                }
            ),
            Destination(
                id="geoname:2643743",
                names={
                    LanguageCode.EN: "London",
                    LanguageCode.ZH: "伦敦",
                    LanguageCode.JA: "ロンドン"
                },
                coordinates={"lat": 51.51, "lng": -0.13},
                country_code="GB",
                administrative_level="city",
                tags={
                    "historical": 0.9,
                    "culture": 0.85,
                    "luxury": 0.7,
                    "family_friendly": 0.7
                },
                metadata={
                    "population": 8900000,
                    "timezone": "Europe/London",
                    "famous_for": ["Big Ben", "British Museum"]
                }
            )
        ]
        
        for dest in sample_destinations:
            self.label_manager.add_destination(dest)
        
        print(f"✅ 已加载 {len(sample_destinations)} 个示例目的地")
    
    def run(self, host: str = "127.0.0.1", port: int = 8080):
        """运行MCP服务器"""
        print("=" * 60)
        print("🚀 目的地发现MCP服务器")
        print("=" * 60)
        print(f"📡 服务器地址: http://{host}:{port}")
        print(f"🔧 运行模式: {'FastMCP' if FASTMCP_AVAILABLE else '模拟模式'}")
        print("-" * 60)
        
        # 显示可用工具
        if hasattr(self.mcp, '_tools'):
            print("🛠️  可用工具:")
            for tool_name in self.mcp._tools.keys():
                print(f"  • {tool_name}")
        else:
            print("🛠️  工具已注册但列表不可用")
        
        # 显示可用资源
        if hasattr(self.mcp, '_resources'):
            print("\n📚 可用资源:")
            for resource_name in self.mcp._resources.keys():
                print(f"  • {resource_name}")
        
        print("-" * 60)
        print("✅ 服务器正在运行...")
        print("📋 使用 Ctrl+C 停止服务器")
        print("=" * 60)
        
        # 启动服务器
        try:
            self.mcp.run()
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            print("💡 提示: 如果使用模拟模式，服务器不会实际监听端口")


# 测试函数
async def test_server_functionality():
    """测试服务器功能"""
    print("\n🧪 测试服务器功能...")
    
    # 创建服务器实例
    server = DestinationDiscoveryServer("test-server")
    
    # 测试1: 搜索标签
    print("\n1. 测试标签搜索:")
    tags = await server.mcp._tools["search_tags_by_prefix"]("bea", "en", 3)
    print(f"   搜索 'bea' 找到 {len(tags)} 个标签:")
    for tag in tags:
        print(f"   - {tag['name']} (分类: {tag['category']})")
    
    # 测试2: 搜索目的地
    print("\n2. 测试目的地搜索:")
    destinations = await server.mcp._tools["search_destinations_by_tags"](
        ["historical", "culture"], "en", 0.1, 2
    )
    print(f"   搜索标签 ['historical', 'culture'] 找到 {len(destinations)} 个目的地:")
    for dest in destinations:
        print(f"   - {dest['name']} (匹配分数: {dest['match_score']:.2f})")
        if dest.get('country_code'):
            print(f"     国家代码: {dest['country_code']}")
    
    # 测试3: 获取分类标签
    print("\n3. 测试获取分类标签:")
    scenery_tags = await server.mcp._tools["get_tags_by_category"]("scenery", "zh")
    print(f"   景观分类标签 ({len(scenery_tags)} 个):")
    for tag in scenery_tags[:3]:  # 只显示前3个
        print(f"   - {tag['name']}")
    
    # 测试4: 添加新目的地
    print("\n4. 测试添加目的地:")
    result = await server.mcp._tools["add_destination"](
        destination_id="test:123",
        names={"en": "Test City", "zh": "测试城市"},
        tags={"historical": 0.8, "beach": 0.6},
        coordinates={"lat": 30.0, "lng": 120.0},
        country_code="CN",
        administrative_level="city"
    )
    print(f"   添加结果: {result['message']}")
    
    # 验证添加的目的地
    new_dest = server.label_manager.destinations.get("test:123")
    if new_dest:
        print(f"   验证: 成功找到目的地 '{new_dest.get_name(LanguageCode.EN)}'")
    
    print("\n✅ 所有功能测试通过!")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="目的地发现MCP服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 默认在 127.0.0.1:8080 启动
  %(prog)s --port 8888        # 在端口 8888 启动
  %(prog)s --host 0.0.0.0     # 监听所有网络接口
  %(prog)s --test             # 运行功能测试
        """
    )
    
    parser.add_argument("--host", default="127.0.0.1",
                       help="服务器监听地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080,
                       help="服务器监听端口 (默认: 8080)")
    parser.add_argument("--test", action="store_true",
                       help="运行功能测试而不启动服务器")
    
    args = parser.parse_args()
    
    if args.test:
        # 运行测试
        asyncio.run(test_server_functionality())
    else:
        # 创建并启动服务器
        server = DestinationDiscoveryServer()
        
        try:
            server.run(host=args.host, port=args.port)
        except KeyboardInterrupt:
            print("\n\n🛑 服务器已停止")
        except Exception as e:
            print(f"\n❌ 服务器运行错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
