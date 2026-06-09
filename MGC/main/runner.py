import sys, util, util, db, sqlite3, os
from constants import MUSIC_PATH, PORT, STATIC_PATH, TEMPLATE_PATH
import threading
from flask_talisman import Talisman

from flask import Flask, request, render_template, session, flash, url_for, redirect, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timedelta

#startup Sequence
app = Flask(
     import_name= "myGymClub",
         template_folder =TEMPLATE_PATH,
             static_folder =STATIC_PATH)

app.secret_key = 'CS442'
app.config['EXPLAIN_TEMPLATE_LOADING'] = ("-d" in sys.argv)

@app.route('/')
def welcome():
   return render_template("welcome.jinja2")

@app.route('/fitness.jpg')
def fitness_image():
   return send_file('templates/fitness.jpg', mimetype='image/jpeg')

@app.route('/home')
def home():
   xp_percentage = db.get_XP(session["username"]) / db.get_xp_cap(session["username"]) * 100
   level = db.get_level(session["username"])
   user_goals = db.get_goals(session["username"])
   streak = db.get_streak(session["username"])
   login_link = url_for('login')
   
   return render_template('home.jinja2',
                          user=session["username"],
                          xp_percentage=xp_percentage,
                          level=level,
                          goals=user_goals,
                          streak=streak,
                          login_link=login_link)

@app.route("/login", methods=["POST", "GET"])
def login():
   if request.method == "POST": #get info and display user page
       user = request.form["user"]
       pw = request.form["pw"]
       record = db.get_user_by_username(user)

       if record and db.validate_pw(user, pw):
           if "pending_join" in session and session["pending_join"] != None:
               return redirect(url_for("events"))

           session["username"] = user
           return redirect(url_for("home"))
       else:
           print(f"{user}, {pw}: {db.validate_pw(user, pw)}")
           flash("Invalid username or password.")
           return redirect(url_for("login"))


   return render_template("login.jinja2")

@app.route("/login/register")
def login_register():
   return redirect(url_for("register"))

@app.route('/add-goals', methods=["POST", "GET"])
def goals():

    if "username" not in session:
        return redirect(url_for("login"))

    edit_goal = request.args.get("edit")

    if request.method == "POST":

        gName = request.form["name"]
        gStyle = request.form["style"]
        gReps = request.form["reps"]
        gRepType = request.form["repType"]
        gSets = request.form["sets"]
        gFreq = request.form["freq"]
        gFreqType = request.form["freqType"]
        gMemo = request.form["memo"]

        if edit_goal:
            db.update_goal(session["username"], edit_goal, gName, gStyle,
                           gReps, gRepType, gSets, gFreq, gFreqType, gMemo)
        else:
            db.add_goal(session["username"], gName, gStyle, gReps,
                        gRepType, gSets, gFreq, gFreqType, gMemo)

        return redirect(url_for("home"))

    goal_data = None
    if edit_goal:
        goals = db.get_goals(session["username"])
        for g in goals:
            if g[1] == edit_goal:
                goal_data = g
                break

    return render_template(
       "goals.jinja2",
       goal=goal_data,
       user=session.get("username"),
       xp_percentage=db.get_XP(session.get("username")) / db.get_xp_cap(session.get("username")) * 100,
       level=db.get_level(session.get("username")),
       streak=db.get_streak(session.get("username")),
       login_link=url_for('logout')
    )

@app.route('/edit-goal', methods=["GET", "POST"])
def edit_goal():

    if "username" not in session:
        return redirect(url_for("login"))

    goal_name = request.args.get("goal")

    if request.method == "POST":
        new_name = request.form.get("name") or None
        new_reps = request.form.get("reps") or None
        new_rep_type = request.form.get("rep_type") or None
        new_sets = request.form.get("sets") or None
        new_frequency = request.form.get("frequency") or None
        new_freq_type = request.form.get("freq_type") or None
        new_memo = request.form.get("memo") or None
        new_style = request.form.get("style") or None

        # Example update (you'll need a DB function)
        db.update_goal(session["username"], goal_name, new_name, new_style, new_reps, new_rep_type, new_sets, new_frequency, new_freq_type, new_memo)

        return redirect(url_for("home"))

    return render_template("edit_goal.jinja2", goal=goal_name)

