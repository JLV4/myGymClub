import sqlite3, os, random, our_scraper
from constants import INIT_NUM_RANDOM_GOALS

db_file = 'myGymClub.db'

import random
import sqlite3


def load_sample_data():
        add_user_record("admin", "admin", True)
        type_options = {
            'ORM': ['pounds'],
            'Exercise': ['reps', 'weight', 'miles', 'minutes', 'calories'],
            'Habit': ['boolean', 'count', 'minutes', 'pages']
        }

        send_friend_request("admin", "chicagofan32")
        accept_friend_request("admin", "chicagofan32")
        add_user_record("chicagofan32", "password", False)
        add_user_record("gymrat77", "password", False)

        add_goal("admin", f"Cardio", "Habit", 50, type_options["Habit"][2], None, 1, "day", "Get that heart pumping!")
        add_goal("admin", f"Swimming", "Habit", 30, type_options["Habit"][2], None, 2, "week", "Make a splash with regular swims!")
        add_goal("admin", f"Stretches", "Habit", 10, type_options["Habit"][2], None, 1, "day", "Start your day with refreshing stretches!")
        add_goal("admin", f"Yoga Practice", "Habit", 3, type_options["Habit"][2], None, 1, "day", "Find your zen with daily yoga sessions!")
        add_goal("admin", f"Plank Hold", "Exercise", 2, type_options["Exercise"][3], 3, 2, "day", "Strengthen your core with planks!")
        add_goal("admin", f"Push-Up Challenge", "Exercise", 20, type_options["Exercise"][0], 1, 1, "day", "Master the push-up with this challenge!")
        add_goal("admin", f"Squat Jumps", "Exercise", 15, type_options["Exercise"][0], 3, 1, "day", "Boost your explosive power with squat jumps!")
        add_goal("admin", f"Burpees", "Exercise", 25, type_options["Exercise"][0], 1, 5, "week", "Burn calories and build strength with burpees!")

def init_db():
    print("Removing database if it exists... ")

    try:
        os.remove(db_file)
        print(f"Successfully deleted {db_file}")
    except FileNotFoundError:
        print("Error: The file does not exist.")
    except PermissionError:
        print("Error: You do not have permission to delete this file.")
    except OSError as e:
        print(f"Error: {e.strerror}")

    print("Initializing database . . .")

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        delete_all_tables(cursor, fast = False)
        create_all_tables(cursor, fast = False)

    print("Loading sample data...")
    load_sample_data()
    print("Sample data loaded!")

    print("Scraping data using our custom UIC REC Scraper... ")
    our_scraper.add_months_event()
    print("Scraping complete!")

    print("Database initialized successfully!")

def reload_tables():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        delete_all_tables(cursor)
        create_all_tables(cursor)
        load_sample_data()


# --------BEGIN TABLE CREATION-------#
def delete_all_tables(cursor, fast = None):
    cursor.execute("DROP TABLE IF EXISTS User_Records")
    cursor.execute("DROP TABLE IF EXISTS Goals")
    cursor.execute("DROP TABLE IF EXISTS Event_Comments")
    cursor.execute("DROP TABLE IF EXISTS Workout_Logs")
    cursor.execute("DROP TABLE IF EXISTS Favorite_Events")
    cursor.execute("DROP TABLE IF EXISTS Scheduled_Workouts")
    cursor.execute("DROP TABLE IF EXISTS Attendance")

    if not fast:
        cursor.execute("DROP TABLE IF EXISTS Rec_Events")

def create_all_tables(cursor, fast = None):
    create_user_record_table(cursor)
    create_workout_logs_table(cursor)
    create_favorite_events_table(cursor)
    create_comments_table(cursor)
    create_scheduled_workouts_table(cursor)
    create_goals_table(cursor)
    create_attendance_table(cursor)
    create_friends_table(cursor)
    create_profile_comments_table(cursor)
    create_gift_xp_table(cursor)
    if not fast:
        create_rec_event_table(cursor)



