import sys

import click
import re
import subprocess as sp

from pathlib import Path


# - ресайзнуть до 512 по одной из сторон (по большей)
# - обрезать до трех секунд
# - убрать звуковой поток
# - откодировать в -c:v libvpx-vp9 -b:v 680K (главное чтобы не больше 256КБ итоговый видос)

class RecipeCreator:
    BITRATE = '680K'

    def __init__(self):
        self.options: list[str] = []

    def yes(self):
        self.options.append('-y')
        return self

    def set_input(self, input_file: str):
        self.options.append(f'-i {input_file}')
        return self

    def convert_to_vp9(self):
        self.options.append(f'-c:v libvpx-vp9 -b:v {self.BITRATE}')
        return self

    def cut(self):
        self.options.append(f'-ss 00:00:00 -to 00:00:03')
        return self

    def remove_audio(self):
        self.options.append('-an')
        return self

    def resize(self, input_width: int, input_height: int):
        print(f'width: {input_width}, height: {input_height}')
        if input_width > input_height:
            output_width = 512
            output_height = int((input_height * 512 / input_width) // 2 * 2)
        else:
            output_width = int((input_width * 512 / input_height) // 2 * 2)
            output_height = 512
        self.options.append(f'-filter:v scale="{output_width}:{output_height}"')
        return self

    def set_output(self, output: str):
        self.options.append(output)
        return self

    def get_recipe(self):
        return ' '.join(self.options)


class Converter:
    def __init__(self, ffmpeg: Path, ffprobe: Path, input_path: Path):
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe
        self.input_path = input_path

    @staticmethod
    def parse_resolution(s: str) -> (int, int):
        return [int(x) for x in re.findall(r'(\d+)x(\d+)', s)[0]]

    def get_resolution(self):
        command = (f"{self.ffprobe}"
                   f" -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0"
                   f" {self.input_path}")
        output = sp.run(command, shell=True, capture_output=True).stdout.decode('utf-8')
        return self.parse_resolution(output)

    def convert(self, output_path: Path):
        width, height = self.get_resolution()
        recipe = RecipeCreator(). \
            yes(). \
            set_input(str(self.input_path)). \
            convert_to_vp9(). \
            cut(). \
            remove_audio(). \
            resize(width, height). \
            set_output(str(output_path)). \
            get_recipe()
        command = f"{self.ffmpeg} {recipe}"
        print(f'Command will be run:\n{command}')
        result = sp.run(command, shell=True)
        if result.returncode == 0:
            print(f'Success!!! File saved to {output_path}')
        else:
            print('Video conversion failed!!!', file=sys.stderr)
            print(result.stderr)


def convert(ffmpeg: Path, ffprobe: Path, input: Path, output: Path):
    converter = Converter(ffmpeg, ffprobe, input)
    converter.convert(output)


@click.command()
@click.option('--ffmpeg', type=click.Path(path_type=Path), default=Path('ffmpeg'))
@click.option('--ffprobe', type=click.Path(path_type=Path), default=Path('ffprobe'))
@click.option('--videos', type=click.Path(writable=True, path_type=Path), required=True)
def convert_cli(ffmpeg: Path, ffprobe: Path, videos: Path):
    convert(ffmpeg, ffprobe, Path('~/Desktop/src.MOV'), Path('test.webm'))


if __name__ == '__main__':
    convert_cli()

