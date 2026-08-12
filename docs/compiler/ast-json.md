# Kaj AST JSON v1

**Status:** Authoritative external interchange specification for Kaj AST JSON v1  
**Scope:** Pure Kaj Core AST as implemented through Checkpoint 3  
**Audience:** Compiler implementers, tooling authors, agents, IDE integrations, tests

## Interpolated strings

An interpolated string uses kind `interpolated_string` with ordered `parts`. A part is either `{"kind":"text","value":"..."}` or `{"kind":"expression","value":<expression node>}`. Semantic types, resolved symbols, and runtime-rendered text are not serialized. Ordinary strings remain `string_literal` nodes.

---

## 1. Purpose

Kaj AST JSON is the canonical machine-readable interchange representation of Kaj's Abstract Syntax Tree.

Kaj supports two source-facing representations that converge on the same internal AST:

```text
Human path

.kaj source
    ↓
lexer
    ↓
parser
    ↓
Internal Kaj AST


Machine/tool path

Kaj AST JSON
    ↓
deserializer
    ↓
Internal Kaj AST
```

The internal AST remains the compiler's working syntax representation.

AST JSON exists so external tools, agents, editors, tests, and future structured tooling can exchange Kaj programs without generating raw `.kaj` syntax.

AST JSON is **not compiler IR**, runtime state, bytecode, or an AST patch protocol.

---

## 2. Version

This document defines:

```text
Kaj AST JSON version 1
```

Canonical documents must contain:

```json
{
  "format": "kaj-ast",
  "version": 1,
  "program": {}
}
```

Required top-level fields:

```text
format
version
program
```

Rules:

```text
format == "kaj-ast"
version == 1
```

A consumer implementing only v1 must reject unsupported versions.

---

## 3. Top-Level Document

The canonical top-level shape is:

```json
{
  "format": "kaj-ast",
  "version": 1,
  "program": {
    "kind": "program",
    "statements": [],
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 0,
        "line": 1,
        "column": 1
      }
    }
  }
}
```

No additional top-level fields are permitted in v1.

---

## 4. Naming Conventions

All public JSON field names use:

```text
snake_case
```

All node discriminators and enum values also use stable lowercase snake_case strings.

Examples:

```text
binary_expression
binding_declaration
not_equal
add_assign
```

Python class names and Python enum representations are not part of the public format.

---

## 5. Node Discriminator

Every serialized AST node has a required:

```text
kind
```

field.

Example:

```json
{
  "kind": "identifier",
  "name": "price",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 5,
      "line": 1,
      "column": 6
    }
  }
}
```

Unknown `kind` values are invalid in AST JSON v1.

---

## 6. Source Locations

Source locations use:

```text
offset
line
column
```

Rules:

```text
offset = zero-based
line   = one-based
column = one-based
```

Canonical representation:

```json
{
  "offset": 8,
  "line": 1,
  "column": 9
}
```

Constraints:

```text
offset >= 0
line >= 1
column >= 1
```

---

## 7. Source Spans

All source-derived AST nodes that carry spans internally must serialize them.

Canonical form:

```json
{
  "start": {
    "offset": 0,
    "line": 1,
    "column": 1
  },
  "end": {
    "offset": 3,
    "line": 1,
    "column": 4
  }
}
```

Kaj spans use:

```text
[start, end)
```

That means:

- start is inclusive
- end is exclusive

At minimum:

```text
end.offset >= start.offset
```

AST JSON cannot verify line/column consistency against source text when the original source file is unavailable.

---

## 8. Unknown Fields

AST JSON v1 is strict.

Unknown fields are invalid.

Example:

```json
{
  "kind": "identifier",
  "nam": "x",
  "span": {}
}
```

must not be silently accepted as an identifier.

This prevents schema mistakes and misspelled fields from being ignored.

---

## 9. Required vs Nullable Fields

A field is either:

- required with a concrete value, or
- required and explicitly nullable where specified.

Do not omit a field merely because its value is absent if this specification defines the field as required nullable.

Example:

```json
"annotation": null
```

is canonical for an untyped binding.

Likewise:

```json
"value": null
```

is canonical for a bare `return`.

---

## 10. Integer Values

Kaj `Int` is arbitrary precision.

Therefore integer literal values are serialized as **base-10 strings**, not JSON numbers.

Canonical:

```json
{
  "kind": "integer_literal",
  "value": "999999999999999999999999999999",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 30,
      "line": 1,
      "column": 31
    }
  }
}
```

Rules:

- `value` must be a string
- it must represent a valid base-10 integer value
- no leading `+`
- negative source values are represented through `unary_expression`, not a negative integer literal node

