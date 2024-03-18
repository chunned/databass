from api import *
from db import *
import art
import datetime


def main():
    # Print banner
    art.tprint('DATABASS v0.1')

    # Print menu and get user choice
    print_menu = True
    while print_menu:
        user_choice = menu_choose()
        match user_choice:
            case "a":
                add_release()
            case "s":
                search_release()
            case "e":
                edit_release()
            case "r":
                remove_release()
            case "q":
                query_stats()
            case "exit":
                print_menu = False


def menu_choose():
    print('Menu')
    print('a - Add new release')
    print('s - Search an existing release')
    print('e - Edit an existing release')
    print('r - Remove an existing release')
    print('q - Query statistics')

    choice = None
    while not choice:
        try:
            choice = input('CHOICE (a, s, e, r, q, EXIT): ')
            if choice not in 'aserq' and choice.lower() != 'exit':
                raise ValueError
        except ValueError:
            print('ERROR: Invalid choice. Please choose one of: a, s, e, r, q, EXIT')
            choice = None
    return choice.lower()


def add_release():
    try:
        release_mbid, artist, label = pick_release()
        release = get_release_data(release_mbid, artist, label)
        # Insert data
        if label:
            label_id = insert_label(cur, con, label)
            release['label_id'] = label_id
        artist_id = insert_artist(cur, con, artist)
        release['artist_id'] = artist_id
        if label:
            pass
        else:
            release['label_id'] = 0

    except TypeError as e:
        print(f"ERROR: {e}")
        print("Release not found on MusicBrainz. Please enter data manually.")
        release, artist, label = manual_data()
    finally:
        insert_release(cur, con, release)


def query_stats():
    total_release_query = "SELECT COUNT(*) FROM release"
    cur.execute(total_release_query)
    total_release_count = cur.fetchone()[0]
    print(f'Releases: {total_release_count}')

    total_artist_query = "SELECT COUNT(*) FROM artist"
    cur.execute(total_artist_query)
    total_artist_count = cur.fetchone()[0]
    print(f'Artists: {total_artist_count}')

    avg_rating_query = "SELECT AVG(rating) FROM release"
    cur.execute(avg_rating_query)
    avg_rating = cur.fetchone()[0]
    print(f'Average rating: {avg_rating}')

    avg_runtime_query = "SELECT AVG(runtime) FROM release"
    cur.execute(avg_runtime_query)
    avg_runtime = cur.fetchone()[0] / 60000
    print(f'Average runtime: {avg_runtime}')

    total_runtime_query = "SELECT SUM(runtime) FROM release"
    cur.execute(total_runtime_query)
    total_runtime = cur.fetchone()[0] / 60000
    print(f'Total runtime: {total_runtime}')

    current_year_listens_query = "SELECT COUNT(*) FROM release WHERE SUBSTR(listen_date, 1, 4) = ?"
    cur.execute(current_year_listens_query, ('2024',))
    listens_this_year = cur.fetchone()[0]
    print(f'Listens in 2024: {listens_this_year}')

    today = datetime.date.today()
    days_this_year = today.timetuple().tm_yday
    try:
        listens_per_day = listens_this_year / days_this_year
    except ZeroDivisionError:
        listens_per_day = 0

    print(f'Listens per day in 2024: {listens_per_day}')

    label_query = "SELECT label.name, COUNT(*) as Count FROM label JOIN release ON release.label_id = label.id GROUP BY label.name ORDER BY Count DESC;"
    cur.execute(label_query)
    row = cur.fetchone()
    print(f'Most listened to Label: {row[0]} - Count: {row[1]}')

    print('---')
    print('Highest Rated Labels (only shows labels with >1 releases)')

    fav_label_query = """
    SELECT label.name, AVG(release.rating) AS Average_Rating, COUNT(release.label_id) as Release_Count 
FROM label  
JOIN release ON release.label_id = label.id
WHERE label.name IS NOT "none" AND label.name IS NOT "[no label]"
GROUP BY label.name
HAVING Release_Count != 1    
ORDER BY Average_Rating DESC
LIMIT 5;"""
    cur.execute(fav_label_query)
    rows = cur.fetchall()
    print("{:<30} {:<15} {:<15}".format('Label Name', 'Average Rating', 'Release Count'))
    for row in rows:
        label_name = row[0]
        avg_rating = row[1]
        release_count = row[2]
        print("{:<30} {:<15.2f} {:<15}".format(label_name, avg_rating, release_count))

    print('---')
    print('Highest rated artists with more than 1 release')

    fav_artist_query = """
    SELECT artist.name, AVG(release.rating) AS Average_Rating, COUNT(release.artist_id) as Release_Count 
FROM artist
JOIN release ON release.artist_id = artist.id
GROUP BY artist.name
HAVING Release_Count != 1    
ORDER BY Average_Rating DESC
LIMIT 5;"""
    cur.execute(fav_artist_query)
    rows = cur.fetchall()

    print("{:<30} {:<15} {:<15}".format('Artist Name', 'Average Rating', 'Release Count'))

    for row in rows:
        artist_name = row[0]
        avg_rating = row[1]
        release_count = row[2]
        print("{:<30} {:<15.2f} {:<15}".format(artist_name, avg_rating, release_count))

    print('---')
    print('Highest number of releases per artist')
    cur.execute("""
    SELECT artist.name, COUNT(release.artist_id) as Count
FROM artist
JOIN release ON release.artist_id = artist.id
WHERE artist.name != "Various Artists"
GROUP BY artist.id
ORDER BY Count DESC
LIMIT 5;""")
    rows = cur.fetchall()

    print("{:<30} {:<10}".format('Artist Name', 'Count'))

    for row in rows:
        artist_name = row[0]
        count = row[1]
        print("{:<30} {:<10}".format(artist_name, count))

    return None


