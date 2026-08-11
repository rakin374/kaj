# 11. Examples

These examples define intended style. They are not yet a frozen grammar suite.

## 11.1 Hello world

```kaj
print("Hello from Kaj")
```

```bash
kaj hello.kaj
```

## 11.2 Function

```kaj
fn greet(name: String) {
    return "Hello, {name}"
}

print(greet("world"))
```

## 11.3 Type inference

```kaj
let name = "Kaj"
let year = 2026
let price = $825.00
let tax_rate = 6.35%
```

## 11.4 Explicit mutation

```kaj
var attempts = 0

while attempts < 3 {
    attempts += 1
    print(attempts)
}
```

## 11.5 Math

```kaj
let prices = [$120.00, $85.50, $40.00]

let subtotal = sum(prices)
let tax = subtotal * 6.35%
let total = subtotal + tax

print(total)
```

## 11.6 Recursive computation

```kaj
fn fibonacci(n: Int) -> Int {
    if n <= 1 {
        return n
    }

    return fibonacci(n - 1) + fibonacci(n - 2)
}

for n in 1 through 10 {
    print(fibonacci(n))
}
```

## 11.7 Pattern matching

```kaj
match payment_result {
    case Confirmed(receipt) {
        print(receipt.id)
    }

    case Declined(reason) {
        print(reason)
    }

    case Uncertain {
        print("Result needs reconciliation")
    }
}
```

## 11.8 Basic task

```kaj
task research {
    goal {
        "Find three relevant products."
    }

    success {
        products.count >= 3
    }

    step gather {
        ...
    }
}
```

## 11.9 Web research

```kaj
use web

task find_monitor {
    goal {
        "Find strong 27-inch monitors under $300."
    }

    success {
        candidates.count >= 3
        every candidates.price is confirmed
    }

    step research {
        web.open("https://example.com")

        observe web.page as results

        extract candidates
            from results

        let affordable = candidates
            .filter(.price <= $300)

        inform user
            "I found {affordable.count} candidates."
    }
}
```

## 11.10 Housing dues workflow

```kaj
use web

task pay_housing_dues {
    goal {
        "Pay every currently due housing obligation."
    }

    success {
        every obligations.payment is verified
        no unresolved conflicts
        no uncertain payment actions
    }

    step find_notice {
        web.open(gmail)

        let results = web.search("monthly housing dues")

        observe web.page as messages

        find dues_email: Email
            in messages
            where .subject contains "dues"

        require dues_email exists

        inform user
            "I found the housing dues notice."
    }

    step discover_obligations after find_notice {
        extract obligations: List<HousingObligation>
            from dues_email

        require obligations.count > 0

        learn obligations
            from dues_email

        inform user
            "I found {obligations.count} current obligations."
    }

    step choose_account after discover_obligations {
        choose user payment_account
            from available_payment_accounts

        require payment_account is confirmed
    }

    for obligation in obligations {
        step prepare_payment(obligation: HousingObligation)
            after choose_account
        {
            web.open(obligation.payment_url)

            observe web.page as portal

            verify portal.unit == obligation.unit
            verify portal.amount == obligation.amount

            require obligation.unit is confirmed
            require obligation.amount is confirmed
            require payment_account is confirmed

            confirm user
                "Pay {obligation.amount} for {obligation.unit} using {payment_account}?"
        }

        step submit_payment(obligation: HousingObligation)
            after prepare_payment
        {
            web.submit(payment)

            expect {
                confirmation.visible
                confirmation.amount == obligation.amount
                confirmation.unit == obligation.unit
            }

            verify payment

            inform user
                "Payment for {obligation.unit} was confirmed."
        }
    }
}
```

## 11.11 Conflict handling

```kaj
if invoice.amount is conflicted {
    ask user
        "The notice says {invoice.amount.notice} but the portal says {invoice.amount.portal}. Which amount should I use?"
    as amount_resolution
}
```

## 11.12 Human handoff

```kaj
handoff user for sign_in
    on payment_portal
```

## 11.13 Effect error

Invalid:

```kaj
fn calculate_total(items: List<Money<USD>>) {
    web.open("https://example.com")
    return sum(items)
}
```

Expected:

```text
EFFECT_NOT_ALLOWED
```

## 11.14 Robot task

```kaj
use robot
use vision

task clear_table {
    goal {
        "Move every cup from the table to the tray."
    }

    success {
        no Cup is on table
        every moved Cup is in tray
    }

    observe vision.scene as scene

    let cups = vision.locate(Cup, in: scene)
        .filter(.surface == table)

    for cup in cups {
        step move(cup: Vision.Object) {
            let grasp = robot.plan_grasp(cup)

            require grasp.is_safe

            robot.move_to(cup)
            robot.grasp(cup, using: grasp)

            verify robot.holds(cup)

            robot.move_to(tray)
            robot.release(cup)

            observe vision.scene as result
            verify cup is in tray
        }
    }
}
```

## 11.15 Navigation task

```kaj
use navigation
use vision
use robot

task deliver_package(destination: Location) {
    goal {
        "Deliver the package to {destination}."
    }

    success {
        robot.position == destination
        package is at destination
    }

    while robot.position != destination {
        observe vision.scene as surroundings

        let route = navigation.plan(
            from: robot.position,
            to: destination,
            avoiding: surroundings.obstacles
        )

        require route.is_safe

        navigation.follow(route)

        when vision.detects(unexpected_obstacle) {
            navigation.stop()
        }
    }

    robot.release(package)
    verify package is at destination
}
```

## 11.16 Audio task

```kaj
use audio

task enhance_rain {
    observe audio.scene as scene

    let rain = audio.locate(Rain, in: scene)

    audio.increase(rain.intensity, by: 20%)

    expect {
        rain.prominence > scene.rain.prominence
        speech.intelligibility >= 0.9
    }

    verify audio.output
}
```

## 11.17 Recursive task traversal

```kaj
recursive step inspect_category(category: Category)
    depth at most 6
{
    observe category as page

    learn page.products
        from page

    for child in page.subcategories {
        recurse inspect_category(child)
    }
}
```

The exact `recursive step`/depth grammar remains open.

## 11.18 Dynamic JSON boundary

```kaj
let raw: Dynamic = json.parse(response.body)
let product = raw.decode<Product>()

print(product.name)
```

## 11.19 Unit-safe robotics math

```kaj
let distance = 2.5 meters
let speed = 0.5 meters / second
let duration = distance / speed

print(duration)
```

Expected inferred type:

```text
Duration
```
