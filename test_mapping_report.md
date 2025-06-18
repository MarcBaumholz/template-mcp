# 🔄 API Schema Mapping Report

**Generated:** 2025-06-16 13:42:04  
**Processing Time:** 165.18 seconds  
**Source:** `examples/sample_employee_data.json`  
**Target Collection:** `stackone_api`

---

## 📊 Executive Summary

This report analyzes **16** source fields against the target API schema and provides intelligent mapping recommendations using multi-agent AI analysis.

### Key Findings
- **Fields Analyzed:** 16
- **Successful Matches:** 7 (43.8%)
- **Average Confidence:** 61.5%
- **Processing Context:** Employee time off and absence management system

## 📈 Confidence Distribution

| Confidence Level | Count | Percentage |
|------------------|-------|------------|
| 🟢 High (>70%)   | 0 | 0.0% |
| 🟡 Moderate (50-70%) | 7 | 43.8% |
| 🟠 Low (30-50%)   | 0 | 0.0% |
| 🔴 No Match (<30%) | 9 | 56.2% |

## 📋 Detailed Field Mappings

### 1. 🟡 `employee`

**Type:** `object`  
**Path:** `employee`  
**Overall Confidence:** 61.5%  
**Recommendation:** Moderate confidence match: Schema

#### 🎯 Top Matches

**1. `Schema` `NO MATCH`**
- **Path:** `Schema`
- **Type:** `schema`
- **Confidence:** 5.7%
- **Reasoning:** RAG similarity: 0.466, Cognitive: 0.057
**2. `Schema` `NO MATCH`**
- **Path:** `Schema`
- **Type:** `schema`
- **Confidence:** 5.7%
- **Reasoning:** RAG similarity: 0.314, Cognitive: 0.057
**3. `Path` `NO MATCH`**
- **Path:** `/employees`
- **Type:** `endpoint`
- **Confidence:** 3.3%
- **Reasoning:** RAG similarity: 0.336, Cognitive: 0.033

#### 🤖 AI Agent Analysis

**FlipInfoAgent** `MODERATE`
- **Insight:** Text analysis fallback
- **Reasoning:** Flip domain analysis: ...

**WorldKnowledgeAgent** `MODERATE`
- **Insight:** General knowledge analysis
- **Reasoning:** World knowledge: ...

**CognitiveMatchingAgent** `LOW`
- **Insight:** Cognitive match for Schema
- **Reasoning:** Cognitive analysis: ...

**Notes:** Analyzed 3 potential matches with 4 agent insights. Context: Employee time off and absence management system...

### 2. 🟡 `emp_id`

**Type:** `string`  
**Path:** `employee.emp_id`  
**Overall Confidence:** 61.5%  
**Recommendation:** Moderate confidence match: Schema

#### 🎯 Top Matches

**1. `Schema` `NO MATCH`**
- **Path:** `Schema`
- **Type:** `schema`
- **Confidence:** 6.7%
- **Reasoning:** RAG similarity: 0.480, Cognitive: 0.067
**2. `Path` `NO MATCH`**
- **Path:** `/employees`
- **Type:** `endpoint`
- **Confidence:** 4.0%
- **Reasoning:** RAG similarity: 0.427, Cognitive: 0.040
**3. `Path` `NO MATCH`**
- **Path:** `/employees/{employee_id}/time-off`
- **Type:** `endpoint`
- **Confidence:** 4.0%
- **Reasoning:** RAG similarity: 0.356, Cognitive: 0.040

#### 🤖 AI Agent Analysis

**FlipInfoAgent** `MODERATE`
- **Insight:** Text analysis fallback
- **Reasoning:** Flip domain analysis: ...

**WorldKnowledgeAgent** `MODERATE`
- **Insight:** General knowledge analysis
- **Reasoning:** World knowledge: ...

**CognitiveMatchingAgent** `LOW`
- **Insight:** Cognitive match for Schema
- **Reasoning:** Cognitive analysis: ...

**Notes:** Analyzed 3 potential matches with 4 agent insights. Context: Employee time off and absence management system...

### 3. 🔴 `full_name`

**Type:** `string`  
**Path:** `employee.full_name`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 4. 🟡 `department`

**Type:** `string`  
**Path:** `employee.department`  
**Overall Confidence:** 61.5%  
**Recommendation:** Moderate confidence match: Path