@app.route('/register', methods=["POST", 'GET'])
def register():
   if request.method == "POST": #get info and display user page
       user = request.form["user"]
       pw = request.form["pw"]
       confirmPW = request.form["pw2"]


       if not user or not pw: #Not null username/password
           flash("Username and password cannot be empty.")
           return redirect(url_for("register"))


       elif(pw != confirmPW): #confirm password matches
           flash("Passwords do not match", "error")
           return redirect(url_for("register"))
       elif (len(pw) < 8):
           flash("Password must be at least 8 characters.")
           return redirect(url_for("register"))


       try:
           db.add_user_record(user, pw, 0)
           #flash("Account created successfully.")
           session["username"] = user
           return redirect(url_for("home"))
       except sqlite3.IntegrityError:
           flash("Username already exists.")
           return redirect(url_for("register"))


   else:
       return render_template("register.jinja2")

@app.route("/join-event/<encrypted_id>", methods=["GET"])
def join_event(encrypted_id):
    username = session.get("username")
    event_id = util.decript_id(encrypted_id)
    
    if not username:
        session["pending_join"] = event_id
        return redirect(url_for("login"))

    db.update_event_attendance(username, event_id, True)
    print(f"User has joined event: {username} | {event_id}")
    return redirect(url_for("events"))



@app.route('/profile', methods=["GET", "POST"])
def profile():
   if "username" not in session:
       flash("You must be logged in to access your profile.")
       return redirect(url_for("login"))


   if request.method == "POST":
       first_name = request.form.get("first_name")
       last_name = request.form.get("last_name")
       email = request.form.get("email")
       gender = request.form.get("gender")
       height = request.form.get("height")
       weight = request.form.get("weight")
       age = request.form.get("age")


       db.update_user_record(
           session["username"], first_name, last_name, email, gender, height, weight, age
       )
       #flash("Profile updated successfully.")
       return redirect(url_for("profile"))


   user_data = db.get_user_by_username(session["username"])
   return render_template(
        "profile.jinja2",
        user=user_data,
        xp_percentage=db.get_XP(session.get("username")) / db.get_xp_cap(session.get("username")) * 100,
        level=db.get_level(session.get("username")),
        streak=db.get_streak(session.get("username")),
        login_link=url_for('logout')
    )

@app.route('/delete-goal')
def delete_goal():
    goal_name = request.args.get("goal")

    if not goal_name:
        flash("Goal not found.")
        return redirect(url_for("home"))

    db.delete_goal(session["username"], goal_name)

    return redirect(url_for("home"))

@app.route('/events')
def events():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    xp_percentage = db.get_XP(username) / db.get_xp_cap(username) * 100
    level = db.get_level(username)
    streak = db.get_streak(username)
    login_link = url_for('logout')
    attendance = db.get_attendance(username)

    events_data = db.get_n_events(20)
    comments_data = {event[0]: db.get_comments(event[0]) for event in events_data}

    join_id = None
    try:
        join_id = session["pending_join"]
    except:
        print(f"{util.now()}: No join id found.")

    if join_id:
        db.update_event_attendance(username, join_id, True)
        session["pending_join"] = None

    return render_template(
        "events.jinja2",
        user=username,
        xp_percentage=xp_percentage,
        level=level,
        streak=streak,
        login_link=login_link,
        events=events_data,
        comments=comments_data,
        added_event_ids=attendance,
        joined_event= (join_id != None),
        join_id = join_id
    )


@app.route("/log-event/<int:event_id>", methods=["POST"])
def log_event(event_id):
    username = session.get("username")
    if not username:
        return {"success": False, "message": "Not logged in"}, 403

    with sqlite3.connect("myGymClub.db") as conn:
        cur = conn.cursor()

        # Check if user is attending this event
        cur.execute("""
            SELECT attending
            FROM Attendance
            WHERE event_id=? AND username=?
        """, (event_id, username))

        result = cur.fetchone()

        if not result:
            return {"success": False, "message": "Event not found or not joined"}, 404

        attending = result[0]

        if attending == 0:
            return {"success": False, "message": "You are not attending this event"}

        # OPTIONAL: prevent double logging (you may want a separate column later)
        # For now, assume attending=1 means it hasn't been "logged" yet

        # Mark as logged (you could reuse attending or add a new column)
        cur.execute("""
            UPDATE Attendance
            SET attending = 0
            WHERE event_id=? AND username=?
        """, (event_id, username))

        conn.commit()

        # Award XP (flat or configurable)
        xp_gained = 50  # you can tune this
        old_level = db.get_level(username)

        db.increment_xp(username, xp_gained)

        xp_to_next_level = db.get_xp_cap(username) - db.get_XP(username)

        return {
            "success": True,
            "xp_gained": xp_gained,
            "old_level": old_level,
            "new_level": db.get_level(username),
            "xp_percentage": db.get_XP(username) / db.get_xp_cap(username) * 100,
            "xp_to_next_level": xp_to_next_level
        }

