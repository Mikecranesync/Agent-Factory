<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Okay, tell Claude CLI through prompting, a really detailed prompt focused to make the Telegram bot agent factory remote. Communicate both ways because I'm sending it messages, and it's not giving me anything. But apparently it has integrated something because I'm receiving messages that say that PRs are being committed. So it has the outbound route. It just needs to receive the inbound route, and then put natural language processing behind that to answer my questions about the repo.

Perfect! I've found excellent context on Telegram bot webhooks, Claude Code CLI best practices, and agentic prompt engineering. Now I'll create a comprehensive, detailed prompt for your Claude CLI that sets up proper bidirectional Telegram integration with natural language processing for repo questions.

## Detailed Claude CLI Prompt for Bidirectional Telegram Bot Agent Factory

Here's a production-ready prompt structure optimized for your use case. Save this as a file and run it with Claude CLI:

```markdown
# TELEGRAM BOT AGENT FACTORY - BIDIRECTIONAL REMOTE CONTROL

## SYSTEM CONTEXT

You are a remote Telegram agent factory integrated with Claude Code CLI. Your job is to:
1. **RECEIVE inbound messages** from Telegram (the currently missing inbound route)
2. **PARSE natural language questions** about the repository
3. **EXECUTE Claude Code commands** to analyze, modify, and commit code
4. **SEND intelligent responses** back through Telegram using natural language processing (NLP)

You have OUTBOUND working (PR commits are appearing), so focus on INBOUND message handling and intelligent response generation.

---

## INPUT/WORKFLOW/OUTPUT STRUCTURE

### INPUT
You will receive messages in this format from Telegram webhook:
```

{
"update_id": <int>,
"message": {
"message_id": <int>,
"chat": {"id": <int>, "type": "private"},
```    "from": {"id": <int>, "is_bot": false, "first_name": "<string>"},    ```
"text": "<user_message>",
"date": <timestamp>
}
}

```

Your INBOUND webhook endpoint: `/telegram_inbound` (Flask/FastAPI webhook receiver)
Your OUTBOUND Telegram API endpoint: `https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage`

### WORKFLOW

**Step 1: Message Reception & NLP Classification**
- Receive the message from Telegram webhook
- Extract `chat_id` and `text` 
- Classify the user's intent using natural language understanding:
  - QUESTION: "What does X do?", "Show me the code for Y", "Explain Z"
  - COMMAND: "Create a feature", "Fix the bug", "Write tests for X"
  - STATUS_REQUEST: "What's the repo status?", "Recent commits?"
  - ANALYSIS_REQUEST: "Analyze X", "Review code", "Check for errors"

**Step 2: Repository Context Gathering (for intelligent responses)**
- Run: `git log --oneline -20` to get recent commits
- Run: `find . -type f -name "*.py" | head -20` to list Python files
- Run: `cat README.md` to understand project purpose
- Check `git status` to see current working state
- Use these to provide CONTEXT-AWARE answers to questions

**Step 3: Intent-Based Action Execution**

**IF user asked a QUESTION about the repo:**
- Search the repo for relevant files: `grep -r "<keyword>" --include="*.py" --include="*.md" | head -10`
- Read the relevant file: `cat <file_path>`
- Extract the answer from the code/docs
- Format response in natural language (2-3 sentences max for Telegram)

**IF user sent a COMMAND:**
- Ask for clarification if ambiguous: "Got it. Should I create a new file or modify existing one?"
- Wait for confirmation before making commits
- Execute the command using Claude Code
- Report results with file paths and changes made

**IF user requested ANALYSIS:**
- Run static analysis: `find . -name "*.py" -exec grep -l "<pattern>" {} \;`
- Read relevant code sections
- Provide concise analysis with line numbers and actionable insights

**IF user asked for STATUS:**
- Run: `git log --oneline -10` and `git status`
- Summarize recent activity and current state

**Step 4: Telegram Response Formatting**
- Keep messages SHORT (under 255 chars for initial response)
- Use Telegram markdown: *bold*, _italic_, `code blocks`
- If response is long, use `split_long_message()` function (see below)
- ALWAYS acknowledge the user's request before executing
- Report success/failure clearly with emojis: ✅ 🔴 ⚠️

### OUTPUT

Send response back to Telegram using:
```

