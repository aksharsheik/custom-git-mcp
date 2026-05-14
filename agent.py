import google.generativeai as genai
import subprocess
import os
import json

genai.configure(api_key="AIzaSyDS56XzNw5LelAQg8t6thx-IoOcg-UwncQ")
model = genai.GenerativeModel("gemini-1.5-flash")

def run_git(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout + result.stderr

def run_agent(instruction):
    print(f"\n🤖 Agent started: {instruction}\n")

    # Ask Gemini to decide what git commands to run
    prompt = f"""
You are a git agent. The user wants: {instruction}

Decide what to do and respond ONLY in this JSON format:
{{
  "commit_message": "your commit message here",
  "branch": "main",
  "action": "commit_and_push"
}}
"""
    response = model.generate_content(prompt)
    text = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        decision = json.loads(text)
        print(f"🔧 Git Status:")
        print(run_git("git status"))
        
        print(f"🔧 Staging all files...")
        print(run_git("git add ."))
        
        commit_msg = decision.get("commit_message", "AI agent commit")
        branch = decision.get("branch", "main")
        
        print(f"🔧 Committing: {commit_msg}")
        print(run_git(f'git commit -m "{commit_msg}"'))
        
        print(f"🔧 Pushing to {branch}...")
        print(run_git(f"git push origin {branch}"))
        
        print("\n✅ Done! AI agent successfully committed and pushed.")
    
    except json.JSONDecodeError:
        print("AI Response:", text)

run_agent("Check my code and commit all changes with a meaningful message and push to main")