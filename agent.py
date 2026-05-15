import google.generativeai as genai
import subprocess
import os
import json
import time
from dotenv import load_dotenv

# =========================
# LOAD API KEY FROM .env
# =========================
load_dotenv(override=True)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY not found in .env file")
    exit(1)

print("✅ API Key Loaded Successfully")

# =========================
# CONFIGURE GEMINI
# =========================
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")

# =========================
# RUN GIT COMMANDS
# =========================
def run_git(cmd):

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=True,
        encoding="utf-8",
        errors="ignore"
    )

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    return stdout, stderr, result.returncode

# =========================
# GET GIT STATUS
# =========================
def get_git_status():

    stdout, stderr, code = run_git("git status")

    print("\n📋 Git Status:\n")
    print(stdout)

    return stdout

# =========================
# GET GIT DIFF
# =========================
def get_git_diff():

    stdout, stderr, code = run_git("git diff")

    # If no unstaged diff, check staged diff
    if not stdout:
        stdout, _, _ = run_git("git diff --cached")

    print("\n🔍 Git Diff:\n")
    print(stdout[:1000])

    return stdout

# =========================
# STAGE ONLY CHANGED FILES
# =========================
def stage_changed_files():

    stdout, stderr, code = run_git("git status --porcelain")

    if not stdout:
        print("ℹ️ No changes found.")
        return False

    files = []

    for line in stdout.splitlines():

        if line.strip():
            filename = line[3:].strip()
            files.append(filename)

    print(f"\n📁 Staging files: {files}")

    for f in files:

        out, err, code = run_git(f'git add "{f}"')

        if code != 0:
            print(f"⚠️ Failed to stage {f}")
            print(err)

    return True

# =========================
# MAIN AGENT
# =========================
def run_agent(instruction):

    print("\n🤖 Agent Started")
    print(f"📝 Instruction: {instruction}")

    # -------------------------
    # CHECK GIT STATUS
    # -------------------------
    status = get_git_status()

    if "nothing to commit" in status.lower():
        print("\n✅ Everything is already up to date.")
        return

    # -------------------------
    # GET GIT DIFF
    # -------------------------
    diff = get_git_diff()

    # -------------------------
    # AI PROMPT
    # -------------------------
    prompt = f"""
You are an AI Git Agent.

The user instruction:
{instruction}

Current git status:
{status}

Git diff:
{diff[:2000]}

Respond ONLY in JSON format:

{{
  "commit_message": "meaningful commit message",
  "branch": "main",
  "action": "commit_and_push"
}}
"""

    # -------------------------
    # GEMINI API CALL
    # -------------------------
    try:

        response = model.generate_content(prompt)

    except Exception as e:

        error_message = str(e)

        if "quota" in error_message.lower():

            print("\n❌ Gemini quota exceeded.")
            print("⏳ Waiting 60 seconds before retrying...\n")

            time.sleep(60)

            try:
                response = model.generate_content(prompt)

            except Exception:
                print("\n❌ Retry failed due to quota limit again.")
                return

        else:
            print(f"\n❌ Gemini API Error:\n{error_message}")
            return

    # -------------------------
    # CLEAN RESPONSE
    # -------------------------
    text = (
        response.text
        .strip()
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    print("\n🤖 AI Response:")
    print(text)

    # -------------------------
    # PARSE JSON
    # -------------------------
    try:

        decision = json.loads(text)

    except json.JSONDecodeError:
        print("\n❌ Invalid AI JSON Response")
        return

    commit_msg = decision.get(
        "commit_message",
        "AI generated commit"
    )

    branch = decision.get(
        "branch",
        "main"
    )

    # -------------------------
    # STAGE FILES
    # -------------------------
    staged = stage_changed_files()

    if not staged:
        print("\n❌ Nothing staged.")
        return

    # -------------------------
    # COMMIT
    # -------------------------
    print(f"\n🔧 Committing:\n{commit_msg}")

    stdout, stderr, code = run_git(
        f'git commit -m "{commit_msg}"'
    )

    if code != 0:
        print("\n❌ Commit Failed")
        print(stderr)
        return

    print("\n✅ Commit Successful")
    print(stdout)

    # -------------------------
    # PUSH
    # -------------------------
    print(f"\n🚀 Pushing to {branch}...")

    stdout, stderr, code = run_git(
        f"git push origin {branch}"
    )

    if code != 0:
        print("\n❌ Push Failed")
        print(stderr)

        print("\n💡 Try this manually:")
        print("git push --set-upstream origin main")

        return

    print("\n✅ Push Successful")
    print(stdout)

    print("\n🎉 DONE! AI Agent completed successfully.")

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":

    user_input = input(
        "\nWhat do you want the agent to do?\n"
        "(Press Enter for default)\n> "
    ).strip()

    if not user_input:
        user_input = (
            "Commit all changes with a meaningful "
            "message and push to main"
        )

    run_agent(user_input)


    # Demo change for senior showcase
    # Testing auto Pyton
    # python