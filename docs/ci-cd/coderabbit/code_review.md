# Code review

> Best practices for performing effective code reviews with CodeRabbit. Learn recommended workflows, command usage, and tips for managing large changes.

<CardGroup cols={2}>
  <Card title="Control and manage code reviews" icon="bot-message-square" href="/guides/commands">
    Learn how to work with CodeRabbit through chat commands
  </Card>

  <Card title="Code review command reference" icon="terminal" href="/reference/review-commands">
    Complete reference for all CodeRabbit review commands
  </Card>
</CardGroup>

## Recommended code-review workflow

<Steps>
  <Step title="Start with incremental review">
    Use `@coderabbitai review` for checking new changes and getting focused
    feedback on recent modifications
  </Step>

  <Step title="Use full review for major changes">
    Use `@coderabbitai full review` when major changes require a fresh
    perspective or comprehensive analysis
  </Step>

  <Step title="Generate summaries">
    Generate summaries after significant updates using `@coderabbitai summary`
    to communicate changes clearly
  </Step>
</Steps>

## Managing large changes

<Steps>
  <Step title="Pause during development">
    Use `@coderabbitai pause` before making multiple commits to prevent
    unnecessary review noise
  </Step>

  <Step title="Resume when ready">
    Resume reviews with `@coderabbitai resume` when you're ready for feedback
  </Step>

  <Step title="Full review for substantial changes">
    Consider `@coderabbitai full review` after substantial changes to get
    comprehensive analysis
  </Step>
</Steps>

## Documentation flow

<Steps>
  <Step title="Finalize implementation">
    Complete your function implementations before generating documentation
  </Step>

  <Step title="Generate docstrings">
    Run `@coderabbitai generate docstrings` to create comprehensive function
    documentation
  </Step>
</Steps>

<Card title="Learn more about docstring generation" icon="book" href="/finishing-touches/docstrings">
  Complete guide to generating and customizing docstrings with CodeRabbit
</Card>

## Best practices

<CardGroup cols={2}>
  <Card title="Command flexibility" icon="terminal">
    * Commands are case-insensitive (`@coderabbitai REVIEW` = `@coderabbitai review`)
    * Commands can be issued by anyone with write access to the repository
    * Multiple commands can be used in sequence as needed
  </Card>

  <Card title="Configuration management" icon="gear">
    * Use `@coderabbitai configuration` to export your settings before making changes
    * Keep a backup of working configurations
    * Test configuration changes on smaller PRs first
  </Card>
</CardGroup>

## Command response time

<AccordionGroup>
  <Accordion title="Immediate commands">
    Most control commands take effect immediately:

    * `@coderabbitai pause`
    * `@coderabbitai resume`
    * `@coderabbitai ignore`
  </Accordion>

  <Accordion title="Review commands">
    Review commands typically complete within a few minutes, depending on:

    * PR size and complexity
    * Number of files changed
    * Codebase size and context
  </Accordion>

  <Accordion title="Generation commands">
    Docstring and summary generation time varies based on:

    * Number of functions to document
    * Complexity of code structure
    * Amount of context needed
  </Accordion>
</AccordionGroup>