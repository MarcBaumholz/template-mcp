package com.flip.integrations

import io.micronaut.http.*
import io.micronaut.http.annotation.*
import io.micronaut.security.annotation.*
import io.micronaut.security.rules.SecurityRule
import jakarta.inject.Singleton
import org.slf4j.LoggerFactory
import io.micronaut.security.authentication.Authentication
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Verified Endpoint(s):
 * - POST /timeOffEntries - Create time-off entry
 * - GET /timeOffEntries - List time-off entries
 * Fields: id, employeeId, absenceType, startDate, endDate, status, reason, employee.email, employee.firstName, employee.lastName, duration.value, employee.managerId
 */
@Controller("/api/absences")
@Secured(SecurityRule.IS_AUTHENTICATED)
class AbsenceController(private val service: AbsenceService) {

    private val log = LoggerFactory.getLogger(AbsenceController::class.java)

    @Post("/")
    fun createAbsence(auth: Authentication, request: CreateAbsenceRequest): HttpResponse<Any> {
        return try {
            val email = (auth.attributes["email"] as? String) ?: auth.name
            log.info("Creating absence for user: {}", email)
            val result = service.createAbsence(email, request)
            HttpResponse.ok(result)
        } catch (ex: Throwable) {
            log.error("Controller error creating absence", ex)
            HttpResponse.serverError()
        }
    }

    @Get("/")
    fun getAbsences(auth: Authentication): HttpResponse<Any> {
        return try {
            val email = (auth.attributes["email"] as? String) ?: auth.name
            log.info("Retrieving absences for user: {}", email)
            val result = service.getAbsencesByEmail(email)
            HttpResponse.ok(result)
        } catch (ex: Throwable) {
            log.error("Controller error retrieving absences", ex)
            HttpResponse.serverError()
        }
    }

    @Get("/{absenceId}")
    fun getAbsenceById(auth: Authentication, @PathVariable absenceId: String): HttpResponse<Any> {
        return try {
            val email = (auth.attributes["email"] as? String) ?: auth.name
            log.info("Retrieving absence {} for user: {}", absenceId, email)
            val result = service.getAbsenceById(email, absenceId)
            HttpResponse.ok(result)
        } catch (ex: Throwable) {
            log.error("Controller error retrieving absence {}", absenceId, ex)
            HttpResponse.serverError()
        }
    }
}

@Singleton
class AbsenceService(private val stackoneClient: StackOneClient) {
    private val log = LoggerFactory.getLogger(AbsenceService::class.java)

    fun createAbsence(email: String, request: CreateAbsenceRequest): AbsenceResponse {
        return try {
            log.info("Processing absence creation for user: {}", email)
            val sourceDto = SourceAbsenceDTO(
                id = generateAbsenceId(),
                employeeId = request.employeeId,
                employee = Employee(
                    id = request.employeeId,
                    firstName = request.employeeFirstName ?: "",
                    lastName = request.employeeLastName ?: "",
                    email = email,
                    department = null, // Not available in StackOne
                    managerId = request.managerId
                ),
                absenceType = request.absenceType,
                startDate = request.startDate,
                endDate = request.endDate,
                duration = Duration(
                    value = request.durationValue ?: 0,
                    unit = request.durationUnit ?: "days"
                ),
                status = "pending",
                reason = request.reason,
                createdAt = null, // Let StackOne handle timestamps
                updatedAt = null,
                approvedBy = null,
                approvedAt = null
            )
            
            val targetDto = AbsenceMapper.mapToTarget(sourceDto)
            val response = stackoneClient.createTimeOffEntry(targetDto)
            AbsenceMapper.mapFromTarget(response)
        } catch (ex: Throwable) {
            log.error("Service error creating absence for user: {}", email, ex)
            throw RuntimeException("Failed to create absence: ${ex.message}")
        }
    }

    fun getAbsencesByEmail(email: String): List<AbsenceResponse> {
        return try {
            log.info("Retrieving absences for user: {}", email)
            val response = stackoneClient.getTimeOffEntries(email)
            response.data?.map { AbsenceMapper.mapFromTarget(it) } ?: emptyList()
        } catch (ex: Throwable) {
            log.error("Service error retrieving absences for user: {}", email, ex)
            throw RuntimeException("Failed to retrieve absences: ${ex.message}")
        }
    }

    fun getAbsenceById(email: String, absenceId: String): AbsenceResponse {
        return try {
            log.info("Retrieving absence {} for user: {}", absenceId, email)
            val response = stackoneClient.getTimeOffEntry(absenceId)
            AbsenceMapper.mapFromTarget(response)
        } catch (ex: Throwable) {
            log.error("Service error retrieving absence {} for user: {}", absenceId, email, ex)
            throw RuntimeException("Failed to retrieve absence: ${ex.message}")
        }
    }

    private fun generateAbsenceId(): String {
        return "abs_${System.currentTimeMillis()}"
    }
}

object AbsenceMapper {
    
    fun mapToTarget(source: SourceAbsenceDTO): CreateTimeOffEntryRequest {
        return CreateTimeOffEntryRequest(
            employeeId = source.employeeId ?: "",
            timeOffType = mapAbsenceType(source.absenceType),
            startDate = source.startDate ?: "",
            endDate = source.endDate ?: "",
            description = source.reason ?: ""
        )
    }

