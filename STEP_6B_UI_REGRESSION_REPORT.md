# STEP 6B: FULL CMS UI REGRESSION & ISOLATION REPORT
## Sales Lead Machine Visual CMS & Frontend Parity Audit

**Date:** November 5, 2026  
**Auditor / Specialist:** Senior QA Automation Engineer, CMS Testing Specialist & Frontend Verification Engineer  
**Status:** PASS (100% Verified Across All Test Suites)

---

## 1. Executive Summary

This report delivers the comprehensive end-to-end verification results for **Step 6B: Full CMS UI Regression, State Isolation, Additional Modules, and Visual Parity Confirmation**.

Rather than relying purely on direct database writes or backend API endpoints, this audit drove the actual **Visual Studio frontend editor** and **Admin Panel** using Playwright automation. The test suite exercised every supported section type through the complete 10-step lifecycle: visual canvas click-to-select, editor inspector card activation, form field editing, draft persistence across browser reloads, anonymous draft isolation, authenticated draft preview (`?mode=draft`), UI publication, public frontend update, and clean baseline restoration.

Additionally, this report formally confirms the resolution of:
1. **The Inverted Eyebrow / H1 Title Bug** and button text discrepancies on inner role pages highlighted in user visual audits.
2. **Step 3 (Padding Normalization) & Step 4 (Section Height Verification)** across homepage split sections `0b9f330`, `184c9a6`, and `b5a6373` (achieving exact **0.0px delta** vs live production).
3. **Enterprise CMS Subsystems:** Real PNG upload with magic-byte validation and database persistence (`media`), Client Logo Wall management (`client_logos`), Team Members (`team_members`), Global Company Info synchronization, and multi-step Form rendering (`/survey/`, `/contact-sales/`, `/contact-us/`).

---

## 2. Priority 3: Visual CMS Editor UI Regression (7 Section Types)

Each section type was evaluated through the strict 10-step operational lifecycle:
1. **Navigate to Page in CMS:** Open visual canvas in the editor.
2. **Click-to-Select:** Click target section on the visual frontend iframe; verify DOM `.cms-selected` class applied.
3. **Inspector Activation:** Verify corresponding inspector card opens with matched anchor ID.
4. **Mutate Representative Field:** Inject unique timestamped regression token into the form input.
5. **Save Draft via UI:** Click "Save Draft"; verify success toast notification and database `draft_data`.
6. **Editor Reload Persistence:** Refresh editor browser window; verify input retains draft value.
7. **Anonymous Draft Isolation:** Fetch URL in unauthenticated session; verify draft content is NOT visible.
8. **Authenticated Draft Preview:** Request URL with `?mode=draft` and admin auth; verify draft content IS visible.
9. **Publish via UI:** Click "Publish Changes" button; verify UI confirms publication and database updates `data`.
10. **Public Live Update & Restoration:** Verify anonymous session immediately sees the published change; then restore baseline data and re-publish to leave the page clean.

### Summary Table of Tested Section Types & Controls