def create_user_record_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS User_Records (
            username TEXT NOT NULL UNIQUE PRIMARY KEY,
            password TEXT NOT NULL,
            isAdmin INTEGER NOT NULL DEFAULT 0,
            experience INTEGER NOT NULL DEFAULT 0,
            xp_cap INTEGER NOT NULL DEFAULT 100,
            level INTEGER NOT NULL DEFAULT 1,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            gender TEXT CHECK (
                gender IN ('male', 'female', 'other')
                OR gender IS NULL
            ),
            height INTEGER,
            weight INTEGER,
            streak INTEGER DEFAULT 1,
            age INTEGER,
            last_login DATE
        );
    """)


def create_profile_comments_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Profile_Comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author    TEXT NOT NULL,
            target    TEXT NOT NULL,
            comment   TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

def create_gift_xp_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Gift_XP_Log (
            giver   TEXT NOT NULL,
            target  TEXT NOT NULL,
            date    TEXT NOT NULL,
            PRIMARY KEY (giver, target, date)
        );
    """)


def get_recent_workouts(username, n=2):
    """Return the n most recent distinct goal_names logged by username."""
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT goal_name
            FROM Workout_Logs
            WHERE username = ?
            ORDER BY date DESC
            LIMIT ?
        """, (username, n))
        return [row[0] for row in cur.fetchall()]

def get_recent_attended_events(username, n=2):
    """Return the n most recent Rec_Events the user is attending."""
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.name
            FROM Attendance a
            JOIN Rec_Events r ON r.event_id = a.event_id
            WHERE a.username = ? AND a.attending = 1
            ORDER BY r.event_id DESC
            LIMIT ?
        """, (username, n))
        return [row[0] for row in cur.fetchall()]

def get_profile_comments(target, n=3):
    """Return the n most recent profile comments left on target's wall."""
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, author, comment, timestamp
            FROM Profile_Comments
            WHERE target = ?
            ORDER BY id DESC
            LIMIT ?
        """, (target, n))
        return cur.fetchall()

def can_gift_xp(giver, target):
    """Return True if giver hasn't gifted XP to target yet today."""
    today = __import__('datetime').date.today().isoformat()
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM Gift_XP_Log
            WHERE giver = ? AND target = ? AND date = ?
        """, (giver, target, today))
        return cur.fetchone() is None

# ── DATA WRITES ───────────────────────────────────────────────────────────────

def add_profile_comment(author, target, comment):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Profile_Comments (author, target, comment)
            VALUES (?, ?, ?)
        """, (author, target, comment))
        conn.commit()

def gift_xp(giver, target, amount=50):
    """Award XP to target and record the gift so it can only happen once/day."""
    today = __import__('datetime').date.today().isoformat()
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO Gift_XP_Log (giver, target, date)
                VALUES (?, ?, ?)
            """, (giver, target, today))
            conn.commit()
        except sqlite3.IntegrityError:
            return False   # already gifted today
    increment_xp(target, amount)
    return True

def create_friends_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Friends (
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'accepted')),
            UNIQUE(sender, receiver)
        );
    """)

def create_scheduled_workouts_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Scheduled_Workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            goal_name TEXT,
            date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            completed INTEGER DEFAULT 0
        );
    """)

def create_goals_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Goals (
            username TEXT NOT NULL,
            goal_name TEXT NOT NULL,
            style TEXT NOT NULL CHECK (style IN ('ORM', 'Exercise', 'Habit')),
            type TEXT NOT NULL,
            reps INTEGER,
            sets INTEGER,
            weight INTEGER,
            frequency INTEGER,
            freq_type TEXT CHECK (
                freq_type IN ('day', 'week', 'month')
                OR freq_type IS NULL
            ),
            memo TEXT
        );
    """)

def create_rec_event_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Rec_Events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            organizer_username TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            memo TEXT,
            location TEXT
        );
    """)

def create_workout_logs_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Workout_Logs (
            username TEXT NOT NULL,
            goal_name TEXT NOT NULL,
            date TEXT NOT NULL
        );
    """)

