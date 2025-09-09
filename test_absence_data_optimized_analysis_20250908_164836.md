# Comprehensive Field Analysis Report

**Generated:** 2025-09-08 16:48:36
**Source:** test_absence_data_optimized.json
**Fields:** 11
**Validation:** Missing data array fields: ['duration']

## duration.value
- **Semantic Description:** Numerical length of time period
- **Use Case:** Calculate payroll or track time off
- **Ground Truth Evidence:**
  1. [schema_properties] (score: 0.43)
```
Properties for GetHrisAbsenceTypesSuccessfulResponseDataResultsInner:
• id (string)
• name (string)
• unit (string) - values: HOURS, DAYS
• half_days_supported (boolean)
• exact_times_supported (boolean)
• remote_id (string)
• remote_data (string)
• changed_at (string)
• remote_deleted_at (string)
```
  2. [schema_properties] (score: 0.40)
```
Properties for AbsenceCreation:
• employee_external_id
• absence_type_external_id
• status (string) - values: REQUESTED, APPROVED
• start_date (string)
• end_date (string)
• start_half_day (boolean)
• end_half_day (boolean)
• amount (number)
• unit (string) - values: DAYS
• employee_note (string)
```
  3. [schema_summary] (score: 0.39)
```
Schema: Absence
Type: object
Required Fields: external_id, start_date, end_date, start_half_day, end_half_day, status, duration, type, created_at, updated_at, is_cancellable, is_deletable
```

## employeeId
- **Semantic Description:** Unique identifier for an employee
- **Use Case:** Link absence records to specific employees
- **Ground Truth Evidence:**
  1. [schema_summary] (score: 0.50)
```
Schema: AbsenceType
Type: object
Description: Represents a type of absence with additional configuration
support which an employee can then consume.
Required Fields: external_id, name, unit, half_days_supported, exact_times_supported, created_at, updated_at
```
  2. [schema_properties] (score: 0.50)
```
Properties for PostHrisAbsencesSuccessfulResponseData:
• id (string)
• remote_id (string)
• employee_id (string)
• approver_id (string)
• start_date (string)
• end_date (string)
• start_half_day (boolean)
• end_half_day (boolean)
• start_time (string)
• end_time (string)
• amount (number)
• unit (string) - values: HOURS, DAYS
• status (string)
• employee_note (string)
• type_id (string)
• changed_at (string)
• remote_deleted_at (string)
• remote_data (string)
```
  3. [schema_properties] (score: 0.48)
```
Properties for AbsenceCreation:
• employee_external_id
• absence_type_external_id
• status (string) - values: REQUESTED, APPROVED
• start_date (string)
• end_date (string)
• start_half_day (boolean)
• end_half_day (boolean)
• amount (number)
• unit (string) - values: DAYS
• employee_note (string)
```

## createdAt
- **Semantic Description:** Timestamp when record was initially created
- **Use Case:** Audit trail and chronological tracking
- **Ground Truth Evidence:**
  1. [schema_summary] (score: 0.57)
```
Schema: AbsenceDurationUnit
Type: string
```
  2. [schema_summary] (score: 0.55)
```
Schema: Absences
Type: object
```
  3. [schema_summary] (score: 0.54)
```
Schema: CreateAbsencesErrorCode
Type: string
```

## id
- **Semantic Description:** Unique identifier for the absence record
- **Use Case:** Primary key for absence management
- **Ground Truth Evidence:**
  1. [schema_summary] (score: 0.59)
```
Schema: AbsenceDurationUnit
Type: string
```
  2. [schema_summary] (score: 0.55)
```
Schema: AbsenceCreation
Type: object
```
  3. [schema_summary] (score: 0.46)
```
Schema: AbsenceStatus
Type: object
Required Fields: mapped, raw
```

## endDate
- **Semantic Description:** Date when the absence period concludes
- **Use Case:** Determine return-to-work date
- **Ground Truth Evidence:**
  1. [schema_properties] (score: 0.54)
```
Properties for Absence:
• external_id
• approver_external_id
• start_date (string)
• end_date (string)
• start_half_day (boolean)
• end_half_day (boolean)
• start_time (string)
• end_time (string)
• duration (object): defines the duration of the absence
• status
• is_cancellable (boolean)
• is_deletable (boolean)
• requestor_comment (string)
• type
• created_at
• updated_at
```
  2. [schema_summary] (score: 0.53)
```
Schema: AbsenceDurationUnit
Type: string
```
  3. [schema_summary] (score: 0.50)
```
Schema: Absence
Type: object
Required Fields: external_id, start_date, end_date, start_half_day, end_half_day, status, duration, type, created_at, updated_at, is_cancellable, is_deletable
```

## duration.unit
- **Semantic Description:** Time unit for duration measurement
- **Use Case:** Standardize time calculations
- **Ground Truth Evidence:**
  1. [schema_properties] (score: 0.45)