@app.route("/events/delete-comment", methods=["POST"])
def delete_comment():
    username = session.get("username")
    if not username:
        flash("You must be logged in to your account to delete a comment.")
        return redirect(url_for("login"))

    comment_id = request.form.get("comment_id")
    if not comment_id:
        flash("Invalid comment.")
        return redirect(url_for("events"))

    success = db.delete_comment(comment_id, username)
    if not success:
        flash("You can only delete your own comments.")

    return redirect(url_for("events"))

@app.route("/log-workout/<int:workout_id>", methods=["POST"])
def log_workout(workout_id):
    username = session.get("username")
    if not username:
        return {"success": False, "message": "Not logged in"}, 403

    with sqlite3.connect("myGymClub.db") as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT goal_name, date, completed
            FROM Scheduled_Workouts
            WHERE id=? AND username=?
        """, (workout_id, username))

        result = cur.fetchone()

        if result:
            goal_name, date, completed = result

            if completed == 1:
                return {"success": False, "message": "Already logged"}

            cur.execute("""
                UPDATE Scheduled_Workouts
                SET completed = 1
                WHERE id=? AND username=?
            """, (workout_id, username))

            conn.commit()


            xp_gained = db.calculate_xp_for_goal(username, goal_name)
            old_level = db.get_level(username)
            db.increment_xp(username, xp_gained)
            xp_to_next_level = db.get_xp_cap(username) - db.get_XP(username)


            # Optional: log in Workout_Logs too
            if goal_name:
                db.add_workout_log(username, goal_name, date)


            return {"success": True,
                   "xp_gained": xp_gained,
                   "old_level": old_level,
                   "new_level": db.get_level(username),
                   "xp_percentage": db.get_XP(username) / db.get_xp_cap(username) * 100,
                   "xp_to_next_level": xp_to_next_level}

    return {"success": False, "message": "Event not found"}, 404

@app.route("/calendar")
def calendar():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    workouts = db.get_scheduled_workouts(username)

    attending_ids = db.get_attendance(username) 
    workout_events = []

    
    for w in workouts:
        id, title, description, goal, date_str, start_time, end_time, completed = w
        workout_events.append({
            "id": id,
            "title": "✔ " + title if completed else title,
            "start": f"{date_str}T{start_time}",
            "end": f"{date_str}T{end_time}",
            "backgroundColor": "green" if completed else "",
            "borderColor": "green" if completed else "",
            "extendedProps": {
                "description": description,
                "goal_name": goal,
                "completed": completed
            }
        })

    attending = [db.get_rec_event(id) for id in attending_ids]

    print(f"events : {attending}")
    print(f"workouts : {workout_events}")


    return render_template(
        "calendar.jinja2",
        events=attending,
        workouts=workout_events,
        user=username,
        xp_percentage=db.get_XP(username) / db.get_xp_cap(username) * 100,
        level=db.get_level(username),
        streak=db.get_streak(username),
        login_link=url_for("logout")
    )

@app.route("/events/add-comment", methods=["POST"])
def add_comment():
    username = session.get("username")
    if not username:
        return {"success": False, "message": "You must be logged in to add a comment."}

    if request.method != "POST":
        return {"success": False, "message": "Invalid request method."}

    event_id = request.form.get("event_id")
    comment = request.form.get("comment")

    print(event_id, username, comment)
    db.add_comment(event_id, username, comment)

    return redirect(url_for("events"))

#-------------------------
@app.route("/schedule-workout", methods=["GET", "POST"])
def schedule_workout():
    username = session.get("username")
    if not username:
        flash("You must be logged in to schedule workouts.")
        return redirect("/login")

    if request.method == "GET":
        goals = db.get_goals(username)
        return render_template(
            "scheduleworkout.jinja2",
            goals=goals,
            xp_percentage=db.get_XP(username) / db.get_xp_cap(username) * 100,
            level=db.get_level(username),
            streak=db.get_streak(username),
            login_link=url_for('logout'),
            user=username
        )

    # -------------------------------
    # Get form data
    title = request.form.get("title")
    description = request.form.get("description")
    start_date_str = request.form.get("start_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    goal_name = request.form.get("goal")
    repeat_weeks = int(request.form.get("repeat") or 1)
    days_selected = request.form.getlist("days")  # e.g. ['mon', 'wed']

    ends_option = request.form.get("ends")  # 'never', 'on', 'after'
    end_date_str = request.form.get("end_date")
    end_after = int(request.form.get("end_after") or 0)

    if not start_date_str or not days_selected:
        flash("You must select a start date and at least one day.")
        return redirect("/schedule-workout")

    # -------------------------------
    # Map day strings to Python weekday numbers
    day_map = {"sun": 6, "mon": 0, "tues": 1, "wed": 2,
               "thurs": 3, "fri": 4, "sat": 5}
    target_weekdays = sorted([day_map[d] for d in days_selected])

    # Parse start and end dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if ends_option == "on" and end_date_str else None

    # -------------------------------
    # Generate scheduled workout dates by individual occurrences
    scheduled_dates = []
    current_date = start_date
    workouts_scheduled = 0
    max_iterations = 1000  # safety

    while True:
        # Schedule all weekdays in the current week
        for weekday in target_weekdays:
            # Calculate the next date for this weekday
            days_ahead = (weekday - current_date.weekday() + 7) % 7
            workout_date = current_date + timedelta(days=days_ahead)

            # Skip if before start_date
            if workout_date < start_date:
                continue

            # Stop if past end_date
            if ends_option == "on" and end_date and workout_date > end_date:
                continue

            scheduled_dates.append(workout_date)
            workouts_scheduled += 1

            # Stop if we hit "end after X occurrences"
            if ends_option == "after" and workouts_scheduled >= end_after:
                break

        if (ends_option == "after" and workouts_scheduled >= end_after) or \
           (ends_option == "on" and end_date and max(scheduled_dates) >= end_date):
            break

        # Move to the same day of the week after repeat_weeks
        current_date += timedelta(weeks=repeat_weeks)

        # Safety check
        if len(scheduled_dates) >= max_iterations:
            break

    scheduled_dates = sorted(list(set(scheduled_dates)))  # remove duplicates if any

    # -------------------------------
    # Insert workouts into database
    with sqlite3.connect('myGymClub.db') as conn:
        cur = conn.cursor()
        for workout_date in scheduled_dates:
            cur.execute("""
                INSERT INTO Scheduled_Workouts
                    (username, title, description, goal_name, date, start_time, end_time, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (username, title, description, goal_name,
                  workout_date.isoformat(), start_time, end_time))
        conn.commit()

    return redirect("/calendar")
