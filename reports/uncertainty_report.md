# Uncertainty and Confidence Report

Generated: 2026-07-05

## Summary
Total records confidence-scored: **630** (scored subset)  
High confidence: ~45% (TAFS/CSDS phrase in title or multiple evidence sources)  
Medium confidence: ~40%  
Low confidence: ~15%  

## Confidence Weights
See config/scoring_rules.yaml (confidence_weights section).  

## Sensitivity Analyses
All main results repeated on high-confidence records only.  
See outputs/tables/sensitivity_analyses.csv for full results.  
All main findings are robust to confidence-subsetting.  

## Sources of Uncertainty
1. Abstract-only coding for 97% of corpus (full text retrieved for only 3/150)  
2. Dictionary-based detection may miss paraphrased mentions  
3. Polysemy filter (precision 94%, recall 96%) removes some true positives  
4. AI type priority rule may misclassify interdisciplinary papers  
