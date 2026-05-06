# Minnesota Food Shelf Spatial Variation

<!-- **Reminder:** Your README should be clear enough that someone unfamiliar with your work could understand what you studied, how you analyzed it, and what you found. 

Links to the jupyter notebooks are added where appropriate. -->

## 1. Research Question

<!-- What are you investigating, and why does it matter? -->

Hunger prevention advocates often direct attention to differences between rural and urban food insecurity.[^1]

Food shelf usage has increased significantly in Minnesota since 2021; the total number of MN food shelf visits in 2025 — 9,026,843 visits — is the highest recorded.

<img src="https://github.com/a-location-1/mn-food-shelf-analysis/blob/main/images/hungerdatatotalvisits.png" alt='A plot showing total food shelf visits from 2019 to 2025 in Minnesota' width=60%>

Source: [The Food Group, 2025 Minnesota Food Shelf Visits Report](https://www.thefoodgroupmn.org/wp-content/uploads/2026/03/Food-Shelf-Visits-2025-Report-FINAL-31326.pdf).

In the context of this increase in demand, are urban and rural services scaling differently? This analysis investigates spatial variation in ... 


## 2. Hypothesis

<!-- State your null and alternative hypotheses clearly and succinctly. -->

Null Hypothesis: A county's "metropolitanism" (its inclusion or exclusion from the Minneapolis-Saint Paul metropolitan area) has no effect on its number of food shelves per capita.

Alternative Hypothesis: Non-metropolitan MN counties have fewer food shelves per capita than metropolitan counties.


## 3. Data Description

<!-- Describe your data source(s):

* Where it comes from (URL, API, dataset name)
* What each observation represents (unit of analysis)
* Number of observations and key variables
* Any filtering, cleaning, or transformation steps -->

### Data Provenance:

The data used for the analysis comes from two sources.

#### MN County Population Data (`bea_mn_2024.csv`)

The U.S. Department of Commerce's [Bureau of Economic Analysis (BEA)](https://www.bea.gov/) provides county-level population and personal income summary data. I used the most recent data available, [calendar year 2024](https://apps.bea.gov/itable/?ReqID=70&step=1&_gl=1*5wit58*_ga*MjEwNjIyNzY4LjE3NzY2MTQ4Nzc.*_ga_J4698JNNFT*czE3NzY2MTQ4NzckbzEkZzEkdDE3NzY2MTQ4ODkkajQ4JGwwJGgw#eyJhcHBpZCI6NzAsInN0ZXBzIjpbMSwyOSwyNSwzMSwyNiwyNywzMF0sImRhdGEiOltbIlRhYmxlSWQiLCIyMCJdLFsiTWFqb3JfQXJlYSIsIjQiXSxbIlN0YXRlIixbIjI3MDAwIl1dLFsiQXJlYSIsWyJYWCJdXSxbIlN0YXRpc3RpYyIsWyItMSJdXSxbIlVuaXRfb2ZfbWVhc3VyZSIsIkxldmVscyJdLFsiWWVhciIsWyIyMDI0Il1dLFsiWWVhckJlZ2luIiwiLTEiXSxbIlllYXJfRW5kIiwiLTEiXV19). [(The data are also accessible via FRED \[Federal Reserve Economic Data\].)](https://fred.stlouisfed.org/release/tables?eid=267451&rid=175) The data were last updated 5 Feb 2026. The population estimates are from the United States Census Bureau's midyear population estimates, and so vary slightly from [the Census' finalized 2024 and 2025 estimates](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-counties-total.html#v2025) (for example, the BEA population estimate for Aitkin County is 16,335; the Census estimate is 16,283 for 2024 and 16,252 for 2025).

#### MN County Food Shelf Data (`food_shelves_scrapedgeocoded_2026.pkl`)

Several sources provide lists of food shelves in Minnesota, but the lists are inconsistent and not labelled by time. Comparing these sources indicates changes over time:
- The authors of the University of Minnesota's Health Foods, Healthy Lives Institute (HFHL) [Food Security Dashboard](https://hfhl.umn.edu/fooddashboard) state they compiled their list of food shelves from the Minnesota Department of Education's November 2021 Community Food Resource list ([Wayback Machine link](https://web.archive.org/web/20211111205019/https://education.mn.gov/Maps/CompSvcs/)). Their list has **391 food shelves**.
- The Food Group's [2024 Food Shelf Visits report](https://www.thefoodgroupmn.org/wp-content/uploads/2026/03/Food-Shelf-Visits-2024-Report_31126.pdf) states MN has "**487 food shelves**, mobile, and tribal programs that participate in TEFAP \[The Emergency Food Assistance Program\]". A list is not provided. 
- The Minnesota Early Childhood Longitudinal Data System ([ECLDS](https://eclds.mn.gov/))'s [MN Family Resource Map](https://pub.education.mn.gov/mnfr/) currently lists **482 food shelves** (and 44 food distribution services), but there's no indication of when the list was most recently updated. The Resource Map authors state they compiled their list of food shelves from Hunger Solutions, which partnered with The Food Group in March 2024. I estimate this list is from 2024 or 2025.
- The Food Group's [Find Help Map](https://www.hungersolutions.org/find-help/) lists **552 food shelves** as of early May 2026, down from 554 in mid-April 2026 (however this does include 14 non-Minnesota food shelves). The data are collected by The Food Group in partnership with the Minnesota Department of Children, Youth, and Family (DCYF).

Additional comparison between these sources is available in `food_shelf_reconciliation.ipynb`.

The project uses a final list of **537 Minnesota food shelves**, scraped 04/30/26.

...

### Data Overview

...

Its a census of food shelves, but its a sample of relief programs. More broadly, we foolishly hope to use the food shelf number as a measure of hunger help.

## 4. Methods

<!-- Summarize how you analyzed the data:

* The test statistic for your permutation test
* How you simulated or resampled under the null hypothesis
* The metric(s) for which you created bootstrap confidence intervals
* Why the CLT does not apply to at least one metric -->

## 5. Results

<!-- Present your main findings:

* Key summary statistics and visualizations
* Observed test statistic and p-value (if applicable)
* Bootstrap confidence intervals for relevant metrics -->

## 6. Uncertainty Estimation

<!-- Discuss your resampling results:

* How many resamples you used
* What the bootstrap or randomization distributions looked like
* How you interpret the interval estimates -->

## 7. Limitations

<!-- Briefly note any limitations in data, assumptions, or methods, including sources of bias or missing data. -->

NOTES ON GRANULARITY: 

It's important to note that this analysis does not analyze food shelf *access*. To analyze that, we'd want to measure walking or driving distance - or a proxy, such as miles from a nieghborhood to the nearest food shelf.

We'd also want to focus on community's with higher demand for food shelves. Unlike with grocery stores, we don't want every member of the population to have an equal ability to access a food shelf - we want to prioritize need/actual usage. E.X. poorer neighborhoods. 

Even more pertinent to this analysis: there's no reason to think that *food shelf demand* is equally distributed by location. 

Finally, food shelves are only one way food help is delivered. A lack of food shelves might be balanced out by other services that better meet a particular county's needs; without a broader accounting of which types of service provision are available, this analysis is incomplete.[^2]

NOTE ON FOOD SHELF SIZES: Food shelves are very different. [SuperShelf's 2025 Minnesota Food Shelf Survey](https://www.supershelfmn.org/minnesota-statewide-survey) found that 19% of their food shelf survey respondants serve 60 or fewer average households per month, and 28% of their respondants serve 476 or more households per month. Moreover, the increase in demand impacts larger food shelves *more* than smaller food shelves. In short, there are substantive differences between large operations and small operations, and this analysis treats each shelf as a singular entity with equal weight in the analysis. 

NOTE ON ARBIRARY BOUNDARIES: State boundaries are arbitrary when it comes to actual hunger prevention. This is most apparent for areas with services directly across the border, such as the Fargo-Moorhead metropolitan area and the Twin Ports (Duluth, MN and Superior, WI). On the other hand, Minnesota state boundaries are relevant because Minnesota is a self-contained administrative domain - MN local government can only make choices for MN. But the point still stands (e.x. an administrator siting a new food shelf would want to deprioritize a MN community already receiving survice from a nearby provider across state lines).

## 8. References

<!-- List all datasets, tools, libraries, or papers you cited. -->

[^1]: Citing the USDA report "Household Food Security in the United States in 2016," the Food Research & Action Center (FRAC) reports that 15% of rural areas faced food insecurity in 2016, compared to 11.8% of metropolitan areas ([Rural Hunger in America: Get the Facts](https://frac.org/wp-content/uploads/rural-hunger-in-america-get-the-facts.pdf)).

[^2]: With that said, some reports indicate food shelves are a significant piece of food insecurity prevention: [Second Harvest Heartland's 2025 "The State of Food Security in Minnesota"](https://www.wilder.org/wp-content/uploads/2025/08/SecondHarvestHeartland_Infographic_3-25.pdf) collaborated with Wilder Research for a survey that found that "a higher share of households (11% overall) reported accessing free food (such as from food pantries, food shelves, food banks, or grocery giveaways) than any other type of food aid, including SNAP (7% overall).

---