| Section Type | Section Name | Page URL | Anchor ID | Field Tested | Click-to-Select | Draft Save | Reload Persist | Draft Isol. | Draft Prev. | UI Publish | Live Update | Restoration | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **hero** | Homepage Hero Section | `/` | `a26d791` | `title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **hero** | Homepage Hero Section | `/` | `a26d791` | `eyebrow` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **hero** | Homepage Hero Section | `/` | `a26d791` | `btn1_text` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **split** | Boost Campaigns Split | `/` | `b5a6373` | `title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **split** | Boost Campaigns Split | `/` | `b5a6373` | `eyebrow` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **card_grid** | Problems Solved Grid | `/problems-we-solve/` | `46f0fd0a` | `title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **card_grid** | Problems Solved Grid | `/problems-we-solve/` | `46f0fd0a` | `card_0_title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **cta_banner**| Cross-Department Banner| `/for-sales/` | `6a7f42f` | `title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **cta_banner**| Cross-Department Banner| `/for-sales/` | `6a7f42f` | `cta_text` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **rich_text** | Privacy Policy Doc | `/privacy-policy/` | `slm-privacy-content` | `title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **team** | Leadership Team Grid | `/about-us/` | `db423c8` | `title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **team** | Leadership Team Grid | `/about-us/` | `db423c8` | `member_0_name`| PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **logo_wall** | Trusted Partners Wall | `/about-us/` | `0f7f56b` | `title` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **logo_wall** | Trusted Partners Wall | `/about-us/` | `0f7f56b` | `logo_0_name` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |

*All 14 control tests succeeded without manual intervention. Output recorded in `STEP_6B_FIELD_LEVEL_RESULTS.csv`.*

---

## 3. Priority 4: State & Scope Isolation Testing

To ensure that edits in one section or page never corrupt adjacent data or prematurely publish unreviewed drafts, rigorous isolation scenarios were executed:

### 3.1 Section-to-Section Isolation (Same Page)
- **Action:** Mutated draft data for Homepage Hero section (`a26d791`).
- **Observation:** Split section `b5a6373` on the same page was independently inspected. Its draft state and published live data remained strictly byte-identical to baseline.
- **Result:** **PASS**.

### 3.2 Page-to-Page Isolation (Cross-Route)
- **Action:** Saved an uncommitted draft mutation on `/for-technology/` (`448e895`).
- **Observation:** Inspected sections on `/for-sales/` (`6693c47`). All sections on `/for-sales/` maintained zero draft changes and pristine baseline data.
- **Result:** **PASS**.

### 3.3 Publish Scope Isolation
- **Action:** Retained a pending uncommitted draft on `/for-sales/` (`6693c47`), while publishing changes on `/for-technology/` (`448e895`).
- **Observation:** The live public `/for-technology/` updated immediately. The live public `/for-sales/` remained untouched, and its draft on `/for-sales/` remained pending and un-published.
- **Result:** **PASS**.

### 3.4 Save/Refresh Idempotency (Anti-Duplication)
- **Action:** Executed 3 consecutive Save Draft -> Reload Editor -> Publish cycles on Split Section `0b9f330`.
- **Observation:** Production baseline split section `0b9f330` contains exactly 1 intro paragraph + 5 bullet description paragraphs (total 6 `<p>` tags). After 3 full cycles, the DOM rendered exactly 6 `<p>` tags. Zero duplication of text, bullet points, or wrapper containers occurred.
- **Result:** **PASS**.

---

## 4. Priority 5: Additional Enterprise CMS Modules

### 4.1 Binary Media Upload & Magic-Byte Validation
- Real PNG file (`\x89PNG\r\n\x1a\n...`) uploaded to `/api/media/upload`.
- **Validation:** Upload succeeded with HTTP 200 and JSON response payload containing `/wp-content/uploads/team/...`.
- **Persistence:** Verified row insertion in PostgreSQL `media` table:
  - `file_name`: Verified matching filename.
  - `mime_type`: Verified `image/png`.
  - `file_path`: Verified physical path on disk.
- **Result:** **PASS**.

### 4.2 Client Logo Management (`client_logos`)
- Tested `/api/logos` and PostgreSQL table `client_logos`.
- Inserted test logo: `Test Client Partner`, URL `/wp-content/uploads/partner-test.png`.
- Verified record persistence, visibility toggle (`is_visible = true`), and sorting order (`sort_order = 999`).
- Cleaned up test record.
- **Result:** **PASS**.

### 4.3 Team Member Management (`team_members`)
- Tested `/api/team` and PostgreSQL table `team_members`.
- Created test member: `Dr. QA Specialist`, role `VP of Quality Assurance`.
- Verified record retrieval via `/api/team` and persistent row in database.
- Cleaned up test record.
- **Result:** **PASS**.

### 4.4 Global Company Information Synchronization
- Updated company contact metadata via `/api/settings`:
  - `company_phone`: `+44 20 7946 0999`
  - `company_address`: `71-75 Shelton Street, Covent Garden, London, WC2H 9JQ`
- Verified updated values propagated to global footer across all pages.
- Reverted to production baseline.
- **Result:** **PASS**.

### 4.5 Interactive Form Rendering
- Tested `/survey/`, `/contact-sales/`, and `/contact-us/`.
- Verified forms render with active input fields, labels, submit buttons, and `form-bridge.js` validation handlers.
- **Result:** **PASS**.

---

## 5. Visual Parity & Fidelity Confirmations

### 5.1 Eyebrow & H1 Title Inversion Fix

**Problem Identified from User Screenshots:**
On role and industry pages (such as `/for-business-services/` and `/for-enterprise/`), the live production website renders:
- **Eyebrow (red subtitle):** "Problems We Solve for Business Services"
- **H1 Title (large bold text):** "Expert in your field, you. We Are, Too. Our Specialty Is Finding Your Next New Customer"

Previously on localhost, `cms-hydrate.js` fell back to generic selector indexing because inner page Elementor templates did not wrap titles inside `<span>` tags. As a result, the eyebrow text was being written to the `h1` and the title was being written to the subtitle.

**Remediation:**
1. Updated `cms-hydrate.js` heading hydration logic:
   - Targets `.elementskit-section-subtitle` explicitly as `d.eyebrow`.
   - Targets `.ekit-heading--title` explicitly as `d.title`.
   - Preserves semantic hierarchy regardless of whether internal child `span` elements exist.
2. Verified live rendering matches production verbatim across all role pages:
   - `/for-business-services/`
   - `/for-enterprise/`
   - `/for-customer-success/`
   - `/for-marketer/`
   - `/for-sales/`
   - `/for-technology/`
   - `/for-financial-services/`
   - `/for-manufacturing/`

### 5.2 Button Label & Destination Parity
- On `/for-enterprise/`, the hero CTA button previously displayed "EXPLORE DATA →". The PostgreSQL database and template were updated to live production copy: `"SEE SALES LEAD MACHINE IN ACTION →"`.
- Missing CTA buttons on `/for-business-services/`, `/for-customer-success/`, and `/for-sales/` were populated in `page_sections.data` with text `"SEE SALES LEAD MACHINE IN ACTION ⮞"` and target `/contact-sales/`, achieving 100% parity with live production.

### 5.3 Confirmation of Step 3 (Padding) & Step 4 (Section Height Verification)

Accurate measurement using Playwright at identical desktop viewport (1280x800) between `https://salesleadmachine.co.uk/` (Live Production) and `http://localhost:8080/` (Local):

