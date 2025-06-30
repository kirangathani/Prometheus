# Prometheus
Scrapes official US government websites to get information on trading activity by members of Congress. 

![image](https://github.com/user-attachments/assets/d7dc7d30-1c05-4852-84d4-e2be134fe886)


## WebScraping UX

From the user's perspective:

```text
 - Instance of HoR is intialised, with the year for which they want to scrape, and the people whose trading information we want to scrape.
 - Operation is carried out.
```

# To Do Now (20250630)
 - We have made the function responsible for downloading the zip files, and storing them in a folder.
 - We now need functionality responsible for extracting the HTML XML files from these zip files.
 - Then we need to put these in a separate folder.
Let's see how far we get with that for now! 

