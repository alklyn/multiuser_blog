import random
import string
import hashlib
import hmac


def hash_str(s, secret):
    """ Return hash of string """
    return hmac.new(secret, s).hexdigest()

def make_secure_val(my_str, secret):
    """
    Make a hash of the input string my_str.

    Output: A string in the form "my_str|hash_of-my_str"
    """
    return "{}|{}".format(my_str, hash_str(my_str, secret))

def check_secure_val(my_hash, secret):
    """
    Check to see if hashed string, my_hash is valid

    Input
    =====
    hashed_str: a string of the form "my_str,HASH"
    where my_str is the original string & HASH is the hash of my_str

    secret: The secret used to hash my_str.

    Ouput
    =====
    my_str: If hashed_str is valid
    None: If hashed_str is not valid
    """
    if my_hash:
        h_list = my_hash.split("|")
        if len(h_list) == 2:
            my_str = h_list[0]
            hashed = h_list[1]
            if hash_str(my_str ,secret) == hashed:
                return my_str


def make_salt():
    """ Generate a string of 8 random letters to use as a salt"""
    return "".join([random.choice(string.letters) for _ in xrange(8)])


def make_pw_hash(username, pssswd, **kw):
    """
    Create a hash of a password.

    Input
    =====
    username: username
    passwd: user's password.
    optional parameter: salt

    Output
    ======
    a hashed password
    of the format:
    HASH(name + passwd + salt),salt
    """
    if kw.get("salt"):
        salt = kw["salt"]
    else:
        salt = make_salt()

    return "{},{}".format(
        hashlib.sha512(username + pssswd + salt).hexdigest(), salt)


def valid_pw(name, pw, h):
    """
    Check if userame/password combination is valid.
    Returns True if a user's password matches its hash.

    """
    salt = h.split(",")[1]
    return h == make_pw_hash(name, pw, salt=salt)


h = make_pw_hash('spez', 'hunter2')
print valid_pw('spez', 'hunter3', h)
