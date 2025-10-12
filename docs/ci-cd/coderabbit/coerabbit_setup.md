# Setup

> Set up CodeRabbit with your Git platform and configure code review behavior for faster, more effective reviews.

CodeRabbit reviews work best when properly connected to your development workflow. This guide shows you how to set up platform access, issue tracking, and configuration that actually improves your team's review process.

## Set up platform access

CodeRabbit integrates differently with each Git platform, using each platform's recommended authentication methods.

<CardGroup cols={3}>
  <Card title="GitHub" icon="github">
    **GitHub App integration**

    Automatic `CodeRabbitAI` bot creation through GitHub's app installation process. No manual setup required.
  </Card>

  <Card title="GitLab" icon="gitlab">
    **Project tokens or service accounts**

    Project access tokens create automatic bot users, or use GitLab service accounts (17.6+) for organization-wide access.
  </Card>

  <Card title="Bitbucket" icon="bitbucket">
    **User account with API tokens**

    Create a dedicated user account and configure API tokens for authentication. No formal service accounts available.
  </Card>
</CardGroup>

<Tabs>
  <Tab title="GitHub">
    **No manual bot account creation required**

    CodeRabbit operates as a GitHub App, automatically creating the `CodeRabbitAI` bot user when you connect your organization.

    **Setup process:**

    1. Install the CodeRabbit app from GitHub Marketplace
    2. Grant repository permissions during installation
    3. `CodeRabbitAI` bot user is created automatically with appropriate access

    App permissions are managed through GitHub's organization settings under "Third-party access."
  </Tab>

  <Tab title="GitLab">
    **Project access tokens (recommended)**

    GitLab automatically creates non-billable bot users when you create project access tokens.

    **Setup process:**

    1. Navigate to **Project Settings → Access Tokens**
    2. Create token with scopes: `api`, `read_repository`, `write_repository`
    3. GitLab creates bot user with format: `project_{id}_bot_{random_string}`
    4. Bot email follows pattern: `project_{id}_bot_{string}@noreply.{gitlab_host}`

    **Alternative: GitLab service accounts (17.6+)**

    Top-level group owners can create dedicated service accounts that don't consume license seats. These provide organization-wide access rather than project-specific access.

    Bot users appear in project member lists but cannot be manually modified or added to other projects.
  </Tab>

  <Tab title="Bitbucket">
    **Create dedicated user account**

    Bitbucket Cloud doesn't have formal service accounts, so create a regular user account dedicated to CodeRabbit.

    **Setup process:**

    1. Create new user account with clear bot username (e.g., `yourorg-coderabbit-bot`)
    2. Add account to your team/workspace with necessary permissions
    3. Navigate to [API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens) in your Atlassian account settings
    4. Click **Create API token with scopes**
    5. Configure token with required scopes:
       * **Account & User:** `read:account`, `read:user:bitbucket`
       * **Repository:** `read:repository:bitbucket`, `write:repository:bitbucket`
       * **Pull Requests:** `read:pullrequest:bitbucket`, `write:pullrequest:bitbucket`
       * **Issues:** `read:issue:bitbucket`, `write:issue:bitbucket`
       * **Workspace:** `read:workspace:bitbucket`, `admin:project:bitbucket`
       * **Webhooks:** `read:webhook:bitbucket`, `write:webhook:bitbucket`
       * **Pipelines:** `read:pipeline:bitbucket`, `read:runner:bitbucket`
    6. Copy and securely store the API token (displayed only once)

    **Security note:** API tokens are tied to individual accounts. Store tokens securely as they provide authenticated access to everything the account can access.
  </Tab>
</Tabs>

For detailed platform-specific instructions, see [Integrate with Git platforms](/platforms/).

## Connect issue tracking

CodeRabbit analyzes whether pull request changes address specific ticketed issues. This works automatically with GitHub and GitLab issues, but requires setup for external systems.

**Built-in integration (no setup required):**

* GitHub Issues
* GitLab Issues

**External systems requiring integration:**

* **Jira** — Connect your Jira instance for issue analysis
* **Linear** — Link Linear issues to pull request context

For external issue systems, see [Integrate issue tracking](/integrations/issue-integrations/).

## Set up team reports

CodeRabbit's reporting feature keeps teams updated on repository changes. Set up these baseline reports using templates in the CodeRabbit web interface:

* **Daily standup report** — Grouped by contributor, shows recent activity
* **Regular release notes** — Grouped by repository, summarizes changes

Access reporting templates at [app.coderabbit.ai](https://app.coderabbit.ai/login) under the Reports section.

For detailed reporting setup, see [Generate reports](/guides/reports-overview).

## Configure review behavior

CodeRabbit gives you two configuration methods. Use both for the most effective setup.

### Web interface for rapid setup

The [CodeRabbit web interface](https://app.coderabbit.ai/login) lets you:

* Set organization-wide code review preferences
* Configure repository-specific settings
* Get familiar with available configuration options

Use **Organization Settings** and **Repositories** pages to establish baseline configuration quickly.

### YAML files for version control

Add a `.coderabbit.yaml` file to repositories for version-controlled configuration.

**Why use YAML configuration:**

* **Version control** — Track changes, view history, revert configurations
* **Pull request integration** — Include setting changes in code reviews
* **Transparency** — All contributors see repository CodeRabbit settings
* **Precedence** — Repository YAML settings override web interface settings

Repository-level `.coderabbit.yaml` settings take precedence over organization settings from the web interface.

For configuration file details, see [Add a configuration file](/getting-started/configure-coderabbit/).

### Speed up reviews with path filters

If your repository contains data or content that doesn't need code review context, use path filters to exclude it.

**Example:** `!dist/**` tells CodeRabbit to ignore everything in the `dist` directory during review preparation.

**Benefits:**

* Faster review preparation
* Reduced contextual noise
* More focused analysis

Configure path filters through the web interface or in your `.coderabbit.yaml` file.

### Keep default settings

CodeRabbit's defaults are chosen for most organizations and situations. We recommend keeping these enabled unless specific requirements dictate otherwise:

* **Cache** — Keeps CodeRabbit's temporary repository memory between reviews, improving review speed.
* **Tools** — CodeRabbit uses all available [open-source linters and analyzers](/tools) by default, providing broad and flexible review coverage.
* **Knowledge base** — Features like learnings and issue tracking require data retention. Opt out only if your organization has strict data-retention policies.

Configure these features through the web interface or `.coderabbit.yaml` file.

## Improve CI/CD integration

CodeRabbit analyzes continuous integration and deployment logs to provide better remediation advice. Configure your CI/CD tools to output specific error information.

**Include in failure output:**

* **File names** associated with failures
* **Line numbers** where failures occurred
* **Detailed explanations** including error codes or diffs

**Example:** [This pull request](https://github.com/ff14-advanced-market-search/temp-fe/pull/47/files) shows expanding CI error context by including a diff for code-formatter check failures.

Better error context leads to more actionable CodeRabbit remediation suggestions during code reviews.

***

## Next steps

* [Code review best practices](/guides/code-review-best-practices)
* [Configure CodeRabbit](/getting-started/configure-coderabbit/)
* [Platform integrations](/platforms/)