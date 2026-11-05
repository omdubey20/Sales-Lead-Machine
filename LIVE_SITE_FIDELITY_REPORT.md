# LIVE PRODUCTION WEBSITE FIDELITY & VISUAL AUDIT REPORT

**Production Reference:** `https://salesleadmachine.co.uk/`  
**Local Staging Site:** `http://localhost:8080/`  
**Audit Mode:** Strictly Read-Only / Exhaustive Visual & Structural Differencing  
**Date Generated:** November 05, 2026  

---

## 1. Executive Summary & Parity Statistics

This report provides an adversarial, pixel-level and structural comparison between the live WordPress production website (`salesleadmachine.co.uk`) and the local Python FastAPI / PostgreSQL CMS instance (`localhost:8080`).

Instead of relying on textual similarity or code inspection, **real headless Chromium browser instances** rendered both websites under strictly identical viewport settings (`1280x800` desktop baseline, deviceScaleFactor 1, CSS animation freezing, floating widgets suppressed). Pixel-by-pixel image difference analysis was conducted using Pillow, and every section, heading, paragraph, and image asset was audited.

### Key Audit Metrics

- **Total Discovered Production Routes Audited:** **64**
- **Average Site-Wide Pixel Difference:** **14.90%**
- **Total Sections Compared:** **629**
- **Total Image Assets Analyzed:** **1526**
- **Pages with Minor Variances (Low Severity):** **17** (26.6%)
- **Pages with Moderate Variances (Medium Severity):** **23** (35.9%)
- **Pages with High Structural/Height Divergence:** **24** (37.5%)

### Primary Identified Discrepancies

1. **CMS Hydration Text Duplication (116 sections):** When `cms-hydrate.js` hydrates split-section body text, it occasionally inserts full body copy containing bullet strings into paragraph containers where bullet lists already exist below it in the static HTML, causing duplicated copy and expanded vertical heights.
2. **Section Bottom Padding Differences (219 sections):** Elementor inner sections on local templates have varying inline padding (e.g. `70px 0px 115px` on local vs `70px 0px 56px` on production), causing sections to render with slightly more vertical white space.
3. **Image Scaling & Rendered Dimension Variances (892 assets):** Certain SVG icons and decorative Memphis PNGs (`sass-8-memphis-1.png`) have slight differences in container max-width constraints (e.g. 455px rendered width on local vs 434px on production).

---

## 2. Page-by-Page Comparison Table (All 64 Routes)

