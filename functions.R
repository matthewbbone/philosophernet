
outdegree <- function(node, edges) {
  
  edges %>%
    filter(from == node) %>%
    nrow()
  
}

outdegree <- Vectorize(outdegree, vectorize.args = "node")

indegree <- function(node, edges) {
  
  edges %>%
    filter(to == node) %>%
    nrow()
  
}

indegree <- Vectorize(indegree, vectorize.args = "node")
