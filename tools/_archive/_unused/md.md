# AI Task: Direct API Schema Mapping
ROLE:
You are an expert AI system integrator. Your task is to analyze the provided OpenAPI specification and map the source fields to the most appropriate destination fields within the spec.
This is a direct-analysis task. You will read the entire API spec and use your reasoning abilities to find the best matches.
## 📜 Source Field Analysis
Here is the analysis of the source data. It contains the fields that need to be mapped, along with their descriptions, data types, and possible synonyms.
```markdown
{analysis_content}
```
## 📄 Full OpenAPI Specification
Here is the complete OpenAPI specification for the destination system. Analyze it carefully to find the correct endpoints and schema properties.
```json
{api_spec_content}
```
## 🧠 Your Reasoning and Mapping Process
Follow these steps methodically for each source field listed in the analysis.
**Step 1: Identify the Target Endpoint**
- First, scan the API spec for the most relevant endpoint. Based on the context (e.g., "Absence Management/time offs"), this might be an endpoint like `POST /absences` or `PUT /timeOffRequests`.
- State the endpoint you have identified.
**Step 2: Locate the Request Body Schema**
- Once you've found the endpoint, locate the schema for its request body (usually found under `requestBody.content['application/json'].schema`).
- This schema contains the destination fields you need to map to.
**Step 3: Map Each Field (Think Step-by-Step)**
For each source field, perform the following reflection:
1.  **Direct Match:** Does a field with the exact same name or a very close synonym exist in the destination schema? If yes, declare it a "Direct Match" and provide the destination field name.
2.  **Semantic Match:** If there's no direct match, search for a field with a similar meaning or purpose. Use the descriptions from both the source analysis and the API spec to guide you. For example, `start_date` might map to `effectiveDate`. Declare this a "Semantic Match" and explain your reasoning.
3.  **No Match:** If you cannot find a suitable match after careful consideration, declare it "No Match" and recommend a `TODO` for manual review. Explain why you couldn't find a match.
**Step 4: Check if the mapping is complete**
- Check if all fields have been mapped.
- If there are fields that still need to be mapped, repeat the process for those fields.
- search the api spec again for the fields that still need to be mapped, and find the best match, this can be a synonym or a field that is most equal, or need a small logic calculation or datatype conversion
- for all fields that still need to be mapped, add a TODO: with what you recommend in the code and why there were no match, think about logic what can be done with what the api spec provides and what is the best way to implement it.
- very important, do not add any fields that are not in the api spec, only add fields that are in the api spec or can be mapped from the api spec, do not haluzinate, if a field is not in the api spec, do not add it, just add a TODO: with what you recommend in the code and why there were no match, think about logic what can be done with what the api spec provides and what is the best way to implement it.
## ➡ Final Output
Produce a clear, structured markdown report that presents the final mapping for each source field. Use the following format:
### **Mapping Results for Endpoint: `[Your Identified Endpoint]`**
| Source Field      | Destination Field | Match Type      | Justification / Notes                               |
|-------------------|-------------------|-----------------|-----------------------------------------------------|
| `[source_field_1]`  | `[destination_field_1]` | `Direct Match`    | `Exact name match.`                                 |
| `[source_field_2]`  | `[destination_field_2]` | `Semantic Match`  | `Maps to 'X' because it represents the same concept.` |
| `[source_field_3]`  | `(No Match)`      | `No Match`        | `TODO: No clear equivalent found for this field.`   |
