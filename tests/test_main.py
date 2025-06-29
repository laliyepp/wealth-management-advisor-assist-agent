from src.main import main

def test_main(capfd):
    main()
    out, _ = capfd.readouterr()
    assert "Hello, Claude!" in out