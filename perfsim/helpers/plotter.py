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


from __future__ import annotations

import json
import os
import random
import webbrowser
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import plotly.figure_factory as pff
# from networkx.drawing.tests.test_pylab import plt
from networkx.drawing.nx_agraph import graphviz_layout
from pandas import DataFrame
from sortedcontainers import SortedList

from perfsim import Utils, Transmission, SimulationScenarioResultDict

if TYPE_CHECKING:
    from perfsim import LoadGenerator


class Plotter:
    """
    This class is responsible for plotting the simulation results.
    """

    @staticmethod
    def draw_topology(cluster):
        """
        Draw the topology of the cluster.
        """

        from networkx.drawing.tests.test_pylab import plt
        nx.draw(cluster.topology)
        plt.show()

    @staticmethod
    def draw_timeline_graph(results: SimulationScenarioResultDict):
        """
        Draw the timeline graph.
        """

        lst = []
        colors = set()
        ticks = set()
        colors_dict = {}
        l = SortedList()

        for sfc_name, sfc_result_dict in results["service_chains"].items():
            for iteration_id, lats_dict in sfc_result_dict["latencies"]['iterations'].items():
                for index, lats in lats_dict.items():
                    lst.append({"Task": index,
                                "Start": sfc_result_dict["arrival_times"]['iterations'][iteration_id][index],
                                "Finish": sfc_result_dict["completion_times"]['iterations'][iteration_id][index],
                                "SFC": sfc_name
                                })
                    ticks.add(sfc_result_dict["arrival_times"]['iterations'][iteration_id][index])
                    l.add(sfc_result_dict["arrival_times"]['iterations'][iteration_id][index])
            while True:
                rand_color = ["#" + ''.join([random.choice('ABCDEF0123456789') for i in range(6)])][0]
                if rand_color not in colors:
                    colors.add(rand_color)
                    break
            colors_dict[sfc_name] = rand_color

        df = pd.DataFrame(lst)

        # fig = px.timeline(df, x_start="Start", x_end="Finish", y="Request ID", color="SFC", index_col="Request ID")

        fig = pff.create_gantt(df, colors=colors_dict, show_colorbar=True, showgrid_x=True, showgrid_y=True,
                               group_tasks=True, index_col="SFC")
        fig.update_layout(xaxis_type='linear')
        fig['layout']['xaxis']['tickformat'] = '%L'

        return fig

    @staticmethod
    def draw_figures(load_generator: LoadGenerator,
                     scenario_name: str,
                     show_events: bool = True,
                     path_to_save_results: str = os.getcwd() + '/results/') -> None:
        """
        Draw the figures for the simulation results.

        :param load_generator:
        :param scenario_name:
        :param show_events:
        :param path_to_save_results:
        """

        __base_path = path_to_save_results + scenario_name
        Utils.mkdir_p(__base_path)
        Utils.mkdir_p(__base_path + "/hosts")
        import seaborn as sns

        palette = sns.color_palette("hls", len(load_generator.threads) + 1)
        threads_color_code = {}

        for (key, _t) in enumerate(load_generator.threads):
            threads_color_code[_t.id] = int(key)

        threads_color_code["idle"] = len(load_generator.threads)

        for host in load_generator.sim.cluster.cluster_scheduler.hosts_dict.values():
            Utils.mkdir_p(__base_path + "/hosts/" + host.name)

            count_of_cores = len(host.cpu.cores)
            # Initialize the figure
            plt.style.use('seaborn-darkgrid')
            plot_margin = 1000

            # create a color palette
            _palette = plt.get_cmap('Set1')
            fig, axes = plt.subplots(count_of_cores, 1, figsize=(10, count_of_cores * 3 / 2))
            axes[0].ticklabel_format(useOffset=False, style="plain")
            axes[1].ticklabel_format(useOffset=False, style="plain")
            _top = 0.98 if count_of_cores == 8 else 0.9
            fig.subplots_adjust(top=_top, bottom=0.12, left=0.055, right=0.965)
            # Same limits for everybody!
            plt.xlim(0, 1000)
            plt.ylim(0, 100)
            # multiple line plot
            num = 0
            counter = 0

            for _core in np.arange(0, count_of_cores):
                num += 1
                df = pd.DataFrame.from_dict(host.cpu.cores[_core].runqueue.threads_total_time).sort_index().fillna(0)
                _counter = len(df) - 1
                try:
                    df.loc[0]["idle"] = 1
                except KeyError:
                    continue
                while _counter > 0:
                    _current_index = df.index[_counter]
                    _previous_index = df.index[_counter - 1]
                    _current_values = df.loc[_current_index]
                    _previous_values = df.loc[_previous_index]
                    if _previous_index + 1 < _current_index:
                        _time_delta = _current_index - _previous_index
                        _value_for_a_nanoseconds = 1 - ((_time_delta - _current_values) / _time_delta)
                        df.loc[int(_previous_index + 1)] = _value_for_a_nanoseconds
                        df.loc[_current_index] = df.loc[_current_index] - _value_for_a_nanoseconds
                        df = df.sort_index().fillna(0)
                    _counter -= 1

                _last_index = df.index[-1] + 1
                df.loc[_last_index] = 0
                df.loc[_last_index]["idle"] = 1
                df = df.sort_index().fillna(0)
                df = df.loc[:, (df != 0).any(axis=0)]
                # df = df[(df.T != 0).any()]
                # Find the right spot on the plot
                ax = plt.gca()
                ax.get_xaxis().get_major_formatter().set_useOffset(False)
                ax.get_yaxis().get_major_formatter().set_useOffset(False)
                ax.get_xaxis().get_major_formatter().set_scientific(False)
                ax.get_yaxis().get_major_formatter().set_scientific(False)
                plt.subplot(count_of_cores, 1, num)

                if len(df) > 0:
                    _len = len(df)
                    df_split = np.array_split(df, _len)
                    _df = DataFrame()

                    for _index, sub_df in enumerate(df_split):
                        time_delta = sub_df.index[0] - (df_split[_index - 1].index[0] if _index != 0 else -1)
                        sum_of_time_slices = sub_df.agg('sum')
                        time_proportion = sum_of_time_slices / time_delta
                        _df[sub_df.index[0]] = time_proportion
                    _df = _df.transpose()
                    # _df.loc[0] = 0
                    _df = _df.sort_index()
                    # plot every group, but discreet
                    for v in _df:
                        a, = plt.plot(_df.index.tolist(),
                                      _df[v],
                                      marker='',
                                      color=palette[threads_color_code[v]],
                                      linewidth=2,
                                      alpha=0.7,
                                      label=_core)
                        # plt.legend(df.columns.tolist())
                        counter += 1
                    counter = 0
                    # Plot the lineplot
                    # plt.plot(df['x'], df[column], marker='', color=palette(num + counter), linewidth=2.4, alpha=0.9, label=column)

                    # Not ticks everywhere
                    if num in range(7):
                        plt.tick_params(labelbottom='off')
                    if num not in [1, 4, 7]:
                        plt.tick_params(labelleft='off')

                    # Add title
                    plt.title(_core, loc='left', fontsize=12, fontweight=0, color=palette[num])
                    # plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
            ax = plt.gca()
            ax.get_xaxis().get_major_formatter().set_useOffset(False)
            ax.get_yaxis().get_major_formatter().set_useOffset(False)
            ax.get_xaxis().get_major_formatter().set_scientific(False)
            ax.get_yaxis().get_major_formatter().set_scientific(False)
            # general title
            plt.suptitle("CPU Usages " + str(host.name),
                         fontsize=13,
                         fontweight=0,
                         color='black',
                         y=0.99 if count_of_cores == 8 else 0.96,
                         style='italic'
                         )

            fig.savefig(__base_path + "/hosts/" + host.name + "/cpu.png", dpi=fig.dpi)

            if show_events:
                levels = []
                # Choose some nice levels
                for i in np.arange(1, 20):
                    levels.append(-1 * i)
                    levels.append(i)

                levels = np.tile(levels, int(np.ceil(len(host.timeline_time) / 6)))[:len(host.timeline_time)]
                fig2, ax2 = plt.subplots(figsize=(20, 10), constrained_layout=True)
                # Create figure and plot a stem plot with the date
                ax2.set(title="Simulation events")

                markerline, stemline, baseline = ax2.stem(host.timeline_time, levels,
                                                          linefmt="C3-", basefmt="k-",
                                                          use_line_collection=True)

                plt.setp(markerline, mec="k", mfc="w", zorder=3)

                # Shift the markers to the baseline by replacing the y-data by zeros.
                markerline.set_ydata(np.zeros(len(host.timeline_time)))

                # annotate lines
                vert = np.array(['top', 'bottom'])[(levels > 0).astype(int)]
                for d, l, r, va in zip(host.timeline_time, levels, host.timeline_event, vert):
                    ax2.annotate(r, xy=(d, l), xytext=(-3, np.sign(l) * 3),
                                 textcoords="offset points", va=va, ha="right")

                plt.setp(ax2.get_xticklabels(), rotation=30, ha="right")

                # remove y axis and spines
                ax2.get_yaxis().set_visible(False)
                for spine in ["left", "top", "right"]:
                    ax2.spines[spine].set_visible(False)

                ax2.margins(y=0.1)
                try:
                    ax = plt.gca()
                    ax.get_xaxis().get_major_formatter().set_useOffset(False)
                    ax.get_yaxis().get_major_formatter().set_useOffset(False)
                    ax.get_xaxis().get_major_formatter().set_scientific(False)
                    ax.get_yaxis().get_major_formatter().set_scientific(False)
                except:
                    pass
                fig2.savefig(__base_path + "/hosts/" + host.name + "/events.png", dpi=fig.dpi)

                plt.show()

    @staticmethod
    def draw_graph(G, name, save_dir: str, output_type: str = "html", with_labels: bool = False, relabel: bool = False,
                   node_labels_map=None, show: bool = False):
        """
        Draw a graph.

        :param G:
        :param name:
        :param save_dir:
        :param output_type:
        :param with_labels:
        :param relabel:
        :param node_labels_map:
        :param show:
        :return:
        """

        pos = nx.spring_layout(G)
        node_labels = {}
        edge_labels = {}
        color_map = []
        router_color = 'green'
        host_color = '#6390AF'
        replica_color = '#FFE5B4'

        for edge in G.edges():
            try:
                edge_data = G.get_edge_data(u=edge[0], v=edge[1])[0]
            except KeyError:
                edge_data = G.get_edge_data(u=edge[0], v=edge[1])
            if type(edge[0]).__name__ in ['Host', 'Router', 'MicroserviceReplica']:
                bandwidth = Transmission.get_bandwidth_on_link(source=edge[0], destination=edge[1])
                link_name = str(edge_data["name"])
                edge_labels[edge] = link_name + " bw:" + "{:.2e}".format(bandwidth)
            elif type(edge[0]).__name__ == 'MicroserviceEndpointFunction':
                edge_labels[edge] = str(list(edge_data.values())[0]["payload"]) + "B"
            elif type(edge[0]).__name__ == 'tuple' and type(edge[0][1]).__name__ == 'MicroserviceEndpointFunction':
                edge_labels[edge] = str(edge_data["payload"]) + "B"

        if output_type == "html":
            cytoscape_json = Plotter.convert_networkx_graph_to_cytoscape_json(G, edge_labels=edge_labels)
            cytoscape_js = Plotter.get_cytoscape_template(ready_script=f'var cy = cytoscape({cytoscape_json});')

            if save_dir is not None:
                file_path = os.path.join(save_dir, f"{name}.html")
                Utils.mkdir_p(save_dir)
                Utils.save_file(file_path=file_path, content=cytoscape_js)
            else:
                file_path = os.path.join(".", f"{name}.html")
            if show:
                webbrowser.open(f"file://{file_path}")
                if save_dir is None:
                    os.remove(file_path)
            return cytoscape_js
        else:
            fig = plt.figure(1, figsize=(12, 12))
            ax = plt.gca()
            plt.title('draw_networkx')
            pos = graphviz_layout(G, prog='dot', args='-Grankdir=LR')
            nx.draw(G, pos, with_labels=with_labels, arrows=True)
            if save_dir is not None and save_dir is not False:
                Utils.mkdir_p(dir_path=save_dir)
                plt.savefig(save_dir + "alt_graph_" + name + ".pdf")
            if show:
                plt.show()

    # Credits: Partially from cytoscape.py (cytoscape_data function)
    @staticmethod
    def convert_networkx_graph_to_cytoscape_json(G, edge_labels: dict = None, node_style: dict = None,
                                                 edge_style: dict = None, layout="euler") -> str:
        """
        Convert a NetworkX graph to a Cytoscape JSON object.

        :param G:
        :param edge_labels:
        :param node_style:
        :param edge_style:
        :param layout:
        :return:
        """

        # load all nodes into nodes array
        final = {}
        final["directed"] = G.is_directed()
        final["multigraph"] = G.is_multigraph()
        # final["elements"] = {"nodes": [], "edges": []}
        final["elements"] = []
        added_nodes = {}

        if node_style is None:
            node_style = {
                'label': 'data(label)',
                'width': '60px',
                'height': '60px',
                'color': 'blue',
                'background-fit': 'contain',
                'background-clip': 'none'
            }
        if edge_style is None:
            edge_style = {
                'label': 'data(label)',
                'text-background-color': 'yellow',
                'text-background-opacity': 0.4,
                'width': '6px',
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'control-point-step-size': '140px'
            }

        for n in G.nodes():
            nparent = None
            ntype = type(n).__name__

            if (ntype == "MicroserviceEndpointFunction" or
                    (ntype == 'tuple' and type(n[1]).__name__ == 'MicroserviceEndpointFunction')):
                _n = n.microservice if ntype != "tuple" else n[1].microservice
                _n_id = str(_n)
                if _n_id not in added_nodes.keys():
                    nparent = {"group": "nodes", "data": {}, "classes": type(_n).__name__}
                    nparent["data"]["id"] = _n_id
                    nparent["data"]["label"] = _n_id
                    added_nodes[_n_id] = nparent
                    final["elements"].append(nparent)
                else:
                    nparent = added_nodes[_n_id]

            nx = {"group": "nodes", "data": {}, "classes": ntype}
            nx_id = str(n)
            nx["data"]["id"] = nx_id
            nx["data"]["label"] = nx_id if ntype != "tuple" else str(n[1])
            if nparent is not None:
                nx["data"]["parent"] = str(n.microservice) if ntype != "tuple" else str(n[1].microservice)
            added_nodes[nx_id] = nx
            # final["elements"]["nodes"].append(nx.copy())
            final["elements"].append(nx)

        for e in G.edges():
            nx = {"group": "edges", "data": {}}
            nx["data"]["id"] = str(e[0]) + "_" + str(e[1])
            nx["data"]["source"] = str(e[0])
            nx["data"]["target"] = str(e[1])
            nx["data"]["label"] = str(edge_labels[e]) if edge_labels else str(e[0]) + "->" + str(e[1])
            # final["elements"]["edges"].append(nx)
            final["elements"].append(nx)

        final["container"] = "----"
        final["layout"] = {}
        final["layout"]["name"] = layout
        final["layout"]["animate"] = "true"
        final["layout"]["randomize"] = "true"
        final["layout"]["gravity"] = "-300"
        final["style"] = [{
            "selector": 'node',
            "style": node_style
        }, {
            "selector": 'edge',
            "style": edge_style
        }, {
            "selector": '.Host',
            "style": {
                # "border-color": "red",
                # 'border-width': 3,
                "shape": "rectangle",
                "background-image": "https://raw.githubusercontent.com/michelgokan/perfsim-assets/main/images/host.png",
                "background-color": "white"
            }
        }, {
            "selector": '.Router',
            "style": {
                # "border-color": "red",
                # 'border-width': 3,
                "shape": "rectangle",
                "background-image": "https://raw.githubusercontent.com/michelgokan/perfsim-assets/main/images/router.png",
                "background-color": "white"
            }
        }, {
            "selector": '.MicroserviceReplica',
            "style": {
                # "border-color": "red",
                # 'border-width': 3,
                "shape": "rectangle",
                "background-image": "https://raw.githubusercontent.com/michelgokan/perfsim-assets/main/images/replica.png",
                "background-color": "white"
            }
        }]
        final = json.dumps(final).replace('\"----\"', "document.getElementById('cy')")

        return final

    @staticmethod
    def get_cytoscape_template(ready_script: str) -> str:
        """
        Get the template for the Cytoscape graph.

        :param ready_script:
        :return:
        """

        return f"""<!DOCTYPE>
<html style=\"height: 100%;\">
    <head>
        <script src=\"https://code.jquery.com/jquery-3.6.0.min.js\"></script>
        <script src=\"https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js\"></script>
        <script src=\"https://cytoscape.org/cytoscape.js-euler/cytoscape-euler.js\"></script>
        <script src=\"https://unpkg.com/webcola@3.4.0/WebCola/cola.min.js\"></script>
        <script src=\"https://cytoscape.org/cytoscape.js-cola/cytoscape-cola.js\"></script>

        <style>
            #cy {{
                width: 100%;
                height: 100%;
            }}
            body {{
                width: 100%;
                height: 100%;
            }}
        </style>
    </head>
    <body>
        <div id=\"cy\"></div>
        <script>
            $(document).ready(function () {{
                {ready_script}
            }});
        </script>
    </body>
</html>
        """

    @staticmethod
    def figures_to_html(figs, filename="dashboard.html"):
        """
        Save a list of figures to an HTML file.

        :param figs:
        :param filename:
        :return:
        """

        with open(filename, 'w') as dashboard:
            dashboard.write("<html><head></head><body><table style='width: 100%; height: 100%'>" + "\n")
            for fig_and_names in figs:
                # inner_html = fig_and_names[1].to_html()
                dashboard.write("<tr><td><iframe id='FileFrame' style='width: 100%; height: 100%'"
                                " src='" + fig_and_names[0] + "'></iframe></td></tr>")
            dashboard.write("</table></body></html>" + "\n")
