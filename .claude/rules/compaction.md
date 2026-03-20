# Context Compaction

When context is compacted (automatically or via `/compact`), preserve the following information in the summary to avoid losing critical session state.

## Always Preserve

- **Modified files**: full list of files created, edited, or deleted in this session
- **Test results**: last test run output, failing tests, coverage numbers
- **Architectural decisions**: any design choices made and their rationale
- **Current task state**: what was completed, what remains, any blockers
- **Error context**: error messages and stack traces that are still being debugged
- **User preferences**: any corrections or feedback the user gave during the session

## Focused Compaction

When using `/compact <focus>`, summarize only what is relevant to the focus topic. Discard unrelated conversation history but still preserve the items above if they intersect with the focus.

## What Can Be Dropped

- Exploratory searches that led nowhere
- File contents that were read but not modified
- Intermediate tool outputs that have been superseded by later results
- Verbose diffs — summarize as "changed X in file Y" instead of repeating the full diff
