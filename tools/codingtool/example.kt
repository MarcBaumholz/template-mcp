package com.getflip.absences.stackone.controllers.mappers

import com.getflip.absences.stackone.hris.absence.management.models.Absence
import com.getflip.absences.stackone.hris.absence.management.models.AbsenceDuration
import com.getflip.absences.stackone.hris.absence.management.models.AbsenceDurationUnit
import com.getflip.absences.stackone.hris.absence.management.models.AbsenceStatus
import com.stackone.stackone_client_java.models.components.TimeOff
import com.stackone.stackone_client_java.models.components.TimeOffValue
import java.time.OffsetDateTime
import java.time.temporal.ChronoUnit

class CreateTimeOffRequestToAbsence {
    companion object {
        fun map(dto: TimeOff): Absence = Absence(
            externalId = dto.id().get() ?: throw IllegalArgumentException("TimeOff ID is required"),
            startDate = dto.startDate().get()?.toLocalDate()
                ?: throw IllegalArgumentException("Start date is required"),
            endDate = dto.endDate().get().toLocalDate() ?: throw IllegalArgumentException("End date is required"),
            startHalfDay = false,
            endHalfDay = false,
            duration = calculateDuration(dto.startDate().get(), dto.endDate().get()),
            status = mapTimeOffStatusToAbsenceStatus(dto.status().get().value()
                .get()),
            isCancellable = true,
            isDeletable = true,
            type = TimeOffTypeEnumToAbsenceTypeMapper.mapTimeOffTypeToAbsenceType(dto.type().get().value()
                .get()),
            createdAt = dto.createdDate().orElse(OffsetDateTime.now()),
            updatedAt = dto.updatedDate().orElse(OffsetDateTime.now()),
        )

        private fun mapTimeOffStatusToAbsenceStatus(timeOffStatus: TimeOffValue?): AbsenceStatus {
            val mappedStatus = when (timeOffStatus) {
                TimeOffValue.APPROVED -> AbsenceStatus.Mapped.APPROVED
                TimeOffValue.CANCELLED -> AbsenceStatus.Mapped.CANCELLED
                TimeOffValue.REJECTED -> AbsenceStatus.Mapped.DECLINED
                TimeOffValue.PENDING -> AbsenceStatus.Mapped.PENDING
                TimeOffValue.UNMAPPED_VALUE -> AbsenceStatus.Mapped.UNKNOWN
                else -> AbsenceStatus.Mapped.UNKNOWN
            }
            return AbsenceStatus(
                raw = timeOffStatus.toString(),
                mapped = mappedStatus
            )
        }

        private fun calculateDuration(startDate: OffsetDateTime?, endDate: OffsetDateTime?): AbsenceDuration {
            val duration = if (startDate != null && endDate != null) {
                MapperHelper.calculateBetweenDates(startDate, endDate, ChronoUnit.DAYS)
            } else {
                0.toDouble()
            }
            return AbsenceDuration(duration, AbsenceDurationUnit.DAYS)
        }
    }
}
