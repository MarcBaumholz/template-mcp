"""
Configuration Manager for MCP Tools
Provides centralized, flexible configuration without hardcoded values
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class BusinessDomain(Enum):
    """Supported business domains for the tools"""
    HR = "human_resources"
    RETAIL = "retail"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    GENERIC = "generic"


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model: str
    temperature: float = 0.1
    max_tokens: int = 4000
    api_key_env: str = "OPENROUTER_API_KEY"
    base_url_env: str = "OPENROUTER_BASE_URL"
    base_url_default: str = "https://openrouter.ai/api/v1"


@dataclass
class FieldExtractionConfig:
    """Field extraction configuration"""
    max_depth: int = 4
    exclude_fields: List[str] = None
    include_patterns: List[str] = None
    business_context: Optional[str] = None
    
    def __post_init__(self):
        if self.exclude_fields is None:
            self.exclude_fields = ["pagination", "page", "pageSize", "total", "metadata", "links"]
        if self.include_patterns is None:
            self.include_patterns = ["data.*", "items.*", "results.*"]


@dataclass
class CodeGenerationConfig:
    """Code generation configuration"""
    default_language: str = "kotlin"
    default_framework: str = "micronaut"
    default_package: str = "com.company.integrations"
    default_company: str = "company"
    default_project: str = "integrations"
    default_backend: str = "api"
    template_path: Optional[str] = None


@dataclass
class RAGConfig:
    """RAG system configuration"""
    default_collection: str = "api_specs"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    score_threshold: float = 0.5
    max_results: int = 10


@dataclass
class MCPToolsConfig:
    """Main configuration for MCP tools"""
    business_domain: BusinessDomain = BusinessDomain.GENERIC
    llm: LLMConfig = None
    field_extraction: FieldExtractionConfig = None
    code_generation: CodeGenerationConfig = None
    rag: RAGConfig = None
    
    def __post_init__(self):
        if self.llm is None:
            self.llm = LLMConfig(
                provider=LLMProvider.OPENROUTER,
                model=os.getenv("LLM_MODEL", "deepseek/deepseek-chat-v3.1:free")
            )
        if self.field_extraction is None:
            self.field_extraction = FieldExtractionConfig()
        if self.code_generation is None:
            self.code_generation = CodeGenerationConfig()
        if self.rag is None:
            self.rag = RAGConfig()


class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("MCP_CONFIG_PATH", "mcp_config.json")
        self._config: Optional[MCPToolsConfig] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or environment"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                self._config = self._dict_to_config(config_data)
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                self._config = MCPToolsConfig()
        else:
            self._config = MCPToolsConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> MCPToolsConfig:
        """Convert dictionary to MCPToolsConfig"""
        # Handle business domain
        if 'business_domain' in data:
            data['business_domain'] = BusinessDomain(data['business_domain'])
        
        # Handle LLM config
        if 'llm' in data:
            llm_data = data['llm']
            if 'provider' in llm_data:
                llm_data['provider'] = LLMProvider(llm_data['provider'])
            data['llm'] = LLMConfig(**llm_data)
        
        # Handle other configs
        if 'field_extraction' in data:
            data['field_extraction'] = FieldExtractionConfig(**data['field_extraction'])
        if 'code_generation' in data:
            data['code_generation'] = CodeGenerationConfig(**data['code_generation'])
        if 'rag' in data:
            data['rag'] = RAGConfig(**data['rag'])
        
        return MCPToolsConfig(**data)
    
    def get_config(self) -> MCPToolsConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, **kwargs):
        """Update configuration"""
        if self._config is None:
            self._config = MCPToolsConfig()
        
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
    
    def save_config(self):
        """Save configuration to file"""
        if self._config is None:
            return
        
        config_dict = asdict(self._config)
        # Convert enums to strings
        config_dict['business_domain'] = config_dict['business_domain'].value
        config_dict['llm']['provider'] = config_dict['llm']['provider'].value
        
        with open(self.config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def get_llm_model(self) -> str:
        """Get configured LLM model"""
        return self._config.llm.model
    
    def get_collection_name(self, custom_name: Optional[str] = None) -> str:
        """Get RAG collection name"""
        if custom_name:
            return custom_name
        return f"{self._config.rag.default_collection}_{self._config.business_domain.value}"
    
    def get_package_name(self, custom_package: Optional[str] = None) -> str:
        """Get package name for code generation"""
        if custom_package:
            return custom_package
        return self._config.code_generation.default_package
    
    def get_company_name(self, custom_company: Optional[str] = None) -> str:
        """Get company name for code generation"""
        if custom_company:
            return custom_company
        return self._config.code_generation.default_company


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> MCPToolsConfig:
    """Get global configuration"""
    return config_manager.get_config()


def update_config(**kwargs):
    """Update global configuration"""
    config_manager.update_config(**kwargs)


def get_llm_model() -> str:
    """Get configured LLM model"""
    return config_manager.get_llm_model()


def get_collection_name(custom_name: Optional[str] = None) -> str:
    """Get RAG collection name"""
    return config_manager.get_collection_name(custom_name)


def get_package_name(custom_package: Optional[str] = None) -> str:
    """Get package name for code generation"""
    return config_manager.get_package_name(custom_package)


def get_company_name(custom_company: Optional[str] = None) -> str:
    """Get company name for code generation"""
    return config_manager.get_company_name(custom_company)
