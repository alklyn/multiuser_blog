"""
signup page
"""

import os
import jinja2
import webapp2
from validate import validate
from hasha2 import make_pw_hash
from hasha2 import valid_pw
from hasha2 import make_secure_val
from hasha2 import check_secure_val
from google.appengine.ext import db
import re


USER_RE =  re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE =  re.compile(r"^.{8,20}$")
EMAIL_RE =  re.compile(r"^[\S]+@[\S]+.[\S]+$")


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = \
    jinja2.Environment(
    loader = jinja2.FileSystemLoader(
        template_dir), autoescape=True)

SECRET = "ma7aK0Ay3HuRud@K0r!y3RiN0taP1rawHoor3P!x1M@gar0"

class User(db.Model):
    """
    Create entity called User.
    Entities are googles's equivalent to tables.
    """
    username = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    joined = db.DateTimeProperty(auto_now_add=True)

def fetch_data(username):
    """Fetch data from db """
    query = """
         SELECT * FROM User WHERE username = '{}'
    """.format(username)
    return db.GqlQuery(query)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class Signup(Handler):
    """
    Take care of user signup.
    """
    def get(self):
        fields = {}
        self.render("signup.html", fields=fields, errors={})

    def validate(self, fields):
        """
        Check if user input is valid
        """
        errors = {}

        if not USER_RE.match(fields["username"]):
            errors["username"] = "That's not a valid username."

        if fields["password"] == fields["verify"]:
            if not PASS_RE.match(fields["password"]):
                errors["password"] = "That's not a valid password."
        else:
            errors["verify"] = "Your passwords didn't match."

        if len(fields["email"]) > 0:
            if not EMAIL_RE.match(fields["email"]):
                errors["email"] = "That's not a valid email."
        return errors

    def post(self):
        """POST handler"""
        fields = {}
        fields["username"] = self.request.get("username")
        fields["password"] = self.request.get("password")
        fields["verify"] = self.request.get("verify")
        fields["email"] = self.request.get("email")

        errors = self.validate(fields)
        if len(errors.keys()):
            self.render("signup.html", fields=fields, errors=errors)
        elif self.check_if_user_exists(fields["username"]):
            errors["username"] = "That user already exists."
            self.render("signup.html", fields=fields, errors=errors)
        else:
            userid = self.create_user(fields)
            new_cookie_val = make_secure_val(str(userid), SECRET)
            self.response.headers.add_header(
                "Set-Cookie",
                "userid={};Path=/".format(new_cookie_val))
            self.redirect("/blog/welcome")

    def create_user(self, fields):
        """
        Create a new user in th database
        """
        # Create a new User object
        username = fields["username"]
        passwd = fields["password"]
        if fields.get("email"):
            email = fields["email"]

        pw_hash = make_pw_hash(username, passwd)
        user = User(username=username, pw_hash=pw_hash)
        user.put() # Save new user to db

        return user.key().id() #return userid

    def check_if_user_exists(self, username):
        """
        Check if someone is already using the name
        """
        query = """
             SELECT * FROM User WHERE username = '{}'
        """.format(username)
        cur = db.GqlQuery(query)
        user = cur.get()
        if user:
            if user.username == username:
                return True
        return False


class Login(Handler):
    """ Handles user logins """
    def get(self):
        fields = {}
        self.render("login.html", username="", error="")

    def post(self):
        """POST handler"""
        fields = {}
        fields["username"] = self.request.get("username")
        fields["password"] = self.request.get("password")

        userid = self.validate_login(fields)
        if userid:
            new_cookie_val = make_secure_val(str(userid), SECRET)
            self.response.headers.add_header(
                "Set-Cookie",
                "userid={};Path=/".format(new_cookie_val))
            self.redirect("/blog/welcome")

        error = "Invalid login."
        self.render("login.html", username=fields["username"], error=error)

    def validate_login(self, fields):
        """
        Test if login is valid.
        If the login is valid return userid
        """
        cur = fetch_data(fields["username"])
        user = cur.get()
        if user:
            if valid_pw(fields["username"], fields["password"], user.pw_hash):
                return user.key().id()


class Logout(Handler):
    """ Handles user logout """
    def get(self):
        fields = {}
        self.response.delete_cookie('userid')
        self.redirect("/blog/signup")


class Welcome(Handler):
    def get(self):
        user_cookie_val = self.request.cookies.get("userid")
        id_str = check_secure_val(user_cookie_val, SECRET)
        if id_str:
            user = User.get_by_id(int(id_str))
            self.render("welcome.html", username=user.username)
        else:
            self.redirect("/blog/signup")


class Blog(db.Model):
    """
    Create entity called content.
    Entities are googles's equivalent to tables.
    """
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class MainPage(Handler):
    def render_blog(self):
        blogs = Blog.all().order("-created")
        self.render("blog.html", blogs=blogs)

    def get(self):
        self.render_blog()


class NewPost(Handler):
    """
    Page for new posts
    """
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            # Create a new content object
            blog = Blog(subject=subject, content=content)
            blog.put()  # Store the content object in the database
            self.redirect("/blog/{}".format(blog.key().id()))
        else:
            error = "Subject and content please."
            self.render(
                "newpost.html",
                error=error,
                content=content,
                subject=subject)


class LastPost(Handler):
    """Display recently created post """
    def render_last_post(self, post_id):
        # query = """
        # SELECT * WHERE __key__ HAS ANCESTOR KEY(Blog, :post_id)
        # ORDER BY created DESC;
        # """
        # blogs = db.GqlQuery(query, post_id=post_id)
        # print("id = {}".format(blogs[0].key().id()))
        blogs = [Blog.get_by_id(int(post_id))]

        self.render("blog.html", blogs=blogs)

    def get(self, post_id):
        self.render_last_post(post_id)


app = webapp2.WSGIApplication([
    ('/blog/signup', Signup),
    ('/blog/welcome', Welcome),
    ('/blog/login', Login),
    ('/blog/logout', Logout),
    ('/blog', MainPage),
    ('/blog/newpost', NewPost),
    ('/blog/(.*)', LastPost)
], debug=True)
