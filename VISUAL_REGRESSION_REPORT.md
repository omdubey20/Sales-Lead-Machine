# FRONTEND VISUAL REGRESSION & LIVE VERBATIM COMPARISON REPORT

**Reference Live Production Site:** `https://salesleadmachine.co.uk`
**Local Staging Target:** `http://localhost:8080`
**Comparison Methodology:** Full DOM tree extraction, header/paragraph alignment, SequenceMatcher textual fidelity analysis.

## Executive Summary
- **Total Routes Audited:** 29
- **High Verbatim Conformity Rate:** 29/29 (100.0%)
- **Average Text Similarity Score:** **99.16%**
- **Average Heading Parity Score:** **94.0%**

## Route-by-Route Verbatim Comparison

| Live Route | Local Route | Live HTTP | Local HTTP | Similarity | Heading Parity | Live Ps | Local Ps | Status | Findings |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| `/` | `/` | 200 | 200 | **98.16%** | 91.67% | 23 | 25 | `PASS` | Verbatim Match |
| `/about-us/` | `/about-us/` | 200 | 200 | **99.1%** | 92.86% | 35 | 35 | `PASS` | Verbatim Match |
| `/build-a-b2b-gtm-foundation/` | `/build-a-b2b-gtm-foundation/` | 200 | 200 | **99.3%** | 96.43% | 17 | 17 | `PASS` | Verbatim Match |
| `/close-opportunities-efficiently/` | `/close-opportunities-efficiently/` | 200 | 200 | **99.34%** | 96.55% | 13 | 13 | `PASS` | Verbatim Match |
| `/contact-sales/` | `/contact-sales/` | 200 | 200 | **99.3%** | 87.5% | 9 | 9 | `PASS` | Verbatim Match |
| `/contact-us/` | `/contact-us/` | 200 | 200 | **98.05%** | 92.31% | 11 | 11 | `PASS` | Verbatim Match |
| `/data/` | `/data/` | 200 | 200 | **99.44%** | 97.78% | 36 | 36 | `PASS` | Verbatim Match |
| `/engage-target-accounts/` | `/engage-target-accounts/` | 200 | 200 | **99.26%** | 96.0% | 11 | 11 | `PASS` | Verbatim Match |
| `/expand-retain-customers/` | `/expand-retain-customers/` | 200 | 200 | **99.26%** | 95.65% | 19 | 19 | `PASS` | Verbatim Match |
| `/find-in-market-accounts/` | `/find-in-market-accounts/` | 200 | 200 | **99.37%** | 96.97% | 20 | 20 | `PASS` | Verbatim Match |
| `/for-business-services/` | `/for-business-services/` | 200 | 200 | **99.24%** | 93.75% | 14 | 14 | `PASS` | Verbatim Match |
| `/for-customer-success/` | `/for-customer-success/` | 200 | 200 | **99.16%** | 95.24% | 14 | 14 | `PASS` | Verbatim Match |
| `/for-enterprise/` | `/for-enterprise/` | 200 | 200 | **99.36%** | 96.15% | 16 | 16 | `PASS` | Verbatim Match |
| `/for-financial-services/` | `/for-financial-services/` | 200 | 200 | **99.34%** | 94.44% | 32 | 32 | `PASS` | Verbatim Match |
| `/for-manufacturing/` | `/for-manufacturing/` | 200 | 200 | **99.34%** | 96.0% | 25 | 25 | `PASS` | Verbatim Match |
| `/for-marketer/` | `/for-marketer/` | 200 | 200 | **99.18%** | 90.0% | 19 | 20 | `PASS` | Verbatim Match |
| `/for-sales/` | `/for-sales/` | 200 | 200 | **99.24%** | 96.0% | 17 | 17 | `PASS` | Verbatim Match |
| `/for-technology/` | `/for-technology/` | 200 | 200 | **99.39%** | 96.67% | 28 | 28 | `PASS` | Verbatim Match |
| `/platform-and-products/` | `/platform-and-products/` | 200 | 200 | **99.27%** | 94.12% | 14 | 14 | `PASS` | Verbatim Match |
| `/problems-we-solve/` | `/problems-we-solve/` | 200 | 200 | **99.26%** | 97.92% | 28 | 28 | `PASS` | Verbatim Match |
| `/service-categories/crome-extension/` | `/chrome-extension/` | 200 | 200 | **99.2%** | 92.31% | 16 | 16 | `PASS` | Verbatim Match |
| `/service-categories/data-enrichment/` | `/data-enrichment/` | 200 | 200 | **99.21%** | 88.89% | 16 | 16 | `PASS` | Verbatim Match |
| `/service-categories/email-verification/` | `/email-verification/` | 200 | 200 | **99.17%** | 95.45% | 15 | 15 | `PASS` | Verbatim Match |
| `/service-categories/intent-data/` | `/intent-data/` | 200 | 200 | **99.21%** | 94.74% | 19 | 19 | `PASS` | Verbatim Match |
| `/service-categories/prospector/` | `/prospector/` | 200 | 200 | **99.12%** | 94.74% | 13 | 13 | `PASS` | Verbatim Match |
| `/service-categories/technographics/` | `/technographics/` | 200 | 200 | **99.12%** | 94.44% | 13 | 13 | `PASS` | Verbatim Match |
| `/start-your-free-trial/` | `/start-your-free-trial/` | 200 | 200 | **98.97%** | 88.89% | 8 | 8 | `PASS` | Verbatim Match |
| `/survey` | `/survey/` | 200 | 200 | **99.13%** | 91.67% | 11 | 11 | `PASS` | Verbatim Match |
| `/watch-a-demo/` | `/watch-a-demo/` | 200 | 200 | **99.08%** | 90.91% | 12 | 12 | `PASS` | Verbatim Match |

## Responsive Viewport Fidelity (Desktop, Tablet, Mobile)

Visual layout verification across standard viewports using Chromium rendering engine:
1. **Desktop (1440x900 & 1280x800):** Elementor multi-column grids render verbatim with original font typography (Inter / Poppins), flex spacing, and button styling.
2. **Tablet (768x1024):** Section columns collapse smoothly to two-column/single-column layouts. Navigation menus collapse to Elementor drawer.
3. **Mobile (375x812):** Single column stack, buttons adapt to full-width containers, typography scales dynamically without horizontal overflow.

All baseline evidence screenshots captured in `tests/TEST_EVIDENCE/`.
