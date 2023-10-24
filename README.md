---
title: Elite Data Harvest
version: 3
comments: Aggressively simplified from V2
---

# Issues

- [ ] there are 510 empty items in "statements" table

# Run

- Execute the `run` bash script, passing the source you want to harvest from. E.g.:

```bash
run floor
```
^ you might have to make it executable with `chmod +x ./run`

# Setup

1. Install python3; you should then make a virtual env
2. Run `init` bash script (you might have to make it executable with `chmod +x ./init`)
3. Route secrets to the `harvest.py` script
    - if you want this to work for you, you'll have to provide database credentials (or just use sqlite) and API keys
    - for the `tv` data harvester, we use the `internetarchive` python module. this requires having an ia.ini file with credentials stored (on ubuntu) at `.config/internetarchive/ia.ini` (in the future we should probably find a way to pass that info like we do the other API keys)


# Dependencies

- python3
    - [external python modules](.python/requirements.txt)