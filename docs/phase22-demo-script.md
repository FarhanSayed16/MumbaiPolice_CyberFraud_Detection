# Demo Script: Mumbai Police Cyber Fraud Detection Platform

**Target Audience:** Senior IPS Officers, Nodal Officers (Cyber Cell), and Potential Sponsor Officers.
**Duration:** 15-20 minutes.
**Goal:** Demonstrate the "10x Efficacy Engine", showing how graph-based correlation cuts investigation time from weeks to minutes, without over-promising on integrations that are currently out of scope (like live banking APIs).

---

## 1. Introduction (2 mins)
**Speaker:** "Good morning, Sir/Ma'am. Today we are presenting a functional prototype of the Cyber Fraud Detection platform. Our primary goal is to address the fragmented nature of financial fraud investigations where officers manually correlate CSVs from multiple banks. This platform automates the money trail discovery using Graph Database technology, instantly linking suspects across seemingly unrelated cases."

## 2. The Current Problem vs. Our Solution (2 mins)
**Speaker:** "Currently, when a victim reports a cyber fraud, the money moves rapidly across 5-6 mule accounts in different banks. By the time an IO receives statements via email and maps them in Excel, the funds are cashed out. 
With our system, once the bank data is ingested, the system automatically draws the money trail. We call this the '10x Efficacy Engine'."

## 3. Live Demonstration (10 mins)

### Step 1: Login & Dashboard
*Action: Log in as `admin.mumbai@maharashtracyber.gov.in`.*
**Speaker:** "We log in securely using Role-Based Access Control. The Dashboard provides a real-time overview of active cases, total amount at risk, and SLA breaches. Every action is logged in an immutable audit trail."

### Step 2: Ingestion
*Action: Navigate to the 'Ingestion' tab.*
**Speaker:** "Here is where the manual work is eliminated. We upload standardized CSVs received from banks or CFCFRMS. The system parses these files, identifies the sender, receiver, amounts, and flags cash-outs automatically."

### Step 3: Case View & Timeline
*Action: Open `Case Scenario 1` from the 'Cases' tab.*
**Speaker:** "Let's look at a specific case. The Case Details view shows the victim information and total amount defrauded. The timeline automatically logs all evidence and actions taken by the IO. It serves as a unified digital case diary."

### Step 4: The Graph Canvas (The "Aha!" Moment)
*Action: Click on 'View Graph' or 'Money Trail'. Expand nodes.*
**Speaker:** "This is the core of the platform. Instead of rows of data, the IO sees a visual network. We can instantly trace where the Rs. 50,000 went. 
Notice how this mule account is also linked to *another* case reported in a different police station? The system connects these dots automatically, exposing the larger syndicate."

### Step 5: Action (Notice Generation)
*Action: Select a mule account and click 'Generate Sec 91 Notice'.*
**Speaker:** "Once we identify a mule account, we can immediately generate a Section 91/106 CRPC notice. The system pre-fills the bank's Nodal Officer details and generates a tamper-proof PDF, ready for digital signature and dispatch. What used to take hours now takes seconds."

## 4. Q&A and "Honest Answers" (5 mins)

**Expected Objection 1: "Does this connect directly to banks to freeze accounts instantly?"**
**Honest Answer:** "Not yet, Sir. Direct API integration with banks (Channel B) requires MoUs and RBI/I4C facilitation. Currently, the system operates on the standardized CSVs you already receive. Our architecture is API-ready, meaning once the legal approvals are in place, the technical integration will be seamless. For now, it drastically speeds up the *analysis* and *notice generation*."

**Expected Objection 2: "Is this replacing NCRP/CFCFRMS?"**
**Honest Answer:** "No, it complements it. NCRP is the national repository. This platform is an operational tool for Mumbai Police IOs to conduct the actual investigation and link cases locally before updating NCRP."

**Expected Objection 3: "How secure is the data?"**
**Honest Answer:** "Very secure. We have implemented strict RBAC, data masking for PII, and an immutable audit log. An officer can only view cases assigned to their unit, unless authorized. The platform is designed to be hosted on secure internal state networks, not the public internet."

---
*End of Demo.*
