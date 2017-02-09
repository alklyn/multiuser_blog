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
from entities import *
import re


USER_RE =  re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE =  re.compile(r"^.{8,20}$")
EMAIL_RE =  re.compile(r"^[\S]+@[\S]+.[\S]+$")
BLOG_NAME = "Some Random Blog"


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = \
    jinja2.Environment(
    loader = jinja2.FileSystemLoader(
        template_dir), autoescape=True)

SECRET = "ma7aK0Ay3HuRud@K0r!y3RiN0taP1rawHoor3P!x1M@gar0"

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

    def is_logged_in(self):
        """
        Check whether the user is logged in. If the user is logged in serve
        them the requested page otherwise redirect to signup page.
        """
        user = self.get_user_from_cookie()

        if user:
            return True
        else:
            return False

    def go_to_requested_page(self, requested_page, **params):
        self.render(
        requested_page,
        params=params)


class Signup(Handler):
    """
    Take care of user signup.
    """
    def get(self):
        """
        Handle GET requests
        """
        params = {
                  "header": "Signup",
                  "errors": {}}
        self.go_to_requested_page("signup.html", **params)

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
        params = {
            "username": self.request.get("username"),
            "password": self.request.get("password"),
            "verify": self.request.get("verify"),
            "email": self.request.get("email"),
            "errors": {}
        }

        errors = self.validate(params)
        if len(errors.keys()):
            params["header"] = "Signup"
            params["errors"] = errors
            self.go_to_requested_page("signup.html", **params)
        else:
            userid = self.create_user(params)
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

        return user.key.id() #return userid

    def check_if_user_exists(self, username):
        """
        Check if someone is already using the username.
        """
        if get_user(username):
            return True
        return False


class Login(Handler):
    """ Handles user logins """
    def get(self):
        params = {
                  "title": "Login",
                  "header": "Login",
                  "username": ""}
        self.go_to_requested_page("login.html", **params)

    def post(self):
        """POST handler"""
        params = {
                  "title": "Login",
                  "header": "Login",
                  "username": self.request.get("username"),
                  "password": self.request.get("password")
                  }

        userid = self.validate_login(params)
        if userid:
            self.login_user(userid)
        else:
            params["error"] = "Invalid login."
            self.go_to_requested_page("login.html", **params)

    def validate_login(self, fields):
        """
        Test if login is valid.
        If the login is valid return userid
        """
        user = get_user(fields["username"])
        if user:
            if valid_pw(fields["username"], fields["password"], user.pw_hash):
                return user.key.id()


class Logout(Handler):
    """
    Handle user logout
    """
    def get(self):
        fields = {}
        self.response.delete_cookie('userid')
        self.redirect("/blog/signup")


class Welcome(Handler):
    """
    Display greeting.
    """
    def get(self):
        """
        Display welcome page after successful login.
        """
        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/signup")
        else:
            params = {
                "is_logged_in": self.is_logged_in(),
                "header": "Welcome {}!".format(user.username)
            }
            self.go_to_requested_page("welcome.html", **params)


class DeleteSuccessful(Handler):
    """
    Display message on successful deletion of post.
    """
    def get(self):
        """
        Handle GET requests.
        """
        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/signup")
        else:
            params = {
                "is_logged_in": self.is_logged_in(),
                "header": "Post successfully deleted!"
            }
            self.go_to_requested_page("delete_successful.html", **params)


class BlogPage(Handler):
    """
    Page for displaying posts.
    """
    def render_blog(self):
        blog_posts = Blog.query().order(-Blog.created)
        user = self.get_user_from_cookie()

        params = {
            "is_logged_in": self.is_logged_in(),
            "header": BLOG_NAME,
            "blog_posts": blog_posts,
            "show_edit": False}
        self.go_to_requested_page("blog.html", **params)

    def get(self):
        self.render_blog()


class CreateOrEditPost(Handler):
    """
    Base class for creating or editing posts.
    """
    def get(self, page, **params):
        """
        Handle GET requests
        """
        params["is_logged_in"] = self.is_logged_in()
        if params["edit_mode"]:
            blog_post = self.get_post_from_cookie()
        else:
            blog_post = None

        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/signup")
        else:
            params["blog_post"] = blog_post
            self.go_to_requested_page(page, **params)

    def post(self, page, **params):
        """
        Handle POST requests.
        """
        print("params: {}".format(params))
        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/signup")

        if self.request.get("choice") == "submit":
            params["subject"] = self.request.get("subject")
            params["content"] = self.request.get("content")

            if params["subject"] and params["content"]:
                self.create_or_edit(user, **params)
            else:
                params["error"] = "Subject and content please."
                self.go_to_requested_page(page, **params)
        else:
            self.cancel(**params)


    def cancel(self, **params):
        """
        Cancel creation of new post or cancel an edit.
        """
        if params["edit_mode"]:
            blog = self.get_post_from_cookie()
            self.redirect("/blog/{}".format(blog.key.id()))
        else:
            self.redirect("/blog/")

    def create_or_edit(self, user, **params):
        """
        Creates a new post or edits an existing one.
        """
        if params["edit_mode"]:
            blog = self.get_post_from_cookie()
            blog.subject = params["subject"]
            blog.content = params["content"]
        else:
            blog = Blog(
                subject=params["subject"],
                content=params["content"],
                posted_by=user.key.id(),
                num_likes=0)

        blog.put()  # Store the entity in the database
        self.redirect("/blog/{}".format(blog.key.id()))


class NewPost(CreateOrEditPost):
    """
    Handler for newpost page.
    """
    def get(self):
        super(NewPost, self).get(
                                "newpost.html",
                                title="New Post",
                                header="New Post",
                                edit_mode=False)

    def post(self):
        super(NewPost, self).post("newpost.html", edit_mode=False)


