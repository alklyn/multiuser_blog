"""
Simple blog app.
"""
import os
import jinja2
import webapp2
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
    Entity for storing user details.
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
    """
    Base class for all the app's request handlers
    """
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def login_user(self, userid):
        """
        Create cookie containing userid & redirect to welcome page
        """
        new_cookie_val = make_secure_val(str(userid), SECRET)
        self.response.headers.add_header(
            "Set-Cookie",
            "userid={};Path=/".format(new_cookie_val))
        self.redirect("/blog/welcome")

    def get_user_from_cookie(self):
        """
        Get user details based on user cookie.
        """
        user_cookie_val = self.request.cookies.get("userid")
        id_str = check_secure_val(user_cookie_val, SECRET)
        if id_str:
            user = User.get_by_id(int(id_str))
            return user

    def get_post_from_cookie(self):
        """
        Get blog post from post_id cookie.
        """
        post_cookie_val = self.request.cookies.get("post_id")
        id_str = check_secure_val(post_cookie_val, SECRET)
        if id_str:
            blog_post = Blog.get_by_id(int(id_str))
            return blog_post

    def is_logged_in(self, requested_page, **params):
        """
        Check whether the user is logged in. If the user is logged in serve
        them the requested page otherwise redirect to signup page.
        """
        user = self.get_user_from_cookie()

        if user:
            params["username"] = user.username
            self.render(
            "{}.html".format(requested_page),
            params=params)
        else:
            self.redirect("/blog/signup")


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
        elif self.check_if_user_exists(fields["username"]):
            errors["username"] = "That user already exists."
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
        else:
            userid = self.create_user(fields)
            new_cookie_val = make_secure_val(str(userid), SECRET)
            self.login_user(userid)

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
            self.login_user(userid)

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
        self.is_logged_in("welcome")


class Blog(db.Model):
    """
    Create entity called blog.
    """
    posted_by = db.IntegerProperty(required=True)
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    def get_poster(self):
        """
        Get the username of the user that created post.
        """
        return User.get_by_id(self.posted_by).username


class BlogPage(Handler):
    """
    Page for displaying posts.
    """
    def render_blog(self):
        blog_posts = Blog.all().order("-created")
        self.is_logged_in("blog", blog_posts=blog_posts, show_edit=False)

    def get(self):
        self.render_blog()


class BlogPost(Handler):
    """
    Base class for creating or editing posts.
    """
    def get(self, page="newpost", edit_mode=False):
        """
        Handle GET requests
        """
        if edit_mode:
            blog_post = self.get_post_from_cookie()
        else:
            blog_post = None

        self.is_logged_in(page, blog_post=blog_post)

    def post(self, edit_mode=False):
        """
        Handle POST requests.
        """
        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/signup")

        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            # Create a new Blog object
            if edit_mode:
                blog = self.get_post_from_cookie()
                blog.subject = subject
                blog.content = content
            else:
                blog = Blog(
                    subject=subject,
                    content=content,
                    posted_by=user.key().id())

            blog.put()  # Store the content object in the database
            self.redirect("/blog/{}".format(blog.key().id()))
        else:
            error = "Subject and content please."
            self.render(
                "{}.html".format(page),
                error=error,
                content=content,
                subject=subject)


class NewPost(BlogPost):
    """
    Handler for newpost page.
    """
    def get(self):
        super(NewPost, self).get()

    def post(self):
        super(NewPost, self).post()


class UpdatePost(BlogPost):
    """
    Handler for updatepost page.
    """
    def get(self):
        super(UpdatePost, self).get(page="updatepost", edit_mode=True)

    def post(self):
        super(UpdatePost, self).post(edit_mode=True)


class SelectedPost(Handler):
    """Display selected post or display latest post."""
    def render_selected_post(self, post_id, **params):
        blog_posts = [Blog.get_by_id(int(post_id))]
        params["blog_posts"] = blog_posts
        params["show_edit"] = True
        self.render("blog.html", params=params)

    def get(self, post_id):
        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/signup")
        self.render_selected_post(post_id)

    def post(self, post_id):
        """
        Handle post requests
        """
        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/login")

        blog_post = Blog.get_by_id(int(post_id))

        # Check if user is the author of the post.
        if user.key().id() == blog_post.posted_by:
            self.set_post_cookie(post_id)
            self.redirect("/blog/updatepost")
        else:
            self.render_selected_post(post_id, invalid_edit=True)



    def set_post_cookie(self, post_id):
        """
        Create cookie containing the id of the post to be edited.
        """
        new_cookie_val = make_secure_val(str(post_id), SECRET)
        self.response.headers.add_header(
            "Set-Cookie",
            "post_id={};Path=/".format(new_cookie_val))

app = webapp2.WSGIApplication([
    ('/blog/signup', Signup),
    ('/blog/welcome', Welcome),
    ('/blog/login', Login),
    ('/blog/logout', Logout),
    ('/blog', BlogPage),
    ('/blog/', BlogPage),
    ('/blog/newpost', NewPost),
    ('/blog/updatepost', UpdatePost),
    ('/blog/(.*)', SelectedPost)
], debug=True)
