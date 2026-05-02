import os
import time
import pandas as pd
from retriever import SupportRetriever
from agent import TriageAgent


def main():
    print("Starting Orchestrator...")
    
    # Get the project root directory (one level up from 'code')
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Initialize Components
    retriever = SupportRetriever()
    agent = TriageAgent()
    
    # 2. Define absolute paths
    # Update these based on where the 'support_tickets' folder actually sits
    input_csv = os.path.join(BASE_DIR, "support_tickets", "support_tickets.csv")
    output_csv = os.path.join(BASE_DIR, "support_tickets", "output.csv")
    
    # Double check if the file exists before reading
    if not os.path.exists(input_csv):
        print(f"❌ Error: Cannot find {input_csv}")
        return

    df = pd.read_csv(input_csv)

    # 1. Force all column names to lowercase
    # 2. Strip any accidental leading/trailing spaces
    df.columns = [c.strip().lower() for c in df.columns]

    print(f"Columns normalized to: {df.columns.tolist()}")

    results = []
    # Now row['issue'] and row['company'] will work perfectly!

    print(f"Processing {len(df)} tickets...\n")

    # 3. Main Processing Loop
    for index, row in df.iterrows():
        issue = row['issue']
        subject = row.get('subject', '')
        company = row['company']

        print(f"\n--- Processing Ticket {index+1} [{company}] ---")
        print(f"Issue: {issue[:100]}...")

        # A. Get strictly filtered context (pass subject for better retrieval)
        context = retriever.get_context(issue, company, subject=subject)
        print(f"Context found: {len(context)} chars")

        # B. Generate Agent Decision
        decision = agent.process_ticket(issue, company, context)

        print(f"Result: Status={decision.get('status')}, Type={decision.get('request_type')}")
        results.append(decision)
        
        # Small delay to let Ollama recover between requests
        time.sleep(1)



    # 4. Save Output
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_csv, index=False)
    print(f"\nAll tickets processed. Results saved to {output_csv}")

if __name__ == "__main__":
    main()
