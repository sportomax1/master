import os
import requests
from datetime import datetime, timezone
import json

def format_time_since(delta):
    """Converts a timedelta object to a user-friendly 'time since' string."""
    seconds = int(delta.total_seconds())
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days > 1 else ''} ago"

def get_github_repos(username):
    """
    Fetch all repositories for a GitHub user.
    Returns list of repo objects with name, url, description, updated_at, etc.
    """
    repos = []
    page = 1
    per_page = 100
    
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page={per_page}&sort=updated"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Error fetching repos: {response.status_code}")
            break
        
        data = response.json()
        if not data:
            break
        
        repos.extend(data)
        page += 1
    
    return repos

def get_repo_files(username, repo_name, path=''):
    """
    Recursively fetch all files from a GitHub repository.
    Returns list of file objects with name, path, html_url, type, etc.
    """
    files = []
    url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{path}"
    
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            return files
        
        items = response.json()
        
        for item in items:
            if item['type'] == 'file':
                files.append(item)
            elif item['type'] == 'dir':
                # Recursively get files from subdirectories
                files.extend(get_repo_files(username, repo_name, item['path']))
    except Exception as e:
        print(f"Error fetching files from {repo_name}/{path}: {e}")
    
    return files

def get_file_last_commit(username, repo_name, file_path):
    """
    Get the last commit timestamp for a specific file.
    """
    url = f"https://api.github.com/repos/{username}/{repo_name}/commits?path={file_path}&page=1&per_page=1"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            commits = response.json()
            if commits:
                commit_date = commits[0]['commit']['committer']['date']
                return datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"Error fetching commit for {file_path}: {e}")
    
    return None

def generate_master_html_index(username='sportomax1', output_file='master_index.html'):
    """
    Generates an HTML index of ALL files across ALL repositories for a GitHub user.
    """
    
    print(f"Fetching repositories for {username}...")
    repos = get_github_repos(username)
    print(f"Found {len(repos)} repositories")
    
    all_files = []
    
    # Collect files from all repos
    for repo in repos:
        repo_name = repo['name']
        print(f"Scanning repository: {repo_name}...")
        
        files = get_repo_files(username, repo_name)
        
        for file in files:
            # Get last commit time for this file
            commit_time = get_file_last_commit(username, repo_name, file['path'])
            
            file_info = {
                'repo': repo_name,
                'name': file['name'],
                'path': file['path'],
                'url': file['html_url'],
                'size': file.get('size', 0),
                'updated_at': commit_time or datetime.now(timezone.utc)
            }
            
            all_files.append(file_info)
    
    # Sort by last updated (most recent first)
    all_files.sort(key=lambda x: x['updated_at'], reverse=True)
    
    print(f"Total files found: {len(all_files)}")
    
    # Generate HTML
    now = datetime.now(timezone.utc)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Index - All Repositories ({username})</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 20px; 
            background-color: #fdfdfd;
            color: #333;
        }}
        .container {{ max-width: 1200px; margin: auto; }}
        h1 {{ 
            border-bottom: 2px solid #eee; 
            padding-bottom: 10px; 
        }}
        
        .search-input {{
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 16px;
        }}
        
        .filter-controls {{
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            font-size: 13px;
            border: 2px solid #ddd;
            background-color: #fff;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 500;
        }}
        
        .filter-btn:hover {{
            background-color: #f0f0f0;
        }}
        
        .filter-btn.active {{
            background-color: #007bff;
            color: #fff;
            border-color: #007bff;
        }}
        
        .stats {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
        }}
        
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        
        .file-item {{
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 10px;
            background-color: #fff;
            transition: box-shadow 0.2s;
        }}
        
        .file-item:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        
        .file-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }}
        
        .file-name {{
            font-weight: 600;
            font-size: 16px;
            color: #0366d6;
            text-decoration: none;
        }}
        
        .file-name:hover {{
            text-decoration: underline;
        }}
        
        .repo-badge {{
            background: #e1e4e8;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: #586069;
        }}
        
        .file-meta {{
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
        }}
        
        .file-path {{
            color: #999;
            font-size: 12px;
            font-family: monospace;
        }}
        
        .time-ago {{
            color: #28a745;
            font-weight: 500;
        }}
        
        .file-size {{
            color: #6f42c1;
        }}
        
        .sort-controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        .sort-btn {{
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: #fff;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .sort-btn.active {{
            background: #007bff;
            color: #fff;
            border-color: #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗂️ Master Index - All Repositories</h1>
        <p style="color: #666; margin-bottom: 20px;">
            Showing all files from <strong>{username}</strong>'s GitHub repositories
        </p>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(repos)}</div>
                <div class="stat-label">Repositories</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(all_files)}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="visibleCount">{len(all_files)}</div>
                <div class="stat-label">Visible Files</div>
            </div>
        </div>
        
        <input 
            type="text" 
            id="searchInput" 
            class="search-input" 
            placeholder="🔍 Search files by name, path, or repository..." 
            onkeyup="filterFiles()"
        >
        
        <div class="filter-controls" id="filterButtons">
            <button class="filter-btn active" onclick="setFilter('all')">All Files</button>
        </div>
        
        <div class="sort-controls">
            <span style="font-weight: 600;">Sort by:</span>
            <button class="sort-btn active" onclick="sortFiles('updated')">Last Updated</button>
            <button class="sort-btn" onclick="sortFiles('name')">Name</button>
            <button class="sort-btn" onclick="sortFiles('repo')">Repository</button>
            <button class="sort-btn" onclick="sortFiles('size')">Size</button>
        </div>
        
        <ul class="file-list" id="fileList">
