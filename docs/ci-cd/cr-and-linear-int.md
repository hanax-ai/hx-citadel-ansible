Linear​
With CodeRabbit, you can easily link your pull requests with Linear. It makes your life simpler by automatically creating Linear issues with all the code context, keeping your issues and pull requests in sync both ways. Plus, it lets you generate issues straight from pull requests, track how you’re hitting your goals, and even turn code review feedback into actionable tasks in Linear.
​
CodeRabbit App​
Navigate to integrations in the CodeRabbit app.
Toggle the Linear switch to enable the integration.
Upon enabling the Linear integration, CodeRabbit will redirect you to the Linear login page. Enter your Linear credentials to authenticate the integration.
​
CodeRabbit Configuration​
Add Linear’s Team Keys to the knowledge_base.linear.team_keys field in your project’s CodeRabbit configuration file at .coderabbit.yaml.
​
Example Usage​
To link a Linear Issue, you can add the Linear Issue via the team key and issue number into the PR description as shown below.

// (Linear Team Key - Issue Number)Closes ENG-123
You can also create new Linear issues directly through CodeRabbit. Learn more in our Issue Creation guide.
​
GitHub​
GitHub issue integration works automatically without any additional setup required.
​
Example Usage​
To link a GitHub Issue, you can add the issue into the PR description as shown below.

// (# GitHub Issue Number)Closes #123
Overview
Overview
This integration allows CodeRabbit to connect your pull requests seamlessly with Linear, enabling bi-directional issue tracking and automated issue creation in Linear with code context.

CodeRabbit creates issues directly from pull requests, tracks completion of issue objectives, and allows developers to convert code review feedback into actionable Linear issues. By bridging the gap between code reviews and project management, CodeRabbit helps maintain code quality while keeping your project tracking up to date.

How it works
Issue Creation:
- When CodeRabbit identifies code quality concerns during its AI code reviews, developers can create new Linear issues with one-click directly from review comments.
- These automatically created issues include context from the code review, linking to the specific pull request and code location.

Issue validation:
- CodeRabbit automatically validates issues from existing Linear tickets during its AI code reviews if you add links to Linear issues in the description of a pull request

- CodeRabbit generates a table of objectives from the linked issue and marks which of those objects were met by the current pull request.

Related issues:

- CodeRabbit indexes issues from the authorized Linear workspace.

- CodeRabbit performs a similarity search on the indexed issues and lists possibly related issues in the summary section of its code reviews for every pull request..

Configure
After logging into CodeRabbit, go to Integrations and toggle the switch to enable Linear integration. You will be prompted to authorize CodeRabbit access to your Linear workspace. Once enabled, CodeRabbit will be able to read and create issues in your workspace and receive real-time updates about the workspace.

