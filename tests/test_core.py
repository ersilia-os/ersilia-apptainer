from ersilia_apptainer.cli import hello

def test_hello():
    assert hello("Ersilia") == "Hello, Ersilia!"