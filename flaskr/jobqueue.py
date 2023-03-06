import threading
from time import sleep


class Job:
    def __init__(self, task, args):
        self.task = task
        self.args = args
        self.lock = threading.Lock()
        self._is_finished = False
        self._result = None
        self._success = False
        self.__result = None
        self._thread = threading.Thread(target=self.worker_thread)
        self._thread.daemon = True
        self._exception = None

    def worker_thread(self):
        try:
            self.__result = self.task(*self.args)
        except Exception as ex:
            self._exception = ex

    def execute(self):
        self._thread.start()

    def update(self):
        if not self._thread.is_alive():
            if self._exception:
                result = self._exception.__str__()
                success = False
            else:
                result = self.__result
                success = True

            self.lock.acquire()
            self._result = result
            self._is_finished = True
            self._success = success
            self.lock.release()

    def is_finished(self):
        self.lock.acquire()
        finished = self._is_finished
        self.lock.release()
        return finished

    def result(self):
        self.lock.acquire()
        result = self._result
        self.lock.release()
        return result

    def success(self):
        self.lock.acquire()
        success = self._success
        self.lock.release()
        return success


class JobQueue:
    def __init__(self, processes: int=8,
                 max_size: int=0,
                 thread_sleep_millis: int=10):
        self._processes = processes
        self._wait_queue = []
        self._queue = []
        self._worker_thread = threading.Thread(target=self.run)
        self._worker_thread.daemon = True
        self._run = True
        self._thread_sleep_seconds = thread_sleep_millis / 1000
        self._max_size = max_size
        self._lock = threading.Lock()
        self._worker_thread.start()

    def run(self):
        while self._run:
            self._lock.acquire()
            while len(self._queue) < self._processes and len(self._wait_queue) > 0:
                job = self._wait_queue.pop(0)
                job.execute()
                self._queue.append(job)
            self._lock.release()

            jobs_to_remove = []
            for job in self._queue:
                job.update()
                if job.is_finished():
                    jobs_to_remove.append(job)

            for job in jobs_to_remove:
                self._queue.remove(job)

            sleep(self._thread_sleep_seconds)
            pass

    def queue(self, task, *args):
        if self._max_size > 0:
            if self.wait_queue_size() >= self._max_size:
                raise Exception('job queue size exceeded!')

        job = Job(task=task, args=args)
        self._lock.acquire()
        self._wait_queue.append(job)
        self._lock.release()
        return job

    def wait_queue_size(self):
        self._lock.acquire()
        size = len(self._wait_queue)
        self._lock.release()
        return size