class UpdatePost(CreateOrEditPost):
    """
    Handler for updatepost page.
    """
    def get(self):
        super(UpdatePost, self).get(
                                "updatepost.html",
                                title="Update Post",
                                header="Update Post",
                                edit_mode=True)

    def post(self):
        super(UpdatePost, self).post("updatepost.html", edit_mode=True)


class SelectedPost(Handler):
    """
    Display selected post or display latest post.
    """

    def render_selected_post(self, post_id, **params):
        """
        Display the post with the id "post_id"
        """
        post_id = int(post_id)

        params["is_logged_in"] = self.is_logged_in()
        params["header"] = BLOG_NAME
        params["show_edit"] = True
        params["blog_comments"] = get_comments(post_id)


        if Blog.get_by_id(int(post_id)):
            params["blog_posts"] = [Blog.get_by_id(int(post_id))]
        else:
            params["blog_posts"] = list()
        self.go_to_requested_page("blog.html", **params)

    def get(self, post_id):
        self.render_selected_post(post_id)

    def post(self, post_id):
        """
        Handle post requests
        """
        post_id = int(post_id)
        user = self.get_user_from_cookie()

        if not user:
            self.redirect("/blog/login")
        else:
            blog_post = Blog.get_by_id(int(post_id))
            userid = user.key.id()

            # Create cookie to keep track of the post we are editing/deleting.
            self.set_post_cookie(post_id)
            choice = self.request.get("choice")

            if choice == "edit_comment":
                self.edit_comment(userid, post_id)
            elif choice == "add_comment":
                self.add_comment(userid, post_id, blog_post)
            else:
                self.edit_or_delete(userid, post_id, choice, blog_post)

    def edit_comment(self, userid, post_id):
        """
        Edit comment.
        """
        comment_id = int(self.request.get("comment_id"))
        # self.response.write(comment_id)
        blog_comment = Comment.get_by_id(comment_id)
        if userid == blog_comment.posted_by:
            blog_comment.content = self.request.get("comment")
            blog_comment.put()
            # Use Post/Redirect/Get pattern to prevent repost.
            self.redirect("/blog/comment_added")
        else:
            comment_invalid_edit = comment_id
            self.render_selected_post(
                post_id,
                comment_invalid_edit=comment_invalid_edit)

    def add_comment(self, userid, post_id, blog_post):
        """
        Add comment to posts.
        """
        blog_comment = Comment(
            post_id=post_id,
            posted_by=userid,
            content=self.request.get("comment"))
        blog_comment.put()
        # Use Post/Redirect/Get pattern to prevent repost.
        self.redirect("/blog/comment_added")

    def edit_or_delete(self, userid, post_id, choice, blog_post):
        """
        Perform edits or deletes or addsremoves likes
        """
        # Check if user is the author of the post.
        if userid == blog_post.posted_by:
            if choice == "delete":
                blog_post.key.delete()
                self.delete_comments(post_id)
                self.redirect("/blog/delete_successful")
            elif choice == "edit":
                self.redirect("/blog/updatepost")
            elif choice == "like":
                self.render_selected_post(post_id, invalid_like=True)
        else:
            if choice == "like":
                self.like_unlike(post_id, userid)
            else:
                self.render_selected_post(post_id, invalid_edit=True)

    def delete_comments(self, post_id):
        """
        Delete all the comments for the post idetified by post_id.
        """
        comments = get_comments(post_id)
        list_of_keys = ndb.put_multi(comments)
        list_of_entities = ndb.get_multi(list_of_keys)
        ndb.delete_multi(list_of_keys)

    def like_unlike(self, post_id, liked_by):
        """
        Update the likes on the given post.
        """
        post_id = int(post_id)
        blog_post = Blog.get_by_id(int(post_id))
        like = get_like(post_id, liked_by)
        if like:
            like.key.delete()
            blog_post.num_likes -= 1
        else:
            like = Likes(post_id=post_id, liked_by=liked_by)
            like.put()
            blog_post.num_likes += 1

        blog_post.put()
        self.redirect("/blog/comment_added")

    def set_post_cookie(self, post_id):
        """
        Create cookie containing the id of the post to be edited.
        """
        new_cookie_val = make_secure_val(str(post_id), SECRET)
        self.response.headers.add_header(
            "Set-Cookie",
            "post_id={};Path=/".format(new_cookie_val))


class CommentAdded(Handler):
    """
    Display message on successful addition of comment.
    """
    def get(self):
        """
        Handle GET requests.
        """
        user = self.get_user_from_cookie()
        if not user:
            self.redirect("/blog/login")
        else:
            blog = self.get_post_from_cookie()
            params = {
                "is_logged_in": self.is_logged_in(),
                "header": "Comment successfully added!",
                "post_id": blog.key.id()}
            self.go_to_requested_page("comment_added.html", **params)


app = webapp2.WSGIApplication([
    ('/blog/signup', Signup),
    ('/blog/signup/', Signup),
    ('/blog/welcome', Welcome),
    ('/blog/login', Login),
    ('/blog/login/', Login),
    ('/blog/logout', Logout),
    ('/blog/logout/', Logout),
    ('/blog', BlogPage),
    ('/blog/', BlogPage),
    ('/blog/newpost', NewPost),
    ('/blog/updatepost', UpdatePost),
    ('/blog/([\d]*)', SelectedPost),
    ('/blog/delete_successful', DeleteSuccessful),
    ('/blog/comment_added', CommentAdded),
], debug=True)
