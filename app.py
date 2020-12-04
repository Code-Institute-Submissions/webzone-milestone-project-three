import os
import math
import pymongo
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_posts")
def home():
    posts = list(mongo.db.posts.find())
    return render_template("home.html", posts=posts)
    # page_limit = 2
    # current_page = int(request.args.get('current_page', 1))
    # total = mongo.db.posts.count()
    # pages = range(1, int(math.ceil(total / page_limit)) + 1)
    # posts = mongo.db.posts.find().sort('_id', pymongo.DESCENDING).skip(
    #                         (current_page - 1)*page_limit).limit(page_limit)

    # return render_template("home.html", post=posts, pages=pages,
    #                        current_page=current_page)


@app.route("/search", methods=["GET", "POST"])
def search():
    search = request.form.get("search")
    posts = list(mongo.db.posts.find({"$text": {"$search": search}}))
    return render_template("home.html", posts=posts)


@app.route("/view_post/<post_id>")
def view_post(post_id):
    the_post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    return render_template('view_post.html', post=the_post)


@app.route("/sign_up", methods=["GET", "POST"])
# def sign_up():
#     return render_template("sign_up.html")
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
    return render_template("sign_up.html")


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
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("sign_in"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("sign_in"))

    return render_template("sign_in.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("sign_in"))

    
@app.route("/sign_out")
def sign_out():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("sign_in"))


@app.route("/create_post", methods=["GET", "POST"])
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
        return redirect(url_for("home"))
    return render_template("create_post.html")


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
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
        return redirect(url_for("home"))

    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    return render_template("edit_post.html", post=post)


@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    # None members can't delete a post
    if "username" not in session:
        flash("A post can only be deleted by it's creator")
        return redirect(url_for("home"))
    mongo.db.posts.remove({"_id": ObjectId(post_id)})
    flash("Post Deleted!")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