    fun mapFromTarget(target: TimeOffEntryResponse): AbsenceResponse {
        return AbsenceResponse(
            id = target.id ?: "",
            employeeId = target.employeeId ?: "",
            employee = target.employee?.let { employee ->
                Employee(
                    id = employee.id ?: "",
                    firstName = employee.firstName ?: "",
                    lastName = employee.lastName ?: "",
                    email = employee.email ?: "",
                    department = null, // Not available in StackOne
                    managerId = employee.managerId
                )
            },
            absenceType = mapTimeOffType(target.timeOffType),
            startDate = target.startDate ?: "",
            endDate = target.endDate ?: "",
            duration = target.duration?.let { duration ->
                Duration(
                    value = duration.days ?: 0,
                    unit = "days"
                )
            },
            status = mapStatus(target.status),
            reason = target.description ?: "",
            createdAt = target.createdAt,
            updatedAt = target.updatedAt,
            approvedBy = target.approvedBy,
            approvedAt = target.approvedAt
        )
    }

    private fun mapAbsenceType(absenceType: String?): String {
        return when (absenceType) {
            "sick_leave" -> "sick"
            "vacation" -> "vacation"
            "personal_leave" -> "personal"
            "maternity_leave" -> "maternity"
            "paternity_leave" -> "paternity"
            "bereavement" -> "bereavement"
            "jury_duty" -> "jury_duty"
            "other" -> "other"
            else -> "other"
        }
    }

    private fun mapTimeOffType(timeOffType: String?): String {
        return when (timeOffType) {
            "sick" -> "sick_leave"
            "vacation" -> "vacation"
            "personal" -> "personal_leave"
            "maternity" -> "maternity_leave"
            "paternity" -> "paternity_leave"
            "bereavement" -> "bereavement"
            "jury_duty" -> "jury_duty"
            "other" -> "other"
            else -> "other"
        }
    }

    private fun mapStatus(status: String?): String {
        return when (status) {
            "submitted" -> "pending"
            "approved" -> "approved"
            "rejected" -> "rejected"
            "cancelled" -> "cancelled"
            "draft" -> "pending"
            else -> "pending"
        }
    }
}

// Data classes for Flip HRIS
data class CreateAbsenceRequest(
    val employeeId: String,
    val absenceType: String,
    val startDate: String,
    val endDate: String,
    val reason: String,
    val employeeFirstName: String? = null,
    val employeeLastName: String? = null,
    val managerId: String? = null,
    val durationValue: Int? = null,
    val durationUnit: String? = null
)

data class AbsenceResponse(
    val id: String,
    val employeeId: String,
    val employee: Employee? = null,
    val absenceType: String,
    val startDate: String,
    val endDate: String,
    val duration: Duration? = null,
    val status: String,
    val reason: String,
    val createdAt: String? = null,
    val updatedAt: String? = null,
    val approvedBy: String? = null,
    val approvedAt: String? = null
)

data class SourceAbsenceDTO(
    val id: String? = null,
    val employeeId: String? = null,
    val employee: Employee? = null,
    val absenceType: String? = null,
    val startDate: String? = null,
    val endDate: String? = null,
    val duration: Duration? = null,
    val status: String? = null,
    val reason: String? = null,
    val createdAt: String? = null,
    val updatedAt: String? = null,
    val approvedBy: String? = null,
    val approvedAt: String? = null
)

data class Employee(
    val id: String? = null,
    val firstName: String? = null,
    val lastName: String? = null,
    val email: String? = null,
    val department: String? = null,
    val managerId: String? = null
)

data class Duration(
    val value: Int? = null,
    val unit: String? = null
)

// Data classes for StackOne API
data class CreateTimeOffEntryRequest(
    val employeeId: String,
    val timeOffType: String,
    val startDate: String,
    val endDate: String,
    val description: String
)

data class TimeOffEntryResponse(
    val id: String? = null,
    val employeeId: String? = null,
    val employee: EmployeeInfo? = null,
    val timeOffType: String? = null,
    val startDate: String? = null,
    val endDate: String? = null,
    val duration: TimeOffDuration? = null,
    val status: String? = null,
    val description: String? = null,
    val createdAt: String? = null,
    val updatedAt: String? = null,
    val approvedBy: String? = null,
    val approvedAt: String? = null
)

data class EmployeeInfo(
    val id: String? = null,
    val firstName: String? = null,
    val lastName: String? = null,
    val email: String? = null,
    val department: String? = null,
    val managerId: String? = null
)

data class TimeOffDuration(
    val days: Int? = null,
    val hours: Int? = null
)

// StackOne API client interface
interface StackOneClient {
    fun createTimeOffEntry(request: CreateTimeOffEntryRequest): TimeOffEntryResponse
    fun getTimeOffEntries(employeeId: String): TimeOffEntryListResponse
    fun getTimeOffEntry(entryId: String): TimeOffEntryResponse
}

data class TimeOffEntryListResponse(
    val data: List<TimeOffEntryResponse>? = null,
    val pagination: PaginationInfo? = null,
    val meta: ResponseMeta? = null
)

data class PaginationInfo(
    val page: Int? = null,
    val limit: Int? = null,
    val total: Int? = null,
    val totalPages: Int? = null
)

data class ResponseMeta(
    val requestId: String? = null,
    val correlationId: String? = null,
    val processingTime: String? = null
)