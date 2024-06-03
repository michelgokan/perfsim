from typing import Dict, Tuple

import pytest

from perfsim import RouterPrototype, TopologyLinkPrototype, Host, Router, TopologyLink, TopologyPrototype


def create_host_topology_prototypes(r_proto: RouterPrototype, l_proto: TopologyLinkPrototype, max_host_count: int) \
        -> Tuple[Dict[str, TopologyPrototype], Dict[str, Host], Dict[str, Router], Dict[str, TopologyLink]]:
    t = {}
    h = {}
    l = {}
    r = {}

    for name, host_prototype in pytest.host_prototypes.items():
        rname = f"router_{max_host_count}host_{name}"
        tauname = f"tau_{max_host_count}host_{name}"
        lnames = []
        hnames = []

        r[rname] = Router.from_router_prototype(name=rname, router_prototype=r_proto)
        for j in range(max_host_count):
            hnames.append(f"{max_host_count}_{name}_{j}")
            h[hnames[j]] = Host.from_host_prototype(name=hnames[j], host_prototype=host_prototype)
            link_index = j * 2
            for k in range(2):
                link_index2 = link_index + k
                lnames.append(f"l{link_index2}_{hnames[j]}")
                l[lnames[link_index2]] = TopologyLink.from_prototype(name=lnames[link_index2],
                                                                     prototype=l_proto,
                                                                     src=h[hnames[j]] if k == 0 else r[rname],
                                                                     dest=r[rname] if k == 0 else h[hnames[j]])
        t[tauname] = TopologyPrototype(name=tauname,
                                       egress_err=0.05,
                                       ingress_err=0.05,
                                       hosts={n: h[n] for n in hnames},
                                       routers={rname: r[rname]},
                                       links={n: l[n] for n in lnames})
    return t, h, r, l