```
Properties for GetHrisAbsenceTypesSuccessfulResponseDataResultsInner:
• id (string)
• name (string)
• unit (string) - values: HOURS, DAYS
• half_days_supported (boolean)
• exact_times_supported (boolean)
• remote_id (string)
• remote_data (string)
• changed_at (string)
• remote_deleted_at (string)
```
  2. [schema_summary] (score: 0.41)
```
Schema: AbsenceStatus
Type: object
Required Fields: mapped, raw
```
  3. [schema_summary] (score: 0.39)
```
Schema: Absence
Type: object
Required Fields: external_id, start_date, end_date, start_half_day, end_half_day, status, duration, type, created_at, updated_at, is_cancellable, is_deletable
```

## startDate
- **Semantic Description:** Date when the absence period begins
- **Use Case:** Schedule coverage and plan workloads
- **Ground Truth Evidence:**
  1. [schema_properties] (score: 0.53)
```
Properties for Absence:
• external_id
• approver_external_id
• start_date (string)
• end_date (string)
• start_half_day (boolean)
• end_half_day (boolean)
• start_time (string)
• end_time (string)
• duration (object): defines the duration of the absence
• status
• is_cancellable (boolean)
• is_deletable (boolean)
• requestor_comment (string)
• type
• created_at
• updated_at
```
  2. [schema_summary] (score: 0.53)
```
Schema: AbsenceDurationUnit
Type: string
```
  3. [schema_summary] (score: 0.48)
```
Schema: Absence
Type: object
Required Fields: external_id, start_date, end_date, start_half_day, end_half_day, status, duration, type, created_at, updated_at, is_cancellable, is_deletable
```

## type
- **Semantic Description:** Category or reason for the absence
- **Use Case:** Track different leave types
- **Ground Truth Evidence:**
  1. [schema_summary] (score: 0.68)
```
Schema: Absences
Type: object
```
  2. [schema_summary] (score: 0.61)
```
Schema: AbsenceDurationUnit
Type: string
```
  3. [schema_summary] (score: 0.61)
```
Schema: AbsenceCreation
Type: object
```

## duration
- **Semantic Description:** Complete time period specification
- **Use Case:** Quick overview of absence length
- **Ground Truth Evidence:**
  1. [schema_properties] (score: 0.43)
```
Properties for GetHrisAbsenceTypesSuccessfulResponseDataResultsInner:
• id (string)
• name (string)
• unit (string) - values: HOURS, DAYS
• half_days_supported (boolean)
• exact_times_supported (boolean)
• remote_id (string)
• remote_data (string)
• changed_at (string)
• remote_deleted_at (string)
```
  2. [operation_parameters] (score: 0.42)
```
Parameters for GET /api/hris/v4/absences:
• unnamed
• unnamed
• unnamed
• x-auth-email (in: header) - Used for identifying the employee
• sort (in: query) - type: array
• date_from (in: query) - REQUIRED - type: string - Specifies the begin (inclusive) of the time range from which absences are queried.
Format: Date in YYYY-MM-DD format.
Time zone: To standardize time zone handling this parameter has to be in UTC.
Restriction: This parameter must not specify a date that is more than 2 years in the past from the current date. This ensures data relevance and optimizes performance by limiting the amount of historical data retrieved.
Example: If today's date is 2024-04-23, the earliest permissible value for date_from would be 2021-04-23.
• date_until (in: query) - REQUIRED - type: string - Specifies the end (inclusive) of the time range from which absences are queried.
Format: Date in YYYY-MM-DD format.
Time zone: To standardize time zone handling this parameter has to be in UTC.
Restriction: The date must not be more than 2 years in the future from the current date to ensure data relevance and optimize performance.
```
  3. [schema_summary] (score: 0.42)
```
Schema: AbsenceType
Type: object
Description: Represents a type of absence with additional configuration
support which an employee can then consume.
Required Fields: external_id, name, unit, half_days_supported, exact_times_supported, created_at, updated_at
```

## updatedAt
- **Semantic Description:** Timestamp when record was last modified
- **Use Case:** Track changes and updates
- **Ground Truth Evidence:**
  1. [schema_summary] (score: 0.53)
```
Schema: AbsenceStatus
Type: object
Required Fields: mapped, raw
```
  2. [schema_summary] (score: 0.49)
```
Schema: Absences
Type: object
```
  3. [schema_summary] (score: 0.46)
```
Schema: AbsenceCreation
Type: object
```

## status
- **Semantic Description:** Current approval state of the absence
- **Use Case:** Workflow management and reporting
- **Ground Truth Evidence:**
  1. [schema_summary] (score: 0.62)
```
Schema: AbsenceDurationUnit
Type: string
```
  2. [schema_properties] (score: 0.58)
```
Properties for AbsenceStatus:
• raw (string): contains the value of the external system if it cannot be mapped because it is unknown.
• mapped (string): defines the type of the status. - values: REQUESTED, PENDING, APPROVED
```
  3. [schema_properties] (score: 0.56)
```
Properties for GetHrisAbsenceTypesSuccessfulResponse:
• status (string) - values: SUCCESS
• data
```

