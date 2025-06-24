# Dependency Breaking Mikado Plan

1. For a characterization test entrypoint
1. Identify all reachable paths
1. Find nodes in the path that access slow or untestable collaborators that harm testability. They may be deep down in the callstack.
1. If the dependency is hard, break it.