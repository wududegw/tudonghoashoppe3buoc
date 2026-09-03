import os
import sys
import io
import json
import base64
import hashlib
import urllib.request
import urllib.error

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

OWNER = "wududegw"
REPO = "tudonghoashoppe3buoc"
BRANCH = "main"

IGNORE_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    "output/temp",
    "output/cleaned_images",
    "output/rendered_videos",
    ".git",
    "venv",
    ".env",
    ".vscode",
    ".idea",
    "thumbs.db",
    "desktop.ini",
    "python-installer.exe",
    "repo.zip",
    "mingit",
]

def is_ignored(rel_path):
    p = rel_path.lower().replace(os.sep, "/")
    for ign in IGNORE_PATTERNS:
        if ign in p:
            return True
    return False

def git_blob_sha(content_bytes):
    header = f"blob {len(content_bytes)}\0".encode("utf-8")
    return hashlib.sha1(header + content_bytes).hexdigest()

def github_api_request(url, token, method="GET", data=None):
    headers = {
        "User-Agent": "ShopeeAutoSync/1.0",
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_msg)
            msg = err_json.get("message", err_msg)
        except Exception:
            msg = err_msg
        raise RuntimeError(f"GitHub API Error [{e.code}]: {msg}")

def get_project_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sub_main = os.path.join(script_dir, "tudonghoashoppe3buoc", "tudonghoashoppe3buoc-main")
    if os.path.exists(os.path.join(sub_main, "main.py")):
        return sub_main
    if os.path.exists(os.path.join(script_dir, "main.py")):
        return script_dir
    default_scratch_main = r"C:\Users\Administrator\.gemini\antigravity\scratch\tudonghoashoppe3buoc\tudonghoashoppe3buoc-main"
    if os.path.exists(os.path.join(default_scratch_main, "main.py")):
        return default_scratch_main
    return script_dir

def sync(token):
    token = token.strip().strip("'").strip('"')
    if not token:
        print("[!] Token GitHub khong duoc de trong.")
        return False

    print("=" * 65)
    print(f">> DANG KET NOI TOI GITHUB: {OWNER}/{REPO} (branch: {BRANCH})")
    print("=" * 65)

    try:
        user_info = github_api_request("https://api.github.com/user", token)
        user_login = user_info.get("login", "unknown")
        print(f"[*] Da xac thuc thanh cong voi tai khoan GitHub: @{user_login}")
    except Exception as e:
        print(f"[!] Loi xac thuc Token: {e}")
        print("    Vui long kiem tra lai Personal Access Token (PAT) va quyen 'repo'.")
        return False

    root_dir = get_project_root()
    print(f"[*] Thu muc du an nguon: {root_dir}")

    print("[*] Dang kiem tra trang thai repository tren GitHub...")
    try:
        ref_data = github_api_request(f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}", token)
        latest_commit_sha = ref_data["object"]["sha"]
        print(f"[*] Commit hien tai tren GitHub: {latest_commit_sha[:8]}")

        tree_data = github_api_request(f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{BRANCH}?recursive=1", token)
        remote_blobs = {item["path"]: item["sha"] for item in tree_data.get("tree", []) if item["type"] == "blob"}
        print(f"[*] Repository tu xa hien co {len(remote_blobs)} tap tin.")
    except Exception as e:
        print(f"[!] Khong the doc thong tin branch {BRANCH}: {e}")
        return False

    local_files = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            rel = os.path.relpath(fp, root_dir).replace(os.sep, "/")
            if is_ignored(rel):
                continue
            with open(fp, "rb") as of:
                content = of.read()
            sha = git_blob_sha(content)
            local_files[rel] = (fp, sha, content)

    print(f"[*] Tim thay {len(local_files)} tap tin hop le trong ma nguon cuc bo.")

    tree_items = []
    uploaded_count = 0
    unchanged_count = 0

    for rel_path, (fp, local_sha, content) in sorted(local_files.items()):
        remote_sha = remote_blobs.get(rel_path)
        if remote_sha == local_sha:
            tree_items.append({
                "path": rel_path,
                "mode": "100644",
                "type": "blob",
                "sha": remote_sha
            })
            unchanged_count += 1
            continue

        action = "Them moi" if remote_sha is None else "Cap nhat"
        print(f"  [+] {action}: {rel_path} ({len(content)} bytes)...")
        b64_content = base64.b64encode(content).decode("ascii")
        blob_resp = github_api_request(
            f"https://api.github.com/repos/{OWNER}/{REPO}/git/blobs",
            token,
            method="POST",
            data={"content": b64_content, "encoding": "base64"}
        )
        new_blob_sha = blob_resp["sha"]
        tree_items.append({
            "path": rel_path,
            "mode": "100644",
            "type": "blob",
            "sha": new_blob_sha
        })
        uploaded_count += 1

    print(f"[*] Da xu ly: {uploaded_count} tap tin moi/cap nhat, {unchanged_count} tap tin khong doi.")

    if uploaded_count == 0 and len(tree_items) == len(remote_blobs):
        print("[OK] Toan bo ma nguon tren GitHub da o trang thai moi nhat, khong co thay doi.")
        return True

    print("[*] Dang tao Git Tree moi...")
    new_tree_resp = github_api_request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees",
        token,
        method="POST",
        data={"tree": tree_items}
    )
    new_tree_sha = new_tree_resp["sha"]

    commit_msg = "Update Shopee Video Automation - Dong bo toan bo ma nguon va Extension"
    print(f"[*] Dang tao Commit: '{commit_msg}'...")
    new_commit_resp = github_api_request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits",
        token,
        method="POST",
        data={
            "message": commit_msg,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        }
    )
    new_commit_sha = new_commit_resp["sha"]
    print(f"[*] Commit SHA moi: {new_commit_sha}")

    print(f"[*] Dang cap nhat branch '{BRANCH}'...")
    github_api_request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
        token,
        method="PATCH",
        data={"sha": new_commit_sha, "force": True}
    )

    print("=" * 65)
    print(">> DONG BO THANH CONG TOAN BO CODE LEN GITHUB!")
    print(f">> Xem tai: https://github.com/{OWNER}/{REPO}")
    print("=" * 65)
    return True

if __name__ == "__main__":
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
    elif "GH_TOKEN" in os.environ:
        token = os.environ["GH_TOKEN"]
    elif "GITHUB_TOKEN" in os.environ:
        token = os.environ["GITHUB_TOKEN"]

    if not token:
        try:
            token = input("Nhap GitHub Token (ghp_...): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Da huy bo.")
            sys.exit(1)

    success = sync(token)
    if not success:
        sys.exit(1)
