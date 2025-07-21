package com.getflip.absences.stackone.workday.mapper

import com.getflip.absences.stackone.workday.common.apis.WorkersApi
import com.getflip.absences.stackone.workday.common.apis.SupervisoryOrganizationsApi
import com.getflip.absences.stackone.workday.common.models.*
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.client.WebClientResponseException
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import java.util.*

/**
 * Maps Flip absence requests to Workday time off entries.
 * 
 * This mapper handles the complete transformation workflow:
 * 1. Employee validation via WorkersApi
 * 2. Approver validation via SupervisoryOrganizationsApi
 * 3. Time off plan selection
 * 4. Date range processing to individual entries
 * 5. Unit calculation for half-day support
 * 6. Time off entry creation
 */
@Component
class AbsenceToWorkdayMapper(
    private val workersApi: WorkersApi,
    private val supervisoryOrganizationsApi: SupervisoryOrganizationsApi
) {

    /**
     * Data class representing a Flip absence request.
     */
    data class FlipAbsenceRequest(
        val employee_id: String,
        val approver_id: String,
        val start_date: String, // ISO date format: "2025-01-16"
        val end_date: String,   // ISO date format: "2025-01-16"
        val reason: String,     // e.g., "Vacation", "Sick Leave", "Personal"
        val start_half_day: Boolean = false,
        val end_half_day: Boolean = false,
        val createdAt: String   // ISO datetime format: "2025-01-16T10:30:00Z"
    )

    /**
     * Result class containing the mapped time off entries and metadata.
     */
    data class WorkdayMappingResult(
        val timeOffEntries: List<TimeOffEntries436f2afb755f100012528fa3260e000f>,
        val employee: WorkerProfileC0a0dce56eb142d39dbffeb505becf7a,
        val selectedPlan: TimeOffPlans581c389cce1410000feacaebd2e40002,
        val approverValidated: Boolean,
        val totalDays: Long,
        val totalUnits: Int
    )

    /**
     * Main mapping function that transforms a Flip absence request to Workday time off entries.
     * 
     * @param flipAbsence The Flip absence request to map
     * @return Mono containing the mapping result with time off entries
     */
    fun mapAbsenceToWorkday(flipAbsence: FlipAbsenceRequest): Mono<WorkdayMappingResult> {
        return validateEmployee(flipAbsence.employee_id)
            .flatMap { employee ->
                validateApprover(employee, flipAbsence.approver_id)
                    .flatMap { approverValid ->
                        selectTimeOffPlan(flipAbsence.employee_id, flipAbsence.reason)
                            .flatMap { selectedPlan ->
                                createTimeOffEntries(flipAbsence, employee, selectedPlan, approverValid)
                            }
                    }
            }
            .doOnError { error ->
                when (error) {
                    is WorkerNotFoundException -> logError("Employee not found: ${flipAbsence.employee_id}")
                    is ApprovalException -> logError("Approval validation failed: ${error.message}")
                    is TimeOffPlanException -> logError("Time off plan issue: ${error.message}")
                    is WebClientResponseException -> logError("Workday API error: ${error.statusCode} - ${error.responseBodyAsString}")
                    else -> logError("Unexpected error during mapping: ${error.message}")
                }
            }
    }

    /**
     * Step 1: Validate employee exists in Workday.
     * Confidence: 95% - Direct API mapping
     */
    private fun validateEmployee(employeeId: String): Mono<WorkerProfileC0a0dce56eb142d39dbffeb505becf7a> {
        return workersApi.workersIDGet(employeeId)
            .doOnError { error ->
                when (error) {
                    is WebClientResponseException -> throw WorkerNotFoundException("Worker $employeeId not found")
                    else -> throw error
                }
            }
            .doOnSuccess { worker ->
                logInfo("Employee validated: ${worker.id} - ${worker.descriptor}")
            }
    }

    /**
     * Step 2: Validate approver is the manager of employee's supervisory organization.
     * Confidence: 85% - Requires supervisory hierarchy validation
     */
    private fun validateApprover(
        employee: WorkerProfileC0a0dce56eb142d39dbffeb505becf7a,
        approverId: String
    ): Mono<Boolean> {
        val primarySupervisoryOrg = employee.primarySupervisoryOrganization?.id
            ?: return Mono.error(ApprovalException("Employee has no supervisory organization"))

        return supervisoryOrganizationsApi.supervisoryOrganizationsIDGet(primarySupervisoryOrg)
            .map { supervisoryOrg ->
                val manager = supervisoryOrg.manager
                    ?: throw ApprovalException("Supervisory organization has no manager")

                if (manager.id != approverId) {
                    throw ApprovalException("Invalid approver: $approverId is not the manager of employee's supervisory organization")
                }

                logInfo("Approver validated: ${manager.id} - ${manager.descriptor}")
                true
            }
    }

    /**
     * Step 3: Select appropriate time off plan based on reason.
     * Confidence: 85% - Semantic matching with fallback
     */
    private fun selectTimeOffPlan(
        employeeId: String,
        reason: String
    ): Mono<TimeOffPlans581c389cce1410000feacaebd2e40002> {
        return workersApi.workersIDTimeOffPlansGet(employeeId)
            .map { response ->
                val timeOffPlans = response.data ?: emptyList()
                
                // First try: exact reason match
                val exactMatch = timeOffPlans.find { plan ->
                    plan.descriptor?.contains(reason, ignoreCase = true) == true
                }
                
                if (exactMatch != null) {
                    logInfo("Exact time off plan match found: ${exactMatch.descriptor}")
                    return@map exactMatch
                }
                
                // Second try: common vacation keywords
                val vacationMatch = timeOffPlans.find { plan ->
                    plan.descriptor?.let { desc ->
                        desc.contains("vacation", ignoreCase = true) ||
                        desc.contains("annual", ignoreCase = true) ||
                        desc.contains("holiday", ignoreCase = true)
                    } == true
                }
                
                if (vacationMatch != null) {
                    logInfo("Vacation time off plan match found: ${vacationMatch.descriptor}")
                    return@map vacationMatch
                }
                
                // Third try: first available plan
                val firstPlan = timeOffPlans.firstOrNull()
                if (firstPlan != null) {
                    logWarning("Using first available time off plan: ${firstPlan.descriptor}")
                    return@map firstPlan
                }
                
                throw TimeOffPlanException("No suitable time off plan found for reason: $reason")
            }
    }

    /**
     * Step 4: Create time off entries for the date range.
     * Confidence: 90% - Complex date range and unit calculation
     */
    private fun createTimeOffEntries(
        flipAbsence: FlipAbsenceRequest,
        employee: WorkerProfileC0a0dce56eb142d39dbffeb505becf7a,
        selectedPlan: TimeOffPlans581c389cce1410000feacaebd2e40002,
        approverValidated: Boolean
    ): Mono<WorkdayMappingResult> {
        return Mono.fromCallable {
            val startDate = LocalDate.parse(flipAbsence.start_date)
            val endDate = LocalDate.parse(flipAbsence.end_date)
            val dateRange = generateDateRange(startDate, endDate)
            
            val timeOffRequest = createTimeOffRequest(flipAbsence)
            val timeOffReference = createTimeOffReference(selectedPlan)
            val employeeReference = createEmployeeReference(employee)
            
            var totalUnits = 0
            
            val timeOffEntries = dateRange.map { date ->
                val units = calculateUnits(
                    date = date,
                    startHalfDay = flipAbsence.start_half_day,
                    endHalfDay = flipAbsence.end_half_day,
                    startDate = startDate,
                    endDate = endDate
                )
                
                totalUnits += units
                
                TimeOffEntries436f2afb755f100012528fa3260e000f(
                    date = date,
                    units = units,
                    employee = employeeReference,
                    timeOff = timeOffReference,
                    timeOffRequest = timeOffRequest,
                    unitOfTime = UnitOfTime436f2afb755f100012528fdc5a960014(
                        descriptor = "Hours", // Assuming hours-based calculation
                        id = "TIME_OFF_UNIT_HOURS"
                    ),
                    descriptor = "Time off entry for ${date} (${units} units)",
                    id = generateTimeOffEntryId(employee.id, date),
                    href = "/workers/${employee.id}/timeOffEntries/${generateTimeOffEntryId(employee.id, date)}"
                )
            }
            
            logInfo("Created ${timeOffEntries.size} time off entries for ${dateRange.size} days, total units: $totalUnits")
            
            WorkdayMappingResult(
                timeOffEntries = timeOffEntries,
                employee = employee,
                selectedPlan = selectedPlan,
                approverValidated = approverValidated,
                totalDays = dateRange.size.toLong(),
                totalUnits = totalUnits
            )
        }
    }

    /**
     * Generate date range from start to end date (inclusive).
     */
    private fun generateDateRange(startDate: LocalDate, endDate: LocalDate): List<LocalDate> {
        val days = ChronoUnit.DAYS.between(startDate, endDate) + 1
        return (0 until days).map { startDate.plusDays(it) }
    }

    /**
     * Calculate units for a specific date based on half-day flags.
     * Confidence: 95% - Precise unit calculation logic
     * 
     * Unit system:
     * - Full day = 8 units (8 hours)
     * - Half day = 4 units (4 hours)
     */
    private fun calculateUnits(
        date: LocalDate,
        startHalfDay: Boolean,
        endHalfDay: Boolean,
        startDate: LocalDate,
        endDate: LocalDate
    ): Int {
        return when {
            date == startDate && date == endDate -> {
                // Single day absence
                when {
                    startHalfDay && endHalfDay -> 0 // Invalid: both half days on same day
                    startHalfDay || endHalfDay -> 4 // Half day = 4 units
                    else -> 8 // Full day = 8 units
                }
            }
            date == startDate -> if (startHalfDay) 4 else 8
            date == endDate -> if (endHalfDay) 4 else 8
            else -> 8 // Full day for middle days
        }
    }

    /**
     * Create time off request with metadata.
     * Confidence: 75% - Metadata mapping
     */
    private fun createTimeOffRequest(flipAbsence: FlipAbsenceRequest): TimeOffRequest436f2afb755f100012528fd1e2e60013 {
        return TimeOffRequest436f2afb755f100012528fd1e2e60013(
            descriptor = "Absence request created at ${flipAbsence.createdAt} for ${flipAbsence.reason}",
            status = "Submitted",
            id = generateRequestId(),
            href = "/timeOffRequests/${generateRequestId()}"
        )
    }

    /**
     * Create time off reference from selected plan.
     */
    private fun createTimeOffReference(selectedPlan: TimeOffPlans581c389cce1410000feacaebd2e40002): TimeOff436f2afb755f100012528fbfc62e0011 {
        return TimeOff436f2afb755f100012528fbfc62e0011(
            id = selectedPlan.id,
            descriptor = selectedPlan.descriptor,
            plan = Plan436f2afb755f1000124523c2d036000a(
                id = selectedPlan.id,
                descriptor = selectedPlan.descriptor,
                href = selectedPlan.href
            ),
            href = selectedPlan.href
        )
    }

    /**
     * Create employee reference from worker profile.
     */
    private fun createEmployeeReference(employee: WorkerProfileC0a0dce56eb142d39dbffeb505becf7a): Employee436f2afb755f100012528fe3effe0015 {
        return Employee436f2afb755f100012528fe3effe0015(
            id = employee.id ?: throw IllegalStateException("Employee ID cannot be null"),
            descriptor = employee.descriptor,
            href = employee.href
        )
    }

    /**
     * Generate unique request ID.
     */
    private fun generateRequestId(): String {
        return "FLIP_REQ_${UUID.randomUUID().toString().replace("-", "").take(12).uppercase()}"
    }

    /**
     * Generate unique time off entry ID.
     */
    private fun generateTimeOffEntryId(employeeId: String?, date: LocalDate): String {
        val employeeIdSafe = employeeId?.take(8) ?: "UNKNOWN"
        val dateStr = date.format(DateTimeFormatter.ofPattern("yyyyMMdd"))
        return "TOE_${employeeIdSafe}_${dateStr}"
    }

    // Logging utilities
    private fun logInfo(message: String) {
        println("[INFO] AbsenceToWorkdayMapper: $message")
    }

    private fun logWarning(message: String) {
        println("[WARN] AbsenceToWorkdayMapper: $message")
    }

    private fun logError(message: String) {
        println("[ERROR] AbsenceToWorkdayMapper: $message")
    }
}

/**
 * Custom exceptions for mapping errors.
 */
class WorkerNotFoundException(message: String) : RuntimeException(message)
class ApprovalException(message: String) : RuntimeException(message)
class TimeOffPlanException(message: String) : RuntimeException(message)

/**
 * Extension functions for easier usage.
 */
fun AbsenceToWorkdayMapper.mapAbsenceToWorkdayBlocking(flipAbsence: AbsenceToWorkdayMapper.FlipAbsenceRequest): AbsenceToWorkdayMapper.WorkdayMappingResult {
    return mapAbsenceToWorkday(flipAbsence).block()
        ?: throw RuntimeException("Failed to map absence to Workday")
}

/**
 * Utility function to create a sample Flip absence request for testing.
 */
fun createSampleFlipAbsenceRequest(): AbsenceToWorkdayMapper.FlipAbsenceRequest {
    return AbsenceToWorkdayMapper.FlipAbsenceRequest(
        employee_id = "WORKER_123",
        approver_id = "MANAGER_456",
        start_date = "2025-01-20",
        end_date = "2025-01-22",
        reason = "Vacation",
        start_half_day = false,
        end_half_day = true,
        createdAt = "2025-01-16T10:30:00Z"
    )
} 