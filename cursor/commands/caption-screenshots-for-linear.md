# Caption Linear Screenshots

Automatically adds descriptive captions to all screenshots in a Linear issue.

## Process

1. **Fetch the issue** using `mcp_Linear_get_issue` with the provided ticket ID
2. **Parse the description** to find all image URLs that do not have a caption already
3. **For each image:**
   - Download the image using `curl`
   - Read and analyze the image content
   - Generate a descriptive caption that explains:
     - What UI components are visible
     - What the screenshot demonstrates
     - Relevant details that relate to the ticket's problem
4. **Update the description** by:
   - Inserting an italicized caption after each image with the format `*[CURSOR CAPTION] Caption text explaining what the screenshot shows.*`
   - Preserve all existing text and formatting
5. **Update the issue** using `mcp_Linear_update_issue` with the enhanced description

## Caption Guidelines

- Be specific and descriptive
- Reference UI elements visible in the screenshot
- Connect the visual to the issue being reported
- Keep captions concise but informative (1-2 sentences)
- Use technical terms when relevant to the issue

## Example

### Input

```markdown
![image.png](https://uploads.linear.app/...)

Blah blah blah
```

### Output

```markdown
![image.png](https://uploads.linear.app/...)

*[CURSOR CAPTION] Screenshot showing the validation badges appearing out of order at the end of the tool chain instead of their proper sequential positions, with the header displaying "Answered" despite failed validations.*

Blah blah blah
```

## Error Handling

- If image URL signature is expired, note this in the output
- If no images found, inform the user
- If download fails, skip that image and continue with others
