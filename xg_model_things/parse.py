from boxcars_py import parse_replay

def parse(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        buf = f.read()
    replay = parse_replay(buf)
    return replay

def test():
    parse(r'C:\Users\Simcha\Documents\My Games\Rocket League\TAGame\Demos\CA6509C8416BF65001C3A99F3501B356.replay')

if __name__ == "__main__":
    import timeit
    num = 10
    print(timeit.timeit(stmt=test, number=num) / num)