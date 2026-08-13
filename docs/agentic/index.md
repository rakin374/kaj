# Agentic Kaj

Agentic Kaj extends the pure language with durable, typed tasks that can pause,
interact with people and host-granted capabilities, compose child tasks, and
execute validated planner proposals.

The initial foundation conforms to **Agentic Kaj Conformance 1**.

Start with these specifications:

- [Tasks](kaj-agentic-tasks-spec.md)
- [Steps and lifecycle](kaj-agentic-steps-and-lifecycle-spec.md)
- [Task contracts](task-contracts.md)
- [Human interaction](human-interaction.md)
- [Persistence and resume](persistence-resume.md)
- [Capabilities](capabilities.md)
- [Task composition](task-composition.md)
- [Planner interface](planner-interface.md)
- [Controlled replanning](controlled-replanning.md)
- [Agentic conformance](agentic-conformance.md)

Agentic code still follows all Pure Kaj typing, scope, formatting, AST JSON,
module, and runtime rules. Capability declarations request authority; only the
host can grant it. Planner output is untrusted Kaj code until normal validation
succeeds.
