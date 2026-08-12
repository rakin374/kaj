# Modules

Kaj v0 imports local source modules. Given:

```text
project/
├── main.kaj
├── math.kaj
└── models/
    └── user.kaj
```

`main.kaj` may contain:

```kaj
import math
import models.user

let user: models.user.User = models.user.make("Alice")
print(math.add(2, 3))
```

`import foo.bar` resolves to `foo/bar.kaj` beneath the directory containing the entry file. Imports create the top-level binding `foo`; access remains qualified.

Dependencies compile and initialize before importers, in source import order, and each module initializes at most once. Transitive dependencies are loaded but do not become direct bindings unless explicitly imported.

Imports do not support remote packages, registries, manifests, versions, aliases, selective imports, or relative imports.

Reference: [module import semantics](../language/imports.md).
