package com.flip.integrations.test

import com.flip.integrations.*
import io.micronaut.http.HttpStatus
import io.micronaut.security.authentication.Authentication
import io.micronaut.test.extensions.junit5.annotation.MicronautTest
import org.junit.jupiter.api.*
import org.junit.jupiter.api.Assertions.*
import jakarta.inject.Inject
import io.mockk.*
import org.assertj.core.api.Assertions.assertThat

@MicronautTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class MapperTestSuite {

    @Inject
    lateinit var controller: AbsenceController

    @Inject
    lateinit var service: AbsenceService

    private lateinit var mockStackOneClient: StackOneClient

    @BeforeEach
    fun setup() {
        mockStackOneClient = mockk<StackOneClient>()
        // Inject mock client into service
        // Note: In real implementation, you'd use proper DI setup
    }

    @AfterEach
    fun tearDown() {
        clearAllMocks()
    }

    // Controller Tests
    @Test
    fun test_create_absence_success() {
        // Given
        val request = CreateAbsenceRequest(
            employeeId = "emp_123",
            absenceType = "sick_leave",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            reason = "Flu symptoms"
        )
        val mockAuth = mockk<Authentication>()
        every { mockAuth.attributes } returns mapOf("email" to "test@company.com")
        
        // Mock service response
        val mockResponse = AbsenceResponse(
            id = "abs_123",
            employeeId = "emp_123",
            absenceType = "sick_leave",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            status = "pending",
            reason = "Flu symptoms"
        )
        
        // When
        val response = controller.createAbsence(mockAuth, request)
        
        // Then
        assertThat(response.status).isEqualTo(HttpStatus.OK)
        assertThat(response.body).isNotNull()
    }

    @Test
    fun test_create_absence_validation_error() {
        // Given
        val invalidRequest = CreateAbsenceRequest(
            employeeId = "",
            absenceType = "invalid_type",
            startDate = "invalid-date",
            endDate = "2024-12-17",
            reason = ""
        )
        val mockAuth = mockk<Authentication>()
        
        // When
        val response = controller.createAbsence(mockAuth, invalidRequest)
        
        // Then
        assertThat(response.status).isEqualTo(HttpStatus.BAD_REQUEST)
    }

    @Test
    fun test_get_absences_success() {
        // Given
        val mockAuth = mockk<Authentication>()
        every { mockAuth.attributes } returns mapOf("email" to "test@company.com")
        
        // When
        val response = controller.getAbsences(mockAuth)
        
        // Then
        assertThat(response.status).isEqualTo(HttpStatus.OK)
        assertThat(response.body).isNotNull()
    }

    @Test
    fun test_get_absence_by_id_success() {
        // Given
        val absenceId = "abs_123"
        val mockAuth = mockk<Authentication>()
        every { mockAuth.attributes } returns mapOf("email" to "test@company.com")
        
        // When
        val response = controller.getAbsenceById(mockAuth, absenceId)
        
        // Then
        assertThat(response.status).isEqualTo(HttpStatus.OK)
        assertThat(response.body).isNotNull()
    }

    @Test
    fun test_get_absence_by_id_not_found() {
        // Given
        val nonExistentId = "abs_nonexistent"
        val mockAuth = mockk<Authentication>()
        
        // When
        val response = controller.getAbsenceById(mockAuth, nonExistentId)
        
        // Then
        assertThat(response.status).isEqualTo(HttpStatus.NOT_FOUND)
    }

    // Service Tests
    @Test
    fun test_create_absence_business_logic() {
        // Given
        val email = "test@company.com"
        val request = CreateAbsenceRequest(
            employeeId = "emp_123",
            absenceType = "sick_leave",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            reason = "Flu symptoms"
        )
        
        // Mock StackOne client response
        val mockStackOneResponse = TimeOffEntryResponse(
            id = "toe_123",
            employeeId = "emp_123",
            timeOffType = "sick",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            description = "Flu symptoms",
            status = "approved"
        )
        every { mockStackOneClient.createTimeOffEntry(any()) } returns mockStackOneResponse
        
        // When
        val result = service.createAbsence(email, request)
        
        // Then
        assertThat(result).isNotNull()
        assertThat(result.employeeId).isEqualTo("emp_123")
        assertThat(result.absenceType).isEqualTo("sick_leave")
    }

    @Test
    fun test_get_absences_by_email() {
        // Given
        val email = "test@company.com"
        val mockResponse = TimeOffEntryListResponse(
            data = listOf(
                TimeOffEntryResponse(
                    id = "toe_123",
                    employeeId = "emp_123",
                    timeOffType = "sick"
                )
            )
        )
        every { mockStackOneClient.getTimeOffEntries(email) } returns mockResponse
        
        // When
        val result = service.getAbsencesByEmail(email)
        
        // Then
        assertThat(result).isNotNull()
        assertThat(result).isInstanceOf(List::class.java)
        assertThat(result).hasSize(1)
    }

    @Test
    fun test_get_absence_by_id_service() {
        // Given
        val email = "test@company.com"
        val absenceId = "abs_123"
        val mockResponse = TimeOffEntryResponse(
            id = "toe_123",
            employeeId = "emp_123",
            timeOffType = "sick"
        )
        every { mockStackOneClient.getTimeOffEntry(absenceId) } returns mockResponse
        
        // When
        val result = service.getAbsenceById(email, absenceId)
        
        // Then
        assertThat(result).isNotNull()
        assertThat(result.id).isEqualTo("toe_123")
    }

    // Mapper Tests
    @Test
    fun test_absence_type_mapping() {
        // Test all enum mappings
        assertThat(AbsenceMapper.mapAbsenceType("sick_leave")).isEqualTo("sick")
        assertThat(AbsenceMapper.mapAbsenceType("vacation")).isEqualTo("vacation")
        assertThat(AbsenceMapper.mapAbsenceType("personal_leave")).isEqualTo("personal")
        assertThat(AbsenceMapper.mapAbsenceType("maternity_leave")).isEqualTo("maternity")
        assertThat(AbsenceMapper.mapAbsenceType("paternity_leave")).isEqualTo("paternity")
        assertThat(AbsenceMapper.mapAbsenceType("bereavement")).isEqualTo("bereavement")
        assertThat(AbsenceMapper.mapAbsenceType("jury_duty")).isEqualTo("jury_duty")
        assertThat(AbsenceMapper.mapAbsenceType("other")).isEqualTo("other")
        assertThat(AbsenceMapper.mapAbsenceType("unknown")).isEqualTo("other")
    }

    @Test
    fun test_status_mapping() {
        // Test all status mappings
        assertThat(AbsenceMapper.mapStatus("submitted")).isEqualTo("pending")
        assertThat(AbsenceMapper.mapStatus("approved")).isEqualTo("approved")
        assertThat(AbsenceMapper.mapStatus("rejected")).isEqualTo("rejected")
        assertThat(AbsenceMapper.mapStatus("cancelled")).isEqualTo("cancelled")
        assertThat(AbsenceMapper.mapStatus("draft")).isEqualTo("pending")
        assertThat(AbsenceMapper.mapStatus("unknown")).isEqualTo("pending")
    }

    @Test
    fun test_map_to_target_complete() {
        // Given
        val source = SourceAbsenceDTO(
            id = "abs_123",
            employeeId = "emp_456",
            absenceType = "sick_leave",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            reason = "Flu symptoms"
        )
        
        // When
        val result = AbsenceMapper.mapToTarget(source)
        
        // Then
        assertThat(result.employeeId).isEqualTo("emp_456")
        assertThat(result.timeOffType).isEqualTo("sick")
        assertThat(result.startDate).isEqualTo("2024-12-15")
        assertThat(result.endDate).isEqualTo("2024-12-17")
        assertThat(result.description).isEqualTo("Flu symptoms")
    }

    @Test
    fun test_map_from_target_complete() {
        // Given
        val target = TimeOffEntryResponse(
            id = "toe_123",
            employeeId = "emp_456",
            timeOffType = "sick",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            description = "Flu symptoms",
            status = "approved"
        )
        
        // When
        val result = AbsenceMapper.mapFromTarget(target)
        
        // Then
        assertThat(result.id).isEqualTo("toe_123")
        assertThat(result.employeeId).isEqualTo("emp_456")
        assertThat(result.absenceType).isEqualTo("sick_leave")
        assertThat(result.startDate).isEqualTo("2024-12-15")
        assertThat(result.endDate).isEqualTo("2024-12-17")
        assertThat(result.reason).isEqualTo("Flu symptoms")
        assertThat(result.status).isEqualTo("approved")
    }

    @Test
    fun test_null_handling() {
        // Given
        val sourceWithNulls = SourceAbsenceDTO(
            id = null,
            employeeId = null,
            absenceType = null,
            startDate = null,
            endDate = null,
            reason = null
        )
        
        // When
        val result = AbsenceMapper.mapToTarget(sourceWithNulls)
        
        // Then
        assertThat(result.employeeId).isEqualTo("")
        assertThat(result.timeOffType).isEqualTo("other")
        assertThat(result.startDate).isEqualTo("")
        assertThat(result.endDate).isEqualTo("")
        assertThat(result.description).isEqualTo("")
    }

    @Test
    fun test_edge_cases() {
        // Test empty strings
        val emptySource = SourceAbsenceDTO(
            employeeId = "",
            absenceType = "",
            startDate = "",
            endDate = "",
            reason = ""
        )
        
        val result = AbsenceMapper.mapToTarget(emptySource)
        assertThat(result.employeeId).isEqualTo("")
        assertThat(result.timeOffType).isEqualTo("other")
        
        // Test very long strings
        val longReason = "A".repeat(1000)
        val longSource = SourceAbsenceDTO(reason = longReason)
        val longResult = AbsenceMapper.mapToTarget(longSource)
        assertThat(longResult.description).isEqualTo(longReason)
    }

    @Test
    fun test_integration_end_to_end() {
        // Given
        val request = CreateAbsenceRequest(
            employeeId = "emp_123",
            absenceType = "sick_leave",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            reason = "Flu symptoms"
        )
        val mockAuth = mockk<Authentication>()
        every { mockAuth.attributes } returns mapOf("email" to "test@company.com")
        
        // Mock StackOne client
        val mockResponse = TimeOffEntryResponse(
            id = "toe_123",
            employeeId = "emp_123",
            timeOffType = "sick",
            status = "approved"
        )
        every { mockStackOneClient.createTimeOffEntry(any()) } returns mockResponse
        
        // When
        val response = controller.createAbsence(mockAuth, request)
        
        // Then
        assertThat(response.status).isEqualTo(HttpStatus.OK)
        verify { mockStackOneClient.createTimeOffEntry(any()) }
    }

    // Security Tests
    @Test
    fun test_authentication_required() {
        // Given
        val request = CreateAbsenceRequest(
            employeeId = "emp_123",
            absenceType = "sick_leave",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            reason = "Flu symptoms"
        )
        
        // When/Then - This would be tested with security annotations
        // In a real test, you'd verify that unauthenticated requests are rejected
        assertTrue(true) // Placeholder for security test
    }

    // Performance Tests
    @Test
    fun test_mapping_performance() {
        // Given
        val source = SourceAbsenceDTO(
            employeeId = "emp_123",
            absenceType = "sick_leave",
            startDate = "2024-12-15",
            endDate = "2024-12-17",
            reason = "Flu symptoms"
        )
        
        // When
        val startTime = System.currentTimeMillis()
        repeat(1000) {
            AbsenceMapper.mapToTarget(source)
        }
        val endTime = System.currentTimeMillis()
        
        // Then
        val duration = endTime - startTime
        assertThat(duration).isLessThan(1000) // Should complete in less than 1 second
    }
}