def create_favorite_events_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Favorite_Events (
            username TEXT NOT NULL,
            event_id INTEGER NOT NULL
        );
    """)

def create_comments_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Event_Comments (
            username TEXT NOT NULL,
            event_id TEXT NOT NULL,
            comment TEXT NOT NULL
        );
    """)

def create_attendance_table(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Attendance (
            username TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            attending INTEGER NOT NULL
        );
    """)
    print("Attendance table created successfully!")
# --------END TABLE CREATION---------#


# --------BEGIN DATA WRITES--------#
def update_event_attendance(username, event_id, joining):
    print(f"Event update: {username} | {event_id} | {joining}")
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()

        ## Check if the user is already attending
        cur.execute(f"""
            SELECT * FROM Attendance
            WHERE event_id = {event_id}
            AND username = "{username}"
        """)

        join_val = 1 if joining else 0

        if not cur.fetchall(): ## If not, add them to the table
            cur.execute(f"""
                INSERT INTO Attendance (username, event_id, attending)
                VALUES ("{username}", {event_id}, {join_val})
            """)
            conn.commit()
            return
        else: ## Otherwise, update their attendance status
            cur.execute(f"""
                UPDATE Attendance
                SET attending={join_val}
                WHERE username='{username}' AND event_id={event_id}
            """)
            conn.commit()
            return

def add_user_record(username, password, isAdmin):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO User_Records (username, password, isAdmin, experience, first_name, last_name, email, gender, height, weight, streak, age) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (username, password, isAdmin, 0, None, None, None, None, None, None, 1, None))
        conn.commit()

def update_user_record(username, first_name, last_name, email, gender, height, weight, age):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE User_Records
            SET first_name=?, last_name=?, email=?, gender=?, height=?, weight=?, age=?
            WHERE username=?
        """, (first_name, last_name, email, gender, height, weight, age, username))
        conn.commit()

def add_scheduled_workout(username, title, description, goal_name, date, start_time, end_time):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Scheduled_Workouts 
            (username, title, description, goal_name, date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, title, description, goal_name, date, start_time, end_time))
        conn.commit()

def add_goal(username, goal_name, style, reps, rep_type, sets, frequency, freq_type, memo):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Goals 
            (username, goal_name, style, type, reps, sets, frequency, freq_type, memo)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (username, goal_name, style, rep_type, reps, sets, frequency, freq_type, memo))
        conn.commit()

def validate_pw(username, pw):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("SELECT password FROM User_Records WHERE username=?", (username,))
        res = cur.fetchone()
        return res[0] == pw

def update_goal(username, old_name, name, style, reps, rep_type, sets, frequency, freq_type, memo):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE Goals
            SET goal_name=?, style=?, type=?, reps=?, sets=?, frequency=?, freq_type=?, memo=?
            WHERE username=? AND goal_name=?
        """, (name, style, rep_type, reps, sets, frequency, freq_type, memo, username, old_name))
        conn.commit()

#friends
def get_friend_status(user1, user2):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT status FROM Friends
            WHERE (sender=? AND receiver=?)
               OR (sender=? AND receiver=?)
        """, (user1, user2, user2, user1))

        row = cur.fetchone()

        if not row:
            return "none"

        return row[0]  # 'pending' or 'accepted'
   

def get_friends(username):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT sender, receiver
            FROM Friends
            WHERE status='accepted'
            AND (sender=? OR receiver=?)
        """, (username, username))

        rows = cur.fetchall()

        friends = []
        for sender, receiver in rows:
            if sender == username:
                friends.append(receiver)
            else:
                friends.append(sender)

        return friends

def get_incoming_requests(username):
    """Return list of usernames who sent a pending request to username."""
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT sender FROM Friends
            WHERE receiver=? AND status='pending'
        """, (username,))
        return [row[0] for row in cur.fetchall()]