#-------------------------

@app.route("/calendar/add-event", methods=["POST"])
def add_event_to_calendar():
    if "username" not in session:
        return jsonify(success=False, message="Not logged in"), 403

    data = request.get_json()
    event_id = data.get("event_id")
    if not event_id:
        return jsonify(success=False, message="No event ID provided"), 400

    event = None
    all_events = db.get_n_events()
    for e in all_events:
        if str(e[0]) == str(event_id):
            event = e
            break

    if not event:
        return jsonify(success=False, message="Event not found"), 404

    username = session["username"]

    title = event[1]
    date_str = event[3]
    raw_start_time = event[4]
    raw_end_time = event[5]
    description = event[6] or ""

    # Convert "7:00 PM" -> "19:00"
    try:
        start_time = datetime.strptime(raw_start_time.strip(), "%I:%M %p").strftime("%H:%M")
        end_time = datetime.strptime(raw_end_time.strip(), "%I:%M %p").strftime("%H:%M")
    except ValueError:
        return jsonify(success=False, message="Invalid event time format"), 400

    already_exists = db.scheduled_event_exists(
        username=username,
        title=title,
        date=date_str,
        start_time=start_time,
        end_time=end_time
    )

    if not already_exists:
        db.add_scheduled_workout(
            username=username,
            title=title,
            description=description,
            goal_name="REC Event",
            date=date_str,
            start_time=start_time,
            end_time=end_time
        )

    return jsonify(success=True, already_added=already_exists)



