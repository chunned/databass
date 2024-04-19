import sqlite3
import datetime


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
    query = ("INSERT INTO artist (mbid, name) VALUES"
             "(:mbid, :name)")
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
    query = ("INSERT INTO label (mbid, name) VALUES"
             "(:mbid, :name)")
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
    stats["total_runtime"] = runtime / 60000

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