def accept_or_cancel_request(current_user, other):
    """If current_user is the receiver, accept. If sender, cancel/withdraw."""
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        # Check if current_user is the receiver
        cur.execute("""
            SELECT 1 FROM Friends
            WHERE sender=? AND receiver=? AND status='pending'
        """, (other, current_user))
        if cur.fetchone():
            cur.execute("""
                UPDATE Friends SET status='accepted'
                WHERE sender=? AND receiver=?
            """, (other, current_user))
        else:
            # current_user is the sender — withdraw the request
            cur.execute("""
                DELETE FROM Friends WHERE sender=? AND receiver=?
            """, (current_user, other))
        conn.commit()

def remove_friend(user1, user2):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM Friends
            WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        """, (user1, user2, user2, user1))
        conn.commit()

def send_friend_request(sender, receiver):
    if sender == receiver:
        return

    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO Friends (sender, receiver, status)
                VALUES (?, ?, 'pending')
            """, (sender, receiver))
            conn.commit()
        except Exception as e:
            print("Friend request error:", e)

def accept_friend_request(sender, receiver):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE Friends
            SET status='accepted'
            WHERE sender=? AND receiver=?
        """, (sender, receiver))

        conn.commit()

def search_users(query):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT username
            FROM User_Records
            WHERE username LIKE ?
            LIMIT 20
        """, (f"%{query}%",))

        return [row[0] for row in cur.fetchall()]

def delete_goal(username, goal_name):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Goals WHERE username=? AND goal_name=?", (username, goal_name))
        conn.commit()

def add_rec_event(name, organizer, date, start_time, end_time, memo, location):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Rec_Events 
            (name, organizer_username, date, start_time, end_time, memo, location)
            VALUES (?,?,?,?,?,?,?)
        """, (name, organizer, date, start_time, end_time, memo, location))
        conn.commit()

def add_workout_log(username, goal_name, date):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Workout_Logs (username, goal_name, date) VALUES (?,?,?)",
                    (username, goal_name, date))
        conn.commit()

def add_comment(event_id, username, comment):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Event_Comments (username, event_id, comment) VALUES (?,?,?)",
                    (username, event_id, comment))
        conn.commit()

def add_favorite_event(username, event_id):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO Favorite_Events (username, event_id) VALUES (?,?)",
                    (username, event_id))
        conn.commit()

def remove_favorite_event(username, event_id):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Favorite_Events WHERE username=? AND event_id=?",
                    (username, event_id))
        conn.commit()

def increment_xp(username, increment):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE User_Records
            SET experience = experience + ?
            WHERE username=?
        """, (increment, username))
        conn.commit()

def update_level(new_xp, new_level, exp_cap, username):
   with sqlite3.connect(db_file) as conn:
       cur = conn.cursor()
       cur.execute("""
       UPDATE User_Records
       SET experience = ?, level = ?, xp_cap = ?
       WHERE username = ?
   """, (new_xp, new_level, exp_cap, username))
   conn.commit()

def increment_xp(username, increment):
   with sqlite3.connect(db_file) as conn:
       cur = conn.cursor()
       cur.execute("""
           SELECT level, experience, xp_cap
           FROM User_Records
           WHERE username=?
       """, (username,))
       result = cur.fetchone()

       new_level, xp, xp_cap = result
       new_xp = xp + increment


       while new_xp >= xp_cap:
           new_level += 1
           new_xp -= xp_cap
           xp_cap += 100  # XP required increases by 50 per level

       update_level(new_xp, new_level, xp_cap, username)



# --------END DATA WRITES---------#


# --------BEGIN DATA READS--------#

def get_level(username):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("SELECT level FROM User_Records WHERE username=?", (username,))
        return cur.fetchone()[0]

def get_xp_cap(username):   
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("SELECT xp_cap FROM User_Records WHERE username=?", (username,))
        return cur.fetchone()[0]

def get_XP(username):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("SELECT experience FROM User_Records WHERE username=?", (username,))
        return cur.fetchone()[0]

def get_streak(username):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("SELECT streak FROM User_Records WHERE username=?", (username,))
        return cur.fetchone()[0]

