# Overview

This is a simple Flask app to manually track music releases you listen to. It's similar to RateYourMusic but has no community aspect.

There are a few things to note before you use it:
- Genre should be as generic as possible
- Use 'tags' like subgenres; i.e. `genre: rock` and `tags: alternative,soft` = soft rock, alternative rock
- Rating is percentage based
- Currently, the release year must be manually entered; this is due to there not being an easy way to distinguish between the original release date and things like reissues/remasters. 
- Album art is currently best-effort; an attempt will be made to grab it from CoverArtArchive and Discogs, but you have no control over what art is picked unless you edit the release after the fact


# Usage
Download the `docker-compose.yml` file: `wget https://raw.githubusercontent.com/chunned/databass/main/docker-compose.yml`

Choose a port to use on line 7.

In the `environment` section:
- Add your Discogs API key and secret. Obtain them [here](https://www.discogs.com/settings/developers).
- Set `DB_FILENAME` to whichever filename you wish to use and `TIMEZONE` to your desired timezone.

In the `volumes` section:
- Optionally, choose a location to store the database outside the docker container. Change `DB_FILENAME` to the value you set in the `environment` section. If you get the error `not a directory: unknown: Are you trying to mount a directory onto a file (or vice-versa)? Check if the specified host path exists and is the expected type ` when running the Docker compose file, you need to do `touch music.db` to create the database file first (otherwise, Docker tries to mount it as a directory, rather than a file). 

Then, run `docker compose up -d` and visit the application at `localhost:<port>`

---

![](/static/screen.png)
