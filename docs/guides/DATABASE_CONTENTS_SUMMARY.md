# SQLite Database Contents Summary

## Database: `indian_legal_db.sqlite`

### Tables Found: 5
1. **legal_documents** - Main documents table
2. **document_categories** - Document categorization (empty)
3. **citations** - Citation relationships (empty)
4. **sqlite_sequence** - SQLite internal table
5. **update_log** - Update tracking (empty)

---

## Legal Documents Table

### Total Documents: **5**

### Document Breakdown:

#### By Document Type:
- **Act**: 2 documents
- **Constitution**: 1 document
- **Judgment**: 1 document
- **Statute**: 1 document

#### By Source:
- **Constitution of India**: 1 document
- **Consumer Protection Act**: 1 document
- **Indian Penal Code**: 1 document
- **Right to Education Act**: 1 document
- **Supreme Court Judgment**: 1 document

#### Date Range: **1860 to 2019**

---

## Sample Documents:

1. **Article 21 of Indian Constitution**
   - Type: Constitution
   - Source: Constitution of India
   - Date: 1950
   - Content: Right to life and personal liberty

2. **Right to Privacy - Puttaswamy Case**
   - Type: Judgment
   - Source: Supreme Court Judgment
   - Date: 2017
   - Content: Landmark privacy judgment

3. **Section 420 of Indian Penal Code**
   - Type: Statute
   - Source: Indian Penal Code
   - Date: 1860
   - Content: Cheating and dishonestly inducing delivery

4. **Right to Education Act 2009**
   - Type: Act
   - Source: Right to Education Act
   - Date: 2009
   - Content: Free and compulsory education

5. **Consumer Protection Act 2019**
   - Type: Act
   - Source: Consumer Protection Act
   - Date: 2019
   - Content: Consumer rights and protection

---

## Database Schema:

### legal_documents columns:
- doc_id (TEXT)
- title (TEXT)
- content (TEXT)
- doc_type (TEXT)
- court (TEXT)
- date (TEXT)
- url (TEXT)
- source (TEXT)
- citations (TEXT)
- keywords (TEXT)
- hash (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

---

## Summary:

- **Total Documents**: 5 sample legal documents
- **Coverage**: Constitution, Acts, Statutes, Judgments
- **Time Range**: 1860-2019
- **Sources**: Indian Constitution, IPC, Acts, Supreme Court
- **Empty Tables**: document_categories, citations, update_log

**Note**: These are the sample documents added for POC demonstration. The database is ready for expansion with more legal documents.