Examples of valid integer values:

```json
"0"
"1"
"42"
"999999999999999999999999"
```

---

## 11. Decimal Values

Kaj `Decimal` is exact.

Decimal literal values are serialized as strings.

Canonical:

```json
{
  "kind": "decimal_literal",
  "value": "19.99",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 5,
      "line": 1,
      "column": 6
    }
  }
}
```

Do not serialize Kaj decimals as JSON floating-point numbers.

The string must be parseable into the exact decimal value represented by the internal AST.

For v1, serializer output should preserve the AST's canonical decimal value representation rather than inventing alternate scientific notation.

---

## 12. String Values

Kaj string literal values serialize as ordinary JSON strings.

Example:

```json
{
  "kind": "string_literal",
  "value": "hello\nworld",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 14,
      "line": 1,
      "column": 15
    }
  }
}
```

AST JSON stores the decoded semantic string value.

It does not preserve:

- original source escape spelling
- exact quote spelling
- raw literal lexeme

AST JSON is an AST format, not a lossless concrete syntax format.

---

## 13. Boolean Values

Boolean literal nodes use JSON booleans.

Example:

```json
{
  "kind": "boolean_literal",
  "value": true,
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 4,
      "line": 1,
      "column": 5
    }
  }
}
```

---

## 14. None Literal

`NoneLiteral` has no payload value.

Canonical form:

```json
{
  "kind": "none_literal",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 4,
      "line": 1,
      "column": 5
    }
  }
}
```

Do not encode the node itself as JSON `null`.

---

# 15. Program

Canonical fields:

```text
kind
statements
span
```

Example:

```json
{
  "kind": "program",
  "statements": [],
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 0,
      "line": 1,
      "column": 1
    }
  }
}
```

`statements` is an ordered array.

---

# 16. Identifier

Fields:

```text
kind
name
span
```

Example:

```json
{
  "kind": "identifier",
  "name": "price",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 5,
      "line": 1,
      "column": 6
    }
  }
}
```

---

# 17. Integer Literal

Fields:

```text
kind
value
span
```

Example:

```json
{
  "kind": "integer_literal",
  "value": "10",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 2,
      "line": 1,
      "column": 3
    }
  }
}
```

---

# 18. Decimal Literal

Fields:

```text
kind
value
span
```

Example:

```json
{
  "kind": "decimal_literal",
  "value": "3.14",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 4,
      "line": 1,
      "column": 5
    }
  }
}
```

---

# 19. String Literal

Fields:

```text
kind
value
span
```

Example:

```json
{
  "kind": "string_literal",
  "value": "hello",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 7,
      "line": 1,
      "column": 8
    }
  }
}
```

---

# 20. Boolean Literal

Fields:

```text
kind
value
span
```

Example:

```json
{
  "kind": "boolean_literal",
  "value": false,
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 5,
      "line": 1,
      "column": 6
    }
  }
}
```

---

# 21. Unary Expression

Fields:

```text
kind
operator
operand
span
```

Canonical operator values:

```text
positive
negate
not
```

Example:

```json
{
  "kind": "unary_expression",
  "operator": "negate",
  "operand": {
    "kind": "integer_literal",
    "value": "42",
    "span": {
      "start": {
        "offset": 1,
        "line": 1,
        "column": 2
      },
      "end": {
        "offset": 3,
        "line": 1,
        "column": 4
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 3,
      "line": 1,
      "column": 4
    }
  }
}
```

---

# 22. Binary Expression

Fields:

```text
kind
operator
left
right
span
```

Canonical operator values:

```text
add
subtract
multiply
divide
modulo
power

equal
not_equal
less
less_equal
greater
greater_equal

and
or
```

Example:

```json
{
  "kind": "binary_expression",
  "operator": "multiply",
  "left": {
    "kind": "identifier",
    "name": "price",
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 5,
        "line": 1,
        "column": 6
      }
    }
  },
  "right": {
    "kind": "identifier",
    "name": "quantity",
    "span": {
      "start": {
        "offset": 8,
        "line": 1,
        "column": 9
      },
      "end": {
        "offset": 16,
        "line": 1,
        "column": 17
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 16,
      "line": 1,
      "column": 17
    }
  }
}
```

---

# 23. Call Argument

If the internal Core AST defines `CallArgument` as a source-derived node with a span, serialize that span.

If the authoritative internal AST defines no span on `CallArgument`, omit `span` from this node.

The canonical semantic fields are:

```text
kind
name
value
```

`name` is nullable.

Positional example:

