from dendron.blackboard import *

def test_set_entry_new_description():
    bb = Blackboard()
    bb["age"] = 32

    age_entry = bb.get_entry("age")
    assert age_entry.key == "age"
    assert age_entry.description == "Autogenerated entry"
    assert age_entry.type_constructor == int

    bb.set_entry("age", description = "An age")

    new_age_entry = bb.get_entry("age")

    assert new_age_entry.key == "age"
    assert new_age_entry.description == "An age"
    assert new_age_entry.type_constructor == int

def test_set_entry_new_type_constructor():
    bb = Blackboard()
    bb["age"] = 32.0

    age_entry = bb.get_entry("age")
    assert age_entry.key == "age"
    assert age_entry.description == "Autogenerated entry"
    assert age_entry.type_constructor == float

    bb.set_entry("age", type_constructor = int)

    new_age_entry = bb.get_entry("age")

    assert new_age_entry.key == "age"
    assert new_age_entry.description == "Autogenerated entry"
    assert new_age_entry.type_constructor == int

    