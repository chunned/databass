# Overview

#### [Screenshots](./screenshots)

Databass is a music diary app. It's similar to RateYourMusic but meant for one user only. Data about releases, artists, and labels is retrieved mainly from MusicBrainz, but also from Discogs. 

The intention for the app is to help you uncover your listening habits, and to that end there will eventually be more sophisticated statistics and charts. Currently, there are some basic statistics:
- Most frequent artist/label (by number of releases logged)
- Artists/labels with highest rating (simple average of all logged release ratings for that entity)
- Favourite label/artist
  - Uses [Bayesian average](https://en.wikipedia.org/wiki/Bayesian_average) to calculate a weighted average. This helps even out the ratings a bit so that the number of releases logged doesn't matter as much.
  - For instance, an artist with five releases each rated 80% has a higher Bayesian average than an artist with only two releases rated 80%

There are a few things to note before you use it:
- Rating is percentage based
- Album art is currently best-effort; an attempt will be made to grab it from CoverArtArchive and Discogs, but you have no control over what art is picked unless you edit the release after the fact

# Usage
Clone the repository, or just download the `docker-compose.yml` and `.env.example` files: `wget https://raw.githubusercontent.com/chunned/databass/main/docker-compose.yml && wget https://raw.githubusercontent.com/chunned/databass/main/.env.example`

Rename `.env.example` to `.env` and fill out the required values. Unless you require a custom configuration, the only required values are the Discogs API key and secret.

Then, run `docker compose up -d` and visit the application at `localhost:<port>`

## Getting Discogs API Key


# Backup and restore
Backup:
```shell
# Note: change '-U postgres' if you change your databass user
sudo docker exec -it databass-postgres-1 pg_dump -U postgres databass > ./backup.sql
```
Restore:
```shell
sudo docker cp ./backup.yml databass-postgres-1:/backup.sql
sudo docker exec -it databass-postgres-1 /bin/sh 
psql databass < backup.sql
```