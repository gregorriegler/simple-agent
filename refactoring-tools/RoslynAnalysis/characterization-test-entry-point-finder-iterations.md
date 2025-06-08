# Entry Point Analysis Tool Plan - Iterative Approach

This document outlines the iterative plan for building an analysis tool that identifies optimal entry points for characterization tests in C# projects using Roslyn.

## Overview

The tool will analyze C# codebases to find the most efficient set of entry points for characterization tests. By using a call graph analysis and set cover algorithm, we can identify a minimal set of public methods that provide maximum code coverage.

## Strategy

1. Build a call graph of the entire codebase
2. Identify candidate entry points (public methods on public classes)
3. Measure reachability for each candidate method
4. Apply a greedy set cover algorithm to select the optimal entry points

## Implementation Iterations

Instead of implementing the tool by components, we'll use an iterative approach where each iteration delivers working functionality that builds toward the complete solution.

### Iteration 1: Basic Project Setup with Method Listing

**Goal:** Create a command-line tool that can load a C# project and list all methods.

- [ ] Create basic project structure in the RoslynAnalysis folder
- [ ] Set up Roslyn dependencies
- [ ] Implement command-line interface with options for target project/solution path
- [ ] Implement solution/project loading using Roslyn
- [ ] Create a simple syntax walker to identify method declarations
- [ ] Output a list of all methods found in the project

**Deliverable:** A tool that can load a C# project and list all methods with their signatures.

### Iteration 2: Basic Call Graph Construction

**Goal:** Extend the tool to build and visualize a simple call graph.

- [ ] Enhance the syntax walker to identify method invocations
- [ ] Build a basic directed graph representation where:
  - Nodes are methods
  - Edges represent method calls
- [ ] Implement a mermaid output of the call graph

**Deliverable:** A tool that can generate and display a basic call graph for a C# project.

### Iteration 3: Entry Point Identification

**Goal:** Identify potential entry points for testing.

- [ ] identify public methods on public classes
- [ ] Enhance the output to highlight entry point methods in the call graph

**Deliverable:** A tool that can identify and display potential entry points for testing.

### Iteration 4: Basic Reachability Analysis

**Goal:** Analyze which methods are reachable from each entry point.

- [ ] Implement basic graph traversal algorithms to determine reachable methods from each entry point
- [ ] Create a simple reachability report for each entry point
- [ ] Enhance the call graph visualization to show reachability from a selected entry point

**Deliverable:** A tool that can show which methods are reachable from each entry point.

### Iteration 5: Coverage Metrics

**Goal:** Calculate and display coverage metrics for entry points.

- [ ] Create a reachability matrix/map for all candidates
- [ ] Calculate coverage metrics for each candidate:
  - Number of methods reachable
  - Percentage of codebase covered
  - Unique methods covered (not covered by other candidates)
- [ ] Enhance the output to include coverage statistics

**Deliverable:** A tool that can rank entry points by their coverage effectiveness.

### Iteration 6: Basic Set Cover Implementation

**Goal:** Implement a simple version of the set cover algorithm.

- [ ] Implement a basic greedy set cover algorithm that:
  - Selects the candidate with maximum additional coverage at each step
  - Continues until a specified number of entry points is reached
- [ ] Output the selected set of entry points with their combined coverage

**Deliverable:** A tool that can recommend a set of entry points to maximize code coverage.