#### 🎯 Top Matches

**1. `Path` `NO MATCH`**
- **Path:** `/employees`
- **Type:** `endpoint`
- **Confidence:** 8.6%
- **Reasoning:** RAG similarity: 0.339, Cognitive: 0.086
**2. `Schema` `NO MATCH`**
- **Path:** `Schema`
- **Type:** `schema`
- **Confidence:** 5.0%
- **Reasoning:** RAG similarity: 0.304, Cognitive: 0.050

#### 🤖 AI Agent Analysis

**FlipInfoAgent** `MODERATE`
- **Insight:** Text analysis fallback
- **Reasoning:** Flip domain analysis: ...

**WorldKnowledgeAgent** `MODERATE`
- **Insight:** General knowledge analysis
- **Reasoning:** World knowledge: ...

**CognitiveMatchingAgent** `LOW`
- **Insight:** Cognitive match for Path
- **Reasoning:** Cognitive analysis: ...

**Notes:** Analyzed 2 potential matches with 4 agent insights. Context: Employee time off and absence management system...

### 5. 🟡 `absence_request`

**Type:** `object`  
**Path:** `employee.absence_request`  
**Overall Confidence:** 61.5%  
**Recommendation:** Moderate confidence match: Schema

#### 🎯 Top Matches

**1. `Schema` `NO MATCH`**
- **Path:** `Schema`
- **Type:** `schema`
- **Confidence:** 1.9%
- **Reasoning:** RAG similarity: 0.397, Cognitive: 0.019

#### 🤖 AI Agent Analysis

**FlipInfoAgent** `MODERATE`
- **Insight:** Text analysis fallback
- **Reasoning:** Flip domain analysis: ...

**WorldKnowledgeAgent** `MODERATE`
- **Insight:** General knowledge analysis
- **Reasoning:** World knowledge: ...

**CognitiveMatchingAgent** `LOW`
- **Insight:** Cognitive match for Schema
- **Reasoning:** Cognitive analysis: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day', 'code': 429, 'metadata': {'hea...

**Notes:** Analyzed 1 potential matches with 4 agent insights. Context: Employee time off and absence management system...

### 6. 🔴 `request_id`

**Type:** `string`  
**Path:** `employee.absence_request.request_id`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 7. 🟡 `start_date`

**Type:** `date`  
**Path:** `employee.absence_request.start_date`  
**Overall Confidence:** 61.5%  
**Recommendation:** Moderate confidence match: Schema

#### 🎯 Top Matches

**1. `Schema` `NO MATCH`**
- **Path:** `Schema`
- **Type:** `schema`
- **Confidence:** 5.0%
- **Reasoning:** RAG similarity: 0.406, Cognitive: 0.050

#### 🤖 AI Agent Analysis

**FlipInfoAgent** `MODERATE`
- **Insight:** Text analysis fallback
- **Reasoning:** Flip domain analysis: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day', 'code': 429, 'metadata': {'h...

**WorldKnowledgeAgent** `MODERATE`
- **Insight:** General knowledge analysis
- **Reasoning:** World knowledge: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day', 'code': 429, 'metadata': {'header...

**CognitiveMatchingAgent** `LOW`
- **Insight:** Cognitive match for Schema
- **Reasoning:** Cognitive analysis: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day', 'code': 429, 'metadata': {'hea...

**Notes:** Analyzed 1 potential matches with 4 agent insights. Context: Employee time off and absence management system...

### 8. 🟡 `end_date`

**Type:** `date`  
**Path:** `employee.absence_request.end_date`  
**Overall Confidence:** 61.5%  
**Recommendation:** Moderate confidence match: Schema

#### 🎯 Top Matches

**1. `Schema` `NO MATCH`**
- **Path:** `Schema`
- **Type:** `schema`
- **Confidence:** 5.7%
- **Reasoning:** RAG similarity: 0.429, Cognitive: 0.057

#### 🤖 AI Agent Analysis

**FlipInfoAgent** `MODERATE`
- **Insight:** Text analysis fallback
- **Reasoning:** Flip domain analysis: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-min. ', 'code': 429, 'metadata': {'headers': {'X-RateLimit-Limit': '20', 'X-RateLimit-Remaini...

