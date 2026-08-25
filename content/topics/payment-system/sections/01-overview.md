# Overview
A payment system processes financial transactions with strict correctness requirements: no duplicate charges, no lost payments, and a complete audit trail. The system must handle payment gateway integration, idempotency, double-entry accounting, and reconciliation.

Financial systems cannot tolerate eventual consistency for core operations; strong consistency is required for the ledger.
