def menu(m: list):
    print("Choose an option")
    for i in range(len(m)):
        o = "{}. {}".format(i, m[i])
        print(o)


def message(e: str):
    print(e)


def error(e: str):
    l = "\033[93m"
    r = "\033[0m"
    print(l + e + r)