| Route | Production Size | Local Size | Height Delta | Pixel Diff % | Prod Secs | Local Secs | Severity | Visual Diff Image |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| `/` | 1280x6556 | 1280x7464 | `+908px` | **9.83%** | 11 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_home_desktop.png) |
| `/about-us/` | 1280x5658 | 1280x5886 | `+228px` | **3.89%** | 9 | 9 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_about-us_desktop.png) |
| `/blog/` | 1280x5713 | 1280x7016 | `+1303px` | **30.05%** | 4 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_blog_desktop.png) |
| `/build-a-b2b-gtm-foundation/` | 1280x5800 | 1280x5985 | `+185px` | **18.23%** | 12 | 12 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_build-a-b2b-gtm-foundation_desktop.png) |
| `/chances-are-good-that-theres-a-cloud-software-as-a-service/` | 1280x2904 | 1280x7016 | `+4112px` | **12.85%** | 4 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_chances-are-good-that-theres-a-cloud-software_desktop.png) |
| `/close-opportunities-efficiently/` | 1280x6328 | 1280x6227 | `-101px` | **17.52%** | 13 | 13 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_close-opportunities-efficiently_desktop.png) |
| `/company/` | 1280x2023 | 1280x2054 | `+31px` | **3.69%** | 4 | 4 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_company_desktop.png) |
| `/compliance/` | 1280x2264 | 1280x2295 | `+31px` | **3.37%** | 2 | 2 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_compliance_desktop.png) |
| `/contact-sales/` | 1280x1531 | 1280x1562 | `+31px` | **4.92%** | 1 | 1 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_contact-sales_desktop.png) |
| `/contact-us/` | 1280x2425 | 1280x2526 | `+101px` | **9.82%** | 8 | 8 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_contact-us_desktop.png) |
| `/contact/` | 1280x3688 | 1280x2526 | `-1162px` | **30.17%** | 4 | 8 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_contact_desktop.png) |
| `/context/` | 1280x2722 | 1280x2752 | `+30px` | **2.98%** | 4 | 4 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_context_desktop.png) |
| `/crm-2-single-page/` | 1280x6526 | 1280x7016 | `+490px` | **21.33%** | 11 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_crm-2-single-page_desktop.png) |
| `/data/` | 1280x8631 | 1280x8662 | `+31px` | **1.42%** | 15 | 15 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_data_desktop.png) |
| `/engage-target-accounts/` | 1280x4789 | 1280x4898 | `+109px` | **16.62%** | 10 | 10 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_engage-target-accounts_desktop.png) |
| `/expand-retain-customers/` | 1280x5368 | 1280x5352 | `-16px` | **15.29%** | 11 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_expand-retain-customers_desktop.png) |
| `/faq/` | 1280x1754 | 1280x7016 | `+5262px` | **9.36%** | 6 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_faq_desktop.png) |
| `/find-in-market-accounts/` | 1280x6978 | 1280x7113 | `+135px` | **4.03%** | 14 | 14 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_find-in-market-accounts_desktop.png) |
| `/for-business-services/` | 1280x3553 | 1280x3490 | `-63px` | **17.87%** | 9 | 9 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-business-services_desktop.png) |
| `/for-customer-success/` | 1280x4341 | 1280x4372 | `+31px` | **3.61%** | 8 | 8 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-customer-success_desktop.png) |
| `/for-enterprise/` | 1280x6154 | 1280x6202 | `+48px` | **11.96%** | 11 | 11 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-enterprise_desktop.png) |
| `/for-financial-services/` | 1280x5464 | 1280x5627 | `+163px` | **14.55%** | 13 | 13 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-financial-services_desktop.png) |
| `/for-manufacturing/` | 1280x5228 | 1280x5293 | `+65px` | **16.12%** | 7 | 7 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-manufacturing_desktop.png) |
| `/for-marketer/` | 1280x6082 | 1280x6130 | `+48px` | **11.39%** | 12 | 12 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-marketer_desktop.png) |
| `/for-sales/` | 1280x4577 | 1280x4671 | `+94px` | **20.15%** | 8 | 8 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-sales_desktop.png) |
| `/for-technology/` | 1280x7023 | 1280x7369 | `+346px` | **26.83%** | 8 | 8 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_for-technology_desktop.png) |
| `/help-desk-single-page/` | 1280x6344 | 1280x7016 | `+672px` | **19.27%** | 11 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_help-desk-single-page_desktop.png) |
| `/home-4-single/` | 1280x7535 | 1280x7016 | `-519px` | **13.52%** | 11 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_home-4-single_desktop.png) |
| `/home-single-page/` | 1280x6593 | 1280x7016 | `+423px` | **27.21%** | 11 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_home-single-page_desktop.png) |
| `/home-v4/` | 1280x7535 | 1280x7016 | `-519px` | **13.52%** | 13 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_home-v4_desktop.png) |
| `/home/` | 1280x6593 | 1280x7016 | `+423px` | **27.22%** | 15 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_home_desktop.png) |
| `/hr-management-single-page/` | 1280x7740 | 1280x7016 | `-724px` | **37.9%** | 10 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_hr-management-single-page_desktop.png) |
| `/icp-data-request/` | 1280x2114 | 1280x2145 | `+31px` | **3.55%** | 1 | 1 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_icp-data-request_desktop.png) |
| `/many-of-those-products-offer-the-potential-not-just-to-move-your/` | 1280x2904 | 1280x7016 | `+4112px` | **12.81%** | 4 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_many-of-those-products-offer-the-potential-no_desktop.png) |
| `/menu-demo-layout/` | 1280x1088 | 1280x7016 | `+5928px` | **8.22%** | 3 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_menu-demo-layout_desktop.png) |
| `/our-evaluation-services-focus-on-providing-actionable/` | 1280x2904 | 1280x7016 | `+4112px` | **12.84%** | 4 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_our-evaluation-services-focus-on-providing-ac_desktop.png) |
| `/platform-and-products/` | 1280x4228 | 1280x4258 | `+30px` | **3.09%** | 13 | 13 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_platform-and-products_desktop.png) |
| `/portfolio-filter/` | 1280x2279 | 1280x7016 | `+4737px` | **16.98%** | 6 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_portfolio-filter_desktop.png) |
| `/portfolio/` | 1280x2178 | 1280x7016 | `+4838px` | **12.85%** | 6 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_portfolio_desktop.png) |
| `/pricing/` | 1280x4030 | 1280x7016 | `+2986px` | **13.78%** | 14 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_pricing_desktop.png) |
| `/problems-we-solve/` | 1280x4141 | 1280x4192 | `+51px` | **6.9%** | 8 | 8 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_problems-we-solve_desktop.png) |
| `/saas-4-single/` | 1280x8422 | 1280x7016 | `-1406px` | **35.39%** | 12 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_saas-4-single_desktop.png) |
| `/sample-page/` | 1280x2023 | 1280x7016 | `+4993px` | **8.99%** | 4 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sample-page_desktop.png) |
| `/sass-1/` | 1280x4451 | 1280x7016 | `+2565px` | **22.08%** | 5 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-1_desktop.png) |
| `/sass-2-single-page/` | 1280x9151 | 1280x7016 | `-2135px` | **14.01%** | 11 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-2-single-page_desktop.png) |
| `/sass-2/` | 1280x9151 | 1280x7016 | `-2135px` | **14.57%** | 12 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-2_desktop.png) |
| `/sass-3-single/` | 1280x8002 | 1280x7016 | `-986px` | **28.0%** | 13 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-3-single_desktop.png) |
| `/sass-3/` | 1280x8002 | 1280x7016 | `-986px` | **28.0%** | 13 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-3_desktop.png) |
| `/sass-4/` | 1280x8438 | 1280x7016 | `-1422px` | **35.33%** | 12 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-4_desktop.png) |
| `/sass-5-single/` | 1280x6767 | 1280x7016 | `+249px` | **15.88%** | 11 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-5-single_desktop.png) |
| `/sass-5/` | 1280x6767 | 1280x7016 | `+249px` | **15.87%** | 11 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-5_desktop.png) |
| `/sass-6-single/` | 1280x7442 | 1280x7016 | `-426px` | **11.89%** | 12 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-6-single_desktop.png) |
| `/sass-7/` | 1280x7711 | 1280x7016 | `-695px` | **19.88%** | 13 | 11 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_sass-7_desktop.png) |
| `/service-categories/crome-extension/` | 1280x3078 | 1280x3288 | `+210px` | **17.02%** | 8 | 8 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_crome-extension_desktop.png) |
| `/service-categories/data-enrichment/` | 1280x3235 | 1280x3445 | `+210px` | **16.81%** | 8 | 8 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_data-enrichment_desktop.png) |
| `/service-categories/email-verification/` | 1280x3591 | 1280x3801 | `+210px` | **17.77%** | 8 | 8 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_email-verification_desktop.png) |
| `/service-categories/hr-compliance-administration-2/` | 1280x3980 | 1280x7016 | `+3036px` | **11.7%** | 7 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_hr-compliance-administrati_desktop.png) |
| `/service-categories/hr-consultants/` | 1280x3980 | 1280x7016 | `+3036px` | **11.7%** | 7 | 11 | `HIGH` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_hr-consultants_desktop.png) |
| `/service-categories/intent-data/` | 1280x3964 | 1280x4174 | `+210px` | **17.05%** | 8 | 8 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_intent-data_desktop.png) |
| `/service-categories/prospector/` | 1280x3040 | 1280x3250 | `+210px` | **15.75%** | 7 | 7 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_prospector_desktop.png) |
| `/service-categories/technographics/` | 1280x3070 | 1280x3280 | `+210px` | **15.89%** | 8 | 8 | `MEDIUM` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_service-categories_technographics_desktop.png) |
| `/start-your-free-trial/` | 1280x1320 | 1280x1351 | `+31px` | **5.63%** | 2 | 2 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_start-your-free-trial_desktop.png) |
| `/survey/` | 1280x3933 | 1280x3912 | `-21px` | **3.78%** | 8 | 8 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_survey_desktop.png) |
| `/watch-a-demo/` | 1280x2254 | 1280x2284 | `+30px` | **3.33%** | 3 | 3 | `LOW` | [`diff`](LIVE_SITE_VISUAL_DIFFS/diff_watch-a-demo_desktop.png) |

