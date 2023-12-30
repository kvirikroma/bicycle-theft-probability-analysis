from random import shuffle


class ReprMixin:
    def __str__(self):
        arguments = ', '.join(f'{arg_name}={getattr(self, arg_name)}' for arg_name in self.__dict__)
        return f"{type(self).__name__}({arguments})"

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
