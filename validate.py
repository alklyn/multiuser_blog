""" Contains functions for validating stuff """
import re


user_re =  re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
pass_re =  re.compile(r"^.{3,20}$")
email_re =  re.compile(r"^[\S]+@[\S]+.[\S]+$")


def validate(fields):
    #dictionary to store error messages
    errors = {}

    if not user_re.match(fields["username"]):
        errors["username"] = "That's not a valid username."

    if fields["password"] == fields["verify"]:
        if not pass_re.match(fields["password"]):
            errors["password"] = "That's not a valid password."
    else:
        errors["verify"] = "Your passwords didn't match."


    if len(fields["email"]) > 0:
        if not email_re.match(fields["email"]):
            errors["email"] = "That's not a valid email."

    return errors