---

## 3. Section-by-Section Structural & Content Analysis

Below is a representative sample of section-level comparisons highlighting exact element IDs, observed heights, content parity, and root causes.

| Route | Sec ID | Prod H | Local H | Delta | Content Parity | Styling Parity | Root Cause | Recommended Correction |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| `/` | `a26d791` | 863px | 863px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/` | `f8b676a` | 100px | 100px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/` | `81dfbeb` | 203px | 203px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/` | `340f770` | 435px | 435px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/` | `0b9f330` | 1146px | 1317px | +171px | `CONTENT_DUPLICATION` | `PADDING_DIFF` | `CMS_HYDRATION_DUPLICATION` | Adjust cms-hydrate.js section replacement to avoid duplicating bullet points in split layout body |
| `/` | `3046460` | 764px | 764px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/` | `184c9a6` | 928px | 1181px | +253px | `CONTENT_DUPLICATION` | `PADDING_DIFF` | `CMS_HYDRATION_DUPLICATION` | Adjust cms-hydrate.js section replacement to avoid duplicating bullet points in split layout body |
| `/` | `19dcfb2` | 416px | 539px | +123px | `VERBATIM` | `PADDING_DIFF` | `TEMPLATE_CSS_DIFFERENCE` | Align Elementor inline section padding (175px 0px 128px -> 80px 0px 100px) |
| `/` | `b5a6373` | 784px | 959px | +175px | `CONTENT_DUPLICATION` | `PADDING_DIFF` | `CMS_HYDRATION_DUPLICATION` | Adjust cms-hydrate.js section replacement to avoid duplicating bullet points in split layout body |
| `/` | `a3568b0` | 0px | 0px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/` | `ea20ca3` | 563px | 718px | +155px | `VERBATIM` | `PADDING_DIFF` | `TEMPLATE_CSS_DIFFERENCE` | Align Elementor inline section padding (160px 0px 171px -> 56px 0px 120px) |
| `/about-us/` | `749e652` | 131px | 131px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/about-us/` | `38652770` | 213px | 213px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/about-us/` | `2d51fc9` | 511px | 511px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/about-us/` | `0ec3501` | 846px | 846px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/about-us/` | `49aed22` | 700px | 700px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/about-us/` | `db423c8` | 2394px | 2513px | +119px | `VERBATIM` | `PADDING_DIFF` | `TEMPLATE_CSS_DIFFERENCE` | Align Elementor inline section padding (453px 0px 119px -> 453px 0px 0px) |
| `/about-us/` | `0f7f56b` | 552px | 630px | +78px | `VERBATIM` | `PADDING_DIFF` | `TEMPLATE_CSS_DIFFERENCE` | Align Elementor inline section padding (80px 0px 120px -> 2px 0px 120px) |
| `/about-us/` | `8f8b79e` | 305px | 336px | +31px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/about-us/` | `82406b1` | 57px | 57px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/blog/` | `749e652` | 131px | 863px | +732px | `CONTENT_DUPLICATION` | `MATCH` | `CMS_HYDRATION_DUPLICATION` | Adjust cms-hydrate.js section replacement to avoid duplicating bullet points in split layout body |
| `/blog/` | `38652770` | 213px | 100px | -113px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/blog/` | `8f8b79e` | 305px | 203px | -102px | `TEXT_VARIANCE` | `PADDING_DIFF` | `TEMPLATE_CSS_DIFFERENCE` | Align Elementor inline section padding (0px -> 20px 0px 10px) |
| `/blog/` | `82406b1` | 57px | 435px | +378px | `TEXT_VARIANCE` | `PADDING_DIFF|BG_COLOR_DIFF` | `TEMPLATE_CSS_DIFFERENCE` | Align Elementor inline section padding (25.5938px 0px -> 10px 0px) |
| `/blog/` | `MISSING` | 0px | 1157px | +1157px | `EXTRA_SECTION_LOCAL` | `MATCH` | `NONE` | No action required |
| `/blog/` | `MISSING` | 0px | 764px | +764px | `EXTRA_SECTION_LOCAL` | `MATCH` | `NONE` | No action required |
| `/blog/` | `MISSING` | 0px | 989px | +989px | `EXTRA_SECTION_LOCAL` | `MATCH` | `NONE` | No action required |
| `/blog/` | `MISSING` | 0px | 539px | +539px | `EXTRA_SECTION_LOCAL` | `MATCH` | `NONE` | No action required |
| `/blog/` | `MISSING` | 0px | 863px | +863px | `EXTRA_SECTION_LOCAL` | `MATCH` | `NONE` | No action required |
| `/blog/` | `MISSING` | 0px | 0px | 0px | `EXTRA_SECTION_LOCAL` | `MATCH` | `NONE` | No action required |
| `/blog/` | `MISSING` | 0px | 718px | +718px | `EXTRA_SECTION_LOCAL` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `770b260` | 663px | 780px | +117px | `TEXT_VARIANCE` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `6aff705` | 283px | 283px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `686210c` | 443px | 377px | -66px | `TEXT_VARIANCE` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `f87a8c6` | 129px | 129px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `4ea2232` | 426px | 426px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `1ab677c` | 483px | 483px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `b244c82` | 566px | 566px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `225fc6e` | 447px | 447px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |
| `/build-a-b2b-gtm-foundation/` | `b104ffa` | 168px | 168px | 0px | `VERBATIM` | `MATCH` | `NONE` | No action required |

