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

The `verify...` function performs the action, hands the outcome to the printer,
and verifies what the printer returned.

    def verify_agent(session):
        actual = session.run()

        verify(print_conversation(actual))
