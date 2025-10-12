#!/usr/bin/env python3
"""
Parse CodeRabbit/Claude review comments and create GitHub issues automatically.
"""

import re
import sys
import json
import os
from typing import List, Dict

def parse_review_text(review_text: str) -> List[Dict[str, str]]:
    """
    Parse review text and extract issues.
    
    Returns list of dicts with: title, body, severity, section
    """
    issues = []
    
    lines = review_text.split('\n')
    current_section = None
    current_issue = None
    current_lines = []
    
    for line in lines:
        # Detect section headers
        if '🔴 CRITICAL ISSUES' in line or 'CRITICAL ISSUES' in line:
            current_section = 'critical'
        elif '🟡 MAJOR ISSUES' in line or 'MAJOR ISSUES' in line:
            current_section = 'major'
        elif '🟢 POSITIVE' in line or 'RECOMMENDED CHANGES' in line:
            # End of issues section
            if current_issue and current_lines:
                issues.append(_create_issue(current_issue, current_lines, current_section))
            break
            
        # Detect numbered items (issue start)
        match = re.match(r'^(\d+)\.\s+(.+)', line)
        if match and current_section:
            # Save previous issue
            if current_issue and current_lines:
                issues.append(_create_issue(current_issue, current_lines, current_section))
            
            # Start new issue
            current_issue = match.group(2).strip()
            current_lines = [line]
        elif current_issue:
            # Continue current issue
            current_lines.append(line)
    
    # Don't forget last issue
    if current_issue and current_lines:
        issues.append(_create_issue(current_issue, current_lines, current_section))
    
    return issues

def _create_issue(title: str, lines: List[str], section: str) -> Dict[str, str]:
    """Create issue dict from parsed data."""
    body = '\n'.join(lines[1:])  # Skip first line (title)
    
    # Extract severity if present
    severity_match = re.search(r'SEVERITY:\s*(HIGH|MEDIUM|LOW|CRITICAL)', body, re.IGNORECASE)
    severity = severity_match.group(1).upper() if severity_match else section.upper()
    
    # Determine labels
    labels = ['code-review', 'automated']
    if 'CRITICAL' in severity or section == 'critical':
        labels.append('critical')
    elif 'HIGH' in severity:
        labels.append('high-priority')
    elif section == 'major':
        labels.append('major')
    
    # Clean up title
    title = re.sub(r'⚠️.*$', '', title).strip()
    title = re.sub(r'\s+', ' ', title).strip()
    
    return {
        'title': f"🔍 {title}",
        'body': f"**From**: Automated Code Review\n**Severity**: {severity}\n\n{body}",
        'labels': labels,
        'severity': severity
    }

def create_github_issues(issues: List[Dict[str, str]], pr_number: str, token: str):
    """Create GitHub issues via API."""
    import urllib.request
    import urllib.error
    
    repo = "hanax-ai/hx-citadel-ansible"
    
    for issue in issues:
        # Add PR reference to body
        issue['body'] += f"\n\n---\n**Related PR**: #{pr_number}\n**Auto-created by**: review parser"
        
        data = {
            'title': issue['title'],
            'body': issue['body'],
            'labels': issue['labels']
        }
        
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues",
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"✅ Created Issue #{result['number']}: {issue['title']}")
        except urllib.error.HTTPError as e:
            print(f"❌ Failed to create issue: {e}")
            print(f"   Response: {e.read().decode('utf-8')}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: parse-review-create-issues.py <review_file> <pr_number> [github_token]")
        sys.exit(1)
    
    review_file = sys.argv[1]
    pr_number = sys.argv[2]
    github_token = sys.argv[3] if len(sys.argv) > 3 else os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("❌ Error: GITHUB_TOKEN not provided")
        sys.exit(1)
    
    # Read review text
    with open(review_file, 'r') as f:
        review_text = f.read()
    
    # Parse issues
    print(f"📝 Parsing review from {review_file}...")
    issues = parse_review_text(review_text)
    print(f"Found {len(issues)} issues to create")
    
    # Create GitHub issues
    if issues:
        print(f"\n🚀 Creating {len(issues)} GitHub issues for PR #{pr_number}...")
        create_github_issues(issues, pr_number, github_token)
        print(f"\n✅ Done! Created {len(issues)} issues")
    else:
        print("⚠️  No issues found to create")

