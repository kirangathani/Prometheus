# Prometheus
Scrapes official US government websites to get information on trading activity by members of Congress. 

![image](https://github.com/user-attachments/assets/d7dc7d30-1c05-4852-84d4-e2be134fe886)


## WebScraping UX

From the user's perspective:

```text
 - Instance of HoR is intialised, with the year for which they want to scrape, and the people whose trading information we want to scrape.
 - Operation is carried out.
```

## Notes - things to fix

 - We need to make sure that the download dir creation does not overwrite an existing download_dir? Can we implement a check before making a new download_dir file?
 - We need to make sure that the programme knows to use the most recent .zip() file when we use pattern matching to find all of the files. We need the one with the highest (n).

# To do next time!!
**We have an issue with the downloading of the files - next time you work on this focus on (1) downloading the files through a clickable link instead of a url navigation (which doesn't trigger chrome's download functionality), and (2) you need to set the download folder preferences through the experimental preferences of chrome instead of through the simple extension of the chrome options list which is done through terminal.**

