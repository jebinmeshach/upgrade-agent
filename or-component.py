import subprocess
import os
import sys

def run_command(cmd, cwd=None):
    """Run a shell command and stream output live"""
    print(f"\n🔹 Running: {' '.join(cmd)}\n")
    process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        sys.exit(f"❌ Command failed: {' '.join(cmd)}")

def upgrade_repo(github_url, github_token, branch_name="refactor/upgrade"):
    repo_name = github_url.split("/")[-1].replace(".git", "")
    repo_owner = github_url.split("/")[-2]

    # ✅ Inject token for authentication
    auth_url = github_url.replace(
        "https://", f"https://{github_token}@"
    )

    # Step 1: Clone repo
    run_command(["git", "clone", auth_url])
    repo_path = os.path.join(os.getcwd(), repo_name)

    java_home = r"C:\Program Files\Java\jdk-11"
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = java_home + r"\bin;" + os.environ["PATH"]

    print("JAVA_HOME set to:", os.environ["JAVA_HOME"])
    print("PATH updated.")

    # Step 2: Build OpenRewrite context
    run_command(["mod", "build", "."], cwd=repo_path)

    # Step 3: Run Java 21 migration
    run_command(["mod", "run", ".", "--recipe", "UpgradeToJava21"], cwd=repo_path)

    
    java_home = r"C:\Program Files\Java\jdk-17"
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = java_home + r"\bin;" + os.environ["PATH"]

    print("JAVA_HOME set to:", os.environ["JAVA_HOME"])
    print("PATH updated.")
    
    # Step 4: Run Spring Boot 3.5 migration
    run_command(["mod", "run", ".", "--recipe", "UpgradeSpringBoot_3_5"], cwd=repo_path)

    # Step 5: Create new branch with recipe changes
    run_command(["mod", "git", "checkout", ".", "-b", branch_name, "--last-recipe-run"], cwd=repo_path)

    # Step 6: Commit changes
    run_command(["git", "add", "."], cwd=repo_path)
    run_command(["git", "commit", "-m", "Upgrade project to Java 21 and Spring Boot 3.5"], cwd=repo_path)

    # ✅ Configure push URL with token
    push_url = f"https://{github_token}@github.com/{repo_owner}/{repo_name}.git"
    run_command(["git", "push", push_url, branch_name], cwd=repo_path)

    print(f"\n✅ Upgrade completed! Branch '{branch_name}' pushed to GitHub.\n")

if __name__ == "__main__":
    # Example usage
    GITHUB_URL = ""
    GITHUB_TOKEN = ""
    upgrade_repo(GITHUB_URL, GITHUB_TOKEN)
