from random import shuffle


class ReprMixin:
    def __repr__(self):
        return str(self)


def distribute_randomly_between_users(data: list, num_of_users: int) -> list:
    users = []
    user_number = 0
    for i in range(len(data)):
        users.append(user_number)
        user_number += 1
        if user_number >= num_of_users:
            user_number = 0
    shuffle(users)
    return zip(data, users)
