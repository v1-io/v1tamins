Update the tool requested by the user to use the enhanced pagination wrapper.

## Required fields in template
To enable enhanced pagination, add these fields to your CustomToolDefinition:
### Required fields
1. pagination_page_size_max: int — Maximum page size the API allows (e.g., 100 for ChurnZero, 200 for HubSpot Search)
### Required (at least one)
2. pagination_next_after_path: Optional[str] — JSONPath to extract the next cursor from the response (e.g., "paging.next.after" for HubSpot, "pages.next.starting_after" for Intercom)
   - OR
3. pagination_cursor_param_name: Optional[str] — Name of the cursor parameter (e.g., "after" for HubSpot, "$skip" for ChurnZero offset-based)
### Optional but recommended
4. pagination_limit_param_name: Optional[str] — Name of the limit parameter (defaults to "limit" if not set)
   - Examples: "limit", "$top" (ChurnZero), "per_page" (Intercom)
5. total_path: Optional[str] — JSONPath to extract total count from response (e.g., "total" for HubSpot, "@odata.count" for ChurnZero)
6. response_data_path: Optional[str] — JSONPath to extract the data array from response (e.g., "results" for HubSpot, "value" for ChurnZero)
## Files associated with enhanced pagination
### Core pagination implementation
1. services/common/lib/integrations/pagination.py
   - Main pagination wrapper (fetch_paginated_data)
   - Handles cursor-based and offset-based pagination
   - Retry logic with exponential backoff
2. services/common/lib/integrations/config_templates.py
   - CustomToolDefinition model with pagination fields (lines 314-326)
   - Field definitions and defaults
### Executors (use pagination)
3. services/common/lib/integrations/direct_http_executor.py
   - _execute_with_pagination() (lines 880-939)
   - Uses fetch_paginated_data for direct HTTP connectors
4. services/common/lib/integrations/custom_tool_executor.py
   - _execute_with_pagination() (lines 367-434)
   - Uses fetch_paginated_data for Composio-based connectors
### Helper utilities
5. services/common/lib/integrations/tool_response_utils.py
   - should_use_pagination() (lines 34-42) — checks if tool supports pagination
   - extract_pagination_params() (lines 45-59) — extracts limit and pagination params
   - merge_pagination_metadata() (lines 62-82) — merges pagination metadata into response
6. services/common/lib/integrations/parameter_normalization.py
   - normalize_parameters() (lines 155-184) — handles parameter normalization for paginated tools
### Example templates (reference implementations)
7. services/common/lib/integrations/connectors/saas/churnzero/template.py
   - OData offset-based pagination ($top/$skip)
   - Example: lines 267-269, 343-345
8. services/common/lib/integrations/connectors/saas/hubspot/template.py
   - Cursor-based pagination (after cursor)
   - Example: lines 244-246, 333-335
9. services/common/lib/integrations/connectors/saas/intercom/template.py
   - Cursor-based pagination (starting_after)
   - Example: lines 54-57
## Example template configuration
Here's what a paginated tool looks like:
python
CustomToolDefinition(
    name="MY_CONNECTOR_LIST_ITEMS",
    endpoint="/items",
    method="GET",
    parameters=[
        ToolParameter(name="limit", type="integer", ...),
        ToolParameter(name="after", type="string", ...),
    ],
    query_parameters=["limit", "after"],
    response_data_path="results",  # Where the data array is in response
    pagination_page_size_max=100,  # REQUIRED: API max page size
    pagination_limit_param_name="limit",  # Optional: defaults to "limit"
    pagination_cursor_param_name="after",  # REQUIRED (or use pagination_next_after_path)
    pagination_next_after_path="paging.next.after",  # REQUIRED (or use pagination_cursor_param_name)
    total_path="total",  # Optional: for total count
)
## How it works
1. should_use_pagination() checks if pagination_page_size_max is set and either pagination_next_after_path or pagination_cursor_param_name is provided.
2. If enabled, the executor calls fetch_paginated_data() which:
   - Makes multiple API requests with appropriate page sizes
   - Handles cursor/offset advancement automatically
   - Aggregates results across pages
   - Respects the default_cap (from get_saas_pagination_default_cap())
   - Returns pagination metadata (pages fetched, total available, etc.)
The wrapper handles overflow pagination: if an agent requests 500 rows but the API max is 100, it fetches 5 pages automatically.





10:59
As long as you have those required fields in the custom tool definition, then it will just work. And if you add those optional parameters, then the truncation guidance message will be the best.
