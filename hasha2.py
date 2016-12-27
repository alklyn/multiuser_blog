import random
import string
import hashlib
import hmac


def hash_str(s, secret):
    """ Return hash of string """
    return hmac.new(secret, s).hexdigest()

def make_secure_val(s, secret):
    """
    Make a hash of the number of visits
    My code didn't work when I used a comma between the hash & the value
    """
    return "{}_{}".format(s, hash_str(s, secret))

def check_secure_val(hashed_str, secret):
    """
    Check to see if hashed string, hashed_str is valid

    Input
    =====
    hashed_str: a string of the format s,HASH
    where s  is the original string & HASH is the hash of s

    secret: The secret used to hash s.

    Ouput
    =====
    s: If hashed_str is valid
    None: If hashed_str is not valid
    """

    print("test val = {}".format(h))
    if h:
        h_list = h.split("_")
        if len(h_list) == 2:
            value = h_list[0]
            hashed = h_list[1]
            if hash_str(value ,secret) == hashed:
                return value
    #I no return value is set None is returned


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
    Implement the function valid_pw() that returns True if a user's password
    matches its hash. You will need to modify make_pw_hash.

    """
    salt = h.split(",")[1]
    return h == make_pw_hash(name, pw, salt=salt)


h = make_pw_hash('spez', 'hunter2')
print valid_pw('spez', 'hunter3', h)