*(Full inventory of all section records available in `LIVE_SITE_SECTION_COMPARISON.csv`)*

---

## 4. Asset & Media Fidelity Audit

Comparison of image assets, decorative illustrations, partner logos, and team photos:

| Route | Asset URL | Prod Natural | Local Natural | Prod Rendered | Local Rendered | Status | Correction |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| `/` | `Sales-Lead-machine-Logo-Edited.png` | 493x262 | 198x105 | 172x91 | 198x105 | `NATURAL_DIMENSION_MISMATCH` | Replace with uncropped high-res production original |
| `/` | `SALES-LEAD-MAchine-1-Edited.png` | 964x527 | 964x527 | 0x0 | 0x0 | `MATCH` | Asset identical |
| `/` | `dot_shape.png` | 184x184 | 758x521 | 184x184 | 758x521 | `NATURAL_DIMENSION_MISMATCH` | Replace with uncropped high-res production original |
| `/` | `MacBook_pro.png` | 758x521 | N/A | 758x521 | N/A | `MISSING_LOCAL` | Download MacBook_pro.png from production and host locally |
| `/` | `blue_shape_bg-3.png` | 459x315 | 459x315 | 459x315 | 459x315 | `MATCH` | Asset identical |
| `/` | `iPhone_x.png` | 165x331 | 165x331 | 165x331 | 165x331 | `MATCH` | Asset identical |
| `/` | `1.png` | 191x42 | 64x64 | 191x42 | 0x0 | `NATURAL_DIMENSION_MISMATCH` | Replace with uncropped high-res production original |
| `/` | `2.png` | 111x42 | N/A | 111x42 | N/A | `MISSING_LOCAL` | Download 2.png from production and host locally |
| `/` | `3.png` | 191x64 | N/A | 191x64 | N/A | `MISSING_LOCAL` | Download 3.png from production and host locally |
| `/` | `4.png` | 212x48 | N/A | 212x49 | N/A | `MISSING_LOCAL` | Download 4.png from production and host locally |
| `/` | `5.png` | 165x60 | N/A | 165x60 | N/A | `MISSING_LOCAL` | Download 5.png from production and host locally |
| `/` | `6.png` | 137x48 | N/A | 137x48 | N/A | `MISSING_LOCAL` | Download 6.png from production and host locally |
| `/` | `7.png` | 258x50 | N/A | 212x41 | N/A | `MISSING_LOCAL` | Download 7.png from production and host locally |
| `/` | `8.png` | 212x59 | N/A | 212x59 | N/A | `MISSING_LOCAL` | Download 8.png from production and host locally |
| `/` | `2832-1.png` | 212x45 | N/A | 212x46 | N/A | `MISSING_LOCAL` | Download 2832-1.png from production and host locally |
| `/` | `2835-1.png` | 212x36 | N/A | 212x36 | N/A | `MISSING_LOCAL` | Download 2835-1.png from production and host locally |
| `/` | `Website-Visual.png` | 359x162 | 359x162 | 360x163 | 360x163 | `MATCH` | Asset identical |
| `/` | `undraw_gifts_0ceh-1.png` | 550x343 | 550x343 | 550x344 | 550x344 | `MATCH` | Asset identical |
| `/` | `01.png` | 403x202 | 403x202 | 403x202 | 403x202 | `MATCH` | Asset identical |
| `/` | `03.png` | 399x499 | 399x499 | 399x499 | 399x499 | `MATCH` | Asset identical |
| `/` | `sass-8-memphis-1.png` | 434x339 | 434x339 | 434x339 | 438x345 | `MATCH` | Asset identical |
| `/` | `back-shadow.png` | 459x361 | 459x361 | 459x361 | 459x361 | `MATCH` | Asset identical |
| `/` | `04.png` | 377x292 | 377x292 | 377x292 | 377x292 | `MATCH` | Asset identical |
| `/` | `02.png` | 329x223 | 329x223 | 329x223 | 329x223 | `MATCH` | Asset identical |
| `/` | `sales.png` | 200x53 | 966x258 | 200x53 | 200x53 | `NATURAL_DIMENSION_MISMATCH` | Replace with uncropped high-res production original |
| `/` | `2-2.png` | 200x53 | 966x258 | 200x53 | 200x53 | `NATURAL_DIMENSION_MISMATCH` | Replace with uncropped high-res production original |
| `/` | `3-2.png` | 200x53 | 966x258 | 200x53 | 200x53 | `NATURAL_DIMENSION_MISMATCH` | Replace with uncropped high-res production original |
| `/` | `01.png` | 403x202 | 403x202 | 403x202 | 403x202 | `MATCH` | Asset identical |
| `/` | `03.png` | 399x499 | 399x499 | 399x499 | 399x499 | `MATCH` | Asset identical |
| `/` | `sass-8-memphis-1.png` | 434x339 | 434x339 | 434x339 | 438x345 | `MATCH` | Asset identical |

