# Godot — Navigation

## Core principle
Navigation is a budgeted service, not something every AI should query every frame.

## Guidance
- Keep navigation meshes as simple as gameplay allows; path cost grows with graph complexity.
- Do not request a fresh path every frame.
- Stagger path/perception updates across agents and frames.
- Repath on meaningful target/path invalidation or scheduled cadence.
- Separate strategic destination choice from low-level movement/avoidance.
- Profile avoidance before enabling it for every crowd agent.
- Prefer cheap local separation for simple infected when full avoidance is unnecessary.
- Partition/stream navigation if future levels become substantially larger.
- Treat dynamic NavigationObstacle3D updates as a cost to budget.

## Arcont model
Infected can use inexpensive pursuit/local separation. Tactical enemies justify richer cover/path queries. Off-screen/distant actors should update less frequently. Bosses/important agents can receive larger budgets.

## References
- Navigation optimization: https://docs.godotengine.org/en/4.7/tutorials/navigation/navigation_optimizing_performance.html
- NavigationAgent3D: https://docs.godotengine.org/en/stable/classes/class_navigationagent3d.html
- NavigationObstacle3D: https://docs.godotengine.org/en/4.7/tutorials/navigation/navigation_using_navigationobstacles.html
- NavigationServer3D: https://docs.godotengine.org/en/stable/classes/class_navigationserver3d.html

## Research queue
- Hierarchical/chunked navigation.
- Crowd avoidance alternatives.
- Cover graph + navmesh hybrid.
- Dynamic destruction and nav invalidation.
- Path-query scheduler with importance tiers.
