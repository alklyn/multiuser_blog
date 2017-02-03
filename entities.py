"""
Contains entities used y the app.
"""
from google.appengine.ext import ndb

class User(ndb.Model):
    """
    Entity for storing user details.
    """
    username = ndb.StringProperty(required=True)
    pw_hash = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=False)
    joined = ndb.DateTimeProperty(auto_now_add=True)

def fetch_data(username):
    """Fetch data from db """
    query = """
         SELECT * FROM User WHERE username = '{}'
    """.format(username)
    return ndb.GqlQuery(query)


class Blog(ndb.Model):
    """
    Create entity for storing blog posts.
    """
    posted_by = ndb.IntegerProperty(required=True)
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    num_likes = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

    def get_poster(self):
        """
        Get the username of the user that created post.
        """
        return User.get_by_id(self.posted_by).username

    def get_posts(self):
        """
        Get all the posts
        """
        return self.query()


class Likes(ndb.Model):
    """
    Create entity for saving likes for posts.
    """
    liked_by = ndb.IntegerProperty(required=True)
    post_id = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)


class Comment(ndb.Model):
    """
    Entity for saving comments.
    """
    #The id of the post commented on
    comment = ndb.TextProperty(required=True)
    post_id = ndb.IntegerProperty(required=True)
    commented_by = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
