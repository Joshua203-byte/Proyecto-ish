from celery import Celery

app = Celery("test", broker="redis://localhost:6379/0")
app.conf.task_always_eager = True

@app.task
def hello():
    return "world"

try:
    print("Testing task execution...")
    result = hello.delay()
    print(f"Result: {result.get()}")
except Exception as e:
    print(f"Failed: {e}")
