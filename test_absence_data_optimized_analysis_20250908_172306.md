# Field Analysis Report

**Generated:** 2025-09-08 17:23:06
**Source:** /Users/marcbaumholz/Library/CloudStorage/OneDrive-FlipGmbH/mcp-personal-server-py/template-mcp/test_absence_data_optimized.json
**Fields:** 3

## employeeId
- **Semantic Description:** Unique identifier for the employee
- **Use Case:** Link absence record to employee
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
  3. [schema_summary] (score: 0.47)
```
Schema: GetHrisAbsenceTypesSuccessfulResponse
Type: object
```

## type
- **Semantic Description:** Category of absence requested
- **Use Case:** Filter or report by absence type
- **Ground Truth Evidence:**
  1. [schema_summary] (score: 0.68)
```
Schema: Absences
Type: object
```
  2. [schema_summary] (score: 0.61)
```
Schema: AbsenceCreation
Type: object
```
  3. [schema_summary] (score: 0.54)
```
Schema: GetHrisAbsenceTypesSuccessfulResponseData
Type: object
```

## status
- **Semantic Description:** Current state of the absence request
- **Use Case:** Track approval workflow progress
- **Ground Truth Evidence:**
  1. [schema_properties] (score: 0.58)
```
Properties for AbsenceStatus:
• raw (string): contains the value of the external system if it cannot be mapped because it is unknown.
• mapped (string): defines the type of the status. - values: REQUESTED, PENDING, APPROVED
```
  2. [schema_properties] (score: 0.56)
```
Properties for GetHrisAbsenceTypesSuccessfulResponse:
• status (string) - values: SUCCESS
• data
```
  3. [schema_summary] (score: 0.53)
```
Schema: AbsenceType
Type: object
Description: Represents a type of absence with additional configuration
support which an employee can then consume.
Required Fields: external_id, name, unit, half_days_supported, exact_times_supported, created_at, updated_at
```

