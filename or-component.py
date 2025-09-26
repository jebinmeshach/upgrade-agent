import subprocess
import os
import sys
import shutil
from test_cases_runner import run_maven_tests, parse_surefire_reports, fix_failing_tests
from datetime import datetime

def run_command(cmd, cwd=None):
    """Run a shell command and stream output live"""
    print(f"\n🔹 Running: {' '.join(cmd)}\n")
    process = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in process.stdout:
         print(line, end="")
    process.wait()
    if process.returncode != 0:
        sys.exit(f"❌ Command failed: {' '.join(cmd)}")

def upgrade_repo(github_url, github_token, branch_name="refactor/upgrade"):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    branch_name = f"{branch_name}_{timestamp}"
    repo_name = github_url.split("/")[-1].replace(".git", "")
    repo_owner = github_url.split("/")[-2]

    auth_url = github_url.replace("https://", f"https://{github_token}@")

    # Step 1: Clone repo
    run_command(["git", "clone", auth_url])
    repo_path = os.path.join(os.getcwd(), repo_name)

    # -------------------------------
    # Step 2: Java 21 Upgrade
    # -------------------------------
    java_home = r"C:\Program Files\Java\jdk-11"
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = java_home + r"\bin;" + os.environ["PATH"]

    print("JAVA_HOME set to:", os.environ["JAVA_HOME"])
    print("PATH updated.")

    run_command(["mod", "build", "."], cwd=repo_path)
    run_command(["mod", "run", ".", "--recipe", "UpgradeToJava21"], cwd=repo_path)
    run_command(["mod", "git", "apply", ".", "--last-recipe-run"], cwd=repo_path)

    # -------------------------------
    # Step 3: Spring Boot 3.5 Upgrade
    # -------------------------------
    java_home = r"C:\Program Files\Java\jdk-17"
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = java_home + r"\bin;" + os.environ["PATH"]

    print("JAVA_HOME set to:", os.environ["JAVA_HOME"])
    print("PATH updated.")

    ##run_command(["mod", "build", "."], cwd=repo_path)
    run_command(["mod", "run", ".", "--recipe", "UpgradeSpringBoot_3_5"], cwd=repo_path)
    run_command(["mod", "git", "apply", ".", "--last-recipe-run"], cwd=repo_path)

    # Step 4: Run tests after migration
    java_home = r"C:\Program Files\Java\jdk-21"
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = java_home + r"\bin;" + os.environ["PATH"]

    print("JAVA_HOME set to:", os.environ["JAVA_HOME"])
    print("PATH updated.")
    run_maven_tests(repo_path)

    # Step 5: Detect failing tests
    failing_tests,_ = parse_surefire_reports(repo_path)

    # Step 6: If failures, fix with Gemini
    if failing_tests:
        fix_failing_tests(repo_path, failing_tests)
        # After fixing, rerun tests
        run_maven_tests(repo_path)
        failing_tests, _ = parse_surefire_reports(repo_path)

    # -------------------------------
    # Step 8: Create new branch for changes
    # -------------------------------

    run_command(["git", "checkout", "-b", branch_name], cwd=repo_path)

    commit_msg = "Migrated to Java 21 and SpringBoot 3.5" if not failing_tests else "Some tests still failing after upgrade"
    run_command(["git", "add", "."], cwd=repo_path)
    run_command(["git", "commit", "-m", commit_msg], cwd=repo_path)
    push_url = f"https://{github_token}@github.com/{repo_owner}/{repo_name}.git"
    run_command(["git", "push", push_url, branch_name], cwd=repo_path)

    print(f"\n✅ Upgrade completed! Branch '{branch_name}' pushed to GitHub.\n")

    if os.path.isdir(repo_path):
        try:
            shutil.rmtree(repo_path)
            print(f"🗑️  Local repo '{repo_path}' deleted successfully.")
        except Exception as e:
            print(f"❌ Failed to delete local repo: {e}")

if __name__ == "__main__":
    GITHUB_URL = ""
    GITHUB_TOKEN = ""
    upgrade_repo(GITHUB_URL, GITHUB_TOKEN)
