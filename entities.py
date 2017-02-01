"""
Contains entities used y the app.
"""

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


class Likes(db.Model):
    """
    Create entity for saving likes for posts.
    """
    liked_by = db.IntegerProperty(required=True)
    post_id = db.IntegerProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class Blog(db.Model):
    """
    Create entity for storing blog posts.
    """
    posted_by = db.IntegerProperty(required=True)
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    num_likes = db.IntegerProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    def get_poster(self):
        """
        Get the username of the user that created post.
        """
        return User.get_by_id(self.posted_by).username
