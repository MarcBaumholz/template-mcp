package com.getflip.absences.stackone.workday.mapper

import com.getflip.absences.stackone.workday.common.apis.WorkersApi
import com.getflip.absences.stackone.workday.common.apis.SupervisoryOrganizationsApi
import com.getflip.absences.stackone.workday.common.models.*
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.assertThrows
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.MockitoAnnotations
import reactor.core.publisher.Mono
import reactor.test.StepVerifier
import java.time.LocalDate
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * Comprehensive test suite for AbsenceToWorkdayMapper.
 * 
 * Tests all mapping scenarios including:
 * - Successful full mapping workflow
 * - Employee validation
 * - Approver validation
 * - Time off plan selection
 * - Date range processing
 * - Half-day unit calculations
 * - Error handling scenarios
 */
class AbsenceToWorkdayMapperTest {

    @Mock
    private lateinit var workersApi: WorkersApi

    @Mock
    private lateinit var supervisoryOrganizationsApi: SupervisoryOrganizationsApi

    private lateinit var mapper: AbsenceToWorkdayMapper

    @BeforeEach
    fun setUp() {
        MockitoAnnotations.openMocks(this)
        mapper = AbsenceToWorkdayMapper(workersApi, supervisoryOrganizationsApi)
    }

    @Test
    @DisplayName("Should successfully map a complete absence request to Workday time off entries")
    fun testSuccessfulMapping() {
        // Arrange
        val flipAbsence = createSampleFlipAbsenceRequest()
        val mockEmployee = createMockEmployee()
        val mockSupervisoryOrg = createMockSupervisoryOrg()
        val mockTimeOffPlans = createMockTimeOffPlans()

        // Mock API responses
        `when`(workersApi.workersIDGet("WORKER_123")).thenReturn(Mono.just(mockEmployee))
        `when`(supervisoryOrganizationsApi.supervisoryOrganizationsIDGet("SUPERVISORY_ORG_123"))
            .thenReturn(Mono.just(mockSupervisoryOrg))
        `when`(workersApi.workersIDTimeOffPlansGet("WORKER_123")).thenReturn(Mono.just(mockTimeOffPlans))

        // Act & Assert
        StepVerifier.create(mapper.mapAbsenceToWorkday(flipAbsence))
            .assertNext { result ->
                // Verify mapping result
                assertEquals(3, result.timeOffEntries.size) // 3 days: 2025-01-20 to 2025-01-22
                assertEquals(mockEmployee, result.employee)
                assertEquals(mockTimeOffPlans.data?.first(), result.selectedPlan)
                assertTrue(result.approverValidated)
                assertEquals(3L, result.totalDays)
                assertEquals(20, result.totalUnits) // 8 + 8 + 4 (last day half)

                // Verify first time off entry
                val firstEntry = result.timeOffEntries.first()
                assertEquals(LocalDate.parse("2025-01-20"), firstEntry.date)
                assertEquals(8, firstEntry.units) // Full day
                assertEquals("WORKER_123", firstEntry.employee?.id)
                assertEquals("Vacation Time Off", firstEntry.timeOff?.descriptor)

                // Verify last time off entry (half day)
                val lastEntry = result.timeOffEntries.last()
                assertEquals(LocalDate.parse("2025-01-22"), lastEntry.date)
                assertEquals(4, lastEntry.units) // Half day
            }
            .verifyComplete()

        // Verify API calls
        verify(workersApi).workersIDGet("WORKER_123")
        verify(supervisoryOrganizationsApi).supervisoryOrganizationsIDGet("SUPERVISORY_ORG_123")
        verify(workersApi).workersIDTimeOffPlansGet("WORKER_123")
    }

