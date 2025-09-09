#!/usr/bin/env python3
"""
Test script for Phase 4 TDD Validation tool
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_phase4_tdd_validation():
    """Test the Phase 4 TDD validation tool"""
    
    print("🧪 Testing Phase 4 TDD Validation Tool")
    print("=" * 50)
    
    try:
        # Import the tool
        from tools.phase4_tdd_validation.phase4_tdd_validator import run_tdd_validation
        
        print("✅ Successfully imported phase4_tdd_validation tool")
        
        # Create test files
        test_kotlin_file = project_root / "test_kotlin_mapper.kt"
        test_mapping_report = project_root / "test_mapping_report.md"
        test_output_dir = project_root / "test_outputs" / "phase4"
        
        # Create test Kotlin file
        test_kotlin_content = """
package com.flip.integrations

import io.micronaut.http.*
import io.micronaut.http.annotation.*
import io.micronaut.security.annotation.*
import io.micronaut.security.rules.SecurityRule
import jakarta.inject.Singleton
import org.slf4j.LoggerFactory

/**
 * Verified Endpoint(s):
 * - POST /api/absences
 * Fields: employeeId, startDate, endDate, type, status
 */
@Controller("/api/absences")
@Secured(SecurityRule.IS_AUTHENTICATED)
class AbsenceController(private val service: AbsenceService) {

    private val log = LoggerFactory.getLogger(AbsenceController::class.java)

    @Post("/")
    fun createAbsence(auth: Authentication, request: CreateAbsenceRequest): HttpResponse<Any> {
        return try {
            val email = (auth.attributes["email"] as? String) ?: auth.name
            val result = service.createAbsence(email, request)
            HttpResponse.ok(result)
        } catch (ex: Throwable) {
            log.error("Controller error", ex)
            HttpResponse.serverError()
        }
    }
}

@Singleton
class AbsenceService(private val facadeClient: FacadeClient) {
    private val log = LoggerFactory.getLogger(AbsenceService::class.java)

    fun createAbsence(email: String, request: CreateAbsenceRequest): AbsenceResponse {
        return try {
            val dto = facadeClient.createAbsence(email, request)
            Mapper.mapToTarget(dto)
        } catch (ex: Throwable) {
            log.error("Service error", ex)
            throw RuntimeException("Failed to create absence")
        }
    }
}

object Mapper {
    fun mapToTarget(source: SourceAbsenceDTO): AbsenceResponse = AbsenceResponse(
        employeeId = source.employee?.id ?: "",
        startDate = source.startDate ?: "",
        endDate = source.endDate ?: "",
        type = source.type ?: "UNKNOWN",
        status = source.status ?: "PENDING"
    )
}

// Data classes
data class CreateAbsenceRequest(
    val employeeId: String,
    val startDate: String,
    val endDate: String,
    val type: String
)

data class AbsenceResponse(
    val employeeId: String,
    val startDate: String,
    val endDate: String,
    val type: String,
    val status: String
)

data class SourceAbsenceDTO(
    val employee: Employee? = null,
    val startDate: String? = null,
    val endDate: String? = null,
    val type: String? = null,
    val status: String? = null
)

data class Employee(
    val id: String? = null
)

interface FacadeClient {
    fun createAbsence(email: String, request: CreateAbsenceRequest): SourceAbsenceDTO
}
"""
        
        test_kotlin_file.write_text(test_kotlin_content, encoding="utf-8")
        print(f"✅ Created test Kotlin file: {test_kotlin_file}")
        
        # Create test mapping report
        test_mapping_content = """
# Field Mapping Report

## Source Fields Analysis
- employeeId: Employee identifier
- startDate: Absence start date
- endDate: Absence end date
- type: Type of absence (sick, vacation, etc.)
- status: Current status of absence

## Target API Mapping
- POST /api/absences: Create absence endpoint
- Fields mapped successfully with proper transformations

## Verification Results
- All endpoints verified against API specification
- Field mappings validated
- Security annotations confirmed
"""
        
        test_mapping_report.write_text(test_mapping_content, encoding="utf-8")
        print(f"✅ Created test mapping report: {test_mapping_report}")
        
        # Run the TDD validation tool
        print("\n🚀 Running Phase 4 TDD validation...")
        result = run_tdd_validation(
            kotlin_file_path=str(test_kotlin_file),
            mapping_report_path=str(test_mapping_report),
            output_directory=str(test_output_dir),
            max_iterations=3
        )
        
        print("✅ TDD validation completed successfully!")
        print(f"📊 Result: {json.dumps(result, indent=2)}")
        
        # Check if output files were created
        if result.get("success"):
            output_dir = Path(result["output_directory"])
            if output_dir.exists():
                files = list(output_dir.glob("*"))
                print(f"📁 Generated {len(files)} files in output directory:")
                for file in files:
                    print(f"   - {file.name}")
            
            cursor_prompt_file = result.get("cursor_prompt_file")
            if cursor_prompt_file and Path(cursor_prompt_file).exists():
                print(f"📝 Cursor prompt file created: {cursor_prompt_file}")
                
                # Show a preview of the prompt
                prompt_content = Path(cursor_prompt_file).read_text(encoding="utf-8")
                print(f"\n📋 Prompt preview (first 500 chars):")
                print("-" * 50)
                print(prompt_content[:500] + "..." if len(prompt_content) > 500 else prompt_content)
                print("-" * 50)
        
        print("\n🎉 Phase 4 TDD validation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup test files
        try:
            if test_kotlin_file.exists():
                test_kotlin_file.unlink()
            if test_mapping_report.exists():
                test_mapping_report.unlink()
            print("🧹 Cleaned up test files")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up test files: {e}")

if __name__ == "__main__":
    success = test_phase4_tdd_validation()
    sys.exit(0 if success else 1)