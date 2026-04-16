"""
配置管理系统
灵活配置，支持热重载
"""
import json
import os
import yaml
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import hashlib
import logging
from pathlib import Path
from threading import Lock
import time

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = 'config'):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.configs: Dict[str, Dict] = {}
        self.config_files: Dict[str, str] = {}
        self.config_hashes: Dict[str, str] = {}
        self.callbacks: Dict[str, List] = {}

        self.lock = Lock()

        # 默认配置Schema
        self.schemas = {
            'agent_llm_config': {
                'type': 'object',
                'required': ['config', 'sp', 'tools'],
                'properties': {
                    'config': {
                        'type': 'object',
                        'required': ['model', 'temperature', 'top_p', 'max_completion_tokens', 'timeout', 'thinking']
                    },
                    'sp': {'type': 'string', 'minLength': 1},
                    'tools': {'type': 'array'}
                }
            }
        }

    def load_config(self, config_name: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            config_name: 配置名称
            file_path: 配置文件路径（可选），如果不提供则使用默认路径

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 文件不存在
            ConfigValidationError: 配置验证失败
        """
        if file_path is None:
            file_path = self.config_dir / f"{config_name}.json"
        else:
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigValidationError(f"配置文件格式错误: {e}")

        # 验证配置
        if config_name in self.schemas:
            self._validate_config(config_name, config)

        # 计算文件hash
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        # 保存配置
        with self.lock:
            self.configs[config_name] = config
            self.config_files[config_name] = str(file_path)
            self.config_hashes[config_name] = file_hash

        logger.info(f"配置加载成功: {config_name}")
        return config

    def reload_config(self, config_name: str) -> bool:
        """
        重新加载配置

        Args:
            config_name: 配置名称

        Returns:
            是否重新加载成功
        """
        if config_name not in self.config_files:
            logger.warning(f"配置 {config_name} 未加载，无法重新加载")
            return False

        try:
            file_path = self.config_files[config_name]

            # 检查文件是否被修改
            with open(file_path, 'rb') as f:
                new_hash = hashlib.md5(f.read()).hexdigest()

            if new_hash == self.config_hashes.get(config_name):
                logger.info(f"配置 {config_name} 未修改，无需重新加载")
                return False

            # 重新加载
            self.load_config(config_name, file_path)

            # 触发回调
            self._trigger_callbacks(config_name)

            logger.info(f"配置重新加载成功: {config_name}")
            return True

        except Exception as e:
            logger.error(f"重新加载配置失败 {config_name}: {e}")
            return False

    def hot_reload(self, config_name: str, interval: float = 1.0, max_iterations: int = None):
        """
        热重载监控

        Args:
            config_name: 配置名称
            interval: 检查间隔（秒）
            max_iterations: 最大迭代次数（None表示无限）
        """
        logger.info(f"开始热重载监控: {config_name}")

        iterations = 0
        while max_iterations is None or iterations < max_iterations:
            try:
                self.reload_config(config_name)
            except Exception as e:
                logger.error(f"热重载检查失败: {e}")

            time.sleep(interval)
            iterations += 1

        logger.info(f"热重载监控结束: {config_name}")

    def save_config(self, config_name: str, config: Dict[str, Any], file_path: Optional[str] = None):
        """
        保存配置文件

        Args:
            config_name: 配置名称
            config: 配置字典
            file_path: 配置文件路径（可选）

        Raises:
            ConfigValidationError: 配置验证失败
        """
        # 验证配置
        if config_name in self.schemas:
            self._validate_config(config_name, config)

        if file_path is None:
            file_path = self.config_dir / f"{config_name}.json"
        else:
            file_path = Path(file_path)

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存配置
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 更新内存中的配置
        with self.lock:
            self.configs[config_name] = config
            self.config_files[config_name] = str(file_path)

            # 计算新hash
            with open(file_path, 'rb') as f:
                self.config_hashes[config_name] = hashlib.md5(f.read()).hexdigest()

        logger.info(f"配置保存成功: {config_name}")

    def get_config(self, config_name: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        获取配置

        Args:
            config_name: 配置名称
            key: 配置键（可选），如果不提供则返回整个配置
            default: 默认值

        Returns:
            配置值
        """
        with self.lock:
            if config_name not in self.configs:
                logger.warning(f"配置 {config_name} 未加载")
                return default

            config = self.configs[config_name]

            if key is None:
                return config

            return config.get(key, default)

    def set_config(self, config_name: str, key: str, value: Any, auto_save: bool = True):
        """
        设置配置

        Args:
            config_name: 配置名称
            key: 配置键
            value: 配置值
            auto_save: 是否自动保存
        """
        with self.lock:
            if config_name not in self.configs:
                self.configs[config_name] = {}

            self.configs[config_name][key] = value

        if auto_save:
            self.save_config(config_name, self.configs[config_name])

    def update_config(self, config_name: str, updates: Dict[str, Any], auto_save: bool = True):
        """
        更新配置

        Args:
            config_name: 配置名称
            updates: 更新字典
            auto_save: 是否自动保存
        """
        with self.lock:
            if config_name not in self.configs:
                self.configs[config_name] = {}

            self.configs[config_name].update(updates)

        if auto_save:
            self.save_config(config_name, self.configs[config_name])

    def _validate_config(self, config_name: str, config: Dict[str, Any]):
        """
        验证配置

        Args:
            config_name: 配置名称
            config: 配置字典

        Raises:
            ConfigValidationError: 配置验证失败
        """
        schema = self.schemas.get(config_name)
        if not schema:
            return

        # 简化验证（实际应该使用jsonschema库）
        if schema.get('type') == 'object':
            for required_field in schema.get('required', []):
                if required_field not in config:
                    raise ConfigValidationError(f"配置缺少必需字段: {required_field}")

            properties = schema.get('properties', {})
            for prop_name, prop_config in properties.items():
                if prop_name in config:
                    prop_value = config[prop_name]

                    # 检查类型
                    expected_type = prop_config.get('type')
                    if expected_type == 'string':
                        if not isinstance(prop_value, str):
                            raise ConfigValidationError(f"字段 {prop_name} 应该是字符串类型")
                        if 'minLength' in prop_config and len(prop_value) < prop_config['minLength']:
                            raise ConfigValidationError(f"字段 {prop_name} 长度不能少于 {prop_config['minLength']}")
                    elif expected_type == 'array':
                        if not isinstance(prop_value, list):
                            raise ConfigValidationError(f"字段 {prop_name} 应该是数组类型")
                    elif expected_type == 'object':
                        if not isinstance(prop_value, dict):
                            raise ConfigValidationError(f"字段 {prop_name} 应该是对象类型")

    def register_callback(self, config_name: str, callback):
        """
        注册配置变更回调

        Args:
            config_name: 配置名称
            callback: 回调函数
        """
        if config_name not in self.callbacks:
            self.callbacks[config_name] = []

        self.callbacks[config_name].append(callback)
        logger.info(f"注册回调: {config_name}")

    def _trigger_callbacks(self, config_name: str):
        """
        触发回调

        Args:
            config_name: 配置名称
        """
        callbacks = self.callbacks.get(config_name, [])
        for callback in callbacks:
            try:
                callback(self.configs[config_name])
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    def list_configs(self) -> List[str]:
        """
        列出所有已加载的配置

        Returns:
            配置名称列表
        """
        return list(self.configs.keys())

    def export_config(self, config_name: str, export_path: str):
        """
        导出配置

        Args:
            config_name: 配置名称
            export_path: 导出路径
        """
        config = self.get_config(config_name)
        if config is None:
            raise ConfigValidationError(f"配置 {config_name} 未加载")

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"配置导出成功: {config_name} -> {export_path}")

    def import_config(self, config_name: str, import_path: str):
        """
        导入配置

        Args:
            config_name: 配置名称
            import_path: 导入路径
        """
        self.load_config(config_name, import_path)
        logger.info(f"配置导入成功: {import_path} -> {config_name}")