import requests

def send_telegram_response(chat_id, message_text):
"""Send response back through Telegram API"""
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
"chat_id": chat_id,
"text": message_text,
"parse_mode": "Markdown"
}
response = requests.post(url, json=payload)
return response.json()

def split_long_message(text, max_length=4096):
"""Split long messages for Telegram (max 4096 chars)"""
messages = []
current = ""
for line in text.split("\n"):
if len(current) + len(line) > max_length:
messages.append(current)
current = line
else:
current += "\n" + line if current else line
if current:
messages.append(current)
return messages

```

**Response format examples:**
- ✅ _"Found 3 files with that pattern. Here's the main one:_\n\n`code snippet`"
- 🔴 _"Error: That file doesn't exist. Did you mean `file_name.py`?"_
- ⚠️ _"Analyzing... (this might take a moment)"_ (then follow with results)

---

## CONTROL FLOW & CONDITIONAL LOGIC

### Decision Tree for Incoming Messages

```

IF message contains ["help", "?", "explain", "what", "how", "show me", "what is"]
→ QUESTION intent
→ grep + read files + extract answer

ELSE IF message contains ["create", "make", "write", "add", "implement", "refactor"]
→ COMMAND intent
→ Ask for confirmation
→ Execute via Claude Code
→ Commit with message

ELSE IF message contains ["analyze", "review", "check", "find bug", "error", "test"]
→ ANALYSIS intent
→ Run static checks
→ Read affected code
→ Report findings

ELSE IF message contains ["status", "recent", "what's new", "commits", "changes"]
→ STATUS intent
→ git log + git status
→ Summarize recent activity

ELSE
→ Ask for clarification
→ "I didn't understand. Ask me about code, request changes, or ask for analysis."

```

### Early Returns (Stop Conditions)

- **IF no bot token provided**: Exit immediately with error message
- **IF chat_id is invalid**: Log error and don't send response (silent fail)
- **IF repo is not initialized**: Alert user and suggest `git init`
- **IF file doesn't exist in repo**: Tell user with suggestions of similar files
- **IF API rate limit hit**: Queue message for retry in 5 seconds

---

## NLP & CONTEXT UNDERSTANDING

### Extract User Intent from Natural Language

```

def extract_intent(message_text):
"""Classify user message intent"""
text_lower = message_text.lower()

    # Intent keywords mapping
    intents = {
        "question": ["what", "how", "explain", "show", "find", "where", "which", "?"],
        "command": ["create", "make", "write", "add", "implement", "refactor", "delete", "rename"],
        "analysis": ["analyze", "review", "check", "find bug", "error", "test", "debug"],
        "status": ["status", "recent", "commits", "changes", "what's new", "latest"]
    }
    
    for intent, keywords in intents.items():
        if any(kw in text_lower for kw in keywords):
            return intent
    
    return "unclear"
    def extract_keywords(message_text):
"""Pull out specific targets from message"""
\# Examples:
\# "What does the parse function do?" → ["parse", "function"]
\# "Create a test for authentication" → ["test", "authentication"]
\# "Analyze database.py for errors" → ["database.py", "errors"]

    import re
    # Find quoted strings, code identifiers, filenames
    quoted = re.findall(r'"([^"]*)"', message_text)
    code_identifiers = re.findall(r'`([^`]*)`', message_text)
    filenames = re.findall(r'(\w+\.py|\w+\.js|\w+\.ts)', message_text)
    
    return {
        "quoted": quoted,
        "code": code_identifiers,
        "files": filenames,
        "raw_text": message_text
    }
    ```

### Build Intelligent Responses

Use repo context to craft relevant answers:

```

