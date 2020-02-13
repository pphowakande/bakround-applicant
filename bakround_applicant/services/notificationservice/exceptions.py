__author__ = "natesymer"

# Exceptions thrown by the notificationservice

class UnspecifiedRecipientException(Exception):
    pass

class EmailNotFoundException(Exception):
    def __init__(self, message, profile_id):
        super().__init__(message)
        self.profile_id = profile_id

class UnverifiedNameException(Exception):
    def __init__(self, message, profile_id):
        super().__init__(message)
        self.profile_id = profile_id

