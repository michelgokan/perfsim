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

from typing import Union, TYPE_CHECKING

from perfsim import LogObserver, Event

if TYPE_CHECKING:
    from perfsim import Cluster, Host, ReplicaThread, Request


class ClusterLogObserver(LogObserver):
    """
    This class is responsible for logging the events of the cluster.
    """

    def __init__(self, cluster: 'Cluster'):
        super().__init__(name="ClusterLogObserver", subject=cluster, logger=cluster.sim.logger)

    @Event
    def after_finish_running_threads_on_a_host(self,
                                               host: 'Host',
                                               completed_threads_on_host: int,
                                               completed_threads_on_all_hosts: int):
        """
        Log the completion of threads on a host.

        :param host:
        :param completed_threads_on_host:
        :param completed_threads_on_all_hosts:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log("  ** Completed execution of " + str(completed_threads_on_host) +
                            " threads on host " + str(host) + " - Total completed" +
                            " threads = " + str(completed_threads_on_all_hosts), 3)

    @Event
    def after_finish_running_a_thread(self,
                                      thread: 'ReplicaThread',
                                      current_completed_threads: int,
                                      completed_threads: int):
        """
        Log the completion of a thread.

        :param thread:
        :param current_completed_threads:
        :param completed_threads:
        :return:
        """

        if self.subject.sim.debug:
            if current_completed_threads == 1:
                self.logger.log(
                    "  ** Completed execution of thread #" + str(thread.id) + " - Total completed threads = " +
                    str(completed_threads) + "/" + str(len(self.subject.cluster_scheduler.active_threads)), 3)

    @Event
    def before_transmitting_requests_in_network(self):
        if self.subject.sim.debug:
            self.logger.log("    *** Number of active transmissions: " +
                            str(len(self.subject.topology.active_transmissions)))

    @Event
    def in_transmitting_an_active_transmission(self,
                                               request: 'Request',
                                               active_subchain_id: int,
                                               duration: Union[int, float]):
        """
        Log the status of the request while transmitting an active transmission.

        :param request:
        :param active_subchain_id:
        :param duration:
        :return:
        """

        if self.subject.sim.debug:
            log = self.logger.log
            log("    *** Checking status of request #" + str(request))
            log("     **** transmission_times=" + str(request.trans_times), 3)
            log("     **** transmission_exact_times=" + str(request.trans_exact_times), 3)

            if request.subchains_status[active_subchain_id] == "IN TRANSMISSION":
                log("    **** Subchain ID " + str(active_subchain_id) +
                    " in this request, has a \"IN TRANSMISSION\" node, let's reduce" +
                    " its transmission time by " + str(duration), 3)

    @Event
    def after_transmitting_an_active_transmission(self,
                                                  request: 'Request',
                                                  active_subchain_id: int,
                                                  duration: Union[int, float]):
        """
        Log the remaining transmission time of the request after transmitting an active transmission.

        :param request:
        :param active_subchain_id:
        :param duration:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log("     ***** Remaining transmission time=" +
                            str(request.trans_times[active_subchain_id]), 3)

            if request.trans_times[active_subchain_id] <= 0:
                self.subject.sim.logger.log("     **** Transmission time <= 0 -> finish transmission", 3)

    @Event
    def before_load_balancing_a_host(self, host: 'Host'):
        """
        Log the host that is going to be load balanced.

        :param host:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log(" ** Load balancing threads in host " + str(host), 3)

    @Event
    def before_calling_is_there_a_thread_that_ends_sooner_function(self, time_of_next_event: Union[int, float]):
        """
        Log the time of the next event before calling the function is_there_a_thread_that_ends_sooner.

        :param time_of_next_event:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log("- Checking if a thread's execution is going to end sooner " +
                            "than next event (which is " + str(time_of_next_event) + ") or" +
                            "not. If so, then we need to change the execution time...", 3)

    @Event
    def before_checking_a_thread_ends_sooner(self,
                                             thread: 'ReplicaThread',
                                             duration_to_finish: Union[int, float],
                                             time_to_finish: Union[int, float],
                                             time_of_next_event: Union[int, float]):
        """
        Log the information of the thread that is going to be checked if it ends sooner than the next event.

        :param thread:
        :param duration_to_finish:
        :param time_to_finish:
        :param time_of_next_event:
        :return:
        """

        if self.subject.sim.debug:
            log = self.logger.log
            log("  ** Initiating to run thread #" + str(thread.id) + " belongs to replica " + str(thread.replica) +
                " on host " + str(thread.core.cpu.host), 3)
            log("   *** It will take " + str(duration_to_finish) + " to execute this thread, therefore, it will " +
                "end at " + str(time_to_finish), 3)
            if time_to_finish < time_of_next_event:
                log("    **** Because it takes less time to complete this thread (end time=" + str(time_to_finish) +
                    ") than starting next planned event (" + str(time_of_next_event) + "), we will replace " +
                    "time_of_next_event with " + str(time_to_finish) + "!", 3)

    @Event
    def after_calling_is_there_a_thread_that_ends_sooner_function(self,
                                                                  result: bool,
                                                                  time_of_next_event: Union[int, float],
                                                                  duration_of_next_event: Union[int, float]):
        """
        Log the result of the function is_there_a_thread_that_ends_sooner.

        :param result:
        :param time_of_next_event:
        :param duration_of_next_event:
        :return:
        """

        if self.subject.sim.debug:
            if result:
                self.logger.log("  ** Next event occurs sooner than finishing at least one thread. Therefore,"
                                " let's run threads only until next event's occurrence. Duration between now and"
                                " next event = " + str(duration_of_next_event), 3)
                self.logger.log("   *** Next event will occur at " + str(time_of_next_event), 3)
            else:
                if self.subject.sim.debug:
                    self.logger.log(" * Going to execute all threads on all hosts for " + str(duration_of_next_event) +
                                    "ns! (until next event)", 3)