"""
    
    # Add file items
    for file in all_files:
        time_since = format_time_since(now - file['updated_at'])
        file_ext = os.path.splitext(file['name'])[1].lower()
        size_kb = file['size'] / 1024 if file['size'] > 0 else 0
        size_str = f"{size_kb:.1f} KB" if size_kb > 0 else "0 KB"
        
        html_content += f"""
            <li class="file-item" data-ext="{file_ext}" data-repo="{file['repo']}" data-name="{file['name'].lower()}" data-path="{file['path'].lower()}" data-updated="{file['updated_at'].timestamp()}" data-size="{file['size']}">
                <div class="file-header">
                    <a href="{file['url']}" class="file-name" target="_blank">{file['name']}</a>
                    <span class="repo-badge">{file['repo']}</span>
                </div>
                <div class="file-path">{file['path']}</div>
                <div class="file-meta">
                    <span class="time-ago">⏱️ {time_since}</span>
                    <span class="file-size">📦 {size_str}</span>
                </div>
            </li>
"""
    
    html_content += """
        </ul>
    </div>
    
    <script>
        let currentFilter = 'all';
        let currentSort = 'updated';
        
        function setFilter(ext) {
            currentFilter = ext;
            
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            filterFiles();
        }
        
        function filterFiles() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const items = document.querySelectorAll('.file-item');
            let visibleCount = 0;
            
            items.forEach(item => {
                const ext = item.dataset.ext;
                const repo = item.dataset.repo.toLowerCase();
                const name = item.dataset.name;
                const path = item.dataset.path;
                
                const matchesFilter = currentFilter === 'all' || ext === currentFilter;
                const matchesSearch = name.includes(searchTerm) || path.includes(searchTerm) || repo.includes(searchTerm);
                
                if (matchesFilter && matchesSearch) {
                    item.style.display = 'block';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            document.getElementById('visibleCount').textContent = visibleCount;
        }
        
        function sortFiles(sortBy) {
            currentSort = sortBy;
            
            // Update button states
            document.querySelectorAll('.sort-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            const list = document.getElementById('fileList');
            const items = Array.from(list.querySelectorAll('.file-item'));
            
            items.sort((a, b) => {
                if (sortBy === 'updated') {
                    return parseFloat(b.dataset.updated) - parseFloat(a.dataset.updated);
                } else if (sortBy === 'name') {
                    return a.dataset.name.localeCompare(b.dataset.name);
                } else if (sortBy === 'repo') {
                    return a.dataset.repo.localeCompare(b.dataset.repo);
                } else if (sortBy === 'size') {
                    return parseInt(b.dataset.size) - parseInt(a.dataset.size);
                }
            });
            
            items.forEach(item => list.appendChild(item));
        }
        
        // Build filter buttons dynamically
        const extensions = new Set();
        document.querySelectorAll('.file-item').forEach(item => {
            const ext = item.dataset.ext;
            if (ext) extensions.add(ext);
        });
        
        const filterContainer = document.getElementById('filterButtons');
        const sortedExts = Array.from(extensions).sort();
        sortedExts.forEach(ext => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.textContent = ext || 'no ext';
            btn.onclick = () => setFilter(ext);
            filterContainer.appendChild(btn);
        });
    </script>
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Master index generated: {output_file}")
    print(f"   - {len(repos)} repositories scanned")
    print(f"   - {len(all_files)} total files indexed")

if __name__ == '__main__':
    generate_master_html_index()
