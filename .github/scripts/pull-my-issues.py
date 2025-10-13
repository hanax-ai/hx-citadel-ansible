#!/usr/bin/env python3
"""
Claude/Agent0 Issue Puller

Pulls assigned issues from GitHub that this agent should work on,
filters out Devin's issues, and creates a prioritized work queue.

Usage: python3 pull-my-issues.py [--agent agent0|claude|devin]
"""

import os
import sys
import json
import requests
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Issue:
    """Represents a GitHub issue"""
    number: int
    title: str
    labels: List[str] = field(default_factory=list)
    assignee: str = ""
    priority: int = 5  # 1 (highest) to 5 (lowest)
    category: str = "general"
    
    def __str__(self):
        priority_icon = "🔴" if self.priority <= 2 else "🟡" if self.priority <= 3 else "🟢"
        return f"{priority_icon} #{self.number}: {self.title} [{self.category}]"


class IssueManager:
    """Manages GitHub issues for agent assignment"""
    
    def __init__(self, repo: str = "hanax-ai/hx-citadel-ansible", agent: str = "agent0"):
        self.repo = repo
        self.agent = agent
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.token = os.environ.get("GITHUB_TOKEN")
        
        if not self.token:
            print("❌ GITHUB_TOKEN environment variable required")
            sys.exit(1)
    
    def fetch_open_issues(self) -> List[Dict[str, Any]]:
        """Fetch all open issues from GitHub"""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }
        
        response = requests.get(
            f"{self.api_base}/issues?state=open&per_page=100",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def categorize_issue(self, issue_data: Dict[str, Any]) -> Issue:
        """Categorize and prioritize an issue"""
        title = issue_data["title"].lower()
        labels = [label["name"] for label in issue_data.get("labels", [])]
        
        # Determine category
        category = "general"
        priority = 5
        
        if any(word in title for word in ["test", "testing", "integration", "e2e"]):
            category = "testing"
            priority = 2
        elif any(word in title for word in ["lint", "ansible-lint", "code quality"]):
            category = "linting"
            priority = 3
        elif any(word in title for word in ["doc", "documentation"]):
            category = "documentation"
            priority = 4
        elif any(word in title for word in ["security", "vault", "secret"]):
            category = "security"
            priority = 1
        elif any(word in title for word in ["ansible", "playbook", "role"]):
            category = "ansible"
            priority = 2
        elif any(word in title for word in ["docker", "deploy", "infrastructure"]):
            category = "infrastructure"
            priority = 2
        elif any(word in title for word in ["fix", "bug", "error"]):
            category = "bug"
            priority = 2
        
        # Adjust priority based on labels
        if "critical" in labels:
            priority = min(priority, 1)
        elif "high-priority" in labels:
            priority = min(priority, 2)
        
        assignee = issue_data.get("assignee", {})
        assignee_login = assignee.get("login", "") if assignee else ""
        
        return Issue(
            number=issue_data["number"],
            title=issue_data["title"],
            labels=labels,
            assignee=assignee_login,
            priority=priority,
            category=category
        )
    
    def filter_my_issues(self, issues: List[Issue]) -> List[Issue]:
        """Filter issues assigned to this agent or unassigned issues this agent should handle"""
        my_issues = []
        
        for issue in issues:
            # Skip if assigned to someone else (especially Devin)
            if issue.assignee and issue.assignee != self.agent:
                continue
            
            # Include if:
            # 1. Assigned to me
            # 2. Unassigned and in my category
            if issue.assignee == self.agent:
                my_issues.append(issue)
            elif not issue.assignee and issue.category in ["testing", "linting", "documentation", "bug"]:
                my_issues.append(issue)
        
        return sorted(my_issues, key=lambda i: (i.priority, i.number))
    
    def display_work_queue(self, issues: List[Issue]):
        """Display prioritized work queue"""
        print("\n" + "═" * 80)
        print(f"   📋 WORK QUEUE FOR {self.agent.upper()}")
        print("═" * 80)
        
        if not issues:
            print("✅ No issues in queue - all caught up!")
            return
        
        # Group by category
        by_category = {}
        for issue in issues:
            by_category.setdefault(issue.category, []).append(issue)
        
        for category, cat_issues in sorted(by_category.items()):
            print(f"\n📂 {category.upper()} ({len(cat_issues)} issues)")
            print("─" * 80)
            for issue in cat_issues:
                print(f"  {issue}")
        
        print("\n" + "═" * 80)
        print(f"Total: {len(issues)} issues")
        print("═" * 80 + "\n")
    
    def export_work_queue(self, issues: List[Issue], output_file: str = "/tmp/my-issues.json"):
        """Export work queue to JSON for programmatic consumption"""
        data = {
            "agent": self.agent,
            "timestamp": None,  # Add timestamp if needed
            "total_issues": len(issues),
            "issues": [
                {
                    "number": i.number,
                    "title": i.title,
                    "priority": i.priority,
                    "category": i.category,
                    "labels": i.labels,
                    "url": f"https://github.com/{self.repo}/issues/{i.number}"
                }
                for i in issues
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Work queue exported to: {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Pull GitHub issues for agent")
    parser.add_argument("--agent", default="agent0", choices=["agent0", "claude", "devin"],
                       help="Agent name")
    parser.add_argument("--export", help="Export to JSON file")
    
    args = parser.parse_args()
    
    manager = IssueManager(agent=args.agent)
    
    print(f"🔍 Fetching open issues from {manager.repo}...")
    raw_issues = manager.fetch_open_issues()
    
    print(f"📦 Processing {len(raw_issues)} issues...")
    categorized = [manager.categorize_issue(issue) for issue in raw_issues]
    
    my_issues = manager.filter_my_issues(categorized)
    
    manager.display_work_queue(my_issues)
    
    if args.export:
        manager.export_work_queue(my_issues, args.export)
    else:
        manager.export_work_queue(my_issues)  # Default location


if __name__ == "__main__":
    main()

