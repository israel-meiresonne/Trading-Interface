from model.tools.Map import Map


def menu(mp: Map):
    msg = mp.get(Map.message)
    choices = mp.get(Map.response)
    message(msg)
    for i in range(len(choices)):
        o = "{}. {}".format(i, choices[i])
        print(o)


def message(e: str):
    print(e)


def error(e: str):
    l = "\033[93m"
    r = "\033[0m"
    print(l + e + r)
