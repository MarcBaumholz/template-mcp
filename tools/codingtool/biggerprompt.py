#TODO MCP tool that uses the tempalte.kt and gives a more detailed prompt back for the Cursor LLM to use 

def generate_enhanced_prompt(mapping_info: str, kotlin_template: str) -> str:
    """
    Generates a detailed prompt for the Cursor LLM.
    Args:
        mapping_info: A string containing the results from a previous mapping analysis.
        kotlin_template: The content of the Kotlin template file.
    Returns:
        A detailed prompt for the LLM.
    """
    test = 2
    if test == 1:
        prompt = f"""
        You are an expert software developer specializing in system integration and data mapping. Your task is to generate Kotlin code based on a pre-existing mapping analysis.
        You will be filling a Kotlin template with logic based on the provided mapping between a source and a target system.
        **CONTEXT:**
        **1. Mapping Analysis Results:**
        The following mapping analysis has been performed. It shows which source fields map to which target fields, confidence scores, and notes.
        ```
        {mapping_info}
        ```
        **2. Kotlin Target Template:**
        This is the target Kotlin code structure that you need to fill. Your goal is to implement the logic to populate an instance of the target data class (e.g., `WorkdayEmployee`) from a source data object.
        ```kotlin
        {kotlin_template}
        ```
        **YOUR TASK:**
        Based on the mapping analysis, complete the Kotlin code. Follow these rules precisely:
        1.  **One-to-One Mapping:** For each field in the target Kotlin class, find its corresponding source field from the mapping analysis. Implement a direct assignment.
        2.  **Authentication:** Ensure any required authentication logic is considered. If the mapping analysis mentions authentication requirements, add comments indicating where to place authentication code. For now, you don't need to implement the full authentication flow.
        3.  **Mismatched or Missing Fields:**
            *   If a target field has **no corresponding source field** in the mapping, or the **data types are incompatible**, mark it with a `// TODO:` comment explaining the issue.
            *   For each `// TODO:`, you **must** also generate a placeholder Kotlin function that would perform the necessary transformation. The function should have a clear name, appropriate parameters, and a `TODO()` body.
        4.  **Transformation Logic Example:**
            *   **Scenario:** The mapping shows `source.startDate` maps to `target.hireDate`, but the target also has an `endEmploymentDate` which is not in the source.
            *   **Your action:**
                *   In the main mapping logic, for `endEmploymentDate`, add a comment: `// TODO: No direct mapping for endEmploymentDate. Requires calculation.`
                *   Generate a helper function like this:
                    ```kotlin
                    fun calculateEndEmploymentDate(hireDate: LocalDate): LocalDate 
                        // TODO: Implement logic to calculate end date, e.g., hireDate.plusYears(1)
                        TODO("Implement end date calculation logic")
                    
                    ```
        Your final output should be **only the completed Kotlin code one template file**, ready to be used. Do not include any explanations outside of the code comments. 
        It should be only one file, the template file, filled with the logic from the mapping analysis. very important.
        """
    else:
        prompt = f"""
            You are a Kotlin code generator. Your task is to fill a Kotlin template with mapping logic based on provided field mapping information.

            **STRICT REQUIREMENTS:**
            - Generate ONLY the completed Kotlin code
            - Do NOT add explanations, comments, or text outside the code
            - Follow the template structure exactly
            - Keep the file small and focused
            - Add TODO comments for unmappable fields
            - Use the exact variable names and types from the template

            **INPUT 1 - TEMPLATE STRUCTURE:**
            ```kotlin
            {kotlin_template}
            ```

            **INPUT 2 - FIELD MAPPING INFORMATION:**
            ```
            {mapping_info}
            ```

            **GENERATION RULES:**

            1. **Replace Template Variables:**
            - Replace all `${...}` placeholders with actual values from mapping context
            - Use descriptive but concise names (e.g., `AbsenceService`, `TimeOffEntry`)

            2. **Field Mapping Strategy:**
            - Direct match: `field = source.directField`
            - Similar match: `field = source.similarField` 
            - Type conversion: `field = source.field.toTargetType()`
            - Missing field: `field = TODO("Map missing field")`

            3. **Function Generation:**
            - Create conversion functions only when needed
            - Use `when` expressions for enum mappings
            - Add TODO for unmapped enum values
            - Keep functions minimal and focused

            4. **Type Aliases:**
            - Add typealias at the end for complex generated types
            - Use the format: `typealias SimpleType = ComplexGeneratedType`

            5. **Error Handling:**
            - Use `!!` for required fields that should never be null
            - Use `?:` with `error()` for critical missing data
            - Keep error messages descriptive but brief

            

            **OUTPUT FORMAT:**
            Return only the complete Kotlin file content. No markdown blocks, no explanations, no additional text.

            **GENERATE THE KOTLIN CODE NOW:**
            ```

            This prompt is specifically designed to:

            1. **Be highly directive** - tells Claude exactly what to do and what not to do
            2. **Focus on the template** - emphasizes following the structure exactly
            3. **Handle missing mappings** - clear instructions for TODO comments
            4. **Keep it minimal** - emphasizes small, focused code, only fill the template, nothing else‚
            5. **Provide concrete patterns** - shows exactly how to handle different mapping scenarios
            6. **Restrict output** - only wants the Kotlin code, nothing else

            The prompt uses the same successful patterns from your `AbsenceMapper.kt` example and ensures Claude will generate clean, focused code that follows your template structure precisely.

            """
    return prompt 