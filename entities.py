"""
Contains entities used by the app.
"""
from google.appengine.ext import ndb

def get_comments(post_id):
    """
    Get comments for the post identified by post_id.
    """
    comments = Comment.query()
    comments = comments.filter(Comment.post_id == post_id)
    return comments


def get_likes(post_id):
    """
    Get likes for the post identified by post_id.
    """
    likes = Likes.query()
    likes = likes.filter(Likes.post_id == post_id)
    return likes.order(-Likes.created)


def get_like(post_id, liked_by):
    """
    Get the like added by user identified by liked_by to the post identified by
    post_id.
    """
    likes = Likes.query()
    likes = likes.filter(Likes.post_id == post_id, Likes.liked_by == liked_by)
    return likes.get()


def get_user(username):
    """
    Get user from their username
    """
    users = User.query()
    users = users.filter(User.username == username)
    return users.get()


class User(ndb.Model):
    """
    Entity for storing user details.
    """
    username = ndb.StringProperty(required=True)
    pw_hash = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=False)
    joined = ndb.DateTimeProperty(auto_now_add=True)


class MyModel(ndb.Model):
    def get_poster(self):
        """
        Get the username of the user that created post.
        """
        return User.get_by_id(self.posted_by).username

class Blog(MyModel):
    """
    Create entity for storing blog posts.
    """
    posted_by = ndb.IntegerProperty(required=True)
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    num_likes = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

    def get_posts(self):
        """
        Get all the posts
        """
        return self.query().order(-Comment.created)


class Likes(ndb.Model):
    """
    Create entity for saving likes for posts.
    """
    liked_by = ndb.IntegerProperty(required=True)
    post_id = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)


class Comment(MyModel):
    """
    Entity for saving comments.
    """
    #The id of the post commented on
    comment = ndb.TextProperty(required=True)
    post_id = ndb.IntegerProperty(required=True)
    posted_by = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