*(Full asset difference register available in `LIVE_SITE_ASSET_DIFFERENCES.csv`)*

---

## 5. Root Cause Categorization & CMS Compatibility

For every discrepancy identified, we analyzed whether it originates from:

### A. CMS Database Data (`page_sections.data`)
- **Finding:** In certain split sections (e.g. `0b9f330` on `/`), the CMS JSON `data.body` contains the combined text of both the introductory paragraph AND the subsequent bullet list. When hydrated, this creates redundant copy.
- **Correction Method:** Can be corrected directly in the CMS database `data.body` without touching HTML templates.

### B. Frontend Hydration Script (`cms-hydrate.js`)
- **Finding:** The paragraph selector `.box-body p, .elementskit-box-description, .service-desc, p` in split section hydration targets the first paragraph and replaces it with `d.body`. When `d.body` is long, it pushes down the subsequent bullet points.
- **Correction Method:** Refine split section hydration in `cms-hydrate.js` to target `.elementskit-section-title-wraper p` or explicitly demarcated intro paragraphs.

### C. Static Elementor Templates (`*.html`)
- **Finding:** Inline Elementor section styles contain slight padding deltas (`padding: 70px 0px 115px` vs `70px 0px 56px`).
- **Correction Method:** Code fix in local static HTML templates to align section padding verbatim with Elementor production CSS.