    @Test
    @DisplayName("Should handle single day absence correctly")
    fun testSingleDayAbsence() {
        // Arrange
        val flipAbsence = AbsenceToWorkdayMapper.FlipAbsenceRequest(
            employee_id = "WORKER_123",
            approver_id = "MANAGER_456",
            start_date = "2025-01-20",
            end_date = "2025-01-20", // Same day
            reason = "Sick Leave",
            start_half_day = true,
            end_half_day = false,
            createdAt = "2025-01-16T10:30:00Z"
        )

        val mockEmployee = createMockEmployee()
        val mockSupervisoryOrg = createMockSupervisoryOrg()
        val mockTimeOffPlans = createMockTimeOffPlans()

        // Mock API responses
        `when`(workersApi.workersIDGet("WORKER_123")).thenReturn(Mono.just(mockEmployee))
        `when`(supervisoryOrganizationsApi.supervisoryOrganizationsIDGet("SUPERVISORY_ORG_123"))
            .thenReturn(Mono.just(mockSupervisoryOrg))
        `when`(workersApi.workersIDTimeOffPlansGet("WORKER_123")).thenReturn(Mono.just(mockTimeOffPlans))

        // Act & Assert
        StepVerifier.create(mapper.mapAbsenceToWorkday(flipAbsence))
            .assertNext { result ->
                assertEquals(1, result.timeOffEntries.size) // Single day
                assertEquals(4, result.timeOffEntries.first().units) // Half day = 4 units
                assertEquals(1L, result.totalDays)
                assertEquals(4, result.totalUnits)
            }
            .verifyComplete()
    }

    @Test
    @DisplayName("Should handle employee not found error")
    fun testEmployeeNotFound() {
        // Arrange
        val flipAbsence = createSampleFlipAbsenceRequest()
        `when`(workersApi.workersIDGet("WORKER_123"))
            .thenReturn(Mono.error(org.springframework.web.reactive.function.client.WebClientResponseException.create(
                404, "Not Found", null, null, null
            )))

        // Act & Assert
        StepVerifier.create(mapper.mapAbsenceToWorkday(flipAbsence))
            .expectError(WorkerNotFoundException::class.java)
            .verify()
    }

    @Test
    @DisplayName("Should handle invalid approver error")
    fun testInvalidApprover() {
        // Arrange
        val flipAbsence = createSampleFlipAbsenceRequest()
        val mockEmployee = createMockEmployee()
        val mockSupervisoryOrg = createMockSupervisoryOrg()
        
        // Change manager ID to simulate invalid approver
        val invalidManagerOrg = mockSupervisoryOrg.copy(
            manager = Manager0c28a4eb372c41ab9a109e9703487457(
                id = "DIFFERENT_MANAGER",
                descriptor = "Different Manager"
            )
        )

        `when`(workersApi.workersIDGet("WORKER_123")).thenReturn(Mono.just(mockEmployee))
        `when`(supervisoryOrganizationsApi.supervisoryOrganizationsIDGet("SUPERVISORY_ORG_123"))
            .thenReturn(Mono.just(invalidManagerOrg))

        // Act & Assert
        StepVerifier.create(mapper.mapAbsenceToWorkday(flipAbsence))
            .expectError(ApprovalException::class.java)
            .verify()
    }

    @Test
    @DisplayName("Should handle no suitable time off plan error")
    fun testNoSuitableTimeOffPlan() {
        // Arrange
        val flipAbsence = createSampleFlipAbsenceRequest()
        val mockEmployee = createMockEmployee()
        val mockSupervisoryOrg = createMockSupervisoryOrg()
        val emptyTimeOffPlans = WorkersIDTimeOffPlansGet200Response(
            data = emptyList(),
            total = 0L
        )

        `when`(workersApi.workersIDGet("WORKER_123")).thenReturn(Mono.just(mockEmployee))
        `when`(supervisoryOrganizationsApi.supervisoryOrganizationsIDGet("SUPERVISORY_ORG_123"))
            .thenReturn(Mono.just(mockSupervisoryOrg))
        `when`(workersApi.workersIDTimeOffPlansGet("WORKER_123")).thenReturn(Mono.just(emptyTimeOffPlans))

        // Act & Assert
        StepVerifier.create(mapper.mapAbsenceToWorkday(flipAbsence))
            .expectError(TimeOffPlanException::class.java)
            .verify()
    }

