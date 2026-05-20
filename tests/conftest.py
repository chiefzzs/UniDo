"""
测试配置文件 - 实现测试环境自动清理

功能：
1. 测试前清理：每个测试开始前清理环境数据
2. 保护报告目录：tests/report/目录不会被清理
3. 生成测试报告：记录测试点、输入、输出、持久化数据
4. 测试数据分离：使用 src/data/test 作为测试数据目录
5. 自动收集：自动收集持久化数据、文件操作记录、事件数据等
"""

import os
import shutil
import json
import pytest
from datetime import datetime
from pathlib import Path

# 设置测试环境
os.environ['STORAGE_ENV'] = 'test'

# 需要清理的目录
TEST_DATA_DIRS = [
    "src/data/test",
    "storage",
    ".pytest_cache",
]

# 需要保护的目录（不清理）
PROTECTED_DIRS = [
    "tests/report",
    "src/data/dev",
]

# 持久化数据文件映射
DATA_FILES_MAP = {
    'projects': 'projects.json',
    'sessions': 'sessions.json',
    'dialogs': 'dialogs.json',
    'messages': 'messages.json',
    'task_groups': 'task_groups.json',
    'tasks': 'tasks.json',
    'llm_calls': 'llm_calls.json',
    'tool_calls': 'tool_calls.json',
    'events': 'events.json',
    'prompts': 'prompts.json',
    'workspace_configs': 'workspace_configs.json',
    'model_configs': 'model_configs.json',
    'tool_configs': 'tool_configs.json',
}

def cleanup_test_data():
    """清理测试数据目录（保护src/report目录）"""
    base_dir = Path(__file__).parent.parent.resolve()
    
    for dir_name in TEST_DATA_DIRS:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            # 检查是否在保护列表中
            protected = False
            for protected_dir in PROTECTED_DIRS:
                protected_path = base_dir / protected_dir
                if str(dir_path).startswith(str(protected_path)):
                    protected = True
                    break
            
            if not protected:
                try:
                    if dir_path.is_dir():
                        shutil.rmtree(dir_path)
                        print(f"已清理目录: {dir_path}")
                    else:
                        dir_path.unlink()
                        print(f"已清理文件: {dir_path}")
                except Exception as e:
                    print(f"警告：清理 {dir_path} 时出错: {e}")