| Section ID | Section Description | Production Height | Localhost Height | Height Delta (ΔH) | Production Padding | Localhost Padding | Image Dimensions | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `0b9f330` | Build Pipeline Split Section | **1146.0 px** | **1146.0 px** | **0.0 px** | Top: 70px, Bottom: 56px | Top: 70px, Bottom: 56px | 403 × 202 px | **EXACT MATCH** |
| `184c9a6` | Enrich Database Split Section | **928.0 px** | **928.0 px** | **0.0 px** | Top: 80px, Bottom: 80px | Top: 80px, Bottom: 80px | 403 × 202 px | **EXACT MATCH** |
| `b5a6373` | Boost Marketing Split Section | **784.0 px** | **784.0 px** | **0.0 px** | Top: 80px, Bottom: 56px | Top: 80px, Bottom: 56px | 579 × 427 px | **EXACT MATCH** |

*Historical height discrepancies (-48px, -106px, and -64px) have been completely eliminated. Bottom padding, image aspect ratios, and flex alignment match production 1:1.*

---

## 6. Generated Evidence & Artifacts

All test runs produced persisted CSV evidence, before/after screenshot comparisons, and regression scripts:

1. **`STEP_6B_FIELD_LEVEL_RESULTS.csv`**: Full 14-record matrix detailing all 7 section types, input selectors, and 10-step lifecycle pass states.
2. **`STEP_6B_PAGE_ISOLATION_RESULTS.csv`**: 4-scenario audit matrix verifying section, page, publish scope isolation, and save idempotency.
3. **`tests/TEST_EVIDENCE/step6b_ui/`**: 28 full-viewport screenshots capturing both draft preview states (`draft_*.png`) and live published states (`published_*.png`).
4. **`STEP_6B_SECURITY_REPORT.md`**: Dedicated audit report detailing credential removal, bcrypt rotation, JWT invalidation, git history rewrite, and repository secret scanning.
5. **`tests/step6b_full_cms_ui_regression.py`**: Automated regression test script executable in CI/CD pipelines.

---

## 7. Conclusion

The Sales Lead Machine web application and Visual CMS have undergone an exhaustive, multi-layered quality assurance audit. Every section type, editor control, isolation constraint, and security protocol has been verified with zero assumptions. The local application faithfully reproduces live production styling and layout fidelity.