def get_scheduled_workouts(username):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, description, goal_name, date, start_time, end_time, completed
            FROM Scheduled_Workouts
            WHERE username=?
        """, (username,))
        return cur.fetchall()

def get_user_by_username(username):
    with sqlite3.connect(db_file, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM User_Records WHERE username=?", (username,))
        return cur.fetchone()

def get_goals(username):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("SELECT username, goal_name, style, type, reps, sets, weight, frequency, freq_type, memo  FROM Goals WHERE username=?", (username,))
        return cur.fetchall()

def get_attendance(username):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT event_id
            FROM Attendance
            WHERE username=?
            AND attending=1""", (username,))

        res = [int(row[0]) for row in cur.fetchall()]

        print(f"Event IDs for {username}'s attendance: {res}")
        return res

def get_comments(event_id):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        # include rowid so each comment can be uniquely referenced for deletion
        cur.execute("SELECT rowid, username, event_id, comment FROM Event_Comments WHERE event_id=?", (event_id,))
        return cur.fetchall()

def delete_comment(comment_id, username):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Event_Comments WHERE rowid=? AND username=?", (comment_id, username))
        conn.commit()
        return cur.rowcount > 0

def get_user_comments_on_event(username, event_id):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Event_Comments WHERE username=? AND event_id=?", (username, event_id))
        raw_result = cur.fetchall()

        result = [res[2] for res in raw_result]
        return result

def get_all_commenters_on_event(event_id):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT username FROM Event_Comments WHERE event_id=?", (event_id,))
        return cur.fetchall()

def get_all_comments():
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT event_id FROM Event_Comments")
        event_ids = [int(row[0]) for row in cur.fetchall()]

        # Event ID -> [(username, comment)]
        output = {}

        for event_id in event_ids:
            commenters = get_all_commenters_on_event(event_id)

            comments = []
            for username in commenters:
                user_comments = get_user_comments_on_event(username[0], event_id)
                result = [(username[0], comment) for comment in user_comments]
                comments.append(result)


            output[event_id] = comments

        return output

def get_favorite_events(username):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Favorite_Events WHERE username=?", (username,))
        return cur.fetchall()

def get_rec_event(id):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()

        cur.execute(f"SELECT * FROM Rec_Events WHERE event_id = {id}")

        return cur.fetchone();

def get_n_events(n=None):
    with sqlite3.connect(db_file, timeout=30) as conn:
        cur = conn.cursor()
        if n:
            cur.execute("SELECT * FROM Rec_Events ORDER BY event_id DESC LIMIT ?", (n,))
        else:
            cur.execute("SELECT * FROM Rec_Events ORDER BY event_id DESC")
        return cur.fetchall()
    
def scheduled_event_exists(username, title, date, start_time, end_time):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1
            FROM Scheduled_Workouts
            WHERE username=? AND title=? AND date=? AND start_time=? AND end_time=?
        """, (username, title, date, start_time, end_time))
        return cur.fetchone() is not None

def get_user_rec_event_keys(username):
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT title, date, start_time, end_time
            FROM Scheduled_Workouts
            WHERE username=? AND goal_name='REC Event'
        """, (username,))
        return cur.fetchall()

def calculate_xp_for_goal(username, goal_name):
 with sqlite3.connect(db_file) as conn:
     cur = conn.cursor()
     cur.execute("""
         SELECT frequency, freq_type, reps, type, sets, style
         FROM Goals
         WHERE username=? AND goal_name=?
     """, (username, goal_name))
     result = cur.fetchone()

     freq, freq_type, reps, rep_type, sets, style = result


     # Default values for missing fields
     freq = freq or 1
     sets = sets or 1
     reps = reps or 1

     # Calculate goal value

     value = freq * sets

     if (style != "Habit"):
         value *= 30
     else:
         value *= 20

     if (freq_type == "week"):
         value *= 0.5
     elif (freq_type == "month"):
         value *= 0.25


     if (rep_type == "miles"):
         value += (reps * 10)
     else:
         value += (reps)


     return int(value)

# --------END DATA READS----------#

def get_exercise_types():
    return []