class TestDataCollector:
    """测试数据收集器 - 收集所有相关的持久化数据（通用机制）"""
    
    @staticmethod
    def get_data_dir():
        """获取测试数据目录路径"""
        base_dir = Path(__file__).parent.parent.resolve()
        return base_dir / "src" / "data" / "test"
    
    @staticmethod
    def collect_all_persistent_data(include_empty=True):
        """收集所有相关的持久化数据
        
        Args:
            include_empty: 是否包含空的实体类型（记录类型但内容为空列表）
        """
        from services.L1_infrastructure.L1b_persistence.persistence_service import get_persistence_service
        
        persistence = get_persistence_service()
        data = {}
        
        # 收集各类型的数据
        entity_types = list(DATA_FILES_MAP.keys())
        
        for entity_type in entity_types:
            try:
                items = persistence.list(entity_type)
                if items:
                    data[entity_type] = items
                elif include_empty:
                    data[entity_type] = []
            except Exception as e:
                print(f"警告：收集 {entity_type} 数据时出错: {e}")
                if include_empty:
                    data[entity_type] = []
        
        return data
    
    @staticmethod
    def collect_filtered_data(filters):
        """收集过滤后的持久化数据
        
        Args:
            filters: 字典格式，如 {'sessions': ['session_id1', 'session_id2']}
        """
        from services.L1_infrastructure.L1b_persistence.persistence_service import get_persistence_service
        
        persistence = get_persistence_service()
        data = {}
        
        for entity_type, ids in filters.items():
            try:
                if isinstance(ids, list) and len(ids) > 0:
                    items = persistence.list(entity_type)
                    filtered_items = []
                    
                    # 根据实体类型确定主键字段
                    id_field_map = {
                        'projects': 'project_id',
                        'sessions': 'session_id',
                        'dialogs': 'dialog_id',
                        'messages': 'message_id',
                        'task_groups': 'task_group_id',
                        'tasks': 'task_id',
                        'llm_calls': 'call_id',
                        'tool_calls': 'call_id',
                        'events': 'record_id',
                    }
                    
                    id_field = id_field_map.get(entity_type, 'entity_id')
                    
                    for item in items:
                        item_id = item.get(id_field) or item.get('entity_id')
                        if item_id and item_id in ids:
                            filtered_items.append(item)
                    
                    if filtered_items:
                        data[entity_type] = filtered_items
            except Exception as e:
                print(f"警告：收集 {entity_type} 数据时出错: {e}")
        
        return data
    
    @staticmethod
    def collect_file_contents(include_empty=True):
        """收集所有数据文件的路径和内容
        
        Args:
            include_empty: 是否包含空文件（记录文件路径但内容为空）
        """
        data_dir = TestDataCollector.get_data_dir()
        file_contents = {}
        
        for entity_type, file_name in DATA_FILES_MAP.items():
            file_path = data_dir / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        file_contents[entity_type] = {
                            'file_path': str(file_path),
                            'record_count': len(content),
                            'content': content
                        }
                except Exception as e:
                    print(f"警告：读取 {file_path} 时出错: {e}")
            elif include_empty:
                # 文件不存在也记录，标记为空
                file_contents[entity_type] = {
                    'file_path': str(file_path),
                    'record_count': 0,
                    'content': [],
                    'exists': False
                }
        
        return file_contents
    
    @staticmethod
    def collect_file_operations():
        """收集文件操作记录"""
        file_contents = TestDataCollector.collect_file_contents()
        operations = []
        
        for entity_type, file_info in file_contents.items():
            if file_info['record_count'] > 0:
                operations.append({
                    'entity_type': entity_type,
                    'file_path': file_info['file_path'],
                    'operation': 'write',
                    'record_count': file_info['record_count'],
                    'sample_data': file_info['content'][-1] if file_info['content'] else None
                })
        
        return operations
    
    @staticmethod
    def validate_persistence(entity_type, expected_ids=None):
        """验证持久化数据是否正确
        
        Args:
            entity_type: 实体类型
            expected_ids: 期望的ID列表
        
        Returns:
            dict: 验证结果
        """
        data_dir = TestDataCollector.get_data_dir()
        file_name = DATA_FILES_MAP.get(entity_type)
        
        if not file_name:
            return {'valid': False, 'error': f"未知的实体类型: {entity_type}"}
        
        file_path = data_dir / file_name
        
        if not file_path.exists():
            return {'valid': False, 'error': f"文件不存在: {file_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            result = {
                'valid': True,
                'file_path': str(file_path),
                'record_count': len(content),
                'data_exists': len(content) > 0
            }
            
            # 如果指定了期望的ID，验证它们是否存在
            if expected_ids:
                id_field_map = {
                    'projects': 'project_id',
                    'sessions': 'session_id',
                    'dialogs': 'dialog_id',
                    'messages': 'message_id',
                    'task_groups': 'task_group_id',
                    'tasks': 'task_id',
                    'llm_calls': 'call_id',
                    'tool_calls': 'call_id',
                    'events': 'record_id',
                }
                id_field = id_field_map.get(entity_type, 'entity_id')
                
                found_ids = [item.get(id_field) for item in content if item.get(id_field)]
                missing_ids = [eid for eid in expected_ids if eid not in found_ids]
                
                result['expected_ids'] = expected_ids
                result['found_ids'] = found_ids
                result['missing_ids'] = missing_ids
                result['all_found'] = len(missing_ids) == 0
            
            return result
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    @staticmethod
    def collect_llm_data():
        """收集LLM相关数据"""
        validation = TestDataCollector.validate_persistence('llm_calls')
        
        if validation['valid'] and validation['data_exists']:
            data_dir = TestDataCollector.get_data_dir()
            file_path = data_dir / 'llm_calls.json'
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            return {
                'file_path': str(file_path),
                'call_count': validation['record_count'],
                'last_call': content[-1] if content else None,
                'validation': validation
            }
        
        return {}
    
    @staticmethod
    def collect_event_data():
        """收集事件相关数据"""
        from services.L1_infrastructure.L1d_events.event_bus import EventBus
        
        try:
            event_bus = EventBus()
            all_events = event_bus.get_all_events()
            
            validation = TestDataCollector.validate_persistence('events')
            
            return {
                'event_count': len(all_events),
                'events': all_events,
                'validation': validation
            }
        except Exception as e:
            print(f"警告：收集事件数据时出错: {e}")
            return {}


@ pytest.fixture(scope="session", autouse=True)
def setup_llm_client_persistence():
    """会话级设置：为LLMClient设置持久化服务"""
    from services.L1_infrastructure.L1c_llm.llm_client import LLMClient
    from services.L1_infrastructure.L1c_llm.llm_client import get_llm_client
    from services.L1_infrastructure.L1b_persistence.persistence_service import get_persistence_service
    
    persistence = get_persistence_service()
    client = get_llm_client()
    client.set_persistence_service(persistence)
    print("已为LLMClient设置持久化服务")