```json
{
  "kind": "call_argument",
  "name": null,
  "value": {
    "kind": "integer_literal",
    "value": "1",
    "span": {
      "start": {
        "offset": 4,
        "line": 1,
        "column": 5
      },
      "end": {
        "offset": 5,
        "line": 1,
        "column": 6
      }
    }
  }
}
```

Named example:

```json
{
  "kind": "call_argument",
  "name": "priority",
  "value": {
    "kind": "integer_literal",
    "value": "2",
    "span": {
      "start": {
        "offset": 17,
        "line": 1,
        "column": 18
      },
      "end": {
        "offset": 18,
        "line": 1,
        "column": 19
      }
    }
  }
}
```

The JSON format must follow the actual authoritative Core AST shape here rather than inventing a span field that does not exist internally.

---

# 24. Call Expression

Fields:

```text
kind
callee
arguments
span
```

Example:

```json
{
  "kind": "call_expression",
  "callee": {
    "kind": "identifier",
    "name": "add",
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 3,
        "line": 1,
        "column": 4
      }
    }
  },
  "arguments": [
    {
      "kind": "call_argument",
      "name": null,
      "value": {
        "kind": "integer_literal",
        "value": "1",
        "span": {
          "start": {
            "offset": 4,
            "line": 1,
            "column": 5
          },
          "end": {
            "offset": 5,
            "line": 1,
            "column": 6
          }
        }
      }
    }
  ],
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 6,
      "line": 1,
      "column": 7
    }
  }
}
```

Argument order must be preserved.

---

# 25. Member Access Expression

Fields:

```text
kind
object
member
span
```

Example:

```json
{
  "kind": "member_access_expression",
  "object": {
    "kind": "identifier",
    "name": "user",
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 4,
        "line": 1,
        "column": 5
      }
    }
  },
  "member": "name",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 9,
      "line": 1,
      "column": 10
    }
  }
}
```

---

# 26. Index Expression

Fields:

```text
kind
object
index
span
```

Example:

```json
{
  "kind": "index_expression",
  "object": {
    "kind": "identifier",
    "name": "items",
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 5,
        "line": 1,
        "column": 6
      }
    }
  },
  "index": {
    "kind": "integer_literal",
    "value": "0",
    "span": {
      "start": {
        "offset": 6,
        "line": 1,
        "column": 7
      },
      "end": {
        "offset": 7,
        "line": 1,
        "column": 8
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 8,
      "line": 1,
      "column": 9
    }
  }
}
```

---

# 27. List Literal

Fields:

```text
kind
elements
span
```

Example:

```json
{
  "kind": "list_literal",
  "elements": [
    {
      "kind": "integer_literal",
      "value": "1",
      "span": {
        "start": {
          "offset": 1,
          "line": 1,
          "column": 2
        },
        "end": {
          "offset": 2,
          "line": 1,
          "column": 3
        }
      }
    }
  ],
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 3,
      "line": 1,
      "column": 4
    }
  }
}
```

Element order must be preserved exactly.

---

# 28. Map Entry

Canonical semantic fields:

```text
kind
key
value
```

If the internal Core AST defines `MapEntry` with a span, serialize it.

If it does not, omit span.

Example:

```json
{
  "kind": "map_entry",
  "key": {
    "kind": "string_literal",
    "value": "Alice",
    "span": {
      "start": {
        "offset": 1,
        "line": 1,
        "column": 2
      },
      "end": {
        "offset": 8,
        "line": 1,
        "column": 9
      }
    }
  },
  "value": {
    "kind": "integer_literal",
    "value": "30",
    "span": {
      "start": {
        "offset": 10,
        "line": 1,
        "column": 11
      },
      "end": {
        "offset": 12,
        "line": 1,
        "column": 13
      }
    }
  }
}
```

---

# 29. Map Literal

Fields:

```text
kind
entries
span
```

Example:

```json
{
  "kind": "map_literal",
  "entries": [
    {
      "kind": "map_entry",
      "key": {
        "kind": "string_literal",
        "value": "Alice",
        "span": {
          "start": {
            "offset": 1,
            "line": 1,
            "column": 2
          },
          "end": {
            "offset": 8,
            "line": 1,
            "column": 9
          }
        }
      },
      "value": {
        "kind": "integer_literal",
        "value": "30",
        "span": {
          "start": {
            "offset": 10,
            "line": 1,
            "column": 11
          },
          "end": {
            "offset": 12,
            "line": 1,
            "column": 13
          }
        }
      }
    }
  ],
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 13,
      "line": 1,
      "column": 14
    }
  }
}
```

Kaj map literals must **not** be serialized as ordinary JSON objects.

Reason:

