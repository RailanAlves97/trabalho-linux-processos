import threading, time, os

def consome_cpu():
    while True:
        sum(i * i for i in range(100000))

threading.Thread(target=consome_cpu, daemon=True).start()

while True:
    print(f"[{time.strftime('%H:%M:%S')}] vivo, PID={os.getpid()}", flush=True)
    time.sleep(1)