def remove_release():
    release_mbid = pick_release()[0]
    # TODO: integrate below for cases when release was manually entered and has no MBID
    # release_title = input("Release title: ")
    # release_artist = input("Release artist: ")
    # cur.execute("SELECT * FROM artist WHERE name COLLATE NOCASE = ?", (release_artist,))
    # artist_id = cur.fetchone()[0]
    # print(artist_id)
    # cur.execute("SELECT * FROM release WHERE title COLLATE NOCASE = ? AND artist_id COLLATE NOCASE = ?", (release_title, artist_id))
    # q = cur.fetchone()
    # print(q)
    x = input("Type 'yes' to delete this release. This is an irreversible process. Anything else will exit: ")
    if x == 'yes':
        delete_query = "DELETE FROM release WHERE mbid = ?"
        cur.execute(delete_query, (release_mbid,))
        con.commit()

    return None


def manual_data():
    # TODO: Finish updating to current schema
    title = ""
    while len(title) < 1:
        try:
            title = input("TITLE: ")
            if len(title) < 1:
                raise ValueError
        except ValueError:
            print("Title cannot be 0 characters.")

    artist = ""
    while len(artist) < 1:
        try:
            artist = input("ARTIST: ")
            if len(artist) < 1:
                raise ValueError
        except ValueError:
            print("Artist cannot be 0 characters.")

    # Check if artist is already in database
    try:
        q = f"SELECT * FROM artist WHERE name COLLATE NOCASE = ?"
        cur.execute(q, (artist,))
        artist_id = cur.fetchone()[0]
    except TypeError:
        # Check if artist exists on MusicBrainz
        try:
            artist_mbid = get_artist_mbid(artist)
            if not artist_mbid:
                raise ValueError
        except ValueError:
            artist_mbid = None
        finally:
            a = {"mbid": artist_mbid, "name": artist}
            insert_artist(cur, con, a)
            artist_id = cur.lastrowid

    label = input("LABEL: ")

    # TODO: proper error checking
    # TODO: check if label exists in musicbrainz
    try:
        # Check if label already exists in database
        q = f"SELECT * FROM label WHERE name COLLATE NOCASE = ?"
        cur.execute(q, (label,))
        label_id = cur.fetchone()[0]
    except TypeError:
        # Check if label exists on MusicBrainz
        try:
            label_mbid = get_label_mbid(label)
            if not label_mbid:
                raise ValueError
        except ValueError:
            label_mbid = None
        finally:
            l = {"mbid": label_mbid, "name": label}
            insert_label(cur, con, l)
            label_id = cur.lastrowid

    release_date = ""
    while len(release_date) < 1:
        try:
            release_date = input("RELEASE YEAR - YYYY: ")
            if release_date == "":
                break
            if len(release_date) != 4:
                raise ValueError
        except ValueError:
            print("Invalid value entered.")

    genre = input("GENRE: ")

    runtime = -1
    while runtime <= 0:
        try:
            runtime = int(input("LENGTH (minutes): "))
            if runtime <= 0:
                raise ValueError
        except ValueError:
            print("Invalid length. Try again.")
    runtime = runtime * 60000  # convert mins to ms for db storage

    rating = -1
    while rating < 0 or rating > 100:
        try:
            rating = int(input("RATING (0-100): "))
            if rating < 0 or rating > 100:
                raise ValueError
        except ValueError:
            print("Invalid rating. Try again.")

    country = input("COUNTRY: ")

    track_count = 0
    while track_count <= 0:
        try:
            track_count = int(input("TRACK COUNT: "))
        except ValueError:
            print("Invalid track count. Try again.")

    listen_date = datetime.date.today().strftime("%Y-%m-%d")
    release = {"title": title,
               "mbid": None,
               "artist_id": artist_id,
               "label_id": label_id,
               "release_date": release_date,
               "listen_date": listen_date,
               "track_count": track_count,
               "country": country,
               "runtime": runtime,
               "rating": rating,
               "genre": genre}

    return release, artist, label


if __name__ == '__main__':
    # Create database connection
    con = create_connection("music.db")
    cur = create_cursor(con)
    # Create tables
    create_tables(cur)

    main()

    con.close()


# TO BE COMPLETED


def edit_release():
    return None


def search_release():
    return None