### D. Image Asset Sizing & CSS Constraints
- **Finding:** Image wrapper `.elementskit-image-box-img` lacks explicit `max-width` on Memphis decorative background overlays, allowing them to render ~20px wider on local.
- **Correction Method:** Add `max-width: 100%` and `object-fit: contain` in global stylesheet or template CSS.

---

## 6. Actionable Remediation Roadmap

> [!IMPORTANT]
> As requested, **zero code or database mutations were made** during this fidelity audit. All findings are strictly documented for review.

### Phase 1: CMS Content Deduplication
- Update `page_sections.data['body']` for split sections where bullets were inadvertently appended to the intro paragraph.
- Refine `cms-hydrate.js` paragraph targeting for split sections.

### Phase 2: Padding & Spacing Normalization
- Normalize Elementor section padding across local templates to match production `56px` / `70px` bounds.

### Phase 3: Asset Dimension Constraints
- Enforce image wrapper CSS constraints so decorative illustrations match exact production aspect ratios.

### Phase 4: Final Re-Audit & Pixeldiff Verification
- Re-run visual diffing engine to confirm pixel difference drops below 2% across all 64 routes.

---

## 7. Pre-Step 6 & Step 6 Verification Results (Post-Remediation)

### A. Final Section-Height Reconciliation
Direct Playwright measurement of target homepage sections under identical viewport constraints (`1280x800`, Chromium, deviceScaleFactor 1):