@app.route("/friends", methods=["GET"])
def friends():
    user = session.get("username")
    query = request.args.get("q", "").strip()

    friends_list = []
    results      = []
    statuses     = {}
    friend_data  = {}
    gift_xp_status = {}
    incoming_requests = []  # NEW

    if user:
        friends_list = db.get_friends(user)
        incoming_requests = db.get_incoming_requests(user)  # NEW

        for f in friends_list:
            f_rec = db.get_user_by_username(f)
            xp     = f_rec["experience"]  if f_rec else 0
            xp_cap = f_rec["xp_cap"]      if f_rec else 100
            level  = f_rec["level"]       if f_rec else 1
            streak = f_rec["streak"]      if f_rec else 0
            goals    = [g[1] for g in db.get_goals(f)][:2]
            workouts = db.get_recent_workouts(f, 2)
            events   = db.get_recent_attended_events(f, 2)
            comments = db.get_profile_comments(f, 3)
            friend_data[f] = {
                "xp": xp, "xp_cap": xp_cap, "level": level, "streak": streak,
                "goals": goals, "workouts": workouts, "events": events, "comments": comments,
            }
            gift_xp_status[f] = not db.can_gift_xp(user, f)

        if query:
            results = db.search_users(query)
            if user in results:
                results.remove(user)
            for r in results:
                statuses[r] = db.get_friend_status(user, r)

    return render_template(
        "friends.html",
        user=user, query=query,
        friends_list=friends_list,
        incoming_requests=incoming_requests,  # NEW
        results=results, statuses=statuses,
        friend_data=friend_data, gift_xp_status=gift_xp_status,
        xp_percentage=(db.get_XP(user) / db.get_xp_cap(user) * 100) if user else 0,
        level=db.get_level(user) if user else 0,
        streak=db.get_streak(user) if user else 0,
        login_link="/logout"
    )


@app.route("/post-profile-comment", methods=["POST"])
def post_profile_comment():
    author = session.get("username")
    if not author:
        flash("You must be logged in to comment.")
        return redirect(url_for("login"))

    target  = request.form.get("target")
    comment = request.form.get("comment", "").strip()

    if target and comment:
        db.add_profile_comment(author, target, comment)

    return redirect(url_for("friends"))


@app.route("/gift-xp", methods=["POST"])
def gift_xp_route():
    giver = session.get("username")
    if not giver:
        return jsonify(success=False, message="Not logged in"), 403

    data   = request.get_json(silent=True) or {}
    target = data.get("target")

    if not target:
        return jsonify(success=False, message="No target specified"), 400

    if giver == target:
        return jsonify(success=False, message="You can't gift XP to yourself!"), 400

    success = db.gift_xp(giver, target, amount=50)

    if success:
        return jsonify(success=True,  message=f"🎁 +50 XP gifted to @{target}!")
    else:
        return jsonify(success=False, message=f"Already gifted XP to @{target} today.")
    
@app.route("/toggle-friend", methods=["POST"])
def toggle_friend():
    user = session.get("username")
    friend = request.form.get("friend")
    if not user:
        return redirect("/login")

    status = db.get_friend_status(user, friend)

    if status == "none":
        db.send_friend_request(user, friend)
    elif status == "pending":
        # if we are the receiver, accept; if we are the sender, cancel
        db.accept_or_cancel_request(user, friend)
    elif status == "accepted":
        db.remove_friend(user, friend)

    return redirect("/friends")


@app.route('/attends', methods=['POST'])
def attends():
    username = session.get("username")
    data = request.get_json(silent=True) or {}
    event_id = data.get("event_id") or request.form.get("event_id")
    if not username or not event_id:
        return redirect(url_for("events"))

    db.update_event_attendance(username, event_id, True)
    print(f"Attends hit: {username} | {event_id}")
    return {"message": "Success", "status": 200}

@app.route('/leaves', methods=['POST'])
def leaves():
    username = session.get("username")
    data = request.get_json(silent=True) or {}
    event_id = data.get("event_id") or request.form.get("event_id")
    if not username or not event_id or not data:
        print("ALERT: Failed leave.")
        return redirect(url_for("events"))

    db.update_event_attendance(username, event_id, False)
    print(f"Leaves hit: {username} | {event_id}")
    return {"message": "Success", "status": 200}


@app.route('/logout')
def logout():
   session.pop("username")
   return redirect(url_for("welcome"))


# Check for the --reset-db flag in command-line arguments
if "--reset-db" in sys.argv and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    print("Restarting database using scraper (heavy)...")
    db.init_db()

if "--reload-tables" in sys.argv and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    print("Restarting database without using scraper (light)...")
    db.reload_tables()

# Finally, run the app
util.print_welcome_message()

app.run(debug=True, port=PORT)
session["pending_join"] = None


