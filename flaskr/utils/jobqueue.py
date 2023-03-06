import threading
from time import sleep


class Job:
    """
    Job contains a thread that encapsulates a task
    Call execute to start the thread
    Call update to update the job state
    Call result to get any result from the threaded task
    Job is made to work in tantrum with a JobQueue. A JobQueue manages a queue of Jobs
    """

    def __init__(self, task, args):
        """
        Constructs job encapsulating task which will be called with args
        :param task: the task
        :param args: the arguments
        """
        self.task = task
        self.args = args
        self.lock = threading.Lock()
        self._is_finished = False
        self._result = None
        self._success = False
        self.__result = None
        self._thread = threading.Thread(target=self.__worker_thread)
        self._thread.daemon = True
        self._exception = None

    def __worker_thread(self):
        """
        The worker thread, will set __result on success or _exception on failure
        """
        try:
            self.__result = self.task(*self.args)
        except Exception as ex:
            self._exception = ex

    def execute(self):
        """
        Starts the worker thread
        """
        self._thread.start()

    def update(self):
        """
        Updates job status, checks Thread status and will set result accordingly (if finished)
        """
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
        """
        Returns True if job is finished, thread-safe
        :return: True if job is finished
        """
        self.lock.acquire()
        finished = self._is_finished
        self.lock.release()
        return finished

    def result(self):
        """
        Returns Results from job, thread-safe
        :return: Results from job
        """
        self.lock.acquire()
        result = self._result
        self.lock.release()
        return result

    def success(self):
        """
        Returns True if job is finished successfully, thread-safe
        :return: True if job is finished successfully
        """
        self.lock.acquire()
        success = self._success
        self.lock.release()
        return success


class JobQueue:
    """
    The JobQueue manages jobs
    Jobs are started in order of which they are queued
    The job queue runs its own daemon thread, updating states of all jobs
    If max_size > 0 the wait queue cannot exceed this size. An exception will be raised when
    queue is called
    """

    def __init__(self, processes: int = 8,
                 max_size: int = 0,
                 thread_sleep_millis: int = 10):
        """
        Constructs a JobQueue and fires up a new thread which manages the jobs
        :param processes: maximum jobs running at once
        :param max_size: maximum size of the wait_queue, default = 0 meaning no limit
        :param thread_sleep_millis: the sleep time in milliseconds to wait after each run cycle
        """
        self._processes = processes
        self._wait_queue = []
        self._queue = []
        self._worker_thread = threading.Thread(target=self.__run)
        self._worker_thread.daemon = True
        self._run = True
        self._thread_sleep_seconds = thread_sleep_millis / 1000
        self._max_size = max_size
        self._lock = threading.Lock()
        self._worker_thread.start()

    def __run(self):
        """
        The worker thread, checks if new jobs are in the wait queue, and executes them if necessary
        """
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

    def queue(self, task, *args):
        """
        Creates a Job around a new task with optional arguments
        Raises an exception if the size of the wait queue exceeds the maximum size
        Thread-Safe method
        :param task: the task to execute
        :param args: the arguments
        :return: A Job encapsulating the task
        """
        if self._max_size > 0:
            if self.wait_queue_size() >= self._max_size:
                raise Exception('job wait queue size exceeded!')

        job = Job(task=task, args=args)
        self._lock.acquire()
        self._wait_queue.append(job)
        self._lock.release()
        return job

    def wait_queue_size(self):
        """
        Returns current wait queue size, thread-safe
        :return: current wait queue size
        """
        self._lock.acquire()
        size = len(self._wait_queue)
        self._lock.release()
        return size