- Kaj map keys are expressions
- keys are not necessarily strings
- entry ordering must be preserved
- duplicate key expressions must remain structurally representable prior to semantic validation

---

# 30. Named Type

Fields:

```text
kind
name
span
```

Example:

```json
{
  "kind": "named_type",
  "name": "Int",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 3,
      "line": 1,
      "column": 4
    }
  }
}
```

---

# 31. Generic Type

Fields follow the authoritative Core AST.

Preferred Core AST shape:

```text
kind
base
arguments
span
```

Example:

```json
{
  "kind": "generic_type",
  "base": {
    "kind": "named_type",
    "name": "List",
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 4,
        "line": 1,
        "column": 5
      }
    }
  },
  "arguments": [
    {
      "kind": "named_type",
      "name": "Int",
      "span": {
        "start": {
          "offset": 5,
          "line": 1,
          "column": 6
        },
        "end": {
          "offset": 8,
          "line": 1,
          "column": 9
        }
      }
    }
  ],
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 9,
      "line": 1,
      "column": 10
    }
  }
}
```

Nested generic types are represented recursively.

---

# 32. Block

Fields:

```text
kind
statements
span
```

Example:

```json
{
  "kind": "block",
  "statements": [],
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 2,
      "line": 1,
      "column": 3
    }
  }
}
```

Statement order must be preserved.

---

# 33. Binding Declaration

Fields:

```text
kind
binding_kind
name
annotation
initializer
span
```

`binding_kind` is one of:

```text
let
var
```

Example:

```json
{
  "kind": "binding_declaration",
  "binding_kind": "let",
  "name": "x",
  "annotation": null,
  "initializer": {
    "kind": "integer_literal",
    "value": "10",
    "span": {
      "start": {
        "offset": 8,
        "line": 1,
        "column": 9
      },
      "end": {
        "offset": 10,
        "line": 1,
        "column": 11
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 10,
      "line": 1,
      "column": 11
    }
  }
}
```

Typed example:

```json
{
  "kind": "binding_declaration",
  "binding_kind": "var",
  "name": "price",
  "annotation": {
    "kind": "named_type",
    "name": "Decimal",
    "span": {
      "start": {
        "offset": 11,
        "line": 1,
        "column": 12
      },
      "end": {
        "offset": 18,
        "line": 1,
        "column": 19
      }
    }
  },
  "initializer": {
    "kind": "decimal_literal",
    "value": "19.99",
    "span": {
      "start": {
        "offset": 21,
        "line": 1,
        "column": 22
      },
      "end": {
        "offset": 26,
        "line": 1,
        "column": 27
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 26,
      "line": 1,
      "column": 27
    }
  }
}
```

---

# 34. Assignment Statement

Fields:

```text
kind
operator
target
value
span
```

Canonical operator values:

```text
assign
add_assign
subtract_assign
multiply_assign
divide_assign
```

Example:

```json
{
  "kind": "assignment_statement",
  "operator": "assign",
  "target": {
    "kind": "identifier",
    "name": "x",
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 1,
        "line": 1,
        "column": 2
      }
    }
  },
  "value": {
    "kind": "integer_literal",
    "value": "1",
    "span": {
      "start": {
        "offset": 4,
        "line": 1,
        "column": 5
      },
      "end": {
        "offset": 5,
        "line": 1,
        "column": 6
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 5,
      "line": 1,
      "column": 6
    }
  }
}
```

---

# 35. Expression Statement

Fields:

```text
kind
expression
span
```

Example:

```json
{
  "kind": "expression_statement",
  "expression": {
    "kind": "call_expression",
    "callee": {
      "kind": "identifier",
      "name": "run",
      "span": {
        "start": {
          "offset": 0,
          "line": 1,
          "column": 1
        },
        "end": {
          "offset": 3,
          "line": 1,
          "column": 4
        }
      }
    },
    "arguments": [],
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 5,
        "line": 1,
        "column": 6
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 5,
      "line": 1,
      "column": 6
    }
  }
}
```

---

# 36. If Statement

Fields:

```text
kind
condition
then_branch
else_branch
span
```

`else_branch` is required and nullable.

It may contain:

```text
null
block
if_statement
```

Example:

```json
{
  "kind": "if_statement",
  "condition": {
    "kind": "identifier",
    "name": "ready",
    "span": {
      "start": {
        "offset": 3,
        "line": 1,
        "column": 4
      },
      "end": {
        "offset": 8,
        "line": 1,
        "column": 9
      }
    }
  },
  "then_branch": {
    "kind": "block",
    "statements": [],
    "span": {
      "start": {
        "offset": 9,
        "line": 1,
        "column": 10
      },
      "end": {
        "offset": 11,
        "line": 1,
        "column": 12
      }
    }
  },
  "else_branch": null,
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 11,
      "line": 1,
      "column": 12
    }
  }
}
```

