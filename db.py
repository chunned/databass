import sqlite3
import datetime
import api


def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)
    return connection


def create_cursor(connection):
    try:
        return connection.cursor()
    except Exception as e:
        print(e)
        return None


def create_tables(cur):
    # Create release table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS release(
    id INTEGER PRIMARY KEY,
    mbid TEXT UNIQUE,
    artist_id INTEGER,
    label_id INTEGER,
    title TEXT,
    release_date TEXT,
    runtime INTEGER,
    rating INTEGER,
    listen_date TEXT,
    track_count INTEGER,
    country TEXT,
    genre TEXT,
    art TEXT,
    FOREIGN KEY (artist_id) REFERENCES artist(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (label_id) REFERENCES label(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
    )
    """)

    # Create ARTIST table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS artist(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mbid TEXT UNIQUE,
        name TEXT
    )    
    """)

    # Create LABEL table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS label(
        id INTEGER PRIMARY KEY,
        mbid TEXT UNIQUE,
        name TEXT
    )    
    """)


def insert_release(cur, con, release):
    query = ("INSERT INTO release (mbid, artist_id, label_id, title, release_date, runtime, rating, listen_date, "
             "track_count, country, genre, art) VALUES (:mbid, :artist_id, :label_id, :title, :release_date, :runtime, "
             ":rating, :listen_date, :track_count, :country, :genre, :art)")
    try:
        cur.execute(query, release)
        con.commit()
        return True
    except sqlite3.IntegrityError as e:
        # print(f"ERROR: {e}")
        # print("Errored SQLite query:")
        # print(query)
        # print("release dictionary:")
        print(release)
        print("release already exists in database")
        return None


def insert_artist(cur, con, artist):
    query = ("INSERT INTO artist (mbid, name, country, type, begin_date, end_date, image) VALUES"
             "(:mbid, :name, :country, :type, :begin_date, :end_date, :image)")
    try:
        cur.execute(query, artist)
        con.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        print(artist)
        print("Artist already exists in database")
        query = "SELECT id FROM artist WHERE mbid = ?"
        cur.execute(query, (artist['mbid'],))
        con.commit()
        return cur.fetchone()[0]


def insert_label(cur, con, label):
    query = ("INSERT INTO label (mbid, name, country, type, begin_date, end_date, image) VALUES"
             "(:mbid, :name, :country, :type, :begin_date, :end_date, :image)")
    try:
        cur.execute(query, label)
        con.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        print(label)
        print("Label already exists in database")
        query = "SELECT id FROM label WHERE mbid = ?"
        cur.execute(query, (label['mbid'],))
        con.commit()
        return cur.fetchone()[0]


def get_stats(cur, con):
    stats = {}

    cur.execute("SELECT COUNT(*) FROM release")
    stats["total_listens"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM artist")
    stats["total_artists"] = cur.fetchone()[0]

    cur.execute("SELECT AVG(rating) FROM release")
    stats["average_rating"] = cur.fetchone()[0]

    cur.execute("SELECT AVG(runtime) FROM release")
    stats["average_runtime"] = cur.fetchone()[0]

    cur.execute("SELECT SUM(runtime) FROM release")
    runtime = cur.fetchone()[0]
    if runtime > 0:
        stats["total_runtime"] = runtime / 60000
    else:
        stats["total_runtime"] = 0

    year = str(datetime.datetime.now().year)
    cur.execute("SELECT COUNT(*) FROM release WHERE SUBSTR(listen_date, 1, 4) = ?",
                (year,))
    stats["this_year"] = cur.fetchone()[0]

    days_this_year = datetime.date.today().timetuple().tm_yday
    try:
        stats["per_day"] = stats["this_year"] / days_this_year
    except ZeroDivisionError:
        stats["per_day"] = 0

    return stats


def update_existing_release(cur, con, release):
    cur.execute("UPDATE release SET mbid = ?, artist_id = ?, label_id = ?, title = ?, release_date = ?,"
                "runtime = ?, rating = ?, listen_date = ?, track_count = ?, country = ?, genre = ?, art = ?"
                "WHERE id = ?",
                (release["mbid"], release["artist_id"], release["label_id"], release["title"],
                 release["release_date"], release["runtime"], release["rating"], release["listen_date"],
                 release["track_count"], release["country"], release["genre"], release["art"], release["id"]))
    con.commit()
    print(f"UPDATED {release["title"]}")


def get_missing_covers(cur, con):
    cur.execute("SELECT * FROM release WHERE art IS NULL")
    data = cur.fetchall()

    for release in data:
        release = list(release)
        #print(release)
        mbid = release[1]

        if mbid:
            art = api.get_cover_art(mbid)
        else:
            art = 'https://static.vecteezy.com/system/resources/thumbnails/005/720/408/small_2x/crossed-image-icon-picture-not-available-delete-picture-symbol-free-vector.jpg'

        release[-1] = art
        release_dict = {"id": release[0], "mbid": release[1], "artist_id": release[2], "label_id": release[3],
                        "title": release[4], "release_date": release[5], "runtime": release[6],
                        "rating": release[7], "listen_date": release[8], "track_count": release[9],
                        "country": release[10], "genre": release[11], "art": release[12]}

        update_existing_release(cur, con, release_dict)


def get_missing_artist_data(cur, con):
    cur.execute("SELECT * FROM artist")
    data = cur.fetchall()

    for artist_entry in data:
        for i, val in enumerate(artist_entry):
            if not val:
                new_data = api.get_artist_data(artist_entry[1])
                query = ("UPDATE artist SET mbid = ?, name = ?, country = ?, type = ?, begin_date = ?, end_date = ?, image = ?"
                         "WHERE artist.mbid = ?")
                cur.execute(query, (
                    new_data["mbid"], new_data["name"], new_data["country"], new_data["type"], new_data["begin_date"],
                    new_data["end_date"], new_data["image"], new_data["mbid"]
                    ))
                con.commit()
                print(f"UPDATED {new_data['name']}")
                break
    return 1


def get_missing_label_data(cur, con):
    cur.execute("SELECT * FROM  label")
    data = cur.fetchall()

    for label_entry in data:
        if label_entry[1] is None:
            pass
        else:
            for i, val in enumerate(label_entry):
                if not val:
                    new_data = api.get_label_data(label_entry[1])
                    query = ("UPDATE LABEL SET mbid = ?, name = ?, country = ?, type = ?, begin_date = ?, end_date = ?"
                             "WHERE mbid = ?")
                    cur.execute(query, (new_data["mbid"], new_data["name"], new_data["country"], new_data["type"],
                                        new_data["begin_date"], new_data["end_date"],
                                        new_data["mbid"]))
                    con.commit()
                    print(f"UPDATED {new_data['name']}")
                    break
    return 1
