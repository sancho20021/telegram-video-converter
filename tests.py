from main import Converter, RecipeCreator


def test_parse_resolution():
    assert Converter.parse_resolution("1920x1440") == [1920, 1440]


def test_reipe_creator():
    recipe = RecipeCreator().\
        yes().\
        set_input('input').\
        convert_to_vp9().\
        cut().\
        remove_audio().\
        resize(1280, 720).\
        set_output('output').\
        get_recipe()
    expected = ('-y -i input '
                '-c:v libvpx-vp9 -b:v 680K '
                '-ss 00:00:00 -to 00:00:03 '
                '-an '
                '-filter:v scale="512:288" '
                'output')
    assert recipe == expected