Do not flatten `else if` into an array unless the internal AST itself uses that representation.

---

# 37. While Statement

Fields:

```text
kind
condition
body
span
```

Example:

```json
{
  "kind": "while_statement",
  "condition": {
    "kind": "identifier",
    "name": "ready",
    "span": {
      "start": {
        "offset": 6,
        "line": 1,
        "column": 7
      },
      "end": {
        "offset": 11,
        "line": 1,
        "column": 12
      }
    }
  },
  "body": {
    "kind": "block",
    "statements": [],
    "span": {
      "start": {
        "offset": 12,
        "line": 1,
        "column": 13
      },
      "end": {
        "offset": 14,
        "line": 1,
        "column": 15
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 14,
      "line": 1,
      "column": 15
    }
  }
}
```

---

# 38. For Statement

Fields:

```text
kind
name
iterable
body
span
```

Example:

```json
{
  "kind": "for_statement",
  "name": "item",
  "iterable": {
    "kind": "identifier",
    "name": "items",
    "span": {
      "start": {
        "offset": 12,
        "line": 1,
        "column": 13
      },
      "end": {
        "offset": 17,
        "line": 1,
        "column": 18
      }
    }
  },
  "body": {
    "kind": "block",
    "statements": [],
    "span": {
      "start": {
        "offset": 18,
        "line": 1,
        "column": 19
      },
      "end": {
        "offset": 20,
        "line": 1,
        "column": 21
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 20,
      "line": 1,
      "column": 21
    }
  }
}
```

---

# 39. Break Statement

Fields:

```text
kind
span
```

Example:

```json
{
  "kind": "break_statement",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 5,
      "line": 1,
      "column": 6
    }
  }
}
```

---

# 40. Continue Statement

Fields:

```text
kind
span
```

Example:

```json
{
  "kind": "continue_statement",
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 8,
      "line": 1,
      "column": 9
    }
  }
}
```

---

# 41. Return Statement

Fields:

```text
kind
value
span
```

`value` is required and nullable.

Bare return:

```json
{
  "kind": "return_statement",
  "value": null,
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 6,
      "line": 1,
      "column": 7
    }
  }
}
```

Return with value:

```json
{
  "kind": "return_statement",
  "value": {
    "kind": "identifier",
    "name": "x",
    "span": {
      "start": {
        "offset": 7,
        "line": 1,
        "column": 8
      },
      "end": {
        "offset": 8,
        "line": 1,
        "column": 9
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 8,
      "line": 1,
      "column": 9
    }
  }
}
```

---

# 42. Parameter

Fields follow the authoritative internal AST.

Canonical semantic fields:

```text
kind
name
type_annotation
mutable
span
```

Example:

```json
{
  "kind": "parameter",
  "name": "value",
  "type_annotation": {
    "kind": "named_type",
    "name": "Decimal",
    "span": {
      "start": {
        "offset": 24,
        "line": 1,
        "column": 25
      },
      "end": {
        "offset": 31,
        "line": 1,
        "column": 32
      }
    }
  },
  "mutable": true,
  "span": {
    "start": {
      "offset": 13,
      "line": 1,
      "column": 14
    },
    "end": {
      "offset": 31,
      "line": 1,
      "column": 32
    }
  }
}
```

If the internal AST uses another explicit mutability representation, the serializer must map it into this stable external boolean or another specifically documented stable form. For v1, `mutable: boolean` is preferred.

---

# 43. Function Declaration

Fields:

```text
kind
name
parameters
return_type
body
span
```

Example:

```json
{
  "kind": "function_declaration",
  "name": "add",
  "parameters": [
    {
      "kind": "parameter",
      "name": "a",
      "type_annotation": {
        "kind": "named_type",
        "name": "Int",
        "span": {
          "start": {
            "offset": 10,
            "line": 1,
            "column": 11
          },
          "end": {
            "offset": 13,
            "line": 1,
            "column": 14
          }
        }
      },
      "mutable": false,
      "span": {
        "start": {
          "offset": 7,
          "line": 1,
          "column": 8
        },
        "end": {
          "offset": 13,
          "line": 1,
          "column": 14
        }
      }
    }
  ],
  "return_type": {
    "kind": "named_type",
    "name": "Int",
    "span": {
      "start": {
        "offset": 18,
        "line": 1,
        "column": 19
      },
      "end": {
        "offset": 21,
        "line": 1,
        "column": 22
      }
    }
  },
  "body": {
    "kind": "block",
    "statements": [],
    "span": {
      "start": {
        "offset": 22,
        "line": 1,
        "column": 23
      },
      "end": {
        "offset": 24,
        "line": 1,
        "column": 25
      }
    }
  },
  "span": {
    "start": {
      "offset": 0,
      "line": 1,
      "column": 1
    },
    "end": {
      "offset": 24,
      "line": 1,
      "column": 25
    }
  }
}
```

