library(ggraph)
library(igraph)
require(tidygraph)
library(tidyverse)
library(graphlayouts)
library(ggforce)
library(scatterpie)
library(extrafont)
extrafont::font_import()

graph <- read_graph("/Users/m/Documents/test.graphml", format = "graphml")

# Not specifying the layout - defaults to "auto"
ggraph(graph, layout = 'linear', circular = TRUE) +
    geom_edge_arc(aes(width=payload, colour = payload), alpha=0.5, arrow = arrow(length = unit(1, 'mm')), end_cap = circle(1, 'mm')) +
    #scale_edge_width(range = c(1, 0.4), guide="none") +
    scale_edge_colour_gradient2(low = "#d19999FF", high = "#8b0000FF") +
      scale_edge_width_continuous(range = c(0.1, 1), guide = "none") +
     geom_node_point(aes(size = workload_heavinesss, colour = workload_type), alpha=0.9) +
       scale_size_continuous(range = c(1,5)) +
       scale_colour_manual(values = c("CPU intensive" = "#FF9045FF", "Disk intensive" = "#158b00FF", "Memory intensive" = "#8b5F83FF", "Network intensive" = "#00008bFF")) +
  theme_graph(base_family = "Arial",base_size = 16, background="white")
