## Acceptance Tests
Arrange, act and assert, in that order, split by a single empty line.
There are no other empty lines, and no arrange/act/assert comments.

    def test_expired_coupon_is_rejected():
        cart = Cart([Book(price=20)])
        coupon = Coupon(expires=YESTERDAY)

        actual = apply_coupon(cart, coupon)

        assert actual == Rejected("expired")

When the input is a simple value, inline it into the call.
Then there is no arrange, and the test is just act and assert.

    def test_unknown_coupon_code_gives_no_discount():
        actual = discount_for("UNKNOWN")

        assert actual == 0

When the whole scenario reads well on a single line, merge all three.

    def test_empty_cart_costs_nothing():
        assert total([]) == 0

## Approval Tests
The test body builds the 'before', then a single empty line, then a single
call to a named `verify...` function.
There are no other empty lines, no comments and no asserts.

    def test_agent_answers_the_question_of_everything():
        session = AgentSession() \
            .asking("What is the answer to life, the universe and everything?") \
            .with_llm_responses(["42"])

        verify_agent(session)

When the 'before' is a simple value, inline it into the verify call.
Then the test is just that call.

    def test_blinker_turns_horizontal():
        verify_next_generation("""
            .#.
            .#.
            .#.
        """)

Name the verifier after the **thing** it verifies, or after the **action** that produces it.
Never name it after one scenario's outcome:

| Test Name (Scenario Outcome) | Bad (the scenario's outcome) | Good (the thing or the action) |
|---|---|---|
| `test_expired_card_declines_order` | `verify_expired_card_declines_order(cart)` | `verify_order(order)` or `verify_checkout(cart)` |
| `test_duplicate_flag_shows_usage_error` | `verify_duplicate_flag_shows_error(cli)` | `verify_cli(cli)` |
| `test_discount_applied_on_checkout` | `verify_discount_applied(cart)` | `verify_order(order)` or `verify_checkout(cart)` |

Start by verifying the thing the action produced.
When the tests keep repeating the same action before the verify, extract both into a verifier named after that action.

    order = checkout(cart)                    verify_checkout(cart)
                                      ->
    verify_order(order)

The verifier runs the action and verifies the printed outcome:

    def verify_agent(session):
        actual = session.run()

        verify(print_conversation(actual))

### State Transitions and Storyboards
When testing state transitions (e.g. before -> action -> after), capture both the before and after states to tell the whole story.

A single verifier or Storyboard can capture the transition:

    def test_archiving_an_active_project():
        project = Project(name="Phoenix", status="active")

        verify_project(project, lambda p: p.archive())

The single `verify_project` captures before, executes the action, captures after, and verifies the printed transition.

When multiple steps or chronological history matter, use a Storyboard:

    def test_order_fulfillment_workflow():
        story = StoryBoard()
        order = Order(items=["Book"])
        story.add_frame(order)

        order.pay()
        story.add_frame(order)

        order.ship()
        story.add_frame(order)

        verify(story)