No effect/capability metadata exists in AST JSON v1.

---

# 44. Binding Kind Values

Canonical values:

```text
let
var
```

Any other string is invalid.

---

# 45. Unary Operator Values

Canonical values:

```text
positive
negate
not
```

Any other string is invalid.

---

# 46. Binary Operator Values

Canonical values:

```text
add
subtract
multiply
divide
modulo
power

equal
not_equal
less
less_equal
greater
greater_equal

and
or
```

Any other string is invalid.

---

# 47. Assignment Operator Values

Canonical values:

```text
assign
add_assign
subtract_assign
multiply_assign
divide_assign
```

Any other string is invalid.

---

# 48. Structural Child Constraints

AST JSON v1 validates AST category structure.

Examples:

```text
Program.statements
    must contain Statement nodes

Block.statements
    must contain Statement nodes

BinaryExpression.left
BinaryExpression.right
    must contain Expression nodes

CallExpression.callee
    must contain an Expression node

CallArgument.value
    must contain an Expression node

ListLiteral.elements
    must contain Expression nodes

MapEntry.key
MapEntry.value
    must contain Expression nodes

BindingDeclaration.annotation
    must be null or a TypeExpression node

BindingDeclaration.initializer
    must contain an Expression node

AssignmentStatement.target
AssignmentStatement.value
    must contain Expression nodes structurally

IfStatement.condition
WhileStatement.condition
ForStatement.iterable
    must contain Expression nodes

FunctionDeclaration.return_type
Parameter.type_annotation
    must contain TypeExpression nodes
```

AST JSON structural validation does not replace later semantic validation.

---

# 49. Semantic Validation Deferred

AST JSON v1 does not determine whether a program is semantically legal.

For example, structurally valid AST JSON may still contain:

```text
unresolved identifiers
break outside a loop
return outside a function
type mismatches
invalid function arguments
non-iterable for-loop expressions
unknown type names
wrong generic arity
```

Those are compiler semantic-analysis concerns.

AST JSON validates the integrity of AST structure and public representation.

---

# 50. Deterministic Serialization

The canonical serializer must produce deterministic output for the same AST and serializer options.

Recommended object field ordering:

Top-level:

```text
format
version
program
```

Node:

```text
kind
node-specific fields
span
```

Do not emit:

```text
timestamps
random IDs
memory addresses
unstable dictionary ordering
```

---

# 51. Unicode JSON Output

Canonical string serialization should preserve readable Unicode.

Recommended:

```python
json.dumps(..., ensure_ascii=False)
```

Example:

```json
{
  "kind": "string_literal",
  "value": "বাংলা 你好 👋"
}
```

is preferred over needless ASCII escape sequences.

---

# 52. Round-Trip Guarantee

For every supported AST document:

```text
AST A
  ↓
serialize
  ↓
AST JSON
  ↓
deserialize
  ↓
AST B
```

must satisfy:

```text
AST B == AST A
```

using the internal AST's structural equality semantics.

This includes:

- node kinds
- child ordering
- source spans
- integer precision
- decimal precision
- Unicode strings
- enum/operator values
- nullable fields

---

# 53. Source-to-AST-JSON Round Trip

For valid `.kaj` source supported through Checkpoint 3:

```text
source
  ↓
lexer
  ↓
parser
  ↓
AST A
  ↓
AST JSON
  ↓
AST B
```

must satisfy:

```text
AST A == AST B
```

---

# 54. AST JSON Is Not Source-Text Preservation

AST JSON v1 does not preserve:

- comments
- whitespace
- exact parentheses
- original numeric spelling beyond semantic value
- original string escape spelling
- original token lexemes
- formatting choices

Therefore:

```text
.kaj source → AST JSON → AST
```

is structurally lossless at the AST level, but not necessarily source-text-identical.

A future formatter can produce canonical `.kaj` from the AST.

---

# 55. AST JSON Is Not Compiler IR

AST JSON represents program syntax.

It must not contain compiler/runtime lowering details such as:

```text
basic blocks
SSA values
temporary registers
resolved symbol addresses
machine types
runtime stack slots
provider handles
task runtime state
compiled instructions
```

Those belong to later IR/runtime layers.

---