def build_intelligent_response(intent, keywords, repo_context):
"""Generate context-aware response"""

    if intent == "question":
        # Search repo for answer
        search_term = keywords['code'] if keywords['code'] else keywords['raw_text']
        results = grep_repo(search_term)  # Uses: grep -r
        
        if results:
            file_content = read_file(results['file'])
            answer = extract_relevant_section(file_content, search_term)
            return f"Found in `{results[^0]['file']}`:\n\n{answer}"
        else:
            return f"⚠️ Couldn't find info about '{search_term}'. Can you be more specific?"
    
    elif intent == "command":
        action = keywords['raw_text']
        return f"⏳ Processing: {action}\n\n[Waiting for your confirmation to proceed]"
    
    # ... more intent handlers
    ```

---

## WEBHOOK SETUP (inbound message receiver)

**Flask/FastAPI endpoint to receive Telegram messages:**

```

from flask import Flask, request, jsonify
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = "<your_bot_token>"
WEBHOOK_URL = "<your_public_url>/telegram_inbound"

@app.route('/telegram_inbound', methods=['POST'])
def telegram_webhook():
"""Receive inbound Telegram messages and route to Claude Agent"""

    try:
        update = request.get_json()
        logging.info(f"Telegram update received: {json.dumps(update)}")
        
        # Extract message info
        if 'message' not in update:
            return jsonify({'status': 'ok'}), 200
        
        message = update['message']
        chat_id = message['chat']['id']
        user_text = message.get('text', '')
        user_id = message['from']['id']
        
        # Log the incoming message
        logging.info(f"Message from {user_id} in chat {chat_id}: {user_text}")
        
        # CRITICAL: Pass to Claude agent for processing
        response = process_with_claude_agent(
            user_message=user_text,
            chat_id=chat_id,
            user_id=user_id
        )
        
        # Send response back to Telegram
        send_to_telegram(chat_id, response)
        
        return jsonify({'status': 'ok'}), 200
    
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    def process_with_claude_agent(user_message, chat_id, user_id):
"""Route message to Claude CLI for intelligent processing"""

    # Build the prompt context
    prompt = f"""
    User Message: {user_message}
    Chat ID: {chat_id}
    User ID: {user_id}
    
    INSTRUCTIONS:
    1. Classify the intent (question/command/analysis/status)
    2. Extract keywords and context from the message
    3. Execute appropriate repo inspection/code commands
    4. Build a natural language response
    5. Return as a single string for Telegram
    """
    
    # Call Claude Code CLI with the prompt
    # This is where your agent factory orchestration happens
    response = call_claude_code_cli(prompt)
    
    return response
    def send_to_telegram(chat_id, message_text):
"""Send response back through Telegram API"""

    import requests
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Split long messages if needed
    for chunk in split_long_message(message_text):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload)
        logging.info(f"Telegram response: {response.json()}")
    
    return response.json()
    if __name__ == '__main__':
app.run(host='0.0.0.0', port=8000)

```

---

## ENVIRONMENT VARIABLES & CONFIGURATION

**Required .env variables:**

```

TELEGRAM_BOT_TOKEN=[your_bot_token_from_@BotFather](mailto:your_bot_token_from_@BotFather)
TELEGRAM_WEBHOOK_URL=<your_public_url>/telegram_inbound
REPO_PATH=<absolute_path_to_your_repo>
CLAUDE_API_KEY=<your_claude_api_key>

```

**Set webhook with Telegram:**

```

curl -X POST https://api.telegram.org/bot{TOKEN}/setWebhook \
-H 'Content-Type: application/json' \
-d '{"url": "https://yourdomain.com/telegram_inbound", "allowed_updates": ["message"]}'

```

---

## EXECUTION INSTRUCTIONS

### For Claude Code CLI:

1. **Save this prompt** as `telegram_agent_prompt.md`
2. **Run in streaming mode** to see real-time thinking:
```

claude -p @telegram_agent_prompt.md --stream

```

3. **Run in JSON mode** to get structured output:
```

claude -p @telegram_agent_prompt.md --json

```

4. **Run with file context** to give agent access to repo structure:
```

claude -p @telegram_agent_prompt.md --file repo_structure.txt

```

5. **Run in loop mode** (for persistent agent):
```

