import re


class Validation:
    FORBIDDEN_DOMAIN_ZONES = {'ru', 'by'}

    @staticmethod
    def is_valid_string(s, pattern):
        return isinstance(s, str) and bool(re.fullmatch(pattern, s))

    @staticmethod
    def is_valid_email(s):
        pattern = r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
        return Validation.is_valid_string(s, pattern)

    @staticmethod
    def is_valid_email_domain(domain):
        zones = set(domain.split('.'))
        if len(Validation.FORBIDDEN_DOMAIN_ZONES.intersection(zones)) > 0:
            return False
        return True

    @staticmethod
    def is_valid_password(s):
        pattern = r'[A-Za-z0-9@#$%^&+=]{8,32}'
        return Validation.is_valid_string(s, pattern)

    @staticmethod
    def is_valid_username(s):
        pattern = r'[a-zA-Z0-9_]{5,25}'
        return Validation.is_valid_string(s, pattern)
        