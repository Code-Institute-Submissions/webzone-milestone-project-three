import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/index")
def index():
    posts = list(mongo.db.posts.find())
    return render_template("index.html", posts=posts)


@app.route("/search", methods=["GET", "POST"])
def search():
    search = request.form.get("search")
    posts = list(mongo.db.posts.find({"$text": {"$search": search}}))
    return render_template("index.html", posts=posts)


@app.route("/view_post/<post_id>")
def view_post(post_id):
    the_post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    return render_template('view_post.html', post=the_post)


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("sign_up"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("index"))
    return render_template("sign_up.html", title="Sign Up")


@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for("index"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("sign_in"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("sign_in"))

    return render_template("sign_in.html", title="Sign In")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("sign_in"))


# Request a user to sign in before taking certain actions
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user" in session and session["user"]:
            return f(*args, **kwargs)
        flash("You need to sign in first")
        return redirect(url_for("sign_in"))
    return wrap


@app.route("/sign_out")
@login_required  # Allow only signed-in users to sign out
def sign_out():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("sign_in"))


@app.route("/create_post", methods=["GET", "POST"])
@login_required  # Allow only signed-in users to create post
def create_post():
    if request.method == "POST":
        post = {
            "post_title": request.form.get("post_title"),
            "post_image": request.form.get("post_image"),
            "image_description": request.form.get("image_description"),
            "post_content": request.form.get("post_content"),
            "read_time": request.form.get("read_time"),
            "created_by": session["user"],
            "created_at": datetime.now().strftime('%B %d %Y')
        }
        mongo.db.posts.insert_one(post)
        flash("Post Successfully Created")
        return redirect(url_for("index"))
    return render_template("create_post.html", title="Create Post")


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if post:
        # Check if the creator of the post is the currently signed-in user
        if post["created_by"] == session["user"]:
            if request.method == "POST":
                post = {
                  "post_title": request.form.get("post_title"),
                  "post_image": request.form.get("post_image"),
                  "image_description": request.form.get("image_description"),
                  "post_content": request.form.get("post_content"),
                  "read_time": request.form.get("read_time"),
                  "created_by": session["user"],
                  "created_at": datetime.utcnow().strftime('%B %d %Y')
                }
                mongo.db.posts.update({"_id": ObjectId(post_id)}, post)
                flash("Post Successfully Updated")
                return redirect(url_for("index"))

            post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
            return render_template("edit_post.html",  post=post)
        # if the signed-in user is not the creator of the post
        else:
            flash("A post can only be edited by its creator")
    # If the post doesn't exist
    else:
        flash("Not found")
    return redirect(url_for("index"))


# A user must be signed-in and be the creator of a post to be able to delete it
@app.route("/delete_post/<post_id>")
@login_required
def delete_post(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if post:
        if post["created_by"] == session["user"]:
            mongo.db.posts.remove({"_id": ObjectId(post_id)})
            flash("Post Deleted!")
        else:
            flash("A post can only be deleted by its creator")
    else:
        flash("Not found")
    return redirect(url_for("index"))


# Error handler for page not found
@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/error_404.html"), 404


# Error handler for internal server error
@app.errorhandler(500)
def something_went_wrong(error):
    return render_template("errors/error_500.html"), 500


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
