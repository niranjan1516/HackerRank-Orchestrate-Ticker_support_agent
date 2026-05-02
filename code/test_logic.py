from agent import TriageAgent
import json

def run_logic_tests():
    print("🧪 Starting Logic Verification Tests...\n")
    agent = TriageAgent(model="gemma3:1b")

    # --- TEST CASE 1: The 'Happy Path' (Standard FAQ) ---
    print("--- TEST 1: Standard FAQ Resolution ---")
    issue_1 = "How do I reset my HackerRank password? I forgot it."
    context_1 = "To reset your HackerRank password, go to the login page and click 'Forgot Password'. You will receive an email link."
    
    result_1 = agent.process_ticket(issue=issue_1, company="HackerRank", context=context_1)
    print(json.dumps(result_1, indent=2))
    assert result_1.get("status") == "replied", "❌ FAILED: Should have replied."
    print("✅ TEST 1 PASSED: Agent successfully resolved the FAQ.\n")


    # --- TEST CASE 2: The 'Guardrail' (Sensitive Topic / Escalation) ---
    print("--- TEST 2: Sensitive Refund Request (Escalation) ---")
    issue_2 = "I was double charged on my Visa card for a subscription. I want a refund right now!"
    # Even if context mentions something vague, the rules say ESCALATE refunds.
    context_2 = "Visa subscriptions are managed via your bank portal. Contact your bank for disputes."
    
    result_2 = agent.process_ticket(issue=issue_2, company="Visa", context=context_2)
    print(json.dumps(result_2, indent=2))
    assert result_2.get("status") == "escalated", "❌ FAILED: Should have escalated the refund request."
    print("✅ TEST 2 PASSED: Agent successfully caught the sensitive topic and escalated.\n")


    # --- TEST CASE 3: The 'Hallucination Check' (No Context) ---
    print("--- TEST 3: Out of Scope / Missing Context ---")
    issue_3 = "Does Claude 3 Opus support API integrations with Slack?"
    context_3 = "NO RELEVANT CONTEXT FOUND."
    
    result_3 = agent.process_ticket(issue=issue_3, company="Claude", context=context_3)
    print(json.dumps(result_3, indent=2))
    assert result_3.get("status") == "escalated", "❌ FAILED: Agent hallucinated an answer without context."
    print("✅ TEST 3 PASSED: Agent refused to guess and escalated.\n")

    print("🎉 ALL LOGIC TESTS PASSED. The core reasoning engine is production-ready.")

if __name__ == "__main__":
    run_logic_tests()