def create_config_manager(config_dir: str = 'config') -> ConfigManager:
    """
    创建配置管理器

    Args:
        config_dir: 配置文件目录

    Returns:
        配置管理器实例
    """
    return ConfigManager(config_dir)


def create_default_agent_config(workspace_path: str) -> Dict[str, Any]:
    """
    创建默认的智能体配置

    Args:
        workspace_path: 工作空间路径

    Returns:
        默认配置字典
    """
    return {
        "config": {
            "model": "doubao-seed-1-6-251015",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_completion_tokens": 10000,
            "timeout": 600,
            "thinking": "disabled"
        },
        "sp": "You are a helpful assistant. Use tools when helpful.",
        "tools": []
    }


if __name__ == "__main__":
    # 测试配置管理器
    print("测试配置管理系统...")

    # 创建配置管理器
    config_manager = create_config_manager('test_config')

    # 创建测试配置
    test_config = create_default_agent_config('/workspace/test')

    # 保存配置
    config_manager.save_config('test_agent', test_config)

    # 加载配置
    loaded_config = config_manager.load_config('test_agent')
    print(f"加载的配置: {loaded_config}")

    # 获取配置
    model = config_manager.get_config('test_agent', 'config.model')
    print(f"模型: {model}")

    # 设置配置
    config_manager.set_config('test_agent', 'test_key', 'test_value')
    print(f"设置后的配置: {config_manager.get_config('test_agent')}")

    # 列出配置
    print(f"已加载的配置: {config_manager.list_configs()}")

    print("\n✅ 配置管理系统测试完成")