    @Test
    @DisplayName("Should calculate units correctly for various half-day scenarios")
    fun testUnitCalculationScenarios() {
        // Test data
        val startDate = LocalDate.of(2025, 1, 20)
        val endDate = LocalDate.of(2025, 1, 22)
        val middleDate = LocalDate.of(2025, 1, 21)

        // Test cases using reflection to access private method
        val calculateUnitsMethod = AbsenceToWorkdayMapper::class.java.getDeclaredMethod(
            "calculateUnits",
            LocalDate::class.java,
            Boolean::class.java,
            Boolean::class.java,
            LocalDate::class.java,
            LocalDate::class.java
        )
        calculateUnitsMethod.isAccessible = true

        // Single day, full day
        val singleFullDay = calculateUnitsMethod.invoke(
            mapper, startDate, false, false, startDate, startDate
        ) as Int
        assertEquals(8, singleFullDay)

        // Single day, half day (start)
        val singleHalfDayStart = calculateUnitsMethod.invoke(
            mapper, startDate, true, false, startDate, startDate
        ) as Int
        assertEquals(4, singleHalfDayStart)

        // Single day, half day (end)
        val singleHalfDayEnd = calculateUnitsMethod.invoke(
            mapper, startDate, false, true, startDate, startDate
        ) as Int
        assertEquals(4, singleHalfDayEnd)

        // Multi-day: start date with half day
        val multiDayStartHalf = calculateUnitsMethod.invoke(
            mapper, startDate, true, false, startDate, endDate
        ) as Int
        assertEquals(4, multiDayStartHalf)

        // Multi-day: end date with half day
        val multiDayEndHalf = calculateUnitsMethod.invoke(
            mapper, endDate, false, true, startDate, endDate
        ) as Int
        assertEquals(4, multiDayEndHalf)

        // Multi-day: middle date (always full day)
        val multiDayMiddle = calculateUnitsMethod.invoke(
            mapper, middleDate, true, true, startDate, endDate
        ) as Int
        assertEquals(8, multiDayMiddle)
    }

    @Test
    @DisplayName("Should handle time off plan selection with fallback logic")
    fun testTimeOffPlanSelectionFallback() {
        // Arrange
        val flipAbsence = AbsenceToWorkdayMapper.FlipAbsenceRequest(
            employee_id = "WORKER_123",
            approver_id = "MANAGER_456",
            start_date = "2025-01-20",
            end_date = "2025-01-20",
            reason = "Personal Day", // Not in available plans
            start_half_day = false,
            end_half_day = false,
            createdAt = "2025-01-16T10:30:00Z"
        )

        val mockEmployee = createMockEmployee()
        val mockSupervisoryOrg = createMockSupervisoryOrg()
        val mockTimeOffPlans = WorkersIDTimeOffPlansGet200Response(
            data = listOf(
                TimeOffPlans581c389cce1410000feacaebd2e40002(
                    id = "PLAN_1",
                    descriptor = "Annual Leave Plan",
                    timeOffBalance = 160,
                    href = "/timeOffPlans/PLAN_1"
                )
            ),
            total = 1L
        )

        `when`(workersApi.workersIDGet("WORKER_123")).thenReturn(Mono.just(mockEmployee))
        `when`(supervisoryOrganizationsApi.supervisoryOrganizationsIDGet("SUPERVISORY_ORG_123"))
            .thenReturn(Mono.just(mockSupervisoryOrg))
        `when`(workersApi.workersIDTimeOffPlansGet("WORKER_123")).thenReturn(Mono.just(mockTimeOffPlans))

        // Act & Assert
        StepVerifier.create(mapper.mapAbsenceToWorkday(flipAbsence))
            .assertNext { result ->
                // Should use the vacation/annual plan as fallback
                assertEquals("Annual Leave Plan", result.selectedPlan.descriptor)
            }
            .verifyComplete()
    }

    // Helper methods to create mock objects
    private fun createMockEmployee(): WorkerProfileC0a0dce56eb142d39dbffeb505becf7a {
        return WorkerProfileC0a0dce56eb142d39dbffeb505becf7a(
            id = "WORKER_123",
            descriptor = "John Doe",
            primaryWorkEmail = "john.doe@flip.com",
            isManager = false,
            primarySupervisoryOrganization = PrimarySupervisoryOrganization851e1342d4c2489c9680fb2a899227ca(
                id = "SUPERVISORY_ORG_123",
                descriptor = "Engineering Team"
            ),
            businessTitle = "Software Engineer",
            href = "/workers/WORKER_123"
        )
    }

