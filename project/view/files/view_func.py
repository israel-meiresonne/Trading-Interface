from model.tools.Map import Map


def menu(mp: Map):
    msg = mp.get(Map.msg)
    cs = mp.get(Map.cs)
    print(msg)
    for i in range(len(cs)):
        o = "{}. {}".format(i, cs[i])
        print(o)


def message(e: str):
    print(e)


def error(e: str):
    l = "\033[93m"
    r = "\033[0m"
    print(l + e + r)
