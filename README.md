# Overview

![](/static/screen.png)

---

This is a simple Flask app to manually track music releases you listen to. It's similar to RateYourMusic but has no community aspect.

There are a few things to note before you use it:
- Genre should be as generic as possible
- Use 'tags' like subgenres; i.e. `genre: rock` and `tags: alternative,soft` = soft rock, alternative rock
- Rating is percentage based
- Currently, the release year must be manually entered; this is due to there not being an easy way to distinguish between the original release date and things like reissues/remasters. 
- Album art is currently best-effort; an attempt will be made to grab it from CoverArtArchive and Discogs, but you have no control over what art is picked unless you edit the release after the fact


# Usage
Clone the repository, or just download the `docker-compose.yml` and `.env.example` files: `wget https://raw.githubusercontent.com/chunned/databass/main/docker-compose.yml && wget https://raw.githubusercontent.com/chunned/databass/main/.env.example`

Rename `.env.example` to `.env` and fill out the required values. Unless you require a custom configuration, the only required values are the Discogs API key and secret.

Then, run `docker compose up -d` and visit the application at `localhost:<port>`