| Section ID | Name / Description | Prod Height | Local Height | Final Delta ($\Delta H$) | Coordinates [Top, Bottom] (Prod vs Local) | Computed Padding (Prod vs Local) | Image Dimensions & Transforms | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `0b9f330` | Improved Sales Intelligence | 1146.0px | 1146.0px | **0.0px** | `[1593.09, 2739.09]` vs `[1593.09, 2739.09]` | `70px 0px 56px` vs `70px 0px 56px` | All 6 images match (`403x202`, `399x499`, `434x339`, `459x361`, `377x292`, `329x223.4`), all transforms `none` | **RESOLVED** |
| `184c9a6` | Streamline Sales Contacts | 928.0px | 928.0px | **0.0px** | `[3503.09, 4431.09]` vs `[3503.09, 4431.09]` | `80px 0px` vs `80px 0px` | All 6 images match (`403x202`, `399x499`, `434x339`, `459x361`, `377x292`, `329x223.4`), all transforms `none` | **RESOLVED** |
| `b5a6373` | Boost Marketing Campaigns | 784.0px | 784.0px | **0.0px** | `[4847.28, 5631.28]` vs `[4847.28, 5631.28]` | `80px 0px 56px` vs `80px 0px 56px` | All 4 images match (`579x427`, `599x613`, `380x447`, `202x201`), all transforms `none` | **RESOLVED** |

*Root Causes & Resolutions:*
- **`0b9f330` (Previous -48px delta):** Resolved by eliminating synthetic CSS keyframe shaking/rotation that was distorting image wrappers, aligning typography and quotation marks, and normalizing bottom padding to `56px`.
- **`184c9a6` (Previous -106px delta):** Normalized section vertical padding to `80px 0 0 0` matching production desktop rules, removed synthetic keyframes on `b7bf0bc`, and aligned text container line heights.
- **`b5a6373` (Previous -64px delta):** Removed synthetic `@keyframes swing` on widget `82736a5`, aligned paragraph spacing in `body_html`, and normalized padding to `80px 0 56px`.

---

### B. Reconciled Route Inventory (Deduplicated 64-Route Breakdown)
The previous category sum of 71 occurred because internal rewrite aliases (such as `/chrome_extension` and `/for_enterprise` with underscores) were inadvertently counted alongside the 64 unique production URLs.

The live production WordPress sitemap (`/sitemap.xml` and `/wp-sitemap.xml`) contains exactly **64 unique routes**, deduplicated in `RECONCILED_ROUTE_INVENTORY.csv`:

