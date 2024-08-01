# Project Rewrite
This branch is for the project rewrite which is integrating various Flask extensions to produce better structured code. The rewrite will bring the application to v0.3. 

To-do, in order of importance:
- [ ] Database - SQLAlchemy
    - Base functionality for defining models and inserting data is complete
- [ ] Frontend - Bootstrap
    - May not end up sticking with this; will see.
- [ ] Frontend - Paginate
- [ ] Debugging - DebugToolbar
- [ ] Frontend - WTForms
  - [ ] Backend - Caching 
- [ ] Database - SQLAlchemy-Searchable (probably not needed)

# Overview

This is a simple Python application intended to track music releases you listen to. Think of it like Last.fm-lite, with all tracking being manual. Databass is more like a music diary than a tracker like Last.fm. A more apt comparison would be Letterboxd for music.

A few years ago, I decided I wanted to start exploring more music I'd never heard before. I started going through the book "1001 Albums to Listen to Before You Die" and wanted to keep some record of where I was in the list, and how I felt about each release. 

For a while, I did this through Obsidian, and used a handful of plugins to set up a workflow where I could quickly add a new release and have some basic querying of the stored data. However, everything was manual. I thought about integrating an API into an Obsidian plugin, but instead I decided I wanted to create a standalone webapp that I can update easily from anywhere. Thus, Databass was born. 

# Usage
Download the `docker-compose.yml` file: `wget https://raw.githubusercontent.com/chunned/databass/main/docker-compose.yml`

Add your Discogs API key and secret. Obtain them [here](https://www.discogs.com/settings/developers).

Choose a port to use on line 7.

Choose a location to store the database on line 12. If you get the error `not a directory: unknown: Are you trying to mount a directory onto a file (or vice-versa)? Check if the specified host path exists and is the expected type ` when running the Docker compose file, you need to do `touch music.db` to create the database file first (otherwise, Docker tries to mount it as a directory, rather than a file). 

Then, run `docker compose up -d` and visit the application at `localhost:<port>`

---

![](/static/screen.png)
