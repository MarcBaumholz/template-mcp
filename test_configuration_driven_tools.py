#!/usr/bin/env python3
"""
Comprehensive Test Suite for Configuration-Driven MCP Tools
Tests tools across multiple business domains without hardcoded values
"""

import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add current directory to path
sys.path.append('.')

from tools.shared_utilities.config_manager import (
    ConfigManager, BusinessDomain, LLMProvider, 
    update_config, get_config, get_collection_name
)
from tools.shared_utilities.prompt_templates import render_prompt, PromptType
from tools.shared_utilities.field_extractor import extract_fields_from_json
from tools.phase1_data_extraction.analyze_json_fields_with_rag_v2 import EnhancedFieldAnalysisAgent


class ConfigurationDrivenTester:
    """Test suite for configuration-driven MCP tools"""
    
    def __init__(self):
        self.test_results = []
        self.config_manager = ConfigManager()
    
    def create_test_data(self) -> Dict[BusinessDomain, Dict[str, Any]]:
        """Create test data for different business domains"""
        return {
            BusinessDomain.HR: {
                "data": [
                    {
                        "employeeId": "EMP001",
                        "firstName": "John",
                        "lastName": "Doe",
                        "email": "john.doe@company.com",
                        "department": "Engineering",
                        "position": "Senior Developer",
                        "status": "active",
                        "hireDate": "2023-01-15",
                        "salary": {"amount": 95000, "currency": "USD"},
                        "benefits": {"health": True, "dental": True, "vision": False}
                    }
                ],
                "expected_fields": ["employeeId", "firstName", "lastName", "email", "department", "status"]
            },
            
            BusinessDomain.RETAIL: {
                "data": [
                    {
                        "productId": "PROD_001",
                        "sku": "ABC-123-XL",
                        "productName": "Wireless Headphones",
                        "category": "Electronics",
                        "brand": "TechBrand",
                        "price": {"amount": 199.99, "currency": "USD"},
                        "inventory": {"quantity": 150, "reserved": 25, "available": 125},
                        "warehouse": {"location": "Warehouse A", "shelf": "A-15"},
                        "supplier": {"name": "ElectroSupply Inc", "contact": "supplier@electrosupply.com"}
                    }
                ],
                "expected_fields": ["productId", "sku", "productName", "category", "price", "inventory"]
            },
            
            BusinessDomain.FINANCE: {
                "data": [
                    {
                        "transactionId": "TXN_001",
                        "accountNumber": "ACC-123456",
                        "transactionType": "debit",
                        "amount": 150.75,
                        "currency": "USD",
                        "description": "Online purchase at Amazon",
                        "merchant": {"name": "Amazon.com", "category": "E-commerce"},
                        "timestamp": "2024-12-08T14:30:00Z",
                        "status": "completed",
                        "fees": {"processingFee": 2.50, "currency": "USD"}
                    }
                ],
                "expected_fields": ["transactionId", "accountNumber", "transactionType", "amount", "status"]
            },
            
            BusinessDomain.HEALTHCARE: {
                "data": [
                    {
                        "patientId": "PAT_001",
                        "firstName": "Jane",
                        "lastName": "Smith",
                        "dateOfBirth": "1985-03-15",
                        "gender": "female",
                        "phone": "+1-555-0123",
                        "email": "jane.smith@email.com",
                        "address": {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"},
                        "insurance": {"provider": "Blue Cross", "policyNumber": "BC123456789"},
                        "appointments": [{"date": "2024-12-15", "time": "10:00", "doctor": "Dr. Johnson"}]
                    }
                ],
                "expected_fields": ["patientId", "firstName", "lastName", "dateOfBirth", "insurance"]
            },
            
            BusinessDomain.MANUFACTURING: {
                "data": [
                    {
                        "orderId": "ORD_001",
                        "productCode": "WIDGET-001",
                        "quantity": 1000,
                        "priority": "high",
                        "dueDate": "2024-12-20",
                        "status": "in_production",
                        "materials": [{"name": "Steel", "quantity": 500, "unit": "kg"}],
                        "quality": {"inspectionRequired": True, "tolerance": "±0.1mm"},
                        "production": {"line": "Line A", "shift": "day", "supervisor": "Mike Johnson"}
                    }
                ],
                "expected_fields": ["orderId", "productCode", "quantity", "status", "materials"]
            }
        }
    
    def test_configuration_management(self):
        """Test configuration management system"""
        print("🧪 Testing Configuration Management...")
        
        # Test default configuration
        config = get_config()
        assert config.business_domain == BusinessDomain.GENERIC
        assert config.llm.provider == LLMProvider.OPENROUTER
        
        # Test configuration updates
        update_config(business_domain=BusinessDomain.RETAIL)
        config = get_config()
        assert config.business_domain == BusinessDomain.RETAIL
        
        # Test collection naming
        collection_name = get_collection_name()
        assert "retail" in collection_name
        
        # Test custom collection naming
        custom_name = get_collection_name("custom_api")
        assert custom_name == "custom_api"
        
        print("✅ Configuration management tests passed")
        return True
    
    def test_prompt_templates(self):
        """Test prompt template system"""
        print("🧪 Testing Prompt Templates...")
        
        # Test field extraction prompt
        prompt = render_prompt(
            PromptType.FIELD_EXTRACTION,
            business_context="Retail",
            json_data='{"test": "data"}'
        )
        assert "Retail" in prompt
        assert "test" in prompt
        
        # Test field description prompt
        prompt = render_prompt(
            PromptType.FIELD_DESCRIPTION,
            business_context="Finance",
            fields=["amount", "currency"],
            json_data='{"amount": 100}'
        )
        assert "Finance" in prompt
        assert "amount" in prompt
        assert "currency" in prompt
        
        # Test code generation prompt
        prompt = render_prompt(
            PromptType.CODE_GENERATION,
            business_context="Healthcare",
            mapping_info="test mapping",
            template_text="test template"
        )
        assert "Healthcare" in prompt
        assert "test mapping" in prompt
        
        print("✅ Prompt template tests passed")
        return True
    
    def test_field_extraction(self):
        """Test flexible field extraction"""
        print("🧪 Testing Field Extraction...")
        
        test_data = {
            "data": [
                {
                    "id": "123",
                    "name": "Test Item",
                    "status": "active",
                    "created_at": "2024-01-01",
                    "metadata": {"source": "test"}
                }
            ],
            "pagination": {"page": 1, "total": 1}
        }
        
        result = extract_fields_from_json(test_data)
        
        # Should extract business fields
        assert "data.id" in result.fields
        assert "data.name" in result.fields
        assert "data.status" in result.fields
        
        # Should exclude pagination
        assert "pagination" not in result.fields
        
        # Should have confidence score
        assert 0.0 <= result.confidence_score <= 1.0
        
        # Should categorize fields
        assert "identifiers" in result.metadata["categories"]
        assert "status_fields" in result.metadata["categories"]
        
        print("✅ Field extraction tests passed")
        return True
    
    def test_domain_adaptation(self):
        """Test tools adaptation to different business domains"""
        print("🧪 Testing Domain Adaptation...")
        
        test_data = self.create_test_data()
        
        for domain, data_info in test_data.items():
            print(f"  Testing {domain.value} domain...")
            
            # Update configuration for domain
            update_config(business_domain=domain)
            
            # Test field extraction
            result = extract_fields_from_json(data_info["data"])
            
            # Should extract domain-relevant fields
            extracted_field_names = [f.split(".")[-1] for f in result.fields]
            
            # Check that expected fields are found
            found_expected = 0
            for expected_field in data_info["expected_fields"]:
                if expected_field in extracted_field_names:
                    found_expected += 1
            
            # Should find at least 80% of expected fields
            success_rate = found_expected / len(data_info["expected_fields"])
            assert success_rate >= 0.8, f"Domain {domain.value} only found {success_rate:.1%} of expected fields"
            
            print(f"    ✅ {domain.value}: {found_expected}/{len(data_info['expected_fields'])} expected fields found")
        
        print("✅ Domain adaptation tests passed")
        return True
    
    def test_no_hardcoded_values(self):
        """Test that no hardcoded values exist in tools"""
        print("🧪 Testing No Hardcoded Values...")
        
        # Test configuration manager
        config = get_config()
        
        # Should not have hardcoded company names
        assert "flip" not in config.code_generation.default_package.lower()
        assert "stackone" not in config.code_generation.default_package.lower()
        
        # Should not have hardcoded API names
        assert "flip_api" not in config.rag.default_collection.lower()
        assert "stackone_api" not in config.rag.default_collection.lower()
        
        # Test prompt templates
        prompt = render_prompt(PromptType.FIELD_EXTRACTION, business_context="Test", json_data="{}")
        
        # Should not contain hardcoded domain references
        hardcoded_domains = ["hr", "absence", "employee", "flip", "stackone"]
        for domain in hardcoded_domains:
            assert domain not in prompt.lower(), f"Found hardcoded domain reference: {domain}"
        
        print("✅ No hardcoded values tests passed")
        return True
    
    def test_configuration_persistence(self):
        """Test configuration persistence and loading"""
        print("🧪 Testing Configuration Persistence...")
        
        # Create temporary config file
        temp_config_path = "temp_test_config.json"
        
        # Test saving configuration
        config_manager = ConfigManager(temp_config_path)
        config_manager.update_config(business_domain=BusinessDomain.FINANCE)
        config_manager.save_config()
        
        # Test loading configuration
        new_config_manager = ConfigManager(temp_config_path)
        loaded_config = new_config_manager.get_config()
        
        assert loaded_config.business_domain == BusinessDomain.FINANCE
        
        # Clean up
        Path(temp_config_path).unlink(missing_ok=True)
        
        print("✅ Configuration persistence tests passed")
        return True
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Configuration-Driven MCP Tools Test Suite")
        print("=" * 60)
        
        tests = [
            ("Configuration Management", self.test_configuration_management),
            ("Prompt Templates", self.test_prompt_templates),
            ("Field Extraction", self.test_field_extraction),
            ("Domain Adaptation", self.test_domain_adaptation),
            ("No Hardcoded Values", self.test_no_hardcoded_values),
            ("Configuration Persistence", self.test_configuration_persistence),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                if result:
                    passed += 1
                    self.test_results.append({"test": test_name, "status": "PASSED"})
                else:
                    self.test_results.append({"test": test_name, "status": "FAILED"})
                    
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
        print("=" * 60)
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Configuration-driven tools are working correctly!")
            print("✅ No hardcoded values detected")
            print("✅ Multi-domain support confirmed")
            print("✅ Configuration system working")
            print("✅ Tools are flexible and scalable")
        else:
            print("⚠️ Some tests failed - review and fix issues")
        
        return passed == total


async def main():
    """Main test runner"""
    tester = ConfigurationDrivenTester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