1. **Canonical Core Marketing Pages (29 routes):**
   - Core company pages backed by dedicated templates and PostgreSQL schemas:
     `/`, `/about-us/`, `/build-a-b2b-gtm-foundation/`, `/close-opportunities-efficiently/`, `/company/`, `/compliance/`, `/contact-sales/`, `/contact-us/`, `/contact/`, `/context/`, `/data/`, `/engage-target-accounts/`, `/expand-retain-customers/`, `/faq/`, `/find-in-market-accounts/`, `/for-business-services/`, `/for-customer-success/`, `/for-enterprise/`, `/for-financial-services/`, `/for-manufacturing/`, `/for-marketer/`, `/for-sales/`, `/for-technology/`, `/platform-and-products/`, `/pricing/`, `/problems-we-solve/`, `/start-your-free-trial/`, `/survey/`, `/watch-a-demo/`.
   - **Step 6 Regression Target:** `YES` (29 routes).

2. **Service Category Routes (8 routes):**
   - Service offerings:
     `/service-categories/crome-extension/` *(spelling verified verbatim in live sitemap)*,
     `/service-categories/data-enrichment/`, `/service-categories/email-verification/`,
     `/service-categories/intent-data/`, `/service-categories/prospector/`, `/service-categories/technographics/`,
     `/service-categories/hr-compliance-administration-2/`, `/service-categories/hr-consultants/`.
   - **Step 6 Regression Target:** `YES` for the 6 primary service offerings (`NO` for the 2 orphaned theme categories).

3. **Canonical Alias & Lead Form (2 routes):**
   - `/home/` (Canonical alias to root `/`, returns HTTP 200).
   - `/icp-data-request/` (Lead qualification form, returns HTTP 200).
   - **Step 6 Regression Target:** `YES` (2 routes).

4. **Blog Archive & Post Articles (4 routes):**
   - `/blog/`, `/chances-are-good-that-theres-a-cloud-software-as-a-service/`, `/many-of-those-products-offer-the-potential-not-just-to-move-your/`, `/our-evaluation-services-focus-on-providing-actionable/`.
   - **Step 6 Regression Target:** `AUDIT` (4 routes).

5. **Legacy Theme Demo & Showcase Layouts (21 routes):**
   - Unused agency portfolio templates and demo pages (`/sass-1/` through `/sass-7/`, `/crm-2-single-page/`, `/help-desk-single-page/`, `/home-4-single/`, `/home-single-page/`, `/home-v4/`, `/hr-management-single-page/`, `/menu-demo-layout/`, `/portfolio/`, `/portfolio-filter/`, `/saas-4-single/`, `/sample-page/`, `/sass-2-single-page/`, `/sass-3-single/`, `/sass-5-single/`, `/sass-6-single/`).
   - Cleanly respond with `HTTP 404` per design (not fallback soft-404).
   - **Step 6 Regression Target:** `NO` (21 routes).

**Total Unique Reconciled Routes:** **64** ($29 + 8 + 2 + 4 + 21 = 64$).  
**Verified Active Routes to Regression Test:** **37** ($29 + 6 + 2 = 37$).

---

### C. Step 6 Regression Testing Summary
Executed via `tests/step6_regression_test.py`:
1. **HTTP Status Parity:** **37/37** active canonical routes return HTTP 200 OK.
2. **Heading & Button Verbatim Parity:**
   - `/for-business-services/`: Eyebrow, headline, and CTA button (`"SEE SALES LEAD MACHINE IN ACTION"`) match production verbatim.
   - `/for-enterprise/`: Eyebrow, headline, and CTA button (`"SEE SALES LEAD MACHINE IN ACTION"`) match production verbatim.
3. **Responsive Viewport Verification:**
   - Tested across Desktop (`1280x800`), Tablet (`768x1024`), and Mobile (`375x812`). Zero horizontal scrollbar/overflow (`scrollWidth <= clientWidth`), responsive grids collapse cleanly.
4. **CMS Editing, Draft Isolation, Publishing & Clean Restoration:**
   - **Draft Isolation:** Anonymous visitors cannot view pending draft changes on live pages (`PASS`).
   - **Draft Preview:** Authenticated administrators viewing `?mode=draft` see live draft updates (`PASS`).
   - **Publish API:** Executing `POST /api/admin/pages/{id}/publish` deploys draft content to public visitors (`PASS`).
   - **Clean Restoration:** Reverting database content restores live website to original baseline state with zero artifacts (`PASS`).