# 56. AST JSON Is Not an AST Patch Format

AST JSON v1 represents a complete AST document.

It does not define:

```text
insert node
remove node
replace node
move node
stable node IDs
patch preconditions
conflict resolution
```

AST patching is a separate future protocol.

---

# 57. No Stable Node IDs in v1

AST JSON v1 does not add synthetic stable IDs to nodes.

If future structured editing or agent replanning requires stable IDs, that must be designed separately.

Do not add IDs opportunistically.

---

# 58. Security and Trust

AST JSON must be treated as untrusted external input.

Deserializers must never use:

```text
eval
exec
pickle
dynamic import based on JSON
arbitrary class lookup by user string
```

Node kinds must be matched against an explicit allowlist of supported AST node kinds.

Deserialization constructs AST data only.

It does not execute Kaj code.

---

# 59. Validation Errors

Invalid AST JSON should fail with structured errors.

Required error categories:

```text
ASTJSON_INVALID_JSON
ASTJSON_INVALID_DOCUMENT
ASTJSON_UNSUPPORTED_VERSION
ASTJSON_UNKNOWN_NODE_KIND
ASTJSON_MISSING_FIELD
ASTJSON_INVALID_FIELD
ASTJSON_INVALID_ENUM_VALUE
```

Implementation may add more specific error codes.

Do not expose ordinary malformed external input as raw internal exceptions such as:

```text
KeyError
TypeError
AttributeError
AssertionError
```

---

# 60. Error Paths

Where practical, validation errors should identify a JSON field path.

Examples:

```text
$.version
$.program.kind
$.program.statements[0].initializer.value
```

Exact path syntax may vary, but should remain consistent and useful.

Kaj source spans should not be fabricated for invalid JSON fields.

---

# 61. Unsupported Version

Example:

```json
{
  "format": "kaj-ast",
  "version": 2,
  "program": {}
}
```

must produce:

```text
ASTJSON_UNSUPPORTED_VERSION
```

A v1 implementation must not silently reinterpret future versions.

---

# 62. Invalid Document Example

This is invalid:

```json
{
  "format": "kaj-ast",
  "version": 1,
  "program": {
    "kind": "identifier",
    "name": "x",
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 1,
        "line": 1,
        "column": 2
      }
    }
  }
}
```

because top-level `program` must contain a node of kind:

```text
program
```

---

# 63. Invalid Integer Example

Invalid:

```json
{
  "kind": "integer_literal",
  "value": 10,
  "span": {}
}
```

because `value` must be a string.

Invalid:

```json
{
  "kind": "integer_literal",
  "value": "ten",
  "span": {}
}
```

because the string is not a valid integer representation.

---

# 64. Invalid Decimal Example

Invalid:

```json
{
  "kind": "decimal_literal",
  "value": 19.99,
  "span": {}
}
```

because decimal values must be strings.

Invalid:

```json
{
  "kind": "decimal_literal",
  "value": "abc",
  "span": {}
}
```

because it is not a valid decimal representation.

---

# 65. Invalid Enum Example

Invalid:

```json
{
  "kind": "binary_expression",
  "operator": "times",
  "left": {},
  "right": {},
  "span": {}
}
```

because:

```text
times
```

is not a valid v1 binary operator value.

The canonical value is:

```text
multiply
```

---

# 66. Complete Example

Kaj source:

```kaj
let total = price * quantity
```

Representative AST JSON:

```json
{
  "format": "kaj-ast",
  "version": 1,
  "program": {
    "kind": "program",
    "statements": [
      {
        "kind": "binding_declaration",
        "binding_kind": "let",
        "name": "total",
        "annotation": null,
        "initializer": {
          "kind": "binary_expression",
          "operator": "multiply",
          "left": {
            "kind": "identifier",
            "name": "price",
            "span": {
              "start": {
                "offset": 12,
                "line": 1,
                "column": 13
              },
              "end": {
                "offset": 17,
                "line": 1,
                "column": 18
              }
            }
          },
          "right": {
            "kind": "identifier",
            "name": "quantity",
            "span": {
              "start": {
                "offset": 20,
                "line": 1,
                "column": 21
              },
              "end": {
                "offset": 28,
                "line": 1,
                "column": 29
              }
            }
          },
          "span": {
            "start": {
              "offset": 12,
              "line": 1,
              "column": 13
            },
            "end": {
              "offset": 28,
              "line": 1,
              "column": 29
            }
          }
        },
        "span": {
          "start": {
            "offset": 0,
            "line": 1,
            "column": 1
          },
          "end": {
            "offset": 28,
            "line": 1,
            "column": 29
          }
        }
      }
    ],
    "span": {
      "start": {
        "offset": 0,
        "line": 1,
        "column": 1
      },
      "end": {
        "offset": 28,
        "line": 1,
        "column": 29
      }
    }
  }
}
```

