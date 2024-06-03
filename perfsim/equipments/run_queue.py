#  Copyright (C) 2020 Michel Gokan Khan
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#  This file is a part of the PerfSim project, which is now open source and available under the GPLv2.
#  Written by Michel Gokan Khan, February 2020


from typing import TYPE_CHECKING, List, Dict

from sortedcontainers import SortedDict

from perfsim import ReplicaThread, ThreadSet

if TYPE_CHECKING:
    from perfsim import Core


class RunQueue:
    """
    RunQueue is a queue of ReplicaThreads.
    """

    #: List of ReplicaThreads
    rq: list[ReplicaThread]

    #: The list of active ReplicaThreads
    active_threads: set[ReplicaThread]

    #: All active best effort threads
    best_effort_active_threads: ThreadSet[ReplicaThread]

    #: All active guaranteed threads
    guaranteed_active_threads: ThreadSet[ReplicaThread]

    #: All active burstable threads
    burstable_active_threads: ThreadSet[ReplicaThread]

    #: All active burstable threads that do not have a limit
    burstable_unlimited_active_threads: ThreadSet[ReplicaThread]

    #: All active burstable threads that have a limit
    burstable_limited_active_threads: ThreadSet[ReplicaThread]

    #: The core that this RunQueue belongs to
    core: 'Core'

    #: The total load of the threads in the run queue
    _load: int

    """ 
    Storing the lightest threads in the runqueue with their load (as the key) and the SortedDict of threads (as the
    value). In the value part (which is a SortedDoct), the key is the vruntime of the thread, and the value is the
    set of threads having that vruntime.
    Because at the end of the day we are using a set, we may still end up having random order of threads with the same
    vruntime. Even though we are only interested in the lightest threads in the run queue, this might affect the
    consistency of the result, as threads with the same load and vruntime might have different number of remaining
    instructions, so the order of the threads might affect the result.
    """
    lightest_threads_in_rq: SortedDict[int, SortedDict[float, set[ReplicaThread]]]

    #: The total number of the best effort threads in the run queue
    _total_best_effort_threads: int

    #: The remaining millicores that can be allocated to threads in the run queue
    _remaining_millicores: int

    #: The total number of the threads in the run queue
    thread_set_dict: Dict[str, set[ThreadSet]]

    def __init__(self, core: 'Core') -> None:
        self.rq = []
        self.lightest_threads_in_rq = SortedDict()
        self._load = 0
        # self.__time = 0
        self.nr = 0
        # self.threads_df = pd.DataFrame(columns=[str(_thread.pid) + str(_thread.id) for _thread in threads])
        self.threads_total_time = {"idle": {}}
        self.core = core
        self.active_threads = set()
        self.best_effort_active_threads = ThreadSet(type_of_set=0)
        self.guaranteed_active_threads = ThreadSet(type_of_set=1)
        self.burstable_active_threads = ThreadSet(type_of_set=2)
        self.burstable_unlimited_active_threads = ThreadSet(type_of_set=3)
        self.burstable_limited_active_threads = ThreadSet(type_of_set=4)
        self._remaining_millicores = self.core.cpu.max_cpu_requests
        self.thread_set_dict = {}

    def reinit(self):
        """
        Reinitialize the run queue.

        :return:
        """

        self.__init__(self.core)

    def requeue_task(self, thread: ReplicaThread) -> None:
        """
        Requeue a thread in the run queue.

        :param thread:
        :return:
        """

        self.dequeue_task_by_thread(thread=thread, load_balance=False)
        self.enqueue_task(thread=thread, load_balance=True)

    @staticmethod
    def __calc_buckets_limits(bucket_limits, fair_share):
        """
        Calculate the bucket limits.

        :param bucket_limits:
        :param fair_share:
        :return:
        """

        _limited_buckets = [b for b in bucket_limits if b is not None and b <= fair_share]
        limited_bucket_count = len(_limited_buckets)
        unlimited_bucket_count = len(bucket_limits) - limited_bucket_count

        return _limited_buckets, limited_bucket_count, unlimited_bucket_count

    @staticmethod
    def __validate_thread_on_rq(thread: ReplicaThread) -> None:
        """
        Validate if the thread is on the run queue.

        :param thread:
        :return:
        """

        if not thread.on_rq:
            raise Exception("How come thread is not in the rq?!")

    def _reset_sum_of_shares_in_sets(self):
        """
        Reset the sum of shares in the sets, i.e., best effort, guaranteed, burstable, burstable unlimited, and
        burstable limited.

        :return:
        """

        self.best_effort_active_threads.sum_cpu_requests = 0
        self.guaranteed_active_threads.sum_cpu_requests = 0
        self.burstable_active_threads.sum_cpu_requests = 0
        self.burstable_unlimited_active_threads.sum_cpu_requests = 0
        self.burstable_limited_active_threads.sum_cpu_requests = 0

    def recalculate_cpu_requests_shares(self) -> None:
        """
        Recalculate the CPU requests shares.

        :return:
        """

        if len(self.active_threads) <= 0:
            return

        self._remaining_millicores = self.core.cpu.max_cpu_requests
        # self._reset_sum_of_shares_in_sets()

        # Even if the thread load goes above a thousand here, it won't be alongside best efforts.
        for thread in self.guaranteed_active_threads:
            self.assign_cpu_requests_share(thread=thread, cpu_requests=thread.process.get_cpu_request_per_thread())

        for thread in self.burstable_active_threads:
            self.assign_cpu_requests_share(thread=thread, cpu_requests=thread.process.get_cpu_request_per_thread())

        self._remaining_millicores -= self.guaranteed_active_threads.sum_cpu_requests + \
                                      self.burstable_active_threads.sum_cpu_requests

        for thread in self.burstable_unlimited_active_threads:
            cpu_req_ratio = thread.process.get_cpu_request_per_thread() / self.burstable_active_threads.sum_cpu_requests
            share = self._remaining_millicores * cpu_req_ratio
            self.assign_cpu_requests_share(thread, thread.cpu_requests_share + share)

        self._remaining_millicores -= self.burstable_unlimited_active_threads.sum_cpu_requests

        if self._remaining_millicores > 0 and len(self.best_effort_active_threads) > 0:
            _fair_share_be = self._remaining_millicores / len(self.best_effort_active_threads)

            for thread in self.best_effort_active_threads:
                self.assign_cpu_requests_share(thread, _fair_share_be)

            self._remaining_millicores -= _fair_share_be * len(self.best_effort_active_threads)

    def run_idle(self, duration: int) -> None:
        """
        Run the idle threads for the given duration.

        :param duration:
        :return:
        """

        try:
            self.threads_total_time["idle"][int(self.core.cpu.host.cluster.sim.time)] = int(duration)
        except OverflowError:
            try:
                self.threads_total_time["idle"][float('inf')] = int(duration)
            except OverflowError:
                self.threads_total_time["idle"][float('inf')] = float('inf')

    # from fair.c
    # /*
    #  * The idea is to set a period in which each task runs once.
    #  *
    #  * When there are too many tasks (sched_nr_latency) we have to stretch
    #  * this period because otherwise the slices get too small.
    #  *
    #  * p = (nr <= nl) ? l : l*nr/nl
    #  */
    # def sched_period(self, nr_running: int) -> int:
    #     nr_latency = self.core.cpu.host.sched_latency_ns / self.core.cpu.host.sched_min_granularity_ns
    #
    #     if nr_running > nr_latency:
    #         return nr_running * self.core.cpu.host.sched_min_granularity_ns
    #     else:
    #         return self.core.cpu.host.sched_latency_ns

    def assign_cpu_requests_share(self, thread: ReplicaThread, cpu_requests: float) -> None:
        """
        Assign the CPU requests share to the thread.

        :param thread:
        :param cpu_requests:
        :return:
        """

        if cpu_requests is None:
            raise Exception("CPU requests cannot be None")

        self.__validate_thread_on_rq(thread)

        if cpu_requests <= self.core.cpu.max_cpu_requests:
            thread.cpu_requests_share = cpu_requests
        else:
            thread.cpu_requests_share = self.core.cpu.max_cpu_requests

    def categorize_thread_into_sets(self, thread: ReplicaThread) -> None:
        """
        Categorize the thread into the sets, i.e., best effort, guaranteed, burstable, burstable unlimited, and
        burstable limited.

        :param thread:
        :return:
        """

        if thread.process.ms_replica.microservice.is_best_effort():
            self.best_effort_active_threads.add(thread)
        elif thread.process.ms_replica.microservice.is_guaranteed():
            self.guaranteed_active_threads.add(thread)
        elif thread.process.ms_replica.microservice.is_burstable():
            self.burstable_active_threads.add(thread)
            if thread.process.ms_replica.microservice.is_unlimited_burstable():
                self.burstable_unlimited_active_threads.add(thread)
            else:
                self.burstable_limited_active_threads.add(thread)
        else:
            raise Exception("Unknown thread type")

    def decategorize_thread_from_sets(self, thread: ReplicaThread) -> None:
        """
        Decategorize the thread from the sets, i.e., best effort, guaranteed, burstable, burstable unlimited, and
        burstable limited.

        :param thread:
        :return:
        """

        if thread.process.ms_replica.microservice.is_best_effort():
            self.best_effort_active_threads.remove(thread)
        elif thread.process.ms_replica.microservice.is_guaranteed():
            self.guaranteed_active_threads.remove(thread)
        elif thread.process.ms_replica.microservice.is_burstable():
            self.burstable_active_threads.remove(thread)
            if thread.process.ms_replica.microservice.is_unlimited_burstable():
                self.burstable_unlimited_active_threads.remove(thread)
            else:
                self.burstable_limited_active_threads.remove(thread)
        else:
            raise Exception("Unknown thread type")

    def enqueue_task(self, thread: ReplicaThread, load_balance: bool = False) -> None:
        """
        Enqueue a thread in the run queue.

        :param thread:
        :param load_balance:
        :return:
        """

        if thread.core is not None:
            raise Exception("Error: ReplicaThread already belongs to a core/runqueue")

        # thread.vruntime = self.rq[0].vruntime if len(self.rq) != 0 else 0
        if thread.instructions <= 0:
            raise Exception("Why on earth a zombie thread is enqueuing on a rq?")

        thread.core = self.core
        self.rq.append(thread)
        self.active_threads.add(thread)
        self.nr += 1
        self.core.cpu.host.cluster.cluster_scheduler.active_threads.add(thread)
        self.categorize_thread_into_sets(thread)

        if thread.on_rq:
            self.load += thread.average_load * thread.load
            self.assign_cpu_requests_share(thread, thread.process.get_cpu_request_per_thread())
        else:
            raise Exception("How come a thread with on_rq==False attempts to get enqueued?")

        df_column_name = str(thread.id)

        if df_column_name not in self.threads_total_time:
            self.threads_total_time[df_column_name] = {0: int(0)}

        if self.core.cpu.host.cluster.sim.log_timeline:
            self.core.cpu.host.timeline_event.append("enq " + df_column_name + " on " + str(self.core.cpu.name))
            self.core.cpu.host.timeline_time.append(str(round(float(self.core.cpu.host.cluster.sim.time), 5)))

        self.core.cpu.host.threads.add(thread)

        if len(self.core.cpu.host.threads) < 2:
            # Activating host " + str(self.core.cpu.host) + " while adding thread " + str(_thread.id)
            self.core.cpu.host.cluster.cluster_scheduler.active_hosts.add(self.core.cpu.host)
        if not self.core.cpu.host.load_balancing_needed:
            # Forcing host " + str(self.core.cpu.host) + " to load balance while adding thread " + str(_thread.id)
            self.core.cpu.host.cluster.cluster_scheduler.hosts_need_load_balancing.add(self.core.cpu.host)
            self.core.cpu.host.load_balancing_needed = True

        self.core.cpu.add_to_threads_sorted(thread=thread, inverted_thread_load=thread.load * -1)
        self.core.cpu.update_idle_pairs(core=self.core)

        if load_balance:
            self.core.cpu.load_balance()

    def enqueue_tasks(self, threads: List[ReplicaThread], load_balance: bool = False) -> None:
        """
        Enqueue a list of threads in the run queue at once.

        :param threads:
        :param load_balance:
        :return:
        """

        for _thread in threads:
            self.enqueue_task(_thread, load_balance=False)

        if load_balance:
            self.core.cpu.load_balance()

    def remove_from_lightest_threads_in_rq(self, thread):
        """
        Remove the thread from the lightest threads in the run queue.

        :param thread:
        :return:
        """

        if thread.load in self.lightest_threads_in_rq:
            if thread.vruntime in self.lightest_threads_in_rq[thread.load]:
                self.lightest_threads_in_rq[thread.load][thread.vruntime].discard(thread)
                if len(self.lightest_threads_in_rq[thread.load][thread.vruntime]) == 0:
                    del self.lightest_threads_in_rq[thread.load][thread.vruntime]
                    if len(self.lightest_threads_in_rq[thread.load]) == 0:
                        del self.lightest_threads_in_rq[thread.load]

    def add_to_lightest_threads_in_rq(self, thread: ReplicaThread):
        """
        Add the thread to the lightest threads in the run queue.

        :param thread:
        :return:
        """

        if thread.load in self.lightest_threads_in_rq:
            if thread.vruntime in self.lightest_threads_in_rq[thread.load]:
                self.lightest_threads_in_rq[thread.load][thread.vruntime].add(thread)
            else:
                self.lightest_threads_in_rq[thread.load][thread.vruntime] = {thread}
        else:
            self.lightest_threads_in_rq[thread.load] = SortedDict({thread.vruntime: {thread}})

    def dequeue_task_by_thread(self, thread: ReplicaThread, load_balance: bool = False) -> None:
        """
        Dequeue a thread from the run queue by the thread.

        :param thread:
        :param load_balance:
        :return:
        """

        if not thread.on_rq:
            raise Exception("How come a thread with on_rq==False attempts to get dequeued?")

        _index = self.rq.index(thread)
        del self.rq[_index]
        self.active_threads.remove(thread)
        self.remove_from_lightest_threads_in_rq(thread=thread)
        self.nr -= 1

        self.decategorize_thread_from_sets(thread)

        thread.core = None
        self.load -= thread.average_load * thread.load

        df_col_name = str(thread.process.pname) + "_" + str(thread.id) + "_" + str(
            int(thread.process.original_cpu_requests_share))
        if self.core.cpu.host.cluster.sim.time != 0:
            if self.core.cpu.host.cluster.sim.log_timeline:
                self.core.cpu.host.timeline_event.append("deq " + df_col_name + " from " + str(self.core.name))
                self.core.cpu.host.timeline_time.append(str(round(float(self.core.cpu.host.cluster.sim.time), 5)))

        if load_balance:
            self.core.cpu.load_balance()

        self.core.cpu.update_idle_pairs(core=self.core)

    # @overload
    # def dequeue_task(self, _thread: int) -> ReplicaThread:
    def dequeue_task_by_thread_index(self, thread: int, load_balance: bool = False) -> ReplicaThread:
        """
        Dequeue a thread from the run queue by the thread index in the run queue.

        :param thread:
        :param load_balance:
        :return:
        """

        t = self.rq[thread]
        self.dequeue_task_by_thread(t, load_balance)
        return t

    @property
    def load(self) -> int:
        """
        Get the load of the run queue.

        :return:
        """

        return self._load

    @load.setter
    def load(self, v: int):
        """
        Set the load of the run queue.

        :param v:
        :return:
        """

        if self._load != v:
            self.core.cpu.remove_from_pairs_sorted(pair_id=self.core.pair_id,
                                                   inverted_pair_load=self.core.cpu.pairs_load[self.core.pair_id] * -1)
            self._load = v
            other_id = self.core.cpu.get_the_other_core_in_pair(core_id=self.core.id_in_cpu)
            if other_id is not None:
                other = self.core.cpu.cores[other_id]
                self.core.cpu.pairs_load[self.core.pair_id] = other.runqueue.load + v
            else:
                self.core.cpu.pairs_load[self.core.pair_id] = v

            self.core.cpu.add_to_pairs_sorted(pair_id=self.core.pair_id,
                                              inverted_pair_load=self.core.cpu.pairs_load[self.core.pair_id] * -1)

    def __lt__(self, other):
        """
        Compare the run queue with another run queue (less than).

        :param other:
        :return:
        """

        if isinstance(other, RunQueue):
            return self.load < other.load

    def __gt__(self, other):
        """
        Compare the run queue with another run queue (greater than).
        :param other:
        :return:
        """

        if isinstance(other, RunQueue):
            return self.load > other.load

    def __le__(self, other):
        """
        Compare the run queue with another run queue (less than or equal to).

        :param other:
        :return:
        """

        if isinstance(other, RunQueue):
            return self.load == other.load or self < other

    def __ge__(self, other):
        """
        Compare the run queue with another run queue (greater than or equal to).

        :param other:
        :return:
        """

        if isinstance(other, RunQueue):
            return self.load == other.load or self > other