@pytest.fixture(scope="session", autouse=True)
def setup_event_bus_persistence():
    """会话级设置：为EventBus设置持久化服务"""
    from services.L1_infrastructure.L1d_events.event_bus import EventBus
    from services.L1_infrastructure.L1b_persistence.persistence_service import get_persistence_service
    
    persistence = get_persistence_service()
    EventBus.set_persistence_service(persistence)
    print("已为EventBus单例设置持久化服务")


@pytest.fixture(scope="session", autouse=True)
def session_cleanup_before():
    """会话级清理：在所有测试开始前清理环境"""
    print("\n=== 会话级清理（测试开始前） ===")
    cleanup_test_data()
    yield


@pytest.fixture(scope="function", autouse=True)
def function_cleanup_before(request):
    """函数级清理：每个测试函数开始前清理数据"""
    print(f"\n=== 函数级清理 - {request.function.__name__}（测试开始前） ===")
    cleanup_test_data()
    yield


@pytest.fixture(scope="module", autouse=True)
def module_cleanup_before(request):
    """模块级清理：每个测试模块开始前清理数据"""
    print(f"\n=== 模块级清理 - {request.module.__name__}（测试开始前） ===")
    cleanup_test_data()
    yield


class TestReport:
    """测试报告生成器"""
    
    @staticmethod
    def get_test_info(request):
        """获取测试信息"""
        # 解析测试类型（ut/it/st）
        test_path = str(Path(request.node.fspath.strpath))
        test_type = "ut"
        if "\\tests\\it\\" in test_path or "/tests/it/" in test_path:
            test_type = "it"
        elif "\\tests\\st\\" in test_path or "/tests/st/" in test_path:
            test_type = "st"
        
        # 解析层级和子层级名
        # 新目录结构: tests/{test_type}/{层级名}/{子层级名}/{用例文件名}.py
        parts = Path(test_path).parts
        try:
            tests_idx = parts.index("tests")
            if tests_idx + 3 < len(parts):
                layer = parts[tests_idx + 2]  # 层级名
                sub_layer = parts[tests_idx + 3]  # 子层级名
            else:
                layer = "unknown"
                sub_layer = "unknown"
        except ValueError:
            layer = "unknown"
            sub_layer = "unknown"
        
        # 解析组件名（从类名中提取）
        class_name = request.node.parent.name.replace("Test", "")
        component = class_name
        
        return {
            "test_type": test_type,
            "layer": layer,
            "sub_layer": sub_layer,
            "component": component,
            "case_name": request.node.name
        }
    
    @staticmethod
    def save_report(request, test_points=None, inputs=None, outputs=None, persistent_data=None, events=None, llm_data=None, tool_calls=None, service_calls=None, file_operations=None):
        """保存测试报告"""
        info = TestReport.get_test_info(request)
        
        # 创建报告目录: tests/report/{test_type}/{层级名}/{子层级名}/
        report_dir = Path(__file__).parent / "report" / info["test_type"] / info["layer"] / info["sub_layer"]
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成报告内容
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_type": info["test_type"],
            "layer": info["layer"],
            "sub_layer": info["sub_layer"],
            "component": info["component"],
            "case_name": info["case_name"],
            "test_points": test_points or [],
            "inputs": inputs or {},
            "outputs": outputs or {},
            "persistent_data": persistent_data or {},
            "events": events or [],
            "llm_data": llm_data or {},
            "tool_calls": tool_calls or [],
            "service_calls": service_calls or [],
            "file_operations": file_operations or []
        }
        
        # 保存报告
        report_path = report_dir / f"{info['case_name']}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"测试报告已保存: {report_path}")
        return report_path


@pytest.fixture(scope="function")
def test_report(request):
    """测试报告fixture - 通用机制：自动收集所有持久化数据"""
    def report_func(**kwargs):
        # 自动收集持久化数据（如果未显式提供）
        if 'persistent_data' not in kwargs or not kwargs['persistent_data']:
            kwargs['persistent_data'] = TestDataCollector.collect_all_persistent_data()
        
        # 自动收集文件操作记录（如果未显式提供）
        if 'file_operations' not in kwargs or not kwargs['file_operations']:
            kwargs['file_operations'] = TestDataCollector.collect_file_operations()
        
        # 自动收集LLM数据（如果未显式提供）
        if 'llm_data' not in kwargs or not kwargs['llm_data']:
            llm_data = TestDataCollector.collect_llm_data()
            if llm_data:
                kwargs['llm_data'] = llm_data
        
        # 自动收集事件数据（如果未显式提供）
        if 'events' not in kwargs or not kwargs['events']:
            event_data = TestDataCollector.collect_event_data()
            if event_data.get('events'):
                kwargs['events'] = event_data['events']
        
        return TestReport.save_report(request, **kwargs)
    
    return report_func


@pytest.fixture(scope="function")
def data_collector():
    """测试数据收集器fixture - 提供通用的数据收集功能"""
    return TestDataCollector
