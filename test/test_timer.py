import time

from app.modules.automation.timer import Timer

if __name__ == '__main__':
    t = Timer(1, count=3).start()
    start_time = time.time()
    while 1:
        if t.reached():
            print("到达")
            break
    print(time.time() - start_time)