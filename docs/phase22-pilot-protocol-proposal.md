# Pilot Protocol Proposal: Real-Data Validation

**Objective:** Conduct a controlled, 4-6 week pilot using historical, closed-case data to validate the time-saving claims of the Cyber Fraud Detection platform and gather frontline officer feedback before pushing for production integration.

---

## 1. The Ask: 5-10 Closed Cases
We request access to 5-10 recently closed cyber fraud cases. 
- **Criteria:** Cases should involve at least 3-4 layers of money movement across different banks.
- **Inputs Required:** The raw CSV bank statements obtained during the investigation, and the final NCRP/Investigation report showing the manually deduced money trail.
- **Why Closed Cases?** By using closed cases, we eliminate operational risk. We can directly compare the platform's automated output against the known, verified outcome compiled by the IO.

## 2. Success Metrics (KPIs)
The pilot will be deemed successful if it meets the following criteria:
1. **Time-to-Trail Reduction:** A 90% reduction in time taken from receiving the CSVs to mapping the 3rd-hop money trail (e.g., reducing a 2-week manual process to under 1 hour).
2. **Accuracy:** 100% correlation match with the human-investigated outcome for the provided cases.
3. **Cross-Case Discovery:** (Bonus) The system identifies at least one overlapping mule account between the 5-10 disparate cases that was previously unnoticed manually.

## 3. Execution Window
- **Duration:** 4 to 6 weeks.
- **Location:** An isolated, secure staging environment (on-premise or secure cloud VPC as directed by Maharashtra Cyber).
- **Champion Officer:** We request the assignment of 1-2 "Champion Officers" (Investigating Officers) who will spend 2 hours a week feeding the data into the system and validating the output.

## 4. Security, PII, and Retention Rules
To ensure data sovereignty and privacy during the pilot:
- **Environment:** The pilot database will be completely isolated from the current demo seed data.
- **Named Access:** Only the designated Champion Officers and 2 cleared technical administrators will have credentials.
- **Data Purge:** At the conclusion of the 6-week window, regardless of outcome, all uploaded CSVs, generated graphs, and case data will be securely purged from the pilot database, generating a cryptographic certificate of destruction.
- **PII Masking:** If requested, names and raw account numbers can be partially masked prior to upload, provided the unique identifiers remain consistent for graph mapping.

---
**Next Steps:** Await formal approval to provision the Staging Pilot environment and schedule the handover of the closed-case CSVs to the Champion Officers.