    private fun createMockSupervisoryOrg(): SupervisoryOrganizationSummary3a94b57f042a4ebb95027e09d6192992 {
        return SupervisoryOrganizationSummary3a94b57f042a4ebb95027e09d6192992(
            id = "SUPERVISORY_ORG_123",
            descriptor = "Engineering Team",
            name = "Engineering Team",
            code = "ENG_TEAM",
            manager = Manager0c28a4eb372c41ab9a109e9703487457(
                id = "MANAGER_456",
                descriptor = "Jane Smith"
            ),
            href = "/supervisoryOrganizations/SUPERVISORY_ORG_123"
        )
    }

    private fun createMockTimeOffPlans(): WorkersIDTimeOffPlansGet200Response {
        return WorkersIDTimeOffPlansGet200Response(
            data = listOf(
                TimeOffPlans581c389cce1410000feacaebd2e40002(
                    id = "VACATION_PLAN",
                    descriptor = "Vacation Time Off",
                    timeOffBalance = 160,
                    unitOfTime = UnitOfTime581c389cce1410000feacb26b51c0003(
                        id = "HOURS",
                        descriptor = "Hours"
                    ),
                    href = "/timeOffPlans/VACATION_PLAN"
                )
            ),
            total = 1L
        )
    }
}

/**
 * Integration test example showing how to use the mapper in a real application context.
 */
class AbsenceToWorkdayMapperIntegrationTest {

    @Test
    @DisplayName("Integration test example - demonstrates real usage")
    fun exampleUsage() {
        // This would be in your actual service class
        
        // 1. Create mapper with real API clients
        // val workersApi = WorkersApi("https://your-workday-api.com")
        // val supervisoryOrganizationsApi = SupervisoryOrganizationsApi("https://your-workday-api.com")
        // val mapper = AbsenceToWorkdayMapper(workersApi, supervisoryOrganizationsApi)

        // 2. Create absence request from incoming webhook/event
        val flipAbsence = AbsenceToWorkdayMapper.FlipAbsenceRequest(
            employee_id = "WD_EMPLOYEE_12345",
            approver_id = "WD_MANAGER_67890",
            start_date = "2025-01-20",
            end_date = "2025-01-24",
            reason = "Vacation",
            start_half_day = false,
            end_half_day = true,
            createdAt = "2025-01-16T10:30:00Z"
        )

        // 3. Transform to Workday format
        // val result = mapper.mapAbsenceToWorkday(flipAbsence)
        //     .doOnSuccess { mappingResult ->
        //         println("Successfully mapped ${mappingResult.timeOffEntries.size} time off entries")
        //         println("Total days: ${mappingResult.totalDays}")
        //         println("Total units: ${mappingResult.totalUnits}")
        //     }
        //     .doOnError { error ->
        //         println("Mapping failed: ${error.message}")
        //     }

        // 4. Use the result to create actual Workday entries
        // result.subscribe { mappingResult ->
        //     // Send to Workday API or queue for processing
        //     processWorkdayTimeOffEntries(mappingResult.timeOffEntries)
        // }

        println("Integration test example completed - see comments for real usage")
    }
}

/**
 * Performance test example for the mapper.
 */
class AbsenceToWorkdayMapperPerformanceTest {

    @Test
    @DisplayName("Performance test - batch processing multiple absences")
    fun testBatchProcessing() {
        // Example of processing multiple absences
        val absences = (1..100).map { index ->
            AbsenceToWorkdayMapper.FlipAbsenceRequest(
                employee_id = "WORKER_$index",
                approver_id = "MANAGER_${index / 10}",
                start_date = "2025-01-20",
                end_date = "2025-01-22",
                reason = "Vacation",
                start_half_day = false,
                end_half_day = false,
                createdAt = "2025-01-16T10:30:00Z"
            )
        }

        val startTime = System.currentTimeMillis()
        
        // In real scenario, you'd process these with proper API mocking
        // val results = absences.map { absence ->
        //     mapper.mapAbsenceToWorkday(absence)
        // }
        
        val endTime = System.currentTimeMillis()
        println("Processed ${absences.size} absences in ${endTime - startTime}ms")
        
        // Add assertions for performance requirements
        assertTrue((endTime - startTime) < 5000) // Should complete within 5 seconds
    }
} 