Exact offsets in generated examples must match the actual parser-created spans.

---

# 67. JSON Schema

The machine-readable schema for this specification lives at:

```text
schemas/ast/v1.json
```

The schema must validate:

- top-level envelope
- `format`
- `version`
- `program`
- all Core AST v1 node kinds
- required fields
- nullability
- source locations/spans
- integer string representation
- decimal string representation
- enum/operator values
- child arrays and child categories
- strict unknown-field rejection where practical

The schema and this document are two representations of the same public contract.

---

# 68. Source of Truth

For Kaj AST JSON v1:

```text
docs/compiler/ast-json.md
        +
schemas/ast/v1.json
        +
serialization/deserialization implementation
        +
serialization conformance tests
```

must agree.

If they disagree, that inconsistency is a Kaj project bug.

The human-readable specification in this file defines the intended contract.

The schema is the machine-readable contract.

The implementation must satisfy both.

---

# 69. Compatibility Rule

Within AST JSON version 1, do not make breaking changes to:

- node kind strings
- required field names
- enum strings
- numeric representation
- top-level envelope shape
- span representation

without intentionally revising the public format.

A breaking redesign should use a new AST JSON version rather than silently changing v1 semantics.

---

# 70. Checkpoint 4 Conformance Requirements

Checkpoint 4 must demonstrate at least:

```text
AST → JSON → AST structural equality

source → parser → AST → JSON → AST structural equality

arbitrary-precision Int exactness

Decimal exactness

Unicode string preservation

source span preservation

deterministic JSON output

unknown node rejection

unknown field rejection

unsupported version rejection

malformed integer rejection

malformed decimal rejection

invalid enum rejection

schema validation of emitted documents
```

---

# 71. Deferred AST JSON Features

Not part of v1:

```text
AST patch documents
stable node IDs
comments/trivia
lossless source reconstruction
compiler IR
task IR
asset IR
resolved symbols
type-checker annotations
runtime state
capability state
agent planning state
formatting metadata
binary serialization
streaming encoding
```

These require separate specifications.

---

# 72. Mental Model

Remember the separation:

```text
.kaj
    human-readable source

AST
    compiler syntax structure

Kaj AST JSON
    machine-readable interchange form of that AST

IR
    compiler/runtime execution-oriented representation
```

Kaj AST JSON exists to exchange syntax structure safely and deterministically across tools and agents without making JSON the compiler's internal execution model.

---

# 73. Checkpoint 10 Record Nodes

During pre-release AST JSON v1 evolution, Checkpoint 10 adds four syntax-only node kinds:

```text
record_declaration
record_field_declaration
record_construction_expression
record_field_initializer
```

`record_declaration` is a statement with `name` and an ordered `fields` array.
Each `record_field_declaration` contains `name` and `type_annotation`.

`record_construction_expression` is an expression with `type_name` and an ordered `fields`
array. Each `record_field_initializer` contains `name` and `value`.

All four nodes include ordinary v1 source spans, reject unknown fields, and preserve source order.
They contain no type-symbol identity, resolved field mapping, semantic type, or runtime value.

---

# 74. Checkpoint 11 Enum and Match Nodes

Checkpoint 11 extends pre-release AST JSON v1 with these syntax-only kinds:

```text
enum_declaration
enum_variant_declaration
enum_payload_field
enum_construction_expression
enum_constructor_argument
match_statement
match_case
enum_pattern
pattern_binding
```

Enum declarations preserve variant and payload-field source order. An enum construction records
`type_name`, `variant_name`, and `arguments`; `arguments` is `null` for the unit syntax and an
ordered array for constructor-call syntax. Match cases contain an enum pattern and one statement
body, with pattern bindings preserved in source order. All nodes carry standard v1 spans and no
resolved symbols, semantic types, exhaustiveness metadata, or runtime values.

---

# 75. Checkpoint 14 Newtype Declaration

Checkpoint 14 adds the syntax-only `newtype_declaration` statement kind. It contains `name` and
`underlying_type`, where the latter is an existing type-expression node. The node carries the
ordinary v1 source span and contains no nominal type symbol, resolved underlying type, constructor
metadata, or runtime wrapper.

---

# 76. Checkpoint 17 Import Declaration

Checkpoint 17 adds `import_declaration` with a non-empty ordered `path` array of identifier
segments. The syntax node contains no resolved filesystem path, loaded module AST, dependency
graph, semantic namespace, or runtime environment.