while true; do
claude -p @telegram_agent_prompt.md --stream
sleep 2
done

```

### Integration with your existing outbound system:

Your PR commits are working because you have **OUTPUT** working. Now add **INPUT** by:

1. Deploy the Flask webhook endpoint above (run on port 8000 with public tunnel using ngrok or your VPS)
2. Register the webhook URL with Telegram using the `setWebhook` command
3. When messages arrive, they hit `/telegram_inbound` which calls Claude
4. Claude processes the message and calls `send_to_telegram()` to respond

---

## KEY BEHAVIORAL EXPECTATIONS

- **Acknowledge immediately**: "Got it, analyzing..." (helps user know it's working)
- **Be concise**: Telegram is mobile-first. Max 2-3 sentences for initial response.
- **Provide context**: "Found in `src/auth.py` line 42:" (shows WHERE you found the answer)
- **Ask clarifying questions**: "Do you mean the `process_data()` function or data processing in general?"
- **Handle errors gracefully**: "⚠️ That file doesn't exist. Try: `list_files` to see what's available."
- **Show progress**: "⏳ Running tests... (about 10 seconds)" for long operations
- **Confirm destructive actions**: "Are you sure you want to delete this? Reply YES to confirm."

---

## DEBUGGING & TESTING

**Test the webhook locally:**

```


# Send test message to your webhook

curl -X POST http://localhost:8000/telegram_inbound \
-H 'Content-Type: application/json' \
-d '{
"message": {
"chat": {"id": 123456789},
"from": {"id": 987654321},
"text": "What does the main function do?"
}
}'

```

**Check webhook is registered:**

```

curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo

```

**View Telegram bot logs:**

```

tail -f telegram_agent.log

```

---

This prompt gives Claude CLI the complete framework to handle **inbound Telegram messages** with **intelligent NLP-based responses** while maintaining your existing **outbound PR commit functionality**. The key additions are the webhook receiver, intent classification, repository context gathering, and smart response formatting for Telegram.

Start with the Flask endpoint, register the webhook, and run the Claude agent against incoming messages. You'll get two-way communication! 🚀
<span style="display:none">[^1][^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^2][^20][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.reddit.com/r/ClaudeAI/comments/1ovm0d2/i_built_a_telegram_bot_to_control_claude_code/
[^2]: https://stackoverflow.com/questions/66386537/how-to-set-webhook-for-telegram-bot-in-python/66387928
[^3]: https://www.youtube.com/watch?v=luqKnexhpFs
[^4]: https://www.appypieautomate.ai/integrate/apps/claude/integrations/telegram
[^5]: https://pinggy.io/blog/how_to_set_up_and_test_telegram_bot_webhook/
[^6]: https://www.anthropic.com/engineering/claude-code-best-practices
[^7]: https://www.reddit.com/r/ClaudeAI/comments/1oao2xq/i_built_a_bot_so_i_can_use_claude_code_cli_from/
[^8]: https://docs.python-telegram-bot.org/en/v21.9/examples.customwebhookbot.html
[^9]: https://claudate.com/skills/agent-factory
[^10]: https://sreeninet.wordpress.com/2025/08/16/the-rise-of-cli-based-ai-coding-agents-claude-code-vs-gemini-cli/
[^11]: https://stackoverflow.com/questions/76884609/deploy-telegram-bot-on-webhooks
[^12]: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
[^13]: https://github.com/RichardAtCT/claude-code-telegram
[^14]: https://www.freecodecamp.org/news/how-to-build-and-deploy-python-telegram-bot-v20-webhooks/
[^15]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
[^16]: https://www.linkedin.com/posts/robertgpt_claude-telegram-mirror-is-a-typescript-bridge-activity-7402945910608969728-6L82
[^17]: https://github.com/gkiryaziev/Python-Telegram.Bot-WebHook
[^18]: https://www.siddharthbharath.com/factory-ai-guide/
[^19]: https://github.com/coleam00/remote-agentic-coding-system
[^20]: https://github.com/python-telegram-bot/python-telegram-bot/discussions/4299```

