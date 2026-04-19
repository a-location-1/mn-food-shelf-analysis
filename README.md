# Minnesota Food Shelf Spatial Variation

## 1. Research Question

What are you investigating, and why does it matter?

In hunger prevention work and social policy analysis more broadly, attention is often directed to the differences between rural and urban service provision.

Food shelf usage has increased significantly in Minnesota since 2021; the total number of MN food shelf visits in 2025 — 9,026,843 visits — is the highest recorded.

<img src="https://github.com/a-location-1/mn-food-shelf-analysis/blob/main/images/hungerdatatotalvisits.png" alt='A plot showing total food shelf visits from 2019 to 2025 in Minnesota' width=60%>

Source: [The Food Group, 2025 Minnesota Food Shelf Visits Report](https://www.thefoodgroupmn.org/wp-content/uploads/2026/03/Food-Shelf-Visits-2025-Report-FINAL-31326.pdf).

In the context of this increase in demand, are urban and rural services scaling differently? This analysis investigates spatial variation in ... 


## 2. Hypothesis

State your null and alternative hypotheses clearly and succinctly.

## 3. Data Description

Describe your data source(s):

* Where it comes from (URL, API, dataset name)
* What each observation represents (unit of analysis)
* Number of observations and key variables
* Any filtering, cleaning, or transformation steps


### Data Provenance:

The data used for the analysis comes from two sources.

#### MN County Population Data (`bea_mn_2024.csv`)

The U.S. Department of Commerce's [Bureau of Economic Analysis (BEA)](https://www.bea.gov/) provides county-level population and personal income summary data. I used the most recent data available, [calendar year 2024](https://apps.bea.gov/itable/?ReqID=70&step=1&_gl=1*5wit58*_ga*MjEwNjIyNzY4LjE3NzY2MTQ4Nzc.*_ga_J4698JNNFT*czE3NzY2MTQ4NzckbzEkZzEkdDE3NzY2MTQ4ODkkajQ4JGwwJGgw#eyJhcHBpZCI6NzAsInN0ZXBzIjpbMSwyOSwyNSwzMSwyNiwyNywzMF0sImRhdGEiOltbIlRhYmxlSWQiLCIyMCJdLFsiTWFqb3JfQXJlYSIsIjQiXSxbIlN0YXRlIixbIjI3MDAwIl1dLFsiQXJlYSIsWyJYWCJdXSxbIlN0YXRpc3RpYyIsWyItMSJdXSxbIlVuaXRfb2ZfbWVhc3VyZSIsIkxldmVscyJdLFsiWWVhciIsWyIyMDI0Il1dLFsiWWVhckJlZ2luIiwiLTEiXSxbIlllYXJfRW5kIiwiLTEiXV19). ([The data are also accessible via FRED \[Federal Reserve Economic Data\].)](https://fred.stlouisfed.org/release/tables?eid=267451&rid=175). The data were last updated 5 Feb 2026. The population estimates are from the United States Census Bureau's midyear population estimates, and so vary slightly from [the Census' finalized 2024 and 2025 estimates](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-counties-total.html#v2025) (for example, the BEA population estimate for Aitkin County is 16,335; the Census estimate is 16,283 for 2024 and 16,252 for 2025).

#### MN County Food Shelf Data

Unlike the population and income data, the food shelf data isn't clearly labelled by time. Comparing different sources that have copied the data indicates the changes over time:
- The authors of the University of Minnesota's Health Foods, Healthy Lives Institute (HFHL) [Food Security Dashboard](https://hfhl.umn.edu/fooddashboard) state they compiled their list of food shelves from the Minnesota Department of Education's November 2021 Community Food Resource list ([Wayback Machine link](https://web.archive.org/web/20211111205019/https://education.mn.gov/Maps/CompSvcs/)). Their list has 391 food shelves.
- The current Minnesota Early Childhood Longitudinal Data System ([ECLDS](https://eclds.mn.gov/))'s [MN Family Resource Map](https://pub.education.mn.gov/mnfr/) lists 526 food shelves, but there's no indication of when the list was most recently updated. The Resource Map authors state they compiled their list of food shelves from Hunger Solutions, which partnered with The Food Group in March 2024. I estimate this list is from 2025.
- The Food Group's [Find Help Map](https://www.hungersolutions.org/find-help/) lists 554 food shelves as of 19 Apr 2026. The data are collected by The Food Group in partnership with the Minnesota Department of Children, Youth, and Family (DCYF). The 2025 report doesn't list the total number of food shelves, but the [2024 report](https://www.thefoodgroupmn.org/wp-content/uploads/2026/03/Food-Shelf-Visits-2024-Report_31126.pdf) states MN has "487 food shelves, mobile, and tribal programs that participate in TEFAP".

In the interest of using the most complete list available, I ran a python script, `scrape_food_shelf_list.py`, to collect the name and address of every listed food shelf.

My plan is to use [the Census Geocoder](https://geocoding.geo.census.gov/geocoder/) to map each address to the correct Minnesota county.






## 4. Methods

Summarize how you analyzed the data:

* The test statistic for your permutation test
* How you simulated or resampled under the null hypothesis
* The metric(s) for which you created bootstrap confidence intervals
* Why the CLT does not apply to at least one metric

## 5. Results

Present your main findings:

* Key summary statistics and visualizations
* Observed test statistic and p-value (if applicable)
* Bootstrap confidence intervals for relevant metrics

## 6. Uncertainty Estimation

Discuss your resampling results:

* How many resamples you used
* What the bootstrap or randomization distributions looked like
* How you interpret the interval estimates

## 7. Limitations

Briefly note any limitations in data, assumptions, or methods, including sources of bias or missing data.

## 8. References

List all datasets, tools, libraries, or papers you cited.

---

**Reminder:** Your README should be clear enough that someone unfamiliar with your work could understand what you studied, how you analyzed it, and what you found.
