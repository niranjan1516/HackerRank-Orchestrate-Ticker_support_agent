import json
import requests
import re
import time


class TriageAgent:
    def __init__(self, model="gemma3:1b"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model

    def _detect_escalation_signals(self, issue: str, context: str, company: str) -> tuple:
        """
        Pre-process ticket to detect obvious escalation patterns without LLM call.
        Returns (should_escalate, reason) or (None, None) if LLM should decide.
        """
        issue_lower = issue.lower()
        
        # High-risk keywords that ALWAYS escalate (financial, legal, security)
        escalation_keywords = [
            "refund me", "give me a refund", "chargeback", "dispute charge",
            "fraud", "hacked", "breach", "security vulnerability", "compromised", 
            "stolen identity", "identity theft", "legal action", "lawyer", "lawsuit",
            "gdpr violation", "dpa violation", "ban the seller", "ban this seller",
            "restore my access immediately", "delete all files", "rm -rf"
        ]
        
        # Out-of-scope / non-support topics
        out_of_scope = [
            "iron man", "movie", "actor", "celebrity", "sports", "weather",
            "politics", "news", "stock price", "bitcoin", "crypto"
        ]
        
        # Critical bug / outage indicators (platform-wide only)
        critical_bug_indicators = [
            "site is down", "pages are not accessible", "none of the pages",
            "complete outage", "platform is down", "server error", "502", "503"
        ]
        
        # Check for obvious out-of-scope
        for keyword in out_of_scope:
            if keyword in issue_lower:
                return (
                    False,
                    {
                        "status": "replied",
                        "product_area": "General Support",
                        "response": "I'm sorry, this request is outside the scope of our support services. I'm unable to assist with this inquiry.",
                        "justification": "The request is unrelated to our products and services.",
                        "request_type": "invalid"
                    }
                )
        
        # Check for critical platform-wide outages only
        for keyword in critical_bug_indicators:
            if keyword in issue_lower:
                return (
                    False,
                    {
                        "status": "escalated",
                        "product_area": "Platform Engineering",
                        "response": "We've identified this as a platform-wide issue. Our engineering team has been notified and is investigating.",
                        "justification": "This appears to be a platform outage affecting multiple users.",
                        "request_type": "bug"
                    }
                )
                
        # Check for high-risk escalation keywords
        for keyword in escalation_keywords:
            if keyword in issue_lower:
                return (
                    False,
                    {
                        "status": "escalated",
                        "product_area": "Security & Compliance",
                        "response": "This request involves a sensitive matter that requires human review. I've escalated this to our support team who will contact you shortly.",
                        "justification": f"This ticket contains sensitive keywords requiring human handling.",
                        "request_type": "product_issue"
                    }
                )
        
        # If no context found, escalate
        if "NO RELEVANT CONTEXT FOUND" in context:
            return (
                False,
                {
                    "status": "escalated",
                    "product_area": "Out of Scope",
                    "response": "I'm sorry, I don't have information on this topic. Escalating to a human agent for further assistance.",
                    "justification": "No relevant support documentation available in our knowledge base.",
                    "request_type": "invalid"
                }
            )
        
        return (None, None)


    def _extract_json(self, text: str) -> dict:
        """Robustly extract JSON from LLM response, handling various formats."""
        if not text:
            return {}
        
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try finding JSON in markdown code blocks
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r"\{.*?\}",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # If the pattern captures the braces too
                    candidate = match if match.strip().startswith("{") else "{" + match + "}"
                    if not match.strip().startswith("{"):
                        continue
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Try to fix common JSON issues
        # Remove trailing commas
        fixed = re.sub(r',\s*}', '}', text)
        fixed = re.sub(r',\s*]', ']', fixed)
        # Fix single quotes
        fixed = fixed.replace("'", '"')
        
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        return {}

    def _validate_and_fix(self, data: dict, issue: str, context: str) -> dict:
        """Ensure the output has all required fields with valid values."""
        valid_statuses = {"replied", "escalated"}
        valid_request_types = {"product_issue", "feature_request", "bug", "invalid"}
        
        # Default values
        status = data.get("status", "").lower().strip()
        if status not in valid_statuses:
            status = "escalated"
        
        request_type = data.get("request_type", "").lower().strip().replace(" ", "_")
        if request_type not in valid_request_types:
            request_type = "product_issue"
        
        product_area = data.get("product_area", "General Support")
        if not product_area or product_area == "Out of Scope":
            product_area = "General Support"
        
        response = data.get("response", "Internal triage required.")
        if not response or len(response) < 10:
            response = "Your request has been received and is being processed."
        
        justification = data.get("justification", "Defaulting to safe handling.")
        if not justification:
            justification = "Based on available documentation and ticket analysis."
        
        return {
            "status": status,
            "product_area": product_area,
            "response": response,
            "justification": justification,
            "request_type": request_type
        }

    def process_ticket(self, issue: str, company: str, context: str) -> dict:
        # Step 1: Check pre-processing rules
        should_escalate, rule_result = self._detect_escalation_signals(issue, context, company)
        if rule_result is not None:
            return rule_result

        # Step 2: Build minimal prompt (reduce Ollama memory pressure)
        system_prompt = f"""You are a support triage agent for {company}. Return JSON.

    ESCALATE: refund/fraud/legal/breach/sensitive action/missing context.
    REPLY: context has HOW-TO and no risk.

    request_type: product_issue|feature_request|bug|invalid

    JSON: status,product_area,response,justification,request_type

    Example:
    Context: "Click Forgot Password."
    Ticket: "I forgot password"
    {{"status":"replied","product_area":"Account","response":"Click Forgot Password.","justification":"Context has instructions.","request_type":"product_issue"}}"""



        user_prompt = f"""CONTEXT FROM HELP CENTER:
    ---
    {context}
    ---

    SUPPORT TICKET:
    Company: {company}
    Issue: {issue}

    Return ONLY the JSON object:"""

        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 0.9,
                "num_predict": 200,
                "num_ctx": 2048
            }
        }

        # Retry logic with exponential backoff for 500 errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = requests.post(self.url, json=payload, timeout=90)
                res.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                if res.status_code == 500 and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"  Ollama 500 error, retrying in {wait}s... (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait)
                    continue
                # Final attempt failed or non-500 error - use fallback
                print(f"  HTTP error after retries: {e}")
                return self._fallback_response(context, "LLM HTTP error")
            except requests.exceptions.ConnectionError:
                return {
                    "status": "escalated",
                    "product_area": "System Error",
                    "response": "Ollama server not running on localhost:11434. Please start the server.",
                    "justification": "LLM inference service is unavailable.",
                    "request_type": "product_issue"
                }

        try:
            raw_output = res.json().get('response', '{}')
            print(f"  Raw LLM output: {raw_output[:200]}...")

            data = self._extract_json(raw_output)
            
            if not data:
                print("  Warning: Could not parse JSON, using fallback.")
                return self._fallback_response(context, "LLM JSON parse failed")

            return self._validate_and_fix(data, issue, context)

        except Exception as e:
            print(f"  Exception during processing: {e}")
            return self._fallback_response(context, f"Exception: {str(e)[:50]}")

    def _fallback_response(self, context: str, error_msg: str = "") -> dict:
        """Fallback when LLM fails - use context directly."""
        # If context is useful, reply with it; otherwise escalate
        if len(context) > 100 and "NO RELEVANT" not in context:
            # Extract first meaningful part as response
            response_text = context[:400].replace('\n', ' ').strip()
            if len(response_text) > 100:
                response_text = response_text[:response_text.rfind('.')+1] or response_text[:100]
            return {
                "status": "replied",
                "product_area": "General Support",
                "response": f"Based on our documentation: {response_text}",
                "justification": f"LLM failed, using context available. Error: {error_msg}",
                "request_type": "product_issue"
            }
        return {
            "status": "escalated",
            "product_area": "General Support",
            "response": "Unable to process automatically. Escalating to human support.",
            "justification": f"No context or LLM failed. Error: {error_msg}",
            "request_type": "product_issue"
        }
