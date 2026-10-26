# Code-to-class mapping rules (`class_map.csv`)

`class_map.csv` is produced by `scripts/06_product_classes.py` (copied here from `tables/i_code_to_class_map.csv`). It covers 10,404 HCPCS codes billed in any year 2019-2024. Columns: HCPCS_Cd, desc (latest CMS description), category, cls (class), stratum (skin, lab, other).

## Step 1. Category (scripts/02_concentration.py), applied in order
1. `####U` -> PLA lab (U).
2. `####M` or `8####` -> Other lab.
3. `Q4100-Q4399` (regex `Q4[1-3]\d\d`) or `A2###` -> Skin substitute product.
4. CMS drug indicator = Y -> Drug (Part B, physician-billed).
5. First character A, B, E, K, or L -> Supply/DME/other.
6. Otherwise -> Professional/procedural.

## Step 2. Class, first match wins
1. Skin substitute product -> one class, "Skin substitute products" (stratum skin).
2. Laboratory -> four lab families (stratum lab, analyzed separately): PLA (####U); multianalyte assays (####M); molecular pathology 811xx-816xx; other laboratory.
3. Nine named service families defined by explicit code lists (extended ambulatory ECG monitoring 93241-93248; mobile cardiac telemetry and event monitoring; remote physiologic monitoring; remote therapeutic monitoring; chronic and principal care management; skin-substitute application procedures 15271-15278; office/outpatient E/M visits; cardiac device remote interrogation; psychotherapy). Exact lists are in the script.
4. Drug classes: for codes in the Drug category or beginning with J, Q, A, or 9, the lower-cased CMS description is matched against molecule keywords for 19 listed classes in the listed order. One listed class (CAR-T cell therapies) matched no codes, so 18 drug classes are populated.
5. All other codes form their own single-code class.

Result: 32 named classes containing 2,064 codes; all remaining codes are single-code classes. Keyword matching depends on CMS description text and can misassign codes; it was not manually reviewed code by code.

## Class measures
- Class spending = sum of member-code allowed amounts. Growth and the $10 million threshold are applied to class totals.
- Pooled class HHI (prespecified class rule) = HHI of state shares of class spending.
- Class provider count = sum of member-code provider counts (upper bound).
- Spending-weighted member-code HHI (exploratory, defined after results were seen) = sum over member codes of (code share of class spending x code state HHI).
