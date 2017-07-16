from nose.tools import assert_dict_equal, assert_true
import rise_gen.combat as combat

def setup():
    pass

def teardown():
    pass

def test_fighters():
    results = combat.main({
        'blue': ['fighter'],
        'red': ['fighter'],
        'level': 1,
        'trials': 1,
    })

    # TODO: make this deterministic
    assert_true(results)
    assert_dict_equal(
        results,
        {
            'blue win %': 0,
            'red win %': 0,
            'rounds': 6,
        },
    )

def test_dummy():
    # TODO: test the content of the generated string, which represents a
    # dictionary; for now, we're just testing whether this errors
    combat.run_test('dummy', {
        'level': 20,
        # This is interpreted as one trial
        # TODO: make this make sense
        'trials': 10,
    })

def test_doubling():
    # TODO: test the content of the generated string, which represents a
    # dictionary; for now, we're just testing whether this errors
    combat.run_test('doubling', {
        'blue': ['fighter'],
        'red': ['fighter'],
        # This is interpreted as one trial
        # TODO: make this make sense
        'trials': 2,
    })
