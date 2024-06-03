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

from typing import List, Tuple, Union, TYPE_CHECKING, Dict

from perfsim import Event, LogObserver

if TYPE_CHECKING:
    from perfsim import ReplicaThread, LoadGenerator, Request, ReplicaThread, MicroserviceReplica, TrafficPrototype


class LoadGeneratorLogObserver(LogObserver):
    """
    This class is responsible for logging the events of the load generator.
    """
    def __init__(self, load_generator: 'LoadGenerator'):
        super().__init__(name="LoadGeneratorLogObserver", subject=load_generator, logger=load_generator.sim.logger)

    @Event
    def before_traffic_start(self):
        """
        Log the start of the traffic.

        :return: None
        """
        if self.subject.sim.debug:
            self.logger.print_all()

    @Event
    def before_requests_start(self):
        """
        Log the start of the requests.

        :return: None
        """

        if self.subject.sim.debug:
            self.logger.log("--- REQUEST ---")

    @Event
    def before_generate_threads(self):
        """
        Log the generation of threads.

        :return: None
        """

        if self.subject.sim.debug:
            self.logger.log("--- THREAD GENERATION ---")

    @Event
    def before_exec_time_estimation(self):
        """
        Log the estimation of the execution time.

        :return: None
        """
        if self.subject.sim.debug:
            self.logger.log("--- EXEC TIME ESTIMATION ---")
            self.logger.log(" * Next network transmission is going to complete at " +
                            str(self.subject.next_trans_completion_times.peekitem(0)[0]), 1)
            self.logger.log(" * Next batch of requests will arrive at " + str(self.subject.next_batch_arrival_time), 1)

    @Event
    def before_executing_threads(self):
        """
        Log the execution of threads.

        :return:
        """
        if self.subject.sim.debug:
            self.logger.log("--- RUN THREADS ---")

    @Event
    def after_completing_load_generation(self):
        """
        Log the completion of the load generation.

        :return:
        """

        if self.subject.sim.debug:
            self.logger.log("--- ***** DONE ***** ---")
            self.logger.log("--- ***** Total execution time = " + str(self.subject.sim.time) + " ***** ---", 1)

    @Event
    def after_next_batch_arrival_time_calculation(self, next_scm_names: list[str], next_batch_arrival_time: int):
        """
        Log the calculation of the next batch arrival time.

        :param next_scm_names:
        :param next_batch_arrival_time:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log("  Next batch of requests belongs to scm ID " + str(next_scm_names) +
                            " and will arrive at " + str(next_batch_arrival_time) + "", 3)

    @Event
    def before_generate_request_threads(self, request: 'Request', subchain_id: int):
        """
        Log the generation of threads for a request.

        :param request:
        :param subchain_id:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log(" * Generating threads in request #" + str(request.id) +
                            " for subchain #" + str(subchain_id))

    @Event
    def after_generate_request_threads(self,
                                       request: 'Request',
                                       subchain_id: int,
                                       threads: Dict[str, 'ReplicaThread'],
                                       current_replicas: List[Tuple[int, 'MicroserviceReplica']]):
        """
        Log the generation of threads for a request.

        :param request:
        :param subchain_id:
        :param threads:
        :param current_replicas:
        :return:
        """

        if self.subject.sim.debug:
            thread_ids = [str(_t.id) for _t in threads.values()]
            replica_pair = current_replicas[subchain_id]
            replica_identifier_in_subchain = replica_pair[0]
            replica = replica_pair[1]

            self.logger.log(" * Generated " + str(len(threads)) + " threads for replica node (" +
                            str(replica_identifier_in_subchain) + "," + str(replica) + ") (total threads count=" +
                            str(len(self.subject.threads)) + ") - threads ids=" + str(thread_ids), 1)

    @Event
    def after_estimating_time_of_next_event(self,
                                            next_trans_completion_time: Union[int, float],
                                            time_of_next_event: Union[int, float],
                                            next_batch_arrival_time: Union[int, float],
                                            estimated_next_event: str,
                                            is_thread_ending_sooner: bool):
        """
        Log the estimation of the time of the next event.

        :param next_trans_completion_time:
        :param time_of_next_event:
        :param next_batch_arrival_time:
        :param estimated_next_event:
        :param is_thread_ending_sooner:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log(" * Next transmission will complete at " + str(next_trans_completion_time), 2)
            self.logger.log(" * Time of next event is " + str(time_of_next_event), 2)
            self.logger.log(" * Next batch arrival time is " + str(next_batch_arrival_time), 2)
            self.logger.log(" * Next estimated event (so far) is " + estimated_next_event, 2)
            self.logger.log(" * Thread completing next = " + str(is_thread_ending_sooner), 2)
            self.logger.log(" * Next estimated event after executing threads is " +
                            self.subject.prediction_for_the_next_event_after_running_threads, 2)

            if self.subject.duration_of_next_event == float('inf'):
                if self.subject.previous_event != "THREAD GEN":
                    self.logger.log("  ** Duration of next event is Infinity! It means there are some leftover "
                                    "threads that were not getting generated in the previous step! "
                                    "Let's check for any left over threads...!", 1)
                else:
                    self.logger.log("   ** Well, the number of active transmissions is " +
                                    str(len(self.subject.sim.cluster.topology.active_transmissions)))
            else:
                self.logger.log("  ** Running threads on hosts for " +
                                str(self.subject.duration_of_next_event) + "ns!", 10)

    @Event
    def before_transmit_requests_in_network(self):
        """
        Log the transmission of requests in the network.

        :return:
        """

        if self.subject.sim.debug:
            self.logger.log("- Transmitting packets for " + str(self.subject.duration_of_next_event) + "ns!", 3)

    @Event
    def after_transmit_requests_in_network_and_load_balancing_threads(self, current_completed_threads: int):
        """
        Log the transmission of requests in the network and the load balancing of threads.

        :param current_completed_threads:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log(" * " + str(current_completed_threads) + " threads completed", 1)
            if self.subject.completed_requests == self.subject.total_requests_count:
                self.logger.log("- No more request to run! DONE!", 1)
            else:
                self.logger.log("- There are remaining threads, next event=" + str(self.subject.next_event), 1)
                self.logger.log("  * completed requests == " + str(self.subject.completed_requests) +
                                " | total requests count == " + str(self.subject.total_requests_count), 10)

    @Event
    def before_request_created(self,
                               request_number: int,
                               scm_name: str,
                               request_id: str,
                               traffic_prototype: 'TrafficPrototype'):
        """
        Log the creation of a request.

        :param request_number:
        :param scm_name:
        :param request_id:
        :param traffic_prototype:
        :return:
        """

        if self.subject.sim.debug:
            self.logger.log(" * Starting request #" + str(request_number) + "/" +
                            str(traffic_prototype.requests_count) + " (id=" + request_id + ") of scm ID " + scm_name, 1)

    @Event
    def after_requests_start(self):
        """
        Log the start of the requests.

        :return:
        """

        if self.subject.sim.debug:
            self.logger.log(" * A batch of requests has been initiated. Next batch will arrive at " +
                            str(self.subject.next_batch_arrival_time), 1)