**WorldKnowledgeAgent** `MODERATE`
- **Insight:** General knowledge analysis
- **Reasoning:** World knowledge: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-min. ', 'code': 429, 'metadata': {'headers': {'X-RateLimit-Limit': '20', 'X-RateLimit-Remaining': ...

**CognitiveMatchingAgent** `LOW`
- **Insight:** Cognitive match for Schema
- **Reasoning:** Cognitive analysis: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-min. ', 'code': 429, 'metadata': {'headers': {'X-RateLimit-Limit': '20', 'X-RateLimit-Remaining...

**Notes:** Analyzed 1 potential matches with 4 agent insights. Context: Employee time off and absence management system...

### 9. 🔴 `absence_type`

**Type:** `string`  
**Path:** `employee.absence_request.absence_type`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found
**Description:** String identifier

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 10. 🔴 `status`

**Type:** `string`  
**Path:** `employee.absence_request.status`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 11. 🔴 `total_days`

**Type:** `integer`  
**Path:** `employee.absence_request.total_days`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 12. 🔴 `reason`

**Type:** `string`  
**Path:** `employee.absence_request.reason`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 13. 🔴 `manager_approval`

**Type:** `object`  
**Path:** `employee.manager_approval`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 14. 🔴 `manager_id`

**Type:** `string`  
**Path:** `employee.manager_approval.manager_id`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

### 15. 🟡 `approval_status`

**Type:** `string`  
**Path:** `employee.manager_approval.approval_status`  
**Overall Confidence:** 61.5%  
**Recommendation:** Moderate confidence match: Path

#### 🎯 Top Matches

**1. `Path` `NO MATCH`**
- **Path:** `/employees`
- **Type:** `endpoint`
- **Confidence:** 6.3%
- **Reasoning:** RAG similarity: 0.307, Cognitive: 0.063

#### 🤖 AI Agent Analysis

**FlipInfoAgent** `MODERATE`
- **Insight:** Text analysis fallback
- **Reasoning:** Flip domain analysis: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-min. ', 'code': 429, 'metadata': {'headers': {'X-RateLimit-Limit': '20', 'X-RateLimit-Remaini...

**WorldKnowledgeAgent** `MODERATE`
- **Insight:** General knowledge analysis
- **Reasoning:** World knowledge: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-min. ', 'code': 429, 'metadata': {'headers': {'X-RateLimit-Limit': '20', 'X-RateLimit-Remaining': ...

**CognitiveMatchingAgent** `LOW`
- **Insight:** Cognitive match for Path
- **Reasoning:** Cognitive analysis: Error: Error code: 429 - {'error': {'message': 'Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day', 'code': 429, 'metadata': {'hea...

**Notes:** Analyzed 1 potential matches with 4 agent insights. Context: Employee time off and absence management system...

### 16. 🔴 `comments`

**Type:** `string`  
**Path:** `employee.manager_approval.comments`  
**Overall Confidence:** 0.0%  
**Recommendation:** No suitable matches found

#### ❌ No Matches Found
No suitable matches were discovered in the target API.

**Notes:** No potential matches discovered in target API

## 💡 Recommendations

### ⚠️ Requires Manual Review
The following **9** fields could not be automatically matched and require manual investigation:

- `full_name` (string)
- `request_id` (string)
- `absence_type` (string)
- `status` (string)
- `total_days` (integer)
- `reason` (string)
- `manager_approval` (object)
- `manager_id` (string)
- `comments` (string)

### 🎯 General Recommendations

1. **High Confidence Matches:** Implement these mappings first as they have strong semantic and contextual alignment.
2. **Moderate Confidence:** Review the AI agent insights and validate matches before implementation.
3. **Low Confidence:** Consider alternative field names or check if target API supports these concepts.
4. **No Matches:** Investigate if these fields exist under different names or if new fields need to be created.

---

## 📝 Report Details

**Request Parameters:**
- **Source JSON:** `examples/sample_employee_data.json`
- **Analysis MD:** `examples/sample_employee_analysis.md`
- **Target Collection:** `stackone_api`
- **Max Matches per Field:** 3

**Processing Information:**
- **Generated At:** 2025-06-16 13:42:04 UTC
- **Processing Time:** 165.18 seconds
- **Tool Version:** Schema Mapping Tool v1.0

*This report was generated by the AI-powered Schema Mapping Tool using multi-agent analysis and cognitive pattern recognition.*