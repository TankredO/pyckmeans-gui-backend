import pytest

from pyckmeans_gui_backend.app.modules import file_explorer


def test_basic():
    fe = file_explorer.FileExplorer('.')
    stat = fe.get_file_stats('.')
    print(stat)

    import pprint

    f = fe.get_file('.')
    pprint.pprint(f.as_dict(2))

    # with open('test.json', 'w') as json_f:
    #     json.dump(f.as_dict(2), json_f, indent=2)

    f2_name = 'test.txt'
    with open(f2_name, 'w') as fh:
        fh.write('Hello World!')
    f2 = fe.get_file(f2_name)
    f2.rename('test_new.txt')
    f2.move('test_new_new.txt', file_explorer=fe)
    f2.delete()

    with pytest.raises(RuntimeError):
        fe.get_file('..')

    with pytest.raises(FileNotFoundError):
        fe.